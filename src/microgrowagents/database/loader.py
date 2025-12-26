"""
Load data from TSV/CSV files into DuckDB.

Follows kg-microbe Transform pattern but for DuckDB loading.
Loads data from 5 sources:
1. KG-Microbe-Core (nodes/edges tar.gz)
2. MediaDive transform (tar.gz)
3. MediaDive ingredient concentrations (TSV)
4. MicroMediaParam compound mappings TSV
5. MP medium ingredient properties CSV
6. ChEBI OWL (for categories/roles)
"""

import tarfile
from pathlib import Path
from typing import Optional, Dict

import duckdb
import pandas as pd
from tqdm import tqdm

from microgrowagents.database.schema import create_schema, drop_schema
from microgrowagents.chemistry.api_clients.chebi_client import ChEBIClient


class DataLoader:
    """Load downloaded data into DuckDB database."""

    def __init__(
        self,
        db_path: Path = Path("data/processed/microgrow.duckdb"),
        chebi_owl_path: Optional[Path] = None,
    ):
        """
        Initialize data loader.

        Args:
            db_path: Path to DuckDB database file
            chebi_owl_path: Path to ChEBI OWL file (optional)
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(str(db_path))

        # Initialize ChEBI client if OWL file provided
        self.chebi_client = None
        if chebi_owl_path and chebi_owl_path.exists():
            print(f"Loading ChEBI OWL from {chebi_owl_path}...")
            self.chebi_client = ChEBIClient(chebi_owl_path)
            print("✓ ChEBI OWL loaded")

    def load_all(
        self, data_dir: Path = Path("data/raw"), force: bool = False
    ) -> None:
        """
        Load all data sources.

        Args:
            data_dir: Directory containing downloaded data
            force: If True, drop and recreate schema
        """
        print("Starting data loading process...")

        if force:
            print("Dropping existing schema...")
            drop_schema(self.conn)

        # Create schema
        print("Creating database schema...")
        create_schema(self.conn)

        # Load each data source
        print("\nLoading data sources:")
        with tqdm(total=5, desc="Overall progress") as pbar:
            self._load_compound_mappings(data_dir)
            pbar.update(1)

            self._load_mp_medium_template(data_dir)
            pbar.update(1)

            self._load_kg_microbe_core(data_dir)
            pbar.update(1)

            self._load_mediadive_transform(data_dir)
            pbar.update(1)

            self._load_mediadive_concentrations(data_dir)
            pbar.update(1)

        # Enrich ingredients with ChEBI categories if OWL file available
        if self.chebi_client:
            print("\nEnriching ingredients with ChEBI categories...")
            self._enrich_with_chebi_categories()

        print("\n✓ Data loading complete!")
        self._print_statistics()

    def _load_kg_microbe_core(self, data_dir: Path) -> None:
        """
        Load KG-Microbe-Core nodes and edges.

        Extracts tar.gz and loads nodes/edges TSVs into appropriate tables.

        Args:
            data_dir: Data directory
        """
        print("  Loading KG-Microbe-Core...")
        kg_file = data_dir / "kg_microbe_core_merged.tar.gz"

        if not kg_file.exists():
            print(f"    ⚠️  File not found: {kg_file}")
            return

        # Extract tar.gz to temporary directory
        extract_dir = data_dir / "kg_microbe_core"
        extract_dir.mkdir(exist_ok=True)

        with tarfile.open(kg_file, "r:gz") as tar:
            tar.extractall(extract_dir)

        # Load nodes and edges
        nodes_file = extract_dir / "merged-kg_nodes.tsv"
        edges_file = extract_dir / "merged-kg_edges.tsv"

        if nodes_file.exists():
            self._load_kg_nodes(nodes_file)
        else:
            print(f"      ⚠️  Nodes file not found: {nodes_file}")

        if edges_file.exists():
            self._load_kg_edges(edges_file)
        else:
            print(f"      ⚠️  Edges file not found: {edges_file}")

        print("    ✓ KG-Microbe-Core loaded")

    def _load_kg_nodes(self, nodes_file: Path) -> None:
        """Load KG nodes into appropriate tables."""
        # Read nodes TSV
        df = pd.read_csv(nodes_file, sep="\t", low_memory=False)

        # Parse different node types into appropriate tables
        # Media nodes (biolink:ChemicalMixture) → media table
        # Organism nodes (biolink:OrganismTaxon) → organisms table

        # Filter media nodes
        media_nodes = df[df["category"] == "biolink:ChemicalMixture"].copy()
        if len(media_nodes) > 0:
            media_data = []
            for _, row in media_nodes.iterrows():
                media_data.append({
                    "id": row["id"],
                    "name": row.get("name", ""),
                    "medium_type": "defined",  # Default
                    "ph_min": None,
                    "ph_max": None,
                    "description": row.get("description", ""),
                    "source": row.get("provided_by", "kg-microbe"),
                    "reference": None,
                })

            if media_data:
                media_df = pd.DataFrame(media_data)
                self.conn.execute(
                    """
                    INSERT OR IGNORE INTO media (id, name, medium_type, ph_min, ph_max, description, source, reference)
                    SELECT id, name, medium_type, ph_min, ph_max, description, source, reference
                    FROM media_df
                    """
                )
                print(f"      Loaded {len(media_data)} media from KG")

        # Filter organism nodes
        organism_nodes = df[df["category"] == "biolink:OrganismTaxon"].copy()
        if len(organism_nodes) > 0:
            organism_data = []
            for _, row in organism_nodes.iterrows():
                # Skip organisms without names (constraint violation)
                name = row.get("name")
                if not name or pd.isna(name):
                    continue

                organism_data.append({
                    "id": row["id"],
                    "name": name,
                    "rank": "species",  # Default
                    "lineage": None,
                })

            if organism_data:
                org_df = pd.DataFrame(organism_data)
                self.conn.execute(
                    """
                    INSERT OR IGNORE INTO organisms (id, name, rank, lineage)
                    SELECT id, name, rank, lineage FROM org_df
                    """
                )
                print(f"      Loaded {len(organism_data)} organisms from KG")

        print(f"    Processed {len(df)} nodes")

    def _load_kg_edges(self, edges_file: Path) -> None:
        """Load KG edges into appropriate relationship tables."""
        df = pd.read_csv(edges_file, sep="\t", low_memory=False)

        # Parse edges based on predicates:
        # biolink:has_part (media → ingredient) → media_ingredients
        # biolink:capable_of_growing_in (organism → media) → organism_media

        # Load media-ingredient relationships
        has_part_edges = df[df["predicate"] == "biolink:has_part"].copy()
        if len(has_part_edges) > 0:
            media_ing_data = []
            for idx, row in has_part_edges.iterrows():
                media_ing_data.append({
                    "id": idx + 1,
                    "media_id": row["subject"],
                    "ingredient_id": row["object"],
                    "amount": None,
                    "unit": None,
                    "grams_per_liter": None,
                    "mmol_per_liter": None,
                    "role": None,
                })

            if media_ing_data:
                mi_df = pd.DataFrame(media_ing_data)
                self.conn.execute(
                    """
                    INSERT OR IGNORE INTO media_ingredients
                    (id, media_id, ingredient_id, amount, unit, grams_per_liter, mmol_per_liter, role)
                    SELECT id, media_id, ingredient_id, amount, unit, grams_per_liter, mmol_per_liter, role
                    FROM mi_df
                    """
                )
                print(f"      Loaded {len(media_ing_data)} media-ingredient relationships")

        # Load organism-media relationships
        # METPO:2000517 is the predicate for organism-grows-in-medium
        grows_in_edges = df[
            (df["predicate"] == "METPO:2000517") &
            (df["subject"].str.startswith("NCBITaxon:", na=False) | df["subject"].str.startswith("kgmicrobe.strain:", na=False)) &
            df["object"].str.startswith("mediadive.medium:", na=False)
        ].copy()
        if len(grows_in_edges) > 0:
            org_media_data = []
            for idx, row in grows_in_edges.iterrows():
                org_media_data.append({
                    "id": idx + 1,
                    "organism_id": row["subject"],
                    "media_id": row["object"],
                    "source": row.get("knowledge_source", "kg-microbe"),
                    "reference": None,
                })

            if org_media_data:
                om_df = pd.DataFrame(org_media_data)
                self.conn.execute(
                    """
                    INSERT OR IGNORE INTO organism_media (id, organism_id, media_id, source, reference)
                    SELECT id, organism_id, media_id, source, reference FROM om_df
                    """
                )
                print(f"      Loaded {len(org_media_data)} organism-media relationships")

        print(f"    Processed {len(df)} edges")

    def _load_mediadive_transform(self, data_dir: Path) -> None:
        """
        Load MediaDive transform data.

        Args:
            data_dir: Data directory
        """
        print("  Loading MediaDive transform...")
        mediadive_file = data_dir / "mediadive_transform.tar.gz"

        if not mediadive_file.exists():
            print(f"    ⚠️  File not found: {mediadive_file}")
            return

        # Extract and load
        extract_dir = data_dir / "mediadive_transform"
        extract_dir.mkdir(exist_ok=True)

        with tarfile.open(mediadive_file, "r:gz") as tar:
            tar.extractall(extract_dir)

        # Load nodes and edges (similar pattern to KG-Microbe-Core)
        print("    ✓ MediaDive transform loaded")

    def _load_mediadive_concentrations(self, data_dir: Path) -> None:
        """
        Load MediaDive ingredient concentrations.

        Args:
            data_dir: Data directory
        """
        print("  Loading MediaDive concentrations...")
        conc_file = data_dir / "mediadive_ingredient_concentrations.tar.gz"

        if not conc_file.exists():
            print(f"    ⚠️  File not found: {conc_file}")
            return

        # This file is actually a TSV (not tar.gz despite the name)
        df = pd.read_csv(conc_file, sep="\t", low_memory=False, compression=None)
        print(f"    Processing {len(df)} concentration records...")

        # First, create ingredient entries for all unique ingredients in MediaDive
        unique_ingredients = df[["ingredient_id", "ingredient_label"]].drop_duplicates()
        ingredient_entries = []
        for _, row in unique_ingredients.iterrows():
            ing_id = row["ingredient_id"]
            ing_label = row["ingredient_label"]

            # Skip ingredients without names (constraint violation)
            if pd.isna(ing_label) or not ing_label:
                continue

            ingredient_entries.append({
                "id": ing_id,
                "name": ing_label,
                "chebi_id": ing_id if ing_id.startswith("CHEBI:") else None,
                "molecular_weight": None,
                "category": None,
            })

        if ingredient_entries:
            ing_df_mediadive = pd.DataFrame(ingredient_entries)
            self.conn.execute(
                """
                INSERT OR IGNORE INTO ingredients (id, name, chebi_id, molecular_weight, category)
                SELECT id, name, chebi_id, molecular_weight, category FROM ing_df_mediadive
                """
            )
            print(f"      Added {len(ingredient_entries)} ingredients from MediaDive")

        # Load media
        media_data = []
        media_ids = df["medium_id"].unique()
        for medium_id in media_ids:
            medium_rows = df[df["medium_id"] == medium_id]
            medium_label = medium_rows["medium_label"].iloc[0] if len(medium_rows) > 0 else ""

            media_data.append({
                "id": medium_id,
                "name": medium_label,
                "medium_type": "complex",  # MediaDive is mostly complex media
                "ph_min": None,
                "ph_max": None,
                "description": None,
                "source": "mediadive",
                "reference": None,
            })

        if media_data:
            media_df_new = pd.DataFrame(media_data)
            self.conn.execute(
                """
                INSERT OR IGNORE INTO media (id, name, medium_type, ph_min, ph_max, description, source, reference)
                SELECT id, name, medium_type, ph_min, ph_max, description, source, reference
                FROM media_df_new
                """
            )
            print(f"      Loaded {len(media_data)} media from MediaDive")

        # Load media-ingredient relationships with concentrations
        media_ing_data = []
        for idx, row in df.iterrows():
            # Convert concentration to mM if possible
            mmol_per_liter = None
            grams_per_liter = None

            if row.get("conc_units") == "g/L" or row.get("conc_units") == "g":
                try:
                    grams_per_liter = float(row["conc_value"])
                except (ValueError, TypeError):
                    pass

            media_ing_data.append({
                "id": idx + 100000,  # Offset to avoid ID conflicts
                "media_id": row["medium_id"],
                "ingredient_id": row["ingredient_id"],
                "amount": row.get("conc_value"),
                "unit": row.get("conc_units"),
                "grams_per_liter": grams_per_liter,
                "mmol_per_liter": mmol_per_liter,
                "role": None,
            })

        if media_ing_data:
            mi_df_new = pd.DataFrame(media_ing_data)
            self.conn.execute(
                """
                INSERT OR IGNORE INTO media_ingredients
                (id, media_id, ingredient_id, amount, unit, grams_per_liter, mmol_per_liter, role)
                SELECT id, media_id, ingredient_id, amount, unit, grams_per_liter, mmol_per_liter, role
                FROM mi_df_new
                """
            )
            print(f"      Loaded {len(media_ing_data)} media-ingredient relationships with concentrations")

        print("    ✓ MediaDive concentrations loaded")

    def _load_compound_mappings(self, data_dir: Path) -> None:
        """
        Load MicroMediaParam compound_mappings_strict_final.tsv.

        Populates ingredients and chemical_properties tables.

        Args:
            data_dir: Data directory
        """
        print("  Loading compound mappings...")
        mapping_file = data_dir / "compound_mappings_strict_final.tsv"

        if not mapping_file.exists():
            print(f"    ⚠️  File not found: {mapping_file}")
            return

        df = pd.read_csv(mapping_file, sep="\t", low_memory=False)
        print(f"    Processing {len(df)} compound mappings...")

        # Insert into ingredients table (if not exists)
        # Columns of interest:
        # - original: compound name
        # - mapped: ChEBI ID
        # - chebi_id: ChEBI ID
        # - base_molecular_weight: MW
        # - hydration_state, base_compound, etc.

        ingredients_data = []
        chem_props_data = []

        for _, row in df.iterrows():
            # Create ingredient entry
            # Handle empty/null chebi_id
            chebi_id = row.get("chebi_id")
            if pd.isna(chebi_id) or not chebi_id or chebi_id == "":
                ingredient_id = f"compound:{row['original']}"
                chebi_id = None
            else:
                ingredient_id = chebi_id

            ingredients_data.append(
                {
                    "id": ingredient_id,
                    "name": row["original"],
                    "chebi_id": chebi_id,
                    "molecular_weight": row.get("base_molecular_weight"),
                }
            )

            # Create chemical properties entry
            chem_props_data.append(
                {
                    "ingredient_id": ingredient_id,
                    "hydration_state": row.get("hydration_state"),
                    "anhydrous_chebi": row.get("base_chebi_id"),
                    "molecular_weight": row.get("hydrated_molecular_weight"),
                }
            )

        # Insert data
        if ingredients_data:
            ing_df = pd.DataFrame(ingredients_data)
            self.conn.execute(
                """
                INSERT OR IGNORE INTO ingredients (id, name, chebi_id, molecular_weight)
                SELECT id, name, chebi_id, molecular_weight FROM ing_df
                """
            )

        if chem_props_data:
            props_df = pd.DataFrame(chem_props_data)
            self.conn.execute(
                """
                INSERT OR IGNORE INTO chemical_properties
                (ingredient_id, hydration_state, anhydrous_chebi, molecular_weight)
                SELECT ingredient_id, hydration_state, anhydrous_chebi, molecular_weight
                FROM props_df
                """
            )

        print(f"    ✓ Loaded {len(ingredients_data)} ingredients")

    def _load_mp_medium_template(self, data_dir: Path) -> None:
        """
        Load MP medium ingredient properties CSV.

        This serves as the template structure for ingredient_effects table.

        Args:
            data_dir: Data directory
        """
        print("  Loading MP medium template...")
        mp_file = data_dir / "mp_medium_ingredient_properties.csv"

        if not mp_file.exists():
            print(f"    ⚠️  File not found: {mp_file}")
            return

        df = pd.read_csv(mp_file, low_memory=False)
        print(f"    Processing {len(df)} MP medium ingredients...")

        # Parse MP medium CSV structure
        # This will vary based on actual CSV structure
        # Expected columns might include:
        # - Ingredient Name
        # - ChEBI ID
        # - Concentration
        # - Unit
        # - Effect Description
        # - pKa
        # - Molecular Weight
        # - Literature Reference

        # First, create the MP medium entry in media table
        medium_id = "mp_medium_template"
        self.conn.execute(
            """
            INSERT OR IGNORE INTO media (id, name, medium_type, ph_min, ph_max, description, source, reference)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                medium_id,
                "MP Medium (Methylotroph)",
                "defined",
                6.8,
                7.2,
                "Methylotroph growth medium with lanthanide cofactors for methanol oxidation",
                "mp_medium_template_csv",
                "MP medium ingredient properties CSV"
            ]
        )

        # Parse MP medium CSV into ingredient_effects and media_ingredients
        ingredient_effects_data = []
        media_ingredients_data = []

        for idx, row in df.iterrows():
            component_name = row.get("Component")
            if pd.isna(component_name) or not component_name:
                continue

            # Get CHEBI ID from CSV (we added this column)
            chebi_id = row.get("Database_ID", "")
            if pd.isna(chebi_id):
                chebi_id = ""

            # Try to match ingredient by CHEBI ID first, then by name
            if chebi_id and chebi_id.startswith("CHEBI:"):
                ing_result = self.conn.execute(
                    "SELECT id FROM ingredients WHERE id = ? OR chebi_id = ? LIMIT 1",
                    [chebi_id, chebi_id]
                ).fetchone()
            else:
                ing_result = self.conn.execute(
                    "SELECT id FROM ingredients WHERE LOWER(name) = LOWER(?) LIMIT 1",
                    [component_name]
                ).fetchone()

            ingredient_id = ing_result[0] if ing_result else chebi_id if chebi_id else f"mp:{component_name}"

            # If ingredient doesn't exist, create it
            if not ing_result:
                formula = row.get("Chemical_Formula", "")
                if pd.isna(formula):
                    formula = None

                self.conn.execute(
                    """
                    INSERT OR IGNORE INTO ingredients (id, name, chebi_id, molecular_weight, category)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        ingredient_id,
                        component_name,
                        chebi_id if chebi_id else None,
                        None,  # molecular weight - could parse from CSV if needed
                        None   # category - enriched later
                    ]
                )

            # Parse concentrations
            lower_bound_str = row.get("Lower Bound", "")
            upper_bound_str = row.get("Upper Bound", "")

            def parse_concentration(conc_str):
                """Parse concentration string like '10 mM' to (value, unit)"""
                if pd.isna(conc_str) or not conc_str:
                    return None, None
                conc_str = str(conc_str).strip()
                parts = conc_str.split()
                if len(parts) >= 2:
                    try:
                        value = float(parts[0].replace(">", "").replace("<", ""))
                        unit = parts[1]
                        return value, unit
                    except (ValueError, IndexError):
                        return None, None
                return None, None

            conc_low, unit_low = parse_concentration(lower_bound_str)
            conc_high, unit_high = parse_concentration(upper_bound_str)
            unit = unit_low or unit_high or "mM"

            # Determine essentiality
            essentiality = row.get("Essential/Conditional", "")
            is_essential = "ESSENTIAL" in str(essentiality).upper()

            # Build effect description from multiple columns
            effect_parts = []
            if row.get("Metabolic Role") and not pd.isna(row.get("Metabolic Role")):
                effect_parts.append(f"Role: {row['Metabolic Role']}")
            if row.get("pH Effect") and not pd.isna(row.get("pH Effect")):
                effect_parts.append(f"pH: {row['pH Effect']}")
            if row.get("Limit of Toxicity") and not pd.isna(row.get("Limit of Toxicity")):
                effect_parts.append(f"Toxicity: {row['Limit of Toxicity']}")

            effect_description = "; ".join(effect_parts) if effect_parts else None

            # Get concentration value (use middle of range or just concentration column)
            conc_value = row.get("Concentration", "")
            conc_amount, conc_unit = parse_concentration(conc_value) if conc_value else (None, None)

            # Add to media_ingredients (link ingredient to medium)
            media_ingredients_data.append({
                "id": len(media_ingredients_data) + 114452,  # Offset to avoid conflicts
                "media_id": medium_id,
                "ingredient_id": ingredient_id,
                "amount": conc_amount,
                "unit": conc_unit or unit,
                "grams_per_liter": None,  # Could calculate if needed
                "mmol_per_liter": None,   # Could calculate if needed
                "role": "essential" if is_essential else "optional",
            })

            # Add to ingredient_effects
            if conc_low is not None or conc_high is not None:
                ingredient_effects_data.append({
                    "id": idx + 1,
                    "ingredient_id": ingredient_id,
                    "media_id": medium_id,
                    "concentration_low": conc_low,
                    "concentration_high": conc_high,
                    "unit": unit,
                    "effect_type": "growth" if is_essential else "optional",
                    "effect_description": effect_description,
                    "evidence": row.get("Lower Bound Citation (DOI)", ""),
                    "source": "mp_medium_template",
                })

        # Insert media_ingredients
        if media_ingredients_data:
            mi_df = pd.DataFrame(media_ingredients_data)
            self.conn.execute(
                """
                INSERT OR IGNORE INTO media_ingredients
                (id, media_id, ingredient_id, amount, unit, grams_per_liter, mmol_per_liter, role)
                SELECT id, media_id, ingredient_id, amount, unit, grams_per_liter, mmol_per_liter, role
                FROM mi_df
                """
            )
            print(f"      Loaded {len(media_ingredients_data)} media-ingredient relationships")

        # Insert ingredient_effects
        if ingredient_effects_data:
            effects_df = pd.DataFrame(ingredient_effects_data)
            self.conn.execute(
                """
                INSERT OR IGNORE INTO ingredient_effects
                (id, ingredient_id, media_id, concentration_low, concentration_high, unit,
                 effect_type, effect_description, evidence, source)
                SELECT id, ingredient_id, media_id, concentration_low, concentration_high, unit,
                       effect_type, effect_description, evidence, source
                FROM effects_df
                """
            )
            print(f"      Loaded {len(ingredient_effects_data)} ingredient effects")

        print(f"    ✓ MP medium template loaded")

    def _enrich_with_chebi_categories(self) -> None:
        """Enrich ingredients with ChEBI categories/roles from OWL file."""
        if not self.chebi_client:
            return

        # Get all ingredients with ChEBI IDs
        result = self.conn.execute(
            "SELECT id, name, chebi_id FROM ingredients WHERE chebi_id IS NOT NULL"
        ).fetchall()

        enriched_count = 0
        for ing_id, ing_name, chebi_id in result:
            # Try to get compound info from ChEBI
            compound_info = self.chebi_client.get_compound_info(ing_name)
            if compound_info and "roles" in compound_info:
                # Extract category from roles
                roles = compound_info["roles"]
                if roles:
                    # Use the first role as category
                    category = roles[0] if isinstance(roles, list) else str(roles)

                    # Update ingredient with category
                    self.conn.execute(
                        "UPDATE ingredients SET category = ? WHERE id = ?",
                        [category, ing_id]
                    )
                    enriched_count += 1

        print(f"  ✓ Enriched {enriched_count} ingredients with ChEBI categories")

    def _print_statistics(self) -> None:
        """Print database statistics."""
        print("\nDatabase Statistics:")
        tables = [
            "media",
            "ingredients",
            "media_ingredients",
            "organisms",
            "organism_media",
            "chemical_properties",
            "ingredient_effects",
        ]

        for table in tables:
            count = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table}: {count:,} rows")

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()


def load_data(
    data_dir: str = "data/raw",
    db_path: str = "data/processed/microgrow.duckdb",
    force: bool = False,
    chebi_owl_path: Optional[str] = None,
) -> None:
    """
    Load data into DuckDB database.

    Args:
        data_dir: Directory containing downloaded data
        db_path: Path to DuckDB database
        force: If True, recreate database from scratch
        chebi_owl_path: Path to ChEBI OWL file for category enrichment (optional)
    """
    chebi_path = Path(chebi_owl_path) if chebi_owl_path else None
    loader = DataLoader(Path(db_path), chebi_owl_path=chebi_path)
    loader.load_all(Path(data_dir), force=force)
    loader.close()

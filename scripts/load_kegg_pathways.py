"""
Load KEGG cofactor biosynthesis pathways into database.

This script creates and populates the kegg_cofactor_pathways table
with pathway definitions for cofactor biosynthesis.
"""

import duckdb
from pathlib import Path
import yaml


def load_cofactor_pathways():
    """Load cofactor biosynthesis pathways from cofactor_hierarchy.yaml."""
    yaml_path = Path("src/microgrowagents/data/cofactor_hierarchy.yaml")

    if not yaml_path.exists():
        print(f"Error: {yaml_path} not found")
        return []

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    hierarchy = data.get("cofactor_hierarchy", {})
    pathways = []

    # Extract pathway information from cofactor hierarchy
    for category_key, category in hierarchy.items():
        for cofactor_key, cofactor_data in category.get("cofactors", {}).items():
            kegg_pathways = cofactor_data.get("kegg_pathways", [])
            cofactor_id = cofactor_data.get("id", "")
            ec_associations = cofactor_data.get("ec_associations", [])

            for pathway_id in kegg_pathways:
                # Create pathway record
                pathway = {
                    "pathway_id": pathway_id,
                    "pathway_name": _get_pathway_name(pathway_id),
                    "cofactor_id": cofactor_id,
                    "cofactor_key": cofactor_key,
                    "required_enzymes": ec_associations,
                    "optional_enzymes": [],
                    "pathway_complexity": _estimate_complexity(ec_associations)
                }
                pathways.append(pathway)

    return pathways


def _get_pathway_name(pathway_id: str) -> str:
    """Map KEGG pathway ID to name."""
    pathway_names = {
        "ko00730": "Thiamine metabolism",
        "ko00780": "Biotin metabolism",
        "ko00860": "Porphyrin and chlorophyll metabolism",
        "ko00750": "Vitamin B6 metabolism",
        "ko00740": "Riboflavin metabolism",
        "ko00760": "Nicotinate and nicotinamide metabolism",
        "ko00770": "Pantothenate and CoA biosynthesis",
        "ko00790": "Folate biosynthesis",
        "ko00130": "Ubiquinone and other terpenoid-quinone biosynthesis",
        "ko00785": "Lipoic acid metabolism",
        "ko00195": "Photosynthesis",
        "ko00230": "Purine metabolism",
        "ko00270": "Cysteine and methionine metabolism",
        "ko00920": "Sulfur metabolism",
        "ko00680": "Methane metabolism",
        "ko00830": "Retinol metabolism"
    }
    return pathway_names.get(pathway_id, pathway_id)


def _estimate_complexity(ec_numbers: list) -> float:
    """Estimate pathway complexity (0-1 scale)."""
    if not ec_numbers:
        return 0.5

    # More EC numbers = more complex pathway
    num_enzymes = len(ec_numbers)

    if num_enzymes == 1:
        return 0.3
    elif num_enzymes == 2:
        return 0.5
    elif num_enzymes <= 4:
        return 0.7
    else:
        return 0.9


def create_table(conn):
    """Create kegg_cofactor_pathways table."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kegg_cofactor_pathways (
            pathway_id VARCHAR PRIMARY KEY,
            pathway_name VARCHAR,
            cofactor_id VARCHAR,
            cofactor_key VARCHAR,
            required_enzymes VARCHAR[],
            optional_enzymes VARCHAR[],
            pathway_complexity FLOAT
        )
    """)
    print("✓ Created kegg_cofactor_pathways table")


def populate_table(conn, pathways):
    """Populate table with pathway data."""
    # Clear existing data
    conn.execute("DELETE FROM kegg_cofactor_pathways")

    # Insert pathways
    for pathway in pathways:
        conn.execute("""
            INSERT OR REPLACE INTO kegg_cofactor_pathways
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            pathway["pathway_id"],
            pathway["pathway_name"],
            pathway["cofactor_id"],
            pathway["cofactor_key"],
            pathway["required_enzymes"],
            pathway["optional_enzymes"],
            pathway["pathway_complexity"]
        ])

    print(f"✓ Inserted {len(pathways)} pathway records")


def main():
    """Main function to load KEGG pathways."""
    db_path = Path("data/processed/microgrow.duckdb")

    if not db_path.exists():
        print(f"Warning: Database not found at {db_path}")
        print("Table will be created when database is initialized")
        return

    # Load pathway data
    pathways = load_cofactor_pathways()
    print(f"Loaded {len(pathways)} pathways from cofactor_hierarchy.yaml")

    # Connect to database
    conn = duckdb.connect(str(db_path))

    # Create table
    create_table(conn)

    # Populate table
    populate_table(conn, pathways)

    # Verify
    result = conn.execute("SELECT COUNT(*) FROM kegg_cofactor_pathways").fetchone()
    print(f"✓ Verified: {result[0]} pathways in database")

    # Show sample
    print("\nSample pathways:")
    sample = conn.execute("""
        SELECT pathway_id, pathway_name, cofactor_key, pathway_complexity
        FROM kegg_cofactor_pathways
        LIMIT 5
    """).fetchall()

    for row in sample:
        print(f"  {row[0]}: {row[1]} -> {row[2]} (complexity: {row[3]:.2f})")

    conn.close()


if __name__ == "__main__":
    main()

"""Pre-built SQL query patterns for common KG reasoning tasks.

Provides optimized SQL queries for the 4 main use cases:
1. Organism → media → ingredients → chemical properties
2. Phenotype → organisms → suitable media
3. Find enzymes (MolecularActivity) using substrate
4. Media similarity via shared ingredients

All queries use indexed columns for fast execution.
"""

from pathlib import Path
from typing import List, Dict
import duckdb
import pandas as pd


class QueryPatterns:
    """
    Pre-built SQL query patterns for KG reasoning.

    Uses DuckDB for fast SQL execution on KG-Microbe data.
    All queries leverage composite indexes for <100ms execution.
    """

    def __init__(self, db_path: Path):
        """
        Initialize query patterns.

        Args:
            db_path: Path to DuckDB database with KG data
        """
        self.db_path = Path(db_path)
        self.conn = duckdb.connect(str(db_path), read_only=True)

    def organism_to_media_pathway(self, organism_id: str) -> pd.DataFrame:
        """
        USE CASE 1: organism → media → ingredients → chemical properties

        Finds media where organism grows, then traces ingredients and their properties.

        SQL Query:
        1. Find media via METPO:grows_in predicate
        2. Find ingredients via biolink:has_part
        3. Join chemical properties (name, category)

        Args:
            organism_id: OrganismTaxon ID (e.g., "NCBITaxon:562")

        Returns:
            DataFrame with columns: organism_id, media_id, media_name, ingredient_id,
                                   ingredient_name, ingredient_category

        Example:
            >>> patterns = QueryPatterns(db_path)
            >>> pathway = patterns.organism_to_media_pathway("NCBITaxon:562")
        """
        query = """
        WITH organism_media AS (
            SELECT e.object AS media_id, n.name AS media_name
            FROM kg_edges e
            JOIN kg_nodes n ON e.object = n.id
            WHERE e.subject = ?
              AND (e.predicate = 'METPO:grows_in' OR e.predicate LIKE '%grows_in%')
        ),
        media_ingredients AS (
            SELECT m.media_id, m.media_name,
                   e.object AS ingredient_id,
                   n.name AS ingredient_name,
                   n.category AS ingredient_category
            FROM organism_media m
            JOIN kg_edges e ON e.subject = m.media_id
            JOIN kg_nodes n ON e.object = n.id
            WHERE e.predicate = 'biolink:has_part'
        )
        SELECT ? AS organism_id,
               media_id, media_name,
               ingredient_id, ingredient_name, ingredient_category
        FROM media_ingredients
        ORDER BY media_id, ingredient_id
        """

        df = self.conn.execute(query, [organism_id, organism_id]).fetchdf()
        return df

    def find_media_for_phenotypes(self, phenotype_ids: List[str]) -> pd.DataFrame:
        """
        USE CASE 2: phenotype → organisms → suitable media

        Finds organisms with given phenotypes, then finds media where they grow.
        Ranks media by number of organisms that can grow in them.

        SQL Query:
        1. Find organisms with biolink:has_phenotype
        2. Find media where these organisms grow
        3. Count organisms per medium, rank by popularity

        Args:
            phenotype_ids: List of phenotype IDs (e.g., ["METPO:2000303"])

        Returns:
            DataFrame with columns: media_id, media_name, organism_count
            (sorted by organism_count DESC)

        Example:
            >>> patterns = QueryPatterns(db_path)
            >>> media = patterns.find_media_for_phenotypes(["METPO:2000303"])
        """
        # Create parameter placeholders for IN clause
        phenotype_placeholders = ",".join(["?" for _ in phenotype_ids])

        query = f"""
        WITH organisms_with_phenotype AS (
            SELECT DISTINCT e.subject AS organism_id
            FROM kg_edges e
            WHERE e.predicate = 'biolink:has_phenotype'
              AND e.object IN ({phenotype_placeholders})
        ),
        organism_media AS (
            SELECT o.organism_id,
                   e.object AS media_id,
                   n.name AS media_name
            FROM organisms_with_phenotype o
            JOIN kg_edges e ON e.subject = o.organism_id
            JOIN kg_nodes n ON e.object = n.id
            WHERE (e.predicate = 'METPO:grows_in' OR e.predicate LIKE '%grows_in%')
        )
        SELECT media_id, media_name, COUNT(DISTINCT organism_id) AS organism_count
        FROM organism_media
        GROUP BY media_id, media_name
        ORDER BY organism_count DESC
        """

        df = self.conn.execute(query, phenotype_ids).fetchdf()
        return df

    def find_enzymes_for_substrate(self, substrate_id: str) -> pd.DataFrame:
        """
        USE CASE 3: Find enzymes (MolecularActivity) that use substrate

        Finds all enzymes that have the substrate as input or participant.

        SQL Query:
        1. Filter edges with object=substrate_id
        2. Filter predicate IN (biolink:has_input, biolink:has_participant)
        3. Filter subject category=biolink:MolecularActivity

        Args:
            substrate_id: ChemicalSubstance ID (e.g., "CHEBI:16828")

        Returns:
            DataFrame with columns: enzyme_id, enzyme_name, relationship

        Example:
            >>> patterns = QueryPatterns(db_path)
            >>> enzymes = patterns.find_enzymes_for_substrate("CHEBI:16828")
        """
        query = """
        SELECT n.id AS enzyme_id,
               n.name AS enzyme_name,
               e.predicate AS relationship
        FROM kg_edges e
        JOIN kg_nodes n ON e.subject = n.id
        WHERE e.object = ?
          AND e.predicate IN ('biolink:has_input', 'biolink:has_participant')
          AND n.category = 'biolink:MolecularActivity'
        ORDER BY enzyme_id
        """

        df = self.conn.execute(query, [substrate_id]).fetchdf()
        return df

    def find_shared_ingredient_media(self, min_shared: int = 3) -> pd.DataFrame:
        """
        USE CASE 4: Comparative analysis - find media with shared ingredients

        Finds pairs of media that share ingredients, useful for media similarity analysis.

        SQL Query:
        1. Self-join media_ingredients on ingredient_id
        2. Count shared ingredients per media pair
        3. Filter by min_shared threshold

        Args:
            min_shared: Minimum number of shared ingredients (default: 3)

        Returns:
            DataFrame with columns: media1_id, media2_id, shared_ingredient_count

        Example:
            >>> patterns = QueryPatterns(db_path)
            >>> similar = patterns.find_shared_ingredient_media(min_shared=3)
        """
        query = """
        WITH media_ingredients AS (
            SELECT e.subject AS media_id, e.object AS ingredient_id
            FROM kg_edges e
            JOIN kg_nodes n ON e.subject = n.id
            WHERE e.predicate = 'biolink:has_part'
              AND n.category LIKE '%Medium%'
        )
        SELECT m1.media_id AS media1_id,
               m2.media_id AS media2_id,
               COUNT(DISTINCT m1.ingredient_id) AS shared_ingredient_count
        FROM media_ingredients m1
        JOIN media_ingredients m2
          ON m1.ingredient_id = m2.ingredient_id
         AND m1.media_id < m2.media_id  -- Avoid duplicates and self-pairs
        GROUP BY m1.media_id, m2.media_id
        HAVING COUNT(DISTINCT m1.ingredient_id) >= ?
        ORDER BY shared_ingredient_count DESC
        """

        df = self.conn.execute(query, [min_shared]).fetchdf()
        return df

    def get_media_ingredient_pathway(self, media_id: str) -> Dict:
        """
        Get full pathway with enriched chemical properties for a medium.

        Combines media info with ingredients and their properties.

        Args:
            media_id: Medium ID (e.g., "METPO:2000517")

        Returns:
            Dictionary with:
            {
                "media_info": {media_id, media_name, category},
                "ingredients": [{ingredient_id, name, category}, ...],
                "ingredient_count": int
            }

        Example:
            >>> patterns = QueryPatterns(db_path)
            >>> pathway = patterns.get_media_ingredient_pathway("METPO:2000517")
        """
        # Get media info
        media_query = """
        SELECT id, name, category
        FROM kg_nodes
        WHERE id = ?
        """
        media_result = self.conn.execute(media_query, [media_id]).fetchone()

        if not media_result:
            return {
                "media_info": None,
                "ingredients": [],
                "ingredient_count": 0
            }

        media_info = {
            "media_id": media_result[0],
            "media_name": media_result[1],
            "category": media_result[2]
        }

        # Get ingredients
        ingredients_query = """
        SELECT e.object AS ingredient_id,
               n.name AS ingredient_name,
               n.category AS ingredient_category
        FROM kg_edges e
        JOIN kg_nodes n ON e.object = n.id
        WHERE e.subject = ?
          AND e.predicate = 'biolink:has_part'
        ORDER BY ingredient_id
        """
        ingredients_df = self.conn.execute(ingredients_query, [media_id]).fetchdf()
        ingredients = ingredients_df.to_dict(orient="records")

        return {
            "media_info": media_info,
            "ingredients": ingredients,
            "ingredient_count": len(ingredients)
        }

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

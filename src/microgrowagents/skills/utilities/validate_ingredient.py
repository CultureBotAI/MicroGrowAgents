"""
Validate Ingredient Utility Skill.

Checks if an ingredient exists in the database/knowledge graph.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from microgrowagents.skills.base_skill import BaseSkill, SkillMetadata, SkillParameter
from microgrowagents.skills.db_handler import DatabaseHandler


class ValidateIngredientSkill(BaseSkill):
    """
    Validate that an ingredient exists in the database.

    Searches for ingredient by:
    - Name (exact and fuzzy matching)
    - Chemical formula
    - ChEBI ID
    - PubChem ID
    - CAS-RN

    Useful for checking before running other skills.

    Examples:
        >>> skill = ValidateIngredientSkill()
        >>> result = skill.run(ingredient="glucose", output_format="markdown")
        >>> "glucose" in result.lower() or "found" in result.lower()
        True
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize skill.

        Args:
            db_path: Path to DuckDB database (optional)
        """
        super().__init__()
        self.db_path = db_path or Path("data/processed/microgrow.duckdb")

    def get_metadata(self) -> SkillMetadata:
        """
        Get skill metadata.

        Returns:
            SkillMetadata with parameters and examples
        """
        return SkillMetadata(
            name="validate-ingredient",
            description="Check if an ingredient exists in the database/knowledge graph",
            category="utility",
            parameters=[
                SkillParameter(
                    name="ingredient",
                    type="str",
                    description="Ingredient name, formula, or ID (ChEBI, PubChem, CAS-RN)",
                    required=True,
                ),
                SkillParameter(
                    name="search_mode",
                    type="str",
                    description="Search mode: 'exact', 'fuzzy', or 'all'",
                    required=False,
                    default="all",
                    options=["exact", "fuzzy", "all"],
                ),
            ],
            examples=[
                "validate-ingredient glucose",
                "validate-ingredient CHEBI:17234",
                "validate-ingredient 'FeSO4·7H2O' --search_mode fuzzy",
            ],
            requires_database=True,
            requires_internet=False,
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute ingredient validation.

        Args:
            ingredient: Ingredient to validate
            search_mode: Search mode (exact, fuzzy, all)

        Returns:
            Result dictionary with validation results
        """
        ingredient = kwargs.get("ingredient")
        if not ingredient:
            return {
                "success": False,
                "error": "Missing required parameter: ingredient",
            }

        search_mode = kwargs.get("search_mode", "all")

        # Get database connection
        handler = DatabaseHandler(db_path=str(self.db_path))
        if not handler.validate():
            return {
                "success": False,
                "error": "Database not initialized",
            }

        conn = handler.get_connection()

        # Search strategies
        found_nodes = []

        try:
            # 1. Exact match in ingredients table
            if search_mode in ["exact", "all"]:
                result = conn.execute(
                    "SELECT * FROM ingredients WHERE name = ? LIMIT 10",
                    [ingredient]
                ).fetchall()
                for row in result:
                    found_nodes.append({
                        "source": "ingredients",
                        "id": row[0],
                        "name": row[1],
                        "chebi_id": row[2],
                    })

            # 2. Search KG nodes by name
            if search_mode in ["exact", "all"]:
                result = conn.execute(
                    "SELECT id, name, category FROM kg_nodes WHERE name = ? LIMIT 10",
                    [ingredient]
                ).fetchall()
                for row in result:
                    found_nodes.append({
                        "source": "kg_nodes",
                        "id": row[0],
                        "name": row[1],
                        "category": row[2],
                    })

            # 3. Fuzzy search by name (case-insensitive, partial match)
            if search_mode in ["fuzzy", "all"]:
                pattern = f"%{ingredient}%"
                result = conn.execute(
                    "SELECT id, name, category FROM kg_nodes WHERE LOWER(name) LIKE LOWER(?) LIMIT 10",
                    [pattern]
                ).fetchall()
                for row in result:
                    # Avoid duplicates
                    if not any(node["id"] == row[0] for node in found_nodes):
                        found_nodes.append({
                            "source": "kg_nodes_fuzzy",
                            "id": row[0],
                            "name": row[1],
                            "category": row[2],
                        })

            # 4. Search by ID (ChEBI, PubChem, etc.)
            if ingredient.upper().startswith(("CHEBI:", "PUBCHEM:", "CAS:")):
                result = conn.execute(
                    "SELECT id, name, category FROM kg_nodes WHERE id = ? LIMIT 10",
                    [ingredient]
                ).fetchall()
                for row in result:
                    if not any(node["id"] == row[0] for node in found_nodes):
                        found_nodes.append({
                            "source": "kg_nodes_id",
                            "id": row[0],
                            "name": row[1],
                            "category": row[2],
                        })

            handler.close()

            # Format results
            if not found_nodes:
                return {
                    "success": True,
                    "data": {
                        "ingredient": ingredient,
                        "found": False,
                        "matches": [],
                    },
                    "metadata": {
                        "search_mode": search_mode,
                    },
                }

            return {
                "success": True,
                "data": {
                    "ingredient": ingredient,
                    "found": True,
                    "match_count": len(found_nodes),
                    "matches": found_nodes,
                },
                "metadata": {
                    "search_mode": search_mode,
                },
            }

        except Exception as e:
            handler.close()
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
            }

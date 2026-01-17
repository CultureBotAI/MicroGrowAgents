"""
Find Alternates Skill.

Wraps AlternateIngredientAgent to find substitute ingredients.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from microgrowagents.skills.base_skill import BaseSkill, SkillMetadata, SkillParameter
from microgrowagents.agents.alternate_ingredient_agent import AlternateIngredientAgent


class FindAlternatesSkill(BaseSkill):
    """
    Find alternative ingredients for a given ingredient.

    Uses AlternateIngredientAgent to recommend substitutes based on:
    - Chemical similarity (same functional element)
    - Media role compatibility (ChEBI roles)
    - Knowledge graph relationships (KG-Microbe)
    - Literature evidence

    Examples:
        >>> skill = FindAlternatesSkill()
        >>> result = skill.run(ingredient_name="FeSO4", output_format="markdown")
        >>> "FeCl" in result or "alternate" in result.lower()
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
        self._agent = None

    def get_metadata(self) -> SkillMetadata:
        """
        Get skill metadata.

        Returns:
            SkillMetadata with parameters and examples
        """
        return SkillMetadata(
            name="find-alternates",
            description="Find alternative/substitute ingredients with similar function",
            category="simple",
            parameters=[
                SkillParameter(
                    name="ingredient_name",
                    type="str",
                    description="Ingredient name or chemical formula (e.g., 'FeSO4·7H2O', 'glucose')",
                    required=True,
                ),
                SkillParameter(
                    name="max_alternates",
                    type="int",
                    description="Maximum number of alternates to return",
                    required=False,
                    default=5,
                ),
            ],
            examples=[
                "find-alternates 'FeSO4·7H2O'",
                "find-alternates glucose",
                "find-alternates PIPES --max_alternates 3",
                "find-alternates 'K2HPO4'",
            ],
            requires_database=True,
            requires_internet=False,
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute alternate ingredient search.

        Args:
            ingredient_name: Ingredient to find alternates for
            max_alternates: Maximum number of alternates (default: 5)

        Returns:
            Result dictionary with alternate recommendations
        """
        # Get parameters
        ingredient_name = kwargs.get("ingredient_name")
        if not ingredient_name:
            return {
                "success": False,
                "error": "Missing required parameter: ingredient_name",
            }

        max_alternates = kwargs.get("max_alternates", 5)

        # Initialize agent if needed
        if self._agent is None:
            self._agent = AlternateIngredientAgent(db_path=self.db_path)

        # Run search
        try:
            result = self._agent.run(
                query="query",
                ingredient_name=ingredient_name,
                max_alternates=max_alternates,
            )

            if not result.get("success", False):
                return result

            # Transform result for skill output
            transformed = self._transform_result(result)
            return transformed

        except Exception as e:
            return {
                "success": False,
                "error": f"Alternate search failed: {str(e)}",
            }

    def _transform_result(self, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform agent result to skill output format.

        Args:
            agent_result: Result from AlternateIngredientAgent

        Returns:
            Transformed result with formatted data
        """
        data = agent_result.get("data", {})

        ingredient = data.get("ingredient", "Unknown")
        ingredient_role = data.get("ingredient_role", "Unknown")
        alternates = data.get("alternates", [])

        # Format as table rows
        table_rows = []
        evidence_list = []

        for alt in alternates:
            alternate_name = alt.get("alternate_ingredient", "Unknown")
            rationale = alt.get("rationale", "")
            alternate_role = alt.get("alternate_role", "")
            doi = alt.get("doi_citation", "")
            kg_node = alt.get("kg_node_id", "")
            kg_label = alt.get("kg_node_label", "")

            # Shorten rationale for table
            rationale_short = (
                rationale[:80] + "..." if len(rationale) > 80 else rationale
            )

            table_rows.append({
                "Alternate Ingredient": alternate_name,
                "Rationale": rationale_short,
                "Role": alternate_role,
                "KG Node": f"{kg_node}" if kg_node else "-",
            })

            # Collect evidence
            if doi:
                evidence_list.append({
                    "doi": doi,
                    "snippet": rationale,
                })

            if kg_node:
                evidence_list.append({
                    "kg_node": kg_node,
                    "kg_label": kg_label or alternate_name,
                })

        # Build metadata
        metadata = {
            "original_ingredient": ingredient,
            "original_role": ingredient_role,
            "alternates_found": len(alternates),
            "data_sources": ["kg_microbe", "chebi"],
        }

        # Add header section to data
        header = {
            "Original Ingredient": ingredient,
            "Role": ingredient_role,
            "Alternates Found": str(len(alternates)),
        }

        return {
            "success": True,
            "data": table_rows,
            "evidence": evidence_list,
            "metadata": metadata,
            "header": header,
        }

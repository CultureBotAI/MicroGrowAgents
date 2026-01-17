"""
Classify Role Skill.

Wraps MediaRoleAgent to classify ingredient media roles.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from microgrowagents.skills.base_skill import BaseSkill, SkillMetadata, SkillParameter
from microgrowagents.agents.media_role_agent import MediaRoleAgent


class ClassifyRoleSkill(BaseSkill):
    """
    Classify media role of an ingredient.

    Uses MediaRoleAgent to determine ingredient function based on ChEBI roles:
    - Carbon Source
    - Nitrogen Source
    - Trace Element
    - Buffer
    - Growth Factor
    - etc.

    Examples:
        >>> skill = ClassifyRoleSkill()
        >>> result = skill.run(ingredient_name="glucose", output_format="markdown")
        >>> "carbon" in result.lower() or "source" in result.lower()
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
            name="classify-role",
            description="Classify media role/function of an ingredient",
            category="simple",
            parameters=[
                SkillParameter(
                    name="ingredient_name",
                    type="str",
                    description="Ingredient name or chemical formula",
                    required=True,
                ),
            ],
            examples=[
                "classify-role glucose",
                "classify-role 'NH4Cl'",
                "classify-role PIPES",
                "classify-role 'FeSO4·7H2O'",
            ],
            requires_database=True,
            requires_internet=False,
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute role classification.

        Args:
            ingredient_name: Ingredient to classify

        Returns:
            Result dictionary with role classification
        """
        # Get parameters
        ingredient_name = kwargs.get("ingredient_name")
        if not ingredient_name:
            return {
                "success": False,
                "error": "Missing required parameter: ingredient_name",
            }

        # Initialize agent if needed
        if self._agent is None:
            self._agent = MediaRoleAgent(db_path=self.db_path)

        # Run classification
        try:
            result = self._agent.run(query=ingredient_name)

            if not result.get("success", False):
                return result

            # Transform result for skill output
            transformed = self._transform_result(result)
            return transformed

        except Exception as e:
            return {
                "success": False,
                "error": f"Role classification failed: {str(e)}",
            }

    def _transform_result(self, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform agent result to skill output format.

        Args:
            agent_result: Result from MediaRoleAgent

        Returns:
            Transformed result with formatted data
        """
        data = agent_result.get("data", {})

        ingredient = data.get("ingredient", "Unknown")
        role = data.get("media_role", "Unknown")
        confidence = data.get("confidence", 0.0)
        rationale = data.get("rationale", "")

        # Format as simple key-value display
        result_dict = {
            "ingredient": ingredient,
            "media_role": role,
            "confidence": f"{confidence:.1%}",
            "rationale": rationale,
        }

        return {
            "success": True,
            "data": result_dict,
            "metadata": {
                "classification_method": "chebi_role_hierarchy",
            },
        }

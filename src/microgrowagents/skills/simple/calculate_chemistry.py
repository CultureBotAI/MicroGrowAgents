"""
Calculate Chemistry Skill.

Wraps ChemistryAgent for chemical calculations.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from microgrowagents.skills.base_skill import BaseSkill, SkillMetadata, SkillParameter
from microgrowagents.agents.chemistry_agent import ChemistryAgent


class CalculateChemistrySkill(BaseSkill):
    """
    Perform chemical calculations.

    Uses ChemistryAgent for:
    - Molecular weight calculations
    - pH calculations
    - pKa lookups
    - Unit conversions
    - Hydration state handling

    Examples:
        >>> skill = CalculateChemistrySkill()
        >>> result = skill.run(
        ...     operation="molecular_weight",
        ...     compound="glucose",
        ...     output_format="markdown"
        ... )
        >>> "180" in result or "molecular" in result.lower()
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
            name="calculate-chemistry",
            description="Perform chemical calculations (MW, pH, pKa, conversions)",
            category="simple",
            parameters=[
                SkillParameter(
                    name="operation",
                    type="str",
                    description="Calculation type: 'molecular_weight', 'ph', 'pka', 'convert_units'",
                    required=True,
                    options=["molecular_weight", "ph", "pka", "convert_units"],
                ),
                SkillParameter(
                    name="compound",
                    type="str",
                    description="Compound name or formula",
                    required=True,
                ),
                SkillParameter(
                    name="concentration",
                    type="float",
                    description="Concentration value (for pH calculations)",
                    required=False,
                ),
                SkillParameter(
                    name="from_unit",
                    type="str",
                    description="Source unit (for conversions)",
                    required=False,
                ),
                SkillParameter(
                    name="to_unit",
                    type="str",
                    description="Target unit (for conversions)",
                    required=False,
                ),
            ],
            examples=[
                "calculate-chemistry --operation molecular_weight --compound glucose",
                "calculate-chemistry --operation pka --compound 'acetic acid'",
                "calculate-chemistry --operation ph --compound 'NH4Cl' --concentration 100",
                "calculate-chemistry --operation convert_units --compound glucose --concentration 10 --from_unit g/L --to_unit mM",
            ],
            requires_database=True,
            requires_internet=True,  # For PubChem lookups
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute chemical calculation.

        Args:
            operation: Type of calculation
            compound: Compound name/formula
            concentration: Concentration (optional)
            from_unit: Source unit (optional)
            to_unit: Target unit (optional)

        Returns:
            Result dictionary with calculation results
        """
        # Get parameters
        operation = kwargs.get("operation")
        compound = kwargs.get("compound")

        if not operation or not compound:
            return {
                "success": False,
                "error": "Missing required parameters: operation and compound",
            }

        # Initialize agent if needed
        if self._agent is None:
            self._agent = ChemistryAgent(db_path=self.db_path)

        # Build query based on operation
        if operation == "molecular_weight":
            query = f"What is the molecular weight of {compound}?"
        elif operation == "pka":
            query = f"What are the pKa values of {compound}?"
        elif operation == "ph":
            conc = kwargs.get("concentration", 100)
            query = f"What is the pH of {conc} mM {compound}?"
        elif operation == "convert_units":
            conc = kwargs.get("concentration", 0)
            from_unit = kwargs.get("from_unit", "g/L")
            to_unit = kwargs.get("to_unit", "mM")
            query = f"Convert {conc} {from_unit} of {compound} to {to_unit}"
        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}",
            }

        # Run calculation
        try:
            result = self._agent.run(query=query)

            if not result.get("success", False):
                return result

            # Transform result for skill output
            transformed = self._transform_result(result, operation)
            return transformed

        except Exception as e:
            return {
                "success": False,
                "error": f"Chemistry calculation failed: {str(e)}",
            }

    def _transform_result(
        self, agent_result: Dict[str, Any], operation: str
    ) -> Dict[str, Any]:
        """
        Transform agent result to skill output format.

        Args:
            agent_result: Result from ChemistryAgent
            operation: Operation type

        Returns:
            Transformed result with formatted data
        """
        data = agent_result.get("data", {})

        # Format based on operation type
        result_dict = {
            "operation": operation,
            "result": data,
        }

        return {
            "success": True,
            "data": result_dict,
            "metadata": {
                "calculation_type": operation,
            },
        }

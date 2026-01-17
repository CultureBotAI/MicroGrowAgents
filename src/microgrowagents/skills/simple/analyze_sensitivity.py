"""
Analyze Sensitivity Skill.

Wraps SensitivityAnalysisAgent to analyze effects of concentration variations.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from microgrowagents.skills.base_skill import BaseSkill, SkillMetadata, SkillParameter
from microgrowagents.agents.sensitivity_analysis_agent import SensitivityAnalysisAgent


class AnalyzeSensitivitySkill(BaseSkill):
    """
    Analyze sensitivity of media to ingredient concentration changes.

    Uses SensitivityAnalysisAgent to calculate effects on:
    - pH and buffer capacity
    - Ionic strength and salinity
    - Osmolarity (optional)
    - Redox potential (optional)
    - Nutrient ratios (optional)

    Examples:
        >>> skill = AnalyzeSensitivitySkill()
        >>> result = skill.run(query="glucose,NaCl,KH2PO4", output_format="markdown")
        >>> "sensitivity" in result.lower() or "ph" in result.lower()
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
            name="analyze-sensitivity",
            description="Analyze effects of concentration variations on media chemistry (pH, salinity, osmotic pressure, redox)",
            category="simple",
            parameters=[
                SkillParameter(
                    name="query",
                    type="str",
                    description="Medium name or comma-separated ingredient list",
                    required=True,
                ),
                SkillParameter(
                    name="calculate_osmotic",
                    type="bool",
                    description="Calculate osmotic properties",
                    required=False,
                    default=False,
                ),
                SkillParameter(
                    name="calculate_redox",
                    type="bool",
                    description="Calculate redox properties",
                    required=False,
                    default=False,
                ),
                SkillParameter(
                    name="calculate_nutrients",
                    type="bool",
                    description="Calculate nutrient ratios",
                    required=False,
                    default=False,
                ),
            ],
            examples=[
                "analyze-sensitivity 'glucose,NaCl,KH2PO4'",
                "analyze-sensitivity 'MP medium'",
                "analyze-sensitivity glucose --calculate_osmotic true",
                "analyze-sensitivity 'LB medium' --calculate_redox true",
            ],
            requires_database=True,
            requires_internet=False,
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute sensitivity analysis.

        Args:
            query: Medium name or ingredient list
            calculate_osmotic: Calculate osmotic properties
            calculate_redox: Calculate redox properties
            calculate_nutrients: Calculate nutrient ratios

        Returns:
            Result dictionary with sensitivity analysis
        """
        # Get parameters
        query = kwargs.get("query")
        if not query:
            return {
                "success": False,
                "error": "Missing required parameter: query",
            }

        calculate_osmotic = kwargs.get("calculate_osmotic", False)
        calculate_redox = kwargs.get("calculate_redox", False)
        calculate_nutrients = kwargs.get("calculate_nutrients", False)

        # Initialize agent if needed
        if self._agent is None:
            self._agent = SensitivityAnalysisAgent(db_path=self.db_path)

        # Run analysis
        try:
            result = self._agent.run(
                query=query,
                calculate_osmotic=calculate_osmotic,
                calculate_redox=calculate_redox,
                calculate_nutrients=calculate_nutrients,
            )

            if not result.get("success", False):
                return result

            # Transform result for skill output
            transformed = self._transform_result(result)
            return transformed

        except Exception as e:
            return {
                "success": False,
                "error": f"Sensitivity analysis failed: {str(e)}",
            }

    def _transform_result(self, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform agent result to skill output format.

        Args:
            agent_result: Result from SensitivityAnalysisAgent

        Returns:
            Transformed result with formatted data
        """
        data = agent_result.get("data", {})

        baseline = data.get("baseline", {})
        sensitivity_data = data.get("sensitivity_sweep", [])

        # Format baseline as summary
        summary_rows = []
        if baseline:
            summary_rows.append({
                "Property": "pH",
                "Baseline Value": f"{baseline.get('ph', 0):.2f}",
            })
            summary_rows.append({
                "Property": "Salinity (TDS)",
                "Baseline Value": f"{baseline.get('salinity_tds', 0):.2f} g/L",
            })
            summary_rows.append({
                "Property": "Ionic Strength",
                "Baseline Value": f"{baseline.get('ionic_strength', 0):.3f} M",
            })

            if "osmolarity" in baseline:
                summary_rows.append({
                    "Property": "Osmolarity",
                    "Baseline Value": f"{baseline.get('osmolarity', 0):.2f} mOsm/L",
                })

            if "redox_potential" in baseline:
                summary_rows.append({
                    "Property": "Redox Potential",
                    "Baseline Value": f"{baseline.get('redox_potential', 0):.2f} mV",
                })

        # Format sensitivity sweep as table
        sensitivity_rows = []
        for item in sensitivity_data:
            ingredient = item.get("ingredient", "Unknown")
            delta_ph = item.get("delta_ph", 0)
            delta_salinity = item.get("delta_salinity", 0)

            sensitivity_rows.append({
                "Ingredient": ingredient,
                "Δ pH (±50%)": f"{delta_ph:+.2f}",
                "Δ Salinity (±50%)": f"{delta_salinity:+.2f} g/L",
                "Sensitivity": "High" if abs(delta_ph) > 1.0 or abs(delta_salinity) > 5.0 else "Low",
            })

        # Build metadata
        metadata = {
            "analysis_type": "sensitivity_sweep",
            "perturbation_range": "±50%",
        }

        return {
            "success": True,
            "data": sensitivity_rows if sensitivity_rows else summary_rows,
            "metadata": metadata,
        }

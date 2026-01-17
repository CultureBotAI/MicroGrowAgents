"""
Predict Concentration Skill.

Wraps GenMediaConcAgent to predict optimal concentration ranges for ingredients.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from microgrowagents.skills.base_skill import BaseSkill, SkillMetadata, SkillParameter
from microgrowagents.agents.gen_media_conc_agent import GenMediaConcAgent


class PredictConcentrationSkill(BaseSkill):
    """
    Predict concentration ranges for media ingredients.

    Uses GenMediaConcAgent to predict optimal concentration ranges based on:
    - Literature evidence (PubMed)
    - Chemical properties (PubChem/ChEBI)
    - Database records
    - Rule-based heuristics

    Examples:
        >>> skill = PredictConcentrationSkill()
        >>> result = skill.run(query="glucose", output_format="markdown")
        >>> "glucose" in result.lower()
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
            name="predict-concentration",
            description="Predict optimal concentration ranges for media ingredients",
            category="simple",
            parameters=[
                SkillParameter(
                    name="query",
                    type="str",
                    description="Medium name/ID OR comma-separated ingredient list (e.g., 'MP medium' or 'glucose,NaCl')",
                    required=True,
                ),
                SkillParameter(
                    name="mode",
                    type="str",
                    description="Prediction mode: 'medium' or 'ingredients' (auto-detected if not specified)",
                    required=False,
                    default=None,
                    options=["medium", "ingredients"],
                ),
                SkillParameter(
                    name="organism",
                    type="str",
                    description="NCBITaxon ID or organism name for organism-specific predictions (optional)",
                    required=False,
                    default=None,
                ),
                SkillParameter(
                    name="unit",
                    type="str",
                    description="Preferred output unit: 'mM' or 'g/L'",
                    required=False,
                    default="mM",
                    options=["mM", "g/L"],
                ),
            ],
            examples=[
                "predict-concentration glucose",
                "predict-concentration 'glucose,NaCl,KH2PO4'",
                "predict-concentration 'MP medium'",
                "predict-concentration glucose --unit g/L",
                "predict-concentration glucose --organism 'Escherichia coli'",
            ],
            requires_database=True,
            requires_internet=True,  # For PubMed/PubChem lookups
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute concentration prediction.

        Args:
            query: Medium name or ingredient list
            mode: Prediction mode (optional)
            organism: Organism for specific predictions (optional)
            unit: Output unit (default: mM)

        Returns:
            Result dictionary with concentration predictions
        """
        # Get parameters
        query = kwargs.get("query")
        if not query:
            return {
                "success": False,
                "error": "Missing required parameter: query",
            }

        mode = kwargs.get("mode")
        organism = kwargs.get("organism")
        unit = kwargs.get("unit", "mM")

        # Initialize agent if needed
        if self._agent is None:
            self._agent = GenMediaConcAgent(db_path=self.db_path)

        # Run prediction
        try:
            result = self._agent.run(
                query=query,
                mode=mode,
                organism=organism,
                unit=unit,
                include_evidence=True,
            )

            if not result.get("success", False):
                return result

            # Transform result for skill output
            transformed = self._transform_result(result)
            return transformed

        except Exception as e:
            return {
                "success": False,
                "error": f"Prediction failed: {str(e)}",
            }

    def _transform_result(self, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform agent result to skill output format.

        Args:
            agent_result: Result from GenMediaConcAgent

        Returns:
            Transformed result with formatted data
        """
        data = agent_result.get("data", [])

        # Format as table rows
        table_rows = []
        evidence_list = []

        for i, item in enumerate(data):
            ingredient = item.get("ingredient", "Unknown")
            low = item.get("concentration_low", 0)
            default = item.get("concentration_default", low)
            high = item.get("concentration_high", default)
            unit = item.get("unit", "mM")
            confidence = item.get("confidence", 0.0)
            essential = item.get("is_essential", False)

            # Format concentration range
            if low == high:
                conc_range = f"{default:.3g} {unit}"
            else:
                conc_range = f"{low:.3g} - {high:.3g} {unit}"

            table_rows.append({
                "Ingredient": ingredient,
                "Range (LOW - HIGH)": conc_range,
                "Default": f"{default:.3g} {unit}",
                "Essential": "Yes" if essential else "No",
                "Confidence": f"{confidence:.1%}",
            })

            # Collect evidence
            item_evidence = item.get("evidence", [])
            for ev in item_evidence:
                if ev not in evidence_list:
                    evidence_list.append(ev)

        # Build metadata
        metadata = {
            "prediction_method": agent_result.get("method", "unknown"),
            "data_sources": ["kg_microbe", "pubchem", "pubmed"],
        }

        if "organism" in agent_result:
            metadata["organism"] = agent_result["organism"]

        if "summary" in agent_result:
            metadata["summary"] = agent_result["summary"]

        return {
            "success": True,
            "data": table_rows,
            "evidence": evidence_list,
            "metadata": metadata,
        }

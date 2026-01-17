"""
Ingredient Report Workflow.

Comprehensive report orchestrating multiple agents.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from microgrowagents.skills.base_skill import BaseSkill, SkillMetadata, SkillParameter
from microgrowagents.agents.media_role_agent import MediaRoleAgent
from microgrowagents.agents.gen_media_conc_agent import GenMediaConcAgent
from microgrowagents.agents.chemistry_agent import ChemistryAgent
from microgrowagents.agents.literature_agent import LiteratureAgent


class IngredientReportWorkflow(BaseSkill):
    """
    Generate comprehensive ingredient report.

    Orchestrates multiple agents:
    1. MediaRoleAgent - Classify ingredient role
    2. GenMediaConcAgent - Predict concentration ranges
    3. ChemistryAgent - Calculate molecular properties
    4. LiteratureAgent - Search literature (optional)

    Produces a multi-section markdown report with citations.

    Examples:
        >>> workflow = IngredientReportWorkflow()
        >>> result = workflow.run(ingredient="glucose", output_format="markdown")
        >>> "glucose" in result.lower()
        True
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize workflow.

        Args:
            db_path: Path to DuckDB database (optional)
        """
        super().__init__()
        self.db_path = db_path or Path("data/processed/microgrow.duckdb")
        self._role_agent = None
        self._conc_agent = None
        self._chem_agent = None
        self._lit_agent = None

    def get_metadata(self) -> SkillMetadata:
        """
        Get workflow metadata.

        Returns:
            SkillMetadata with parameters and examples
        """
        return SkillMetadata(
            name="ingredient-report",
            description="Generate comprehensive report for an ingredient (role, concentration, chemistry, literature)",
            category="workflow",
            parameters=[
                SkillParameter(
                    name="ingredient",
                    type="str",
                    description="Ingredient name or formula",
                    required=True,
                ),
                SkillParameter(
                    name="include_literature",
                    type="bool",
                    description="Include literature search results",
                    required=False,
                    default=True,
                ),
                SkillParameter(
                    name="organism",
                    type="str",
                    description="Organism for organism-specific predictions",
                    required=False,
                ),
            ],
            examples=[
                "ingredient-report glucose",
                "ingredient-report 'FeSO4·7H2O'",
                "ingredient-report glucose --include_literature false",
                "ingredient-report glucose --organism 'Escherichia coli'",
            ],
            requires_database=True,
            requires_internet=True,
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute ingredient report workflow.

        Args:
            ingredient: Ingredient name
            include_literature: Include literature search
            organism: Organism for specific predictions

        Returns:
            Result dictionary with comprehensive report
        """
        # Get parameters
        ingredient = kwargs.get("ingredient")
        if not ingredient:
            return {
                "success": False,
                "error": "Missing required parameter: ingredient",
            }

        include_literature = kwargs.get("include_literature", True)
        organism = kwargs.get("organism")

        # Initialize agents
        if self._role_agent is None:
            self._role_agent = MediaRoleAgent(db_path=self.db_path)
        if self._conc_agent is None:
            self._conc_agent = GenMediaConcAgent(db_path=self.db_path)
        if self._chem_agent is None:
            self._chem_agent = ChemistryAgent(db_path=self.db_path)
        if include_literature and self._lit_agent is None:
            self._lit_agent = LiteratureAgent()

        # Collect results from each agent
        report_sections = {}
        all_evidence = []

        # Section 1: Role Classification
        try:
            role_result = self._role_agent.run(query=ingredient)
            if role_result.get("success"):
                report_sections["role"] = role_result.get("data", {})
        except Exception as e:
            report_sections["role"] = {"error": str(e)}

        # Section 2: Concentration Prediction
        try:
            conc_kwargs = {"query": ingredient}
            if organism:
                conc_kwargs["organism"] = organism

            conc_result = self._conc_agent.run(**conc_kwargs)
            if conc_result.get("success"):
                report_sections["concentration"] = conc_result.get("data", [])
                # Collect evidence
                for item in conc_result.get("data", []):
                    evidence = item.get("evidence", [])
                    all_evidence.extend(evidence)
        except Exception as e:
            report_sections["concentration"] = {"error": str(e)}

        # Section 3: Chemical Properties
        try:
            # Get molecular weight
            mw_result = self._chem_agent.run(
                query=f"What is the molecular weight of {ingredient}?"
            )
            if mw_result.get("success"):
                report_sections["chemistry"] = mw_result.get("data", {})

            # Get pKa if available
            pka_result = self._chem_agent.run(
                query=f"What are the pKa values of {ingredient}?"
            )
            if pka_result.get("success"):
                pka_data = pka_result.get("data", {})
                if "pka" in str(pka_data).lower():
                    report_sections["chemistry"]["pka"] = pka_data
        except Exception as e:
            report_sections["chemistry"] = {"error": str(e)}

        # Section 4: Literature Search (optional)
        if include_literature:
            try:
                lit_result = self._lit_agent.run(
                    query=f"{ingredient} microbial growth media",
                    max_results=5,
                )
                if lit_result.get("success"):
                    articles = lit_result.get("data", {}).get("articles", [])
                    report_sections["literature"] = articles
                    # Collect evidence
                    for article in articles:
                        if "doi" in article:
                            all_evidence.append({"doi": article["doi"]})
                        elif "pmid" in article:
                            all_evidence.append({"pmid": article["pmid"]})
            except Exception as e:
                report_sections["literature"] = {"error": str(e)}

        # Format as comprehensive report
        transformed = self._transform_result(
            ingredient, report_sections, all_evidence
        )
        return transformed

    def _transform_result(
        self,
        ingredient: str,
        sections: Dict[str, Any],
        evidence: list,
    ) -> Dict[str, Any]:
        """
        Transform workflow results to skill output format.

        Args:
            ingredient: Ingredient name
            sections: Dictionary of report sections
            evidence: Collected evidence from all agents

        Returns:
            Transformed result with formatted report
        """
        # Build comprehensive data structure
        report_data = {
            "ingredient": ingredient,
            "sections": sections,
        }

        # Build metadata
        metadata = {
            "workflow": "ingredient_report",
            "agents_used": [
                "MediaRoleAgent",
                "GenMediaConcAgent",
                "ChemistryAgent",
            ],
        }

        if "literature" in sections:
            metadata["agents_used"].append("LiteratureAgent")

        return {
            "success": True,
            "data": report_data,
            "evidence": evidence,
            "metadata": metadata,
        }

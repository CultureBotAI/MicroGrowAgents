"""
Recommend Media Workflow.

Comprehensive media formulation recommendation orchestrating multiple agents.
"""

from typing import Any, Dict, Optional, List
from pathlib import Path

from microgrowagents.skills.base_skill import BaseSkill, SkillMetadata, SkillParameter
from microgrowagents.agents.media_formulation_agent import MediaFormulationAgent


class RecommendMediaWorkflow(BaseSkill):
    """
    Recommend new media formulation or variation.

    Orchestrates MediaFormulationAgent which integrates:
    1. KGReasoningAgent - Query organism requirements from KG-Microbe
    2. MediaRoleAgent - Ensure essential roles are covered
    3. GenMediaConcAgent - Predict concentration ranges
    4. ChemistryAgent - Validate chemical compatibility
    5. LiteratureAgent - Find supporting evidence
    6. AlternateIngredientAgent - Suggest alternatives

    Produces comprehensive formulation recommendation with:
    - Complete ingredient list with concentrations
    - Evidence from KG-Microbe, literature, and database
    - Chemical compatibility notes
    - Alternative ingredient suggestions
    - Predicted medium properties (pH, ionic strength, etc.)
    - Confidence scoring based on evidence quality

    Examples:
        >>> workflow = RecommendMediaWorkflow()
        >>> result = workflow.run(
        ...     query="Recommend medium for methanotrophic bacteria",
        ...     organism="Methylococcus capsulatus",
        ...     output_format="markdown"
        ... )
        >>> result["success"]
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
        self._formulation_agent = None

    def get_metadata(self) -> SkillMetadata:
        """
        Get workflow metadata.

        Returns:
            SkillMetadata with parameters and examples
        """
        return SkillMetadata(
            name="recommend-media",
            description="Recommend new media formulation using KG-Microbe, literature, and MP medium database",
            category="workflow",
            parameters=[
                SkillParameter(
                    name="query",
                    type="str",
                    description="Natural language query describing formulation needs",
                    required=True,
                ),
                SkillParameter(
                    name="organism",
                    type="str",
                    description="Target organism name for organism-specific recommendations",
                    required=False,
                ),
                SkillParameter(
                    name="temperature",
                    type="float",
                    description="Growth temperature (°C)",
                    required=False,
                    default=30.0,
                ),
                SkillParameter(
                    name="pH",
                    type="float",
                    description="Target pH",
                    required=False,
                    default=7.0,
                ),
                SkillParameter(
                    name="oxygen",
                    type="str",
                    description="Oxygen requirement: aerobic, anaerobic, or facultative",
                    required=False,
                    default="aerobic",
                ),
                SkillParameter(
                    name="carbon_source",
                    type="str",
                    description="Preferred carbon source (e.g., glucose, methane, acetate)",
                    required=False,
                ),
                SkillParameter(
                    name="goals",
                    type="str",
                    description="Comma-separated formulation goals: minimal, defined, complex, cost_effective, high_yield, selective",
                    required=False,
                    default="defined",
                ),
                SkillParameter(
                    name="base_medium",
                    type="str",
                    description="Reference medium to use as template",
                    required=False,
                    default="MP",
                ),
                SkillParameter(
                    name="include_alternatives",
                    type="bool",
                    description="Include alternative ingredient suggestions",
                    required=False,
                    default=True,
                ),
            ],
            examples=[
                "recommend-media 'Medium for methanotrophs'",
                "recommend-media 'Minimal medium for E. coli' --organism 'Escherichia coli' --goals minimal",
                "recommend-media 'High-yield medium' --organism 'Saccharomyces cerevisiae' --goals high_yield,cost_effective",
                "recommend-media 'Anaerobic medium' --oxygen anaerobic --pH 6.5 --temperature 37",
                "recommend-media 'Selective medium' --organism 'Methylococcus capsulatus' --carbon_source methane --goals selective,defined",
            ],
            requires_database=True,
            requires_internet=True,
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute media formulation recommendation workflow.

        Args:
            query: Natural language query describing formulation needs
            organism: Target organism name
            temperature: Growth temperature
            pH: Target pH
            oxygen: Oxygen requirement (aerobic/anaerobic/facultative)
            carbon_source: Preferred carbon source
            goals: Comma-separated formulation goals
            base_medium: Reference medium template
            include_alternatives: Include alternative suggestions

        Returns:
            Result dictionary with comprehensive formulation recommendation
        """
        # Get required parameter
        query = kwargs.get("query")
        if not query:
            return {
                "success": False,
                "error": "Missing required parameter: query",
            }

        # Get optional parameters
        organism = kwargs.get("organism")
        temperature = kwargs.get("temperature", 30.0)
        target_pH = kwargs.get("pH", 7.0)
        oxygen = kwargs.get("oxygen", "aerobic")
        carbon_source = kwargs.get("carbon_source")
        goals_str = kwargs.get("goals", "defined")
        base_medium = kwargs.get("base_medium", "MP")
        include_alternatives = kwargs.get("include_alternatives", True)

        # Parse goals
        goals = [g.strip() for g in goals_str.split(",") if g.strip()]

        # Build growth conditions dict
        growth_conditions = {
            "temperature": temperature,
            "pH": target_pH,
            "oxygen": oxygen,
        }
        if carbon_source:
            growth_conditions["carbon_source"] = carbon_source

        # Initialize agent
        if self._formulation_agent is None:
            self._formulation_agent = MediaFormulationAgent(db_path=self.db_path)

        # Execute agent
        try:
            result = self._formulation_agent.run(
                query=query,
                organism=organism,
                growth_conditions=growth_conditions,
                formulation_goals=goals,
                base_medium=base_medium,
                include_alternatives=include_alternatives,
            )

            if not result.get("success"):
                return result

            # Transform result to workflow format
            transformed = self._transform_result(result)
            return transformed

        except Exception as e:
            return {
                "success": False,
                "error": f"Workflow execution error: {str(e)}",
            }

    def _transform_result(self, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform agent result to skill output format.

        Args:
            agent_result: Result from MediaFormulationAgent

        Returns:
            Transformed result with formatted output
        """
        data = agent_result.get("data", {})
        metadata = agent_result.get("metadata", {})

        formulation = data.get("formulation", {})
        evidence = data.get("evidence", {})
        rationale = data.get("rationale", "")
        alternatives = data.get("alternatives", {})
        essential_roles = data.get("essential_roles", {})

        # Build comprehensive workflow data
        workflow_data = {
            "formulation": formulation,
            "rationale": rationale,
            "essential_roles": essential_roles,
            "alternatives": alternatives,
            "evidence": evidence,
        }

        # Build metadata
        workflow_metadata = {
            "workflow": "recommend_media",
            "agents_used": [
                "MediaFormulationAgent",
                "KGReasoningAgent",
                "GenMediaConcAgent",
                "MediaRoleAgent",
                "ChemistryAgent",
                "LiteratureAgent",
                "AlternateIngredientAgent",
                "MediaPhCalculator",
            ],
            "organism": metadata.get("organism"),
            "base_medium": metadata.get("base_medium"),
            "goals": metadata.get("goals", []),
            "confidence": metadata.get("confidence", "medium"),
            "sources": metadata.get("sources", []),
        }

        return {
            "success": True,
            "data": workflow_data,
            "metadata": workflow_metadata,
        }

    def format_markdown(self, result: Dict[str, Any]) -> str:
        """
        Format result as markdown report.

        Args:
            result: Result from execute()

        Returns:
            Markdown-formatted report
        """
        if not result.get("success"):
            return f"## Error\n\n{result.get('error', 'Unknown error')}"

        data = result.get("data", {})
        metadata = result.get("metadata", {})

        formulation = data.get("formulation", {})
        rationale = data.get("rationale", "")
        essential_roles = data.get("essential_roles", {})
        alternatives = data.get("alternatives", {})
        evidence = data.get("evidence", {})

        # Build markdown
        md_lines = []

        # Header
        name = formulation.get("name", "Media Formulation Recommendation")
        md_lines.append(f"# {name}\n")

        # Overview
        organism = formulation.get("organism")
        if organism:
            md_lines.append(f"**Target Organism:** {organism}\n")

        description = formulation.get("description")
        if description:
            md_lines.append(f"**Description:** {description}\n")

        goals = formulation.get("goals", [])
        if goals:
            md_lines.append(f"**Goals:** {', '.join(goals)}\n")

        confidence = metadata.get("confidence", "medium")
        md_lines.append(f"**Confidence:** {confidence.upper()}\n")

        # Rationale
        md_lines.append(f"## Rationale\n\n{rationale}\n")

        # Formulation Table
        md_lines.append("## Formulation\n")

        ingredients = formulation.get("ingredients", [])
        if ingredients:
            md_lines.append("| Ingredient | Role | Concentration | Range (Low-High) | Unit | Confidence |")
            md_lines.append("|-----------|------|---------------|------------------|------|------------|")

            for ing in ingredients:
                ingredient = ing.get("ingredient", "N/A")
                role = ing.get("role", "N/A")
                conc = ing.get("concentration", "N/A")
                range_info = ing.get("range", {})
                low = range_info.get("low", "N/A")
                high = range_info.get("high", "N/A")
                unit = ing.get("unit", "mM")
                conf = ing.get("confidence", "medium")

                md_lines.append(
                    f"| {ingredient} | {role} | {conc} | {low} - {high} | {unit} | {conf} |"
                )

            md_lines.append("")

        # Properties
        properties = formulation.get("properties", {})
        if properties:
            md_lines.append("## Predicted Properties\n")
            for key, value in properties.items():
                formatted_key = key.replace("_", " ").title()
                md_lines.append(f"- **{formatted_key}:** {value}")
            md_lines.append("")

        # Essential Roles Coverage
        if essential_roles:
            md_lines.append("## Essential Nutrient Roles Coverage\n")
            required_roles = {k: v for k, v in essential_roles.items() if v.get("required")}
            optional_roles = {k: v for k, v in essential_roles.items() if not v.get("required")}

            if required_roles:
                md_lines.append("### Required Roles")
                for role, info in required_roles.items():
                    priority = info.get("priority", "medium")
                    rationale = info.get("rationale", "")
                    md_lines.append(f"- **{role}** (Priority: {priority}): {rationale}")
                md_lines.append("")

            if optional_roles:
                md_lines.append("### Optional Roles")
                for role, info in optional_roles.items():
                    priority = info.get("priority", "low")
                    rationale = info.get("rationale", "")
                    md_lines.append(f"- **{role}** (Priority: {priority}): {rationale}")
                md_lines.append("")

        # Compatibility Notes
        compat_notes = formulation.get("compatibility_notes", [])
        if compat_notes:
            md_lines.append("## Chemical Compatibility Notes\n")
            for note in compat_notes:
                md_lines.append(f"- {note}")
            md_lines.append("")

        # Alternative Ingredients
        if alternatives:
            md_lines.append("## Alternative Ingredients\n")
            for ingredient, alts in alternatives.items():
                if alts:
                    md_lines.append(f"\n### Alternatives for {ingredient}\n")
                    for alt in alts[:3]:  # Top 3
                        alt_name = alt.get("alternative", "N/A")
                        rationale_alt = alt.get("rationale", "N/A")
                        md_lines.append(f"- **{alt_name}**: {rationale_alt}")
            md_lines.append("")

        # Evidence Sources
        md_lines.append("## Evidence Sources\n")

        # KG-Microbe evidence
        kg_evidence = evidence.get("kg_microbe", {})
        pathways = kg_evidence.get("pathways", [])
        metabolites = kg_evidence.get("metabolites", [])

        if pathways or metabolites:
            md_lines.append("### KG-Microbe Knowledge Graph")
            if pathways:
                md_lines.append(f"- **Pathways identified:** {len(pathways)}")
            if metabolites:
                md_lines.append(f"- **Metabolites identified:** {len(metabolites)}")
            md_lines.append("")

        # Literature evidence
        lit_evidence = evidence.get("literature", {})
        org_studies = lit_evidence.get("organism_studies", [])
        ing_studies = lit_evidence.get("ingredient_studies", {})

        if org_studies:
            md_lines.append("### Literature - Organism Studies")
            for study in org_studies[:5]:  # Top 5
                title = study.get("title", "N/A")
                doi = study.get("doi", "")
                if doi:
                    md_lines.append(f"- {title} (DOI: {doi})")
                else:
                    md_lines.append(f"- {title}")
            md_lines.append("")

        if ing_studies:
            md_lines.append("### Literature - Ingredient Studies")
            for ingredient, studies in ing_studies.items():
                md_lines.append(f"\n**{ingredient}:**")
                for study in studies[:3]:  # Top 3 per ingredient
                    title = study.get("title", "N/A")
                    doi = study.get("doi", "")
                    if doi:
                        md_lines.append(f"- {title} (DOI: {doi})")
                    else:
                        md_lines.append(f"- {title}")
            md_lines.append("")

        # MP Medium Database
        sources = metadata.get("sources", [])
        if "MP Medium Database" in sources or "MP medium database" in [s.lower() for s in sources]:
            md_lines.append("### MP Medium Database")
            md_lines.append(
                "- Concentration ranges and ingredient properties from MP medium database "
                "with 158 ingredients and 90.5% citation coverage."
            )
            md_lines.append("")

        # Footer
        md_lines.append("---")
        md_lines.append(
            f"\n*Generated by MicroGrowAgents recommend-media workflow "
            f"using {len(metadata.get('agents_used', []))} specialized agents.*"
        )

        return "\n".join(md_lines)

    def format_json(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format result as JSON (passthrough).

        Args:
            result: Result from execute()

        Returns:
            Result dictionary as-is
        """
        return result

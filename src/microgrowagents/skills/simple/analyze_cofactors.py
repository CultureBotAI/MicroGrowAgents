"""
Analyze Cofactors Skill.

Wraps CofactorMediaAgent to analyze cofactor requirements from genome annotations.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from microgrowagents.skills.base_skill import BaseSkill, SkillMetadata, SkillParameter
from microgrowagents.agents.cofactor_media_agent import CofactorMediaAgent


class AnalyzeCofactorsSkill(BaseSkill):
    """
    Analyze cofactor requirements from genome annotations.

    Uses CofactorMediaAgent to:
    - Extract EC numbers from Bakta genome annotations
    - Map EC numbers to required cofactors (44 cofactors across 5 categories)
    - Determine which cofactors are in MP medium (existing) vs missing (new)
    - Integrate evidence from genome, KG-Microbe, KEGG pathways, and literature

    Data Sources:
    - ChEBI: Chemical identifiers (DOI: 10.1093/nar/gkv1031)
    - KEGG: Biosynthesis pathways (DOI: 10.1093/nar/gkac963)
    - BRENDA: EC-to-cofactor relationships (DOI: 10.1093/nar/gky1048)
    - KG-Microbe: 1.5M nodes for enzyme-substrate queries

    Examples:
        >>> skill = AnalyzeCofactorsSkill()
        >>> result = skill.run(
        ...     organism="SAMN31331780",  # M. extorquens AM-1
        ...     base_medium="MP",
        ...     output_format="markdown"
        ... )
        >>> result["success"]
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
            name="analyze-cofactors",
            description="Analyze cofactor requirements from Bakta genome annotations",
            category="simple",
            parameters=[
                SkillParameter(
                    name="organism",
                    type="str",
                    description="Organism genome ID (SAMN) or name",
                    required=True,
                ),
                SkillParameter(
                    name="base_medium",
                    type="str",
                    description="Base medium for comparison (default: MP)",
                    required=False,
                    default="MP",
                ),
            ],
            examples=[
                "analyze-cofactors SAMN31331780",  # M. extorquens AM-1
                "analyze-cofactors 'Methylococcus capsulatus'",
                "analyze-cofactors SAMN08769567 --base_medium MP",  # M. radiotolerans
            ],
            requires_database=True,
            requires_internet=False,
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute cofactor analysis.

        Args:
            organism: Organism genome ID or name
            base_medium: Base medium for comparison (default: MP)

        Returns:
            Result dictionary with cofactor table and recommendations

        Raises:
            ValueError: If organism not found in database
        """
        organism = kwargs.get("organism")
        base_medium = kwargs.get("base_medium", "MP")

        if not organism:
            return {
                "success": False,
                "error": "organism parameter is required",
            }

        # Initialize agent
        if self._agent is None:
            self._agent = CofactorMediaAgent(self.db_path)

        # Run analysis
        result = self._agent.run(
            query=f"Analyze cofactor requirements for {organism}",
            organism=organism,
            base_medium=base_medium,
        )

        return result

    def format_result(self, result: Dict[str, Any], output_format: str) -> str:
        """
        Format result for output.

        Args:
            result: Result dictionary from execute()
            output_format: Output format (markdown or json)

        Returns:
            Formatted string
        """
        if output_format == "json":
            return self._format_json(result)

        # Markdown format
        if not result.get("success"):
            return f"**Error**: {result.get('error', 'Unknown error')}"

        data = result.get("data", {})
        metadata = result.get("metadata", {})

        cofactor_table = data.get("cofactor_table", [])
        cofactor_requirements = data.get("cofactor_requirements", [])
        existing_coverage = data.get("existing_coverage", [])
        new_recommendations = data.get("new_recommendations", [])

        output = [
            f"# Cofactor Analysis: {metadata.get('organism', 'Unknown')}",
            "",
            "## Summary",
            f"- **Cofactors Identified**: {len(cofactor_requirements)}",
            f"- **Existing in {metadata.get('base_medium', 'MP')} Medium**: {len(existing_coverage)}",
            f"- **Missing/Gaps**: {len(new_recommendations)}",
            "",
            "## Cofactor Table",
            "",
        ]

        # Group by category
        from collections import defaultdict
        by_category = defaultdict(list)
        for row in cofactor_table:
            by_category[row.get("Category", "other")].append(row)

        category_order = ["vitamins", "metals", "nucleotides", "energy_cofactors", "other"]
        for category in category_order:
            if category not in by_category:
                continue

            output.append(f"### {category.upper().replace('_', ' ')}")
            output.append("")
            output.append("| Cofactor | Ingredient | Status | Rationale |")
            output.append("|----------|-----------|--------|-----------|")

            for row in sorted(by_category[category], key=lambda x: (x.get("Status", ""), x.get("Cofactor", ""))):
                cofactor = row.get("Cofactor", "")
                ingredient = row.get("Ingredient", "")
                status = row.get("Status", "")
                rationale = row.get("Rationale", "")

                # Emoji for status
                status_emoji = "✅" if status == "existing" else "❌"

                output.append(f"| {cofactor} | {ingredient} | {status_emoji} {status} | {rationale} |")

            output.append("")

        # Data sources
        output.extend([
            "## Data Sources",
            "",
            "- **ChEBI**: Chemical identifiers ([DOI: 10.1093/nar/gkv1031](https://doi.org/10.1093/nar/gkv1031))",
            "- **KEGG**: Biosynthesis pathways ([DOI: 10.1093/nar/gkac963](https://doi.org/10.1093/nar/gkac963))",
            "- **BRENDA**: EC-to-cofactor mappings ([DOI: 10.1093/nar/gky1048](https://doi.org/10.1093/nar/gky1048))",
            "- **KG-Microbe**: 1.5M nodes for enzyme-substrate relationships",
            "",
            f"📊 **Analysis Sources**: {', '.join(metadata.get('sources', []))}",
        ])

        return "\n".join(output)

"""
Analyze Genome Skill.

Wraps GenomeFunctionAgent to analyze Bakta genome annotations.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from microgrowagents.skills.base_skill import BaseSkill, SkillMetadata, SkillParameter
from microgrowagents.agents.genome_function_agent import GenomeFunctionAgent


class AnalyzeGenomeSkill(BaseSkill):
    """
    Analyze genome function from Bakta annotations.

    Uses GenomeFunctionAgent to:
    - Query enzymes by EC number (with wildcard support: 1.1.*.*)
    - Detect auxotrophies (biosynthetic pathway gaps)
    - Find transporters for nutrient uptake
    - Identify cofactor requirements
    - Check pathway completeness (KEGG)

    Database:
    - 57 Bakta-annotated genomes
    - 667K annotated features
    - EC numbers, GO terms, KEGG IDs, gene products

    Examples:
        >>> skill = AnalyzeGenomeSkill()
        >>> result = skill.run(
        ...     query="Find all oxidoreductases",
        ...     organism="Methylococcus capsulatus",
        ...     ec_pattern="1.*.*.*",
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
            name="analyze-genome",
            description="Analyze genome function from Bakta annotations (enzymes, auxotrophies, transporters)",
            category="simple",
            parameters=[
                SkillParameter(
                    name="query",
                    type="str",
                    description="Natural language query describing analysis",
                    required=True,
                ),
                SkillParameter(
                    name="organism",
                    type="str",
                    description="Organism genome ID (SAMN) or name",
                    required=True,
                ),
                SkillParameter(
                    name="analysis_type",
                    type="str",
                    description="Type of analysis: enzymes, auxotrophies, transporters, cofactors, pathways",
                    required=False,
                    default="enzymes",
                    options=["enzymes", "auxotrophies", "transporters", "cofactors", "pathways"],
                ),
                SkillParameter(
                    name="ec_pattern",
                    type="str",
                    description="EC number pattern for enzyme queries (e.g., 1.1.*.* for all dehydrogenases)",
                    required=False,
                ),
                SkillParameter(
                    name="pathway",
                    type="str",
                    description="KEGG pathway ID for pathway completeness check (e.g., ko00730)",
                    required=False,
                ),
            ],
            examples=[
                "analyze-genome 'Find oxidoreductases' SAMN31331780 --ec_pattern '1.*.*.*'",
                "analyze-genome 'Check vitamin biosynthesis' 'Methylococcus capsulatus' --analysis_type auxotrophies",
                "analyze-genome 'Find methanol dehydrogenase' SAMN31331780 --ec_pattern '1.1.2.*'",
                "analyze-genome 'Check thiamine pathway' SAMN31331780 --pathway ko00730",
            ],
            requires_database=True,
            requires_internet=False,
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute genome analysis.

        Args:
            query: Natural language query
            organism: Organism genome ID or name
            analysis_type: Type of analysis (enzymes, auxotrophies, transporters, cofactors, pathways)
            ec_pattern: EC number pattern (for enzyme queries)
            pathway: KEGG pathway ID (for pathway checks)

        Returns:
            Result dictionary with analysis results

        Raises:
            ValueError: If organism not found or invalid parameters
        """
        query = kwargs.get("query")
        organism = kwargs.get("organism")
        analysis_type = kwargs.get("analysis_type", "enzymes")
        ec_pattern = kwargs.get("ec_pattern")
        pathway = kwargs.get("pathway")

        if not organism:
            return {
                "success": False,
                "error": "organism parameter is required",
            }

        # Initialize agent
        if self._agent is None:
            self._agent = GenomeFunctionAgent(self.db_path)

        # Route to appropriate method based on analysis type
        try:
            if analysis_type == "enzymes" and ec_pattern:
                result = self._agent.find_enzymes(
                    organism=organism,
                    ec_number=ec_pattern,
                )
            elif analysis_type == "auxotrophies":
                result = self._agent.detect_auxotrophies(
                    organism=organism,
                )
            elif analysis_type == "transporters":
                result = self._agent.find_transporters(
                    organism=organism,
                )
            elif analysis_type == "cofactors":
                result = self._agent.find_cofactor_requirements(
                    organism=organism,
                )
            elif analysis_type == "pathways" and pathway:
                result = self._agent.check_pathway_completeness(
                    organism=organism,
                    pathway_id=pathway,
                )
            else:
                # Default: run general genome query
                result = self._agent.run(
                    query=query,
                    organism=organism,
                    analysis_type=analysis_type,
                )

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

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

        output = [
            f"# Genome Analysis: {metadata.get('organism', 'Unknown')}",
            "",
            "## Results",
            "",
        ]

        # Format based on data type
        if isinstance(data, list):
            # List of genes/enzymes
            output.append(f"**Total Results**: {len(data)}")
            output.append("")

            if data:
                output.append("| Gene ID | Product | EC Number | GO Terms |")
                output.append("|---------|---------|-----------|----------|")

                for item in data[:50]:  # Limit to 50 rows
                    gene_id = item.get("gene_id", "")
                    product = item.get("product", "")[:60]  # Truncate long products
                    ec_number = item.get("ec_number", "")
                    go_terms = ", ".join(item.get("go_terms", [])[:3])  # First 3 GO terms

                    output.append(f"| {gene_id} | {product} | {ec_number} | {go_terms} |")

                if len(data) > 50:
                    output.append("")
                    output.append(f"*...and {len(data) - 50} more results*")

        elif isinstance(data, dict):
            # Structured data (auxotrophies, pathway completeness)
            for key, value in data.items():
                output.append(f"### {key.replace('_', ' ').title()}")
                output.append("")

                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            output.append(f"- **{item.get('name', 'Unknown')}**: {item.get('status', '')}")
                        else:
                            output.append(f"- {item}")
                elif isinstance(value, dict):
                    for k, v in value.items():
                        output.append(f"- **{k}**: {v}")
                else:
                    output.append(f"- {value}")

                output.append("")

        # Metadata
        if metadata:
            output.extend([
                "## Analysis Metadata",
                "",
                f"- **Genome ID**: {metadata.get('genome_id', 'N/A')}",
                f"- **Features Analyzed**: {metadata.get('total_features', 'N/A')}",
                f"- **Database**: {metadata.get('database', 'microgrow.duckdb')}",
                "",
            ])

        # Data source
        output.extend([
            "## Data Source",
            "",
            "- **Bakta Annotations**: 57 genomes, 667K features",
            "- **Annotation Types**: EC numbers, GO terms, KEGG IDs, gene products",
            "- **Pattern Matching**: Wildcard EC numbers supported (e.g., `1.1.*.*`)",
        ])

        return "\n".join(output)

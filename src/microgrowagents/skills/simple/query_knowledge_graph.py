"""
Query Knowledge Graph Skill.

Wraps KGReasoningAgent to query KG-Microbe knowledge graph.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from microgrowagents.skills.base_skill import BaseSkill, SkillMetadata, SkillParameter
from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent


class QueryKnowledgeGraphSkill(BaseSkill):
    """
    Query KG-Microbe knowledge graph.

    Uses KGReasoningAgent to query:
    - 1.5M nodes (organisms, chemicals, genes, proteins, pathways)
    - 5.1M edges (relationships between entities)
    - Biolink model predicates (has_input, has_participant, etc.)

    Query Types:
    1. **Organism → Media**: Find media where organism grows
    2. **Phenotype → Media**: Find media for specific phenotypes
    3. **Enzyme → Substrate**: Find enzymes using specific substrates
    4. **Pathway Reasoning**: Explore metabolic pathways
    5. **Graph Algorithms**: Shortest paths, centrality, communities

    Examples:
        >>> skill = QueryKnowledgeGraphSkill()
        >>> result = skill.run(
        ...     query="Find media for Methylococcus capsulatus",
        ...     query_type="organism_media",
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
            name="query-knowledge-graph",
            description="Query KG-Microbe knowledge graph (1.5M nodes, 5.1M edges)",
            category="simple",
            parameters=[
                SkillParameter(
                    name="query",
                    type="str",
                    description="Natural language query for knowledge graph",
                    required=True,
                ),
                SkillParameter(
                    name="query_type",
                    type="str",
                    description="Type of KG query: organism_media, phenotype_media, enzyme_substrate, pathway, graph_algorithm",
                    required=False,
                    default="organism_media",
                    options=["organism_media", "phenotype_media", "enzyme_substrate", "pathway", "graph_algorithm"],
                ),
                SkillParameter(
                    name="entity_id",
                    type="str",
                    description="Entity ID (organism, chemical, gene) for targeted queries",
                    required=False,
                ),
                SkillParameter(
                    name="relationship_type",
                    type="str",
                    description="Biolink predicate type (e.g., biolink:has_input, biolink:participates_in)",
                    required=False,
                ),
                SkillParameter(
                    name="max_hops",
                    type="int",
                    description="Maximum number of hops for graph traversal",
                    required=False,
                    default=2,
                ),
            ],
            examples=[
                "query-knowledge-graph 'Find media for Methylococcus capsulatus' --query_type organism_media",
                "query-knowledge-graph 'Find enzymes using NAD+' --query_type enzyme_substrate --entity_id CHEBI:15846",
                "query-knowledge-graph 'Methane oxidation pathway' --query_type pathway",
                "query-knowledge-graph 'Central hubs in metabolic network' --query_type graph_algorithm",
            ],
            requires_database=True,
            requires_internet=False,
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute knowledge graph query.

        Args:
            query: Natural language query
            query_type: Type of KG query
            entity_id: Entity ID for targeted queries
            relationship_type: Biolink predicate type
            max_hops: Maximum graph traversal hops

        Returns:
            Result dictionary with KG query results

        Raises:
            ValueError: If invalid query parameters
        """
        query = kwargs.get("query")
        query_type = kwargs.get("query_type", "organism_media")
        entity_id = kwargs.get("entity_id")
        relationship_type = kwargs.get("relationship_type")
        max_hops = kwargs.get("max_hops", 2)

        if not query:
            return {
                "success": False,
                "error": "query parameter is required",
            }

        # Initialize agent
        if self._agent is None:
            self._agent = KGReasoningAgent(self.db_path)

        # Execute query
        try:
            result = self._agent.run(
                query=query,
                query_type=query_type,
                entity_id=entity_id,
                relationship_type=relationship_type,
                max_hops=max_hops,
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
            f"# Knowledge Graph Query Results",
            "",
            f"**Query**: {metadata.get('query', 'N/A')}",
            f"**Query Type**: {metadata.get('query_type', 'N/A')}",
            "",
            "## Results",
            "",
        ]

        # Format based on data type
        if isinstance(data, list):
            # List of entities or relationships
            output.append(f"**Total Results**: {len(data)}")
            output.append("")

            if data and len(data) > 0:
                # Determine table structure based on first item
                first_item = data[0]

                if "subject" in first_item and "predicate" in first_item:
                    # Triple format (subject, predicate, object)
                    output.append("| Subject | Predicate | Object | Evidence |")
                    output.append("|---------|-----------|--------|----------|")

                    for item in data[:100]:  # Limit to 100 rows
                        subject = item.get("subject", "")[:40]
                        predicate = item.get("predicate", "").replace("biolink:", "")
                        obj = item.get("object", "")[:40]
                        evidence = item.get("evidence_type", "")

                        output.append(f"| {subject} | {predicate} | {obj} | {evidence} |")

                else:
                    # General entity format
                    output.append("| Entity ID | Name | Type | Properties |")
                    output.append("|-----------|------|------|------------|")

                    for item in data[:100]:
                        entity_id = item.get("id", item.get("entity_id", ""))[:30]
                        name = item.get("name", "")[:40]
                        entity_type = item.get("type", item.get("category", ""))
                        props = str(item.get("properties", {}))[:50]

                        output.append(f"| {entity_id} | {name} | {entity_type} | {props} |")

                if len(data) > 100:
                    output.append("")
                    output.append(f"*...and {len(data) - 100} more results*")

        elif isinstance(data, dict):
            # Structured data (graph metrics, pathway info)
            for key, value in data.items():
                output.append(f"### {key.replace('_', ' ').title()}")
                output.append("")

                if isinstance(value, list):
                    for item in value[:20]:  # Limit to 20 items
                        if isinstance(item, dict):
                            output.append(f"- **{item.get('name', item.get('id', 'Unknown'))}**: {item.get('score', item.get('value', ''))}")
                        else:
                            output.append(f"- {item}")
                elif isinstance(value, dict):
                    for k, v in value.items():
                        output.append(f"- **{k}**: {v}")
                else:
                    output.append(f"- {value}")

                output.append("")

        # Query metadata
        if metadata:
            output.extend([
                "## Query Metadata",
                "",
                f"- **Nodes Queried**: {metadata.get('nodes_queried', 'N/A')}",
                f"- **Edges Traversed**: {metadata.get('edges_traversed', 'N/A')}",
                f"- **Query Time**: {metadata.get('query_time_ms', 'N/A')} ms",
                f"- **Max Hops**: {metadata.get('max_hops', 'N/A')}",
                "",
            ])

        # KG-Microbe info
        output.extend([
            "## KG-Microbe Knowledge Graph",
            "",
            "- **Nodes**: 1.5M (organisms, chemicals, genes, proteins, pathways)",
            "- **Edges**: 5.1M relationships",
            "- **Schema**: Biolink model predicates",
            "- **Performance**: GRAPE graph algorithms (10-100x faster)",
            "- **Database**: DuckDB with indexed queries",
            "",
            "**Relationship Types**:",
            "- `biolink:has_input` - Enzyme-substrate",
            "- `biolink:has_participant` - Pathway participants",
            "- `biolink:has_part` - Media-ingredient composition",
            "- `biolink:participates_in` - Entity-pathway associations",
        ])

        return "\n".join(output)

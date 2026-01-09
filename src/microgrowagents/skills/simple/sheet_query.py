"""
Sheet Query Skill.

User-facing skill for querying information sheets with 3 output formats:
1. Markdown tables with citations
2. Simple JSON data
3. Evidence-rich reports

Author: MicroGrowAgents Team
"""

from pathlib import Path
from typing import Any, Dict, Optional

from microgrowagents.agents.sheet_query_agent import SheetQueryAgent
from microgrowagents.skills.base_skill import BaseSkill, SkillMetadata, SkillParameter


class SheetQuerySkill(BaseSkill):
    """
    Query information sheets from data/sheets_* directories.

    Provides 4 query types with 3 output formats:
    - Entity lookup: Find entities by ID/name/type
    - Cross-reference: Find related entities and publications
    - Publication search: Full-text search in publications
    - Filtered queries: SQL-like filtering

    Output formats:
    - markdown: Formatted tables with citation links
    - json: Raw data structures
    - evidence_report: Detailed reports with excerpts

    Examples:
        >>> skill = SheetQuerySkill()
        >>> result = skill.run(
        ...     collection_id="cmm",
        ...     query_type="entity_lookup",
        ...     entity_id="CHEBI:52927",
        ...     output_format="markdown"
        ... )
        >>> "CHEBI:52927" in result
        True
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize skill.

        Args:
            db_path: Path to DuckDB database
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
            name="sheet-query",
            description="Query information sheets (TSV + publications)",
            category="simple",
            parameters=[
                SkillParameter(
                    name="collection_id",
                    type="str",
                    description="Collection ID (e.g., 'cmm', 'xyz')",
                    required=True
                ),
                SkillParameter(
                    name="query_type",
                    type="str",
                    description="Query type: 'entity_lookup', 'cross_reference', 'publication_search', 'filtered'",
                    required=True,
                    options=["entity_lookup", "cross_reference", "publication_search", "filtered"]
                ),
                SkillParameter(
                    name="entity_id",
                    type="str",
                    description="Entity ID for lookup/cross-reference",
                    required=False
                ),
                SkillParameter(
                    name="entity_name",
                    type="str",
                    description="Entity name for lookup",
                    required=False
                ),
                SkillParameter(
                    name="entity_type",
                    type="str",
                    description="Entity type filter (chemical, gene, strain, etc.)",
                    required=False
                ),
                SkillParameter(
                    name="keyword",
                    type="str",
                    description="Keyword for publication search",
                    required=False
                ),
                SkillParameter(
                    name="table_name",
                    type="str",
                    description="Table name for filtered queries",
                    required=False
                ),
                SkillParameter(
                    name="filter_conditions",
                    type="dict",
                    description="Filter conditions (JSON dict)",
                    required=False
                ),
                SkillParameter(
                    name="source_entity_id",
                    type="str",
                    description="Source entity ID for cross-reference",
                    required=False
                ),
                SkillParameter(
                    name="output_format",
                    type="str",
                    description="Output format: 'markdown', 'json', 'evidence_report'",
                    required=False,
                    default="markdown",
                    options=["markdown", "json", "evidence_report"]
                )
            ],
            examples=[
                "sheet-query --collection-id cmm --query-type entity_lookup --entity-id CHEBI:52927",
                "sheet-query --collection-id cmm --query-type publication_search --keyword lanthanide",
                "sheet-query --collection-id cmm --query-type cross_reference --source-entity-id K23995"
            ],
            requires_database=False  # We handle database ourselves via agent
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute sheet query.

        Args:
            **kwargs: Query parameters (collection_id, query_type, etc.)

        Returns:
            Result dictionary with success, data, metadata
        """
        # Validate required parameters
        collection_id = kwargs.get("collection_id")
        if not collection_id:
            return {
                "success": False,
                "error": "collection_id is required"
            }

        query_type = kwargs.get("query_type")
        if not query_type:
            return {
                "success": False,
                "error": "query_type is required"
            }

        # Initialize agent
        if self._agent is None:
            self._agent = SheetQueryAgent(self.db_path)

        # Route to appropriate query method
        query = f"{query_type} query for collection {collection_id}"

        if query_type == "entity_lookup":
            return self._agent.entity_lookup(query=query, **kwargs)

        elif query_type == "cross_reference":
            # Ensure source_entity_id is present
            if not kwargs.get("source_entity_id"):
                return {
                    "success": False,
                    "error": "source_entity_id is required for cross_reference queries"
                }
            return self._agent.cross_reference_query(query=query, **kwargs)

        elif query_type == "publication_search":
            # Ensure keyword is present
            if not kwargs.get("keyword") and not kwargs.get("keywords"):
                return {
                    "success": False,
                    "error": "keyword is required for publication_search queries"
                }
            return self._agent.publication_search(query=query, **kwargs)

        elif query_type == "filtered":
            return self._agent.filtered_query(query=query, **kwargs)

        else:
            return {
                "success": False,
                "error": f"Unknown query_type: {query_type}. Use: entity_lookup, cross_reference, publication_search, or filtered"
            }

    def _format_output(self, result: Dict[str, Any], output_format: str) -> str:
        """
        Format skill output with custom formatters.

        Args:
            result: Result dictionary from agent
            output_format: Output format ('markdown', 'json', 'evidence_report')

        Returns:
            Formatted string
        """
        if output_format == "json":
            return super()._format_json(result)
        elif output_format == "evidence_report":
            return self._format_evidence_report(result)
        else:  # markdown (default)
            return self._format_markdown_tables(result)

    def _format_markdown_tables(self, result: Dict[str, Any]) -> str:
        """
        Format result as markdown tables with citations.

        Args:
            result: Result dictionary

        Returns:
            Markdown formatted string with tables and citation links
        """
        if not result.get("success"):
            return f"# Error\n\n{result.get('error', 'Unknown error')}"

        data = result.get("data", {})
        metadata = result.get("metadata", {})
        output = ""

        # Title
        query_type = metadata.get("query_type", "Query")
        collection_id = metadata.get("collection_id", "unknown")
        output += f"# Sheet Query Results: {collection_id}\n\n"

        # Entities table
        if "entities" in data:
            entities = data["entities"]
            output += f"## Entities ({len(entities)} found)\n\n"

            if entities:
                # Build markdown table
                output += "| ID | Name | Type | Properties |\n"
                output += "|----|----|------|------------|\n"

                for entity in entities[:50]:  # Limit to 50 for display
                    entity_id = entity.get("entity_id", "")
                    entity_name = entity.get("entity_name", "")
                    entity_type = entity.get("entity_type", "")

                    # Format key properties
                    props = entity.get("properties", {})
                    prop_str = ", ".join([f"{k}: {v}" for k, v in list(props.items())[:3]])
                    if len(props) > 3:
                        prop_str += "..."

                    output += f"| {entity_id} | {entity_name} | {entity_type} | {prop_str} |\n"

                if len(entities) > 50:
                    output += f"\n*Showing 50 of {len(entities)} entities*\n"
            else:
                output += "*No entities found*\n"

            output += "\n"

        # Related entities
        if "related_entities" in data:
            related = data["related_entities"]
            output += f"## Related Entities ({len(related)} found)\n\n"

            if related:
                output += "| ID | Name | Type | Relationship |\n"
                output += "|----|----|------|-------------|\n"

                for entity in related[:30]:
                    entity_id = entity.get("entity_id", "")
                    entity_name = entity.get("entity_name", "")
                    entity_type = entity.get("entity_type", "")
                    relationship = entity.get("relationship", "related")

                    output += f"| {entity_id} | {entity_name} | {entity_type} | {relationship} |\n"

                if len(related) > 30:
                    output += f"\n*Showing 30 of {len(related)} related entities*\n"
            else:
                output += "*No related entities found*\n"

            output += "\n"

        # Publications with citations
        if "publications" in data:
            pubs = data["publications"]
            output += f"## Publications ({len(pubs)} found)\n\n"

            for i, pub in enumerate(pubs[:10], 1):
                pub_id = pub.get("publication_id", "")
                pub_type = pub.get("publication_type", "")
                title = pub.get("title", "")
                entity_count = pub.get("entity_count", 0)
                excerpt = pub.get("excerpt", "")

                # Create citation link
                if pub_type == "pmid":
                    pmid = pub_id.replace("pmid:", "")
                    link = f"[PMID:{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)"
                elif pub_type == "doi":
                    doi = pub_id.replace("doi:", "")
                    link = f"[{doi}](https://doi.org/{doi})"
                else:
                    link = pub_id

                output += f"### {i}. {link}\n\n"

                if title:
                    output += f"**Title**: {title}\n\n"

                if entity_count:
                    output += f"**Referenced by**: {entity_count} entities\n\n"

                if excerpt:
                    output += f"**Excerpt**: {excerpt}\n\n"

            if len(pubs) > 10:
                output += f"\n*Showing 10 of {len(pubs)} publications*\n"

            output += "\n"

        # Source entity (for cross-reference)
        if "source_entity" in data and data["source_entity"]:
            source = data["source_entity"]
            output += f"## Source Entity\n\n"
            output += f"- **ID**: {source.get('entity_id')}\n"
            output += f"- **Name**: {source.get('entity_name')}\n"
            output += f"- **Type**: {source.get('entity_type')}\n\n"

        return output.strip()

    def _format_evidence_report(self, result: Dict[str, Any]) -> str:
        """
        Format result as evidence-rich report with publication excerpts.

        Args:
            result: Result dictionary

        Returns:
            Detailed report with cross-references and excerpts
        """
        if not result.get("success"):
            return f"# Error\n\n{result.get('error', 'Unknown error')}"

        data = result.get("data", {})
        metadata = result.get("metadata", {})
        output = ""

        # Title
        collection_id = metadata.get("collection_id", "unknown")
        output += f"# Evidence Report: {collection_id}\n\n"

        # Source entity details (if present)
        if "source_entity" in data and data["source_entity"]:
            source = data["source_entity"]
            output += f"## Entity Details\n\n"
            output += f"**{source.get('entity_type', 'Entity').title()}**: {source.get('entity_name')}\n\n"
            output += f"**ID**: {source.get('entity_id')}\n\n"

            props = source.get("properties", {})
            if props:
                output += "### Properties\n\n"
                for key, value in props.items():
                    if value and str(value).strip():
                        output += f"- **{key}**: {value}\n"
                output += "\n"

        # Primary entities
        if "entities" in data:
            entities = data["entities"]
            output += f"## Entities ({len(entities)})\n\n"

            for entity in entities[:20]:
                output += f"### {entity.get('entity_name')}\n\n"
                output += f"- **ID**: {entity.get('entity_id')}\n"
                output += f"- **Type**: {entity.get('entity_type')}\n"

                # Key properties
                props = entity.get("properties", {})
                for key, value in list(props.items())[:5]:
                    if value and str(value).strip():
                        output += f"- **{key}**: {value}\n"

                output += "\n"

            if len(entities) > 20:
                output += f"*...and {len(entities) - 20} more entities*\n\n"

        # Related entities
        if "related_entities" in data:
            related = data["related_entities"]
            output += f"## Related Entities ({len(related)})\n\n"

            # Group by type
            by_type = {}
            for entity in related:
                etype = entity.get("entity_type", "unknown")
                if etype not in by_type:
                    by_type[etype] = []
                by_type[etype].append(entity)

            for etype, entities in sorted(by_type.items()):
                output += f"### {etype.title()}s ({len(entities)})\n\n"
                for entity in entities[:10]:
                    output += f"- **{entity.get('entity_id')}**: {entity.get('entity_name')}\n"
                    if "relationship" in entity:
                        output += f"  - *{entity['relationship']}*\n"

                if len(entities) > 10:
                    output += f"  - *...and {len(entities) - 10} more*\n"

                output += "\n"

        # Publication evidence
        if "publications" in data:
            pubs = data["publications"]
            output += f"## Publication Evidence\n\n"

            for i, pub in enumerate(pubs[:5], 1):
                pub_id = pub.get("publication_id", "")
                pub_type = pub.get("publication_type", "")
                title = pub.get("title", "")
                full_text = pub.get("full_text", "")
                excerpt = pub.get("excerpt", "")

                # Title with link
                if pub_type == "pmid":
                    pmid = pub_id.replace("pmid:", "")
                    output += f"### {i}. PMID:{pmid}\n\n"
                    output += f"[View on PubMed](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)\n\n"
                elif pub_type == "doi":
                    doi = pub_id.replace("doi:", "")
                    output += f"### {i}. {doi}\n\n"
                    output += f"[View DOI](https://doi.org/{doi})\n\n"
                else:
                    output += f"### {i}. {pub_id}\n\n"

                if title:
                    output += f"**Title**: {title}\n\n"

                # Excerpt or first 500 chars
                if excerpt:
                    output += f"> {excerpt}\n\n"
                elif full_text:
                    excerpt_text = full_text[:500]
                    if len(full_text) > 500:
                        excerpt_text += "..."
                    output += f"> {excerpt_text}\n\n"

                if "entity_count" in pub:
                    output += f"**Referenced by**: {pub['entity_count']} entities in this collection\n\n"

            if len(pubs) > 5:
                output += f"*...and {len(pubs) - 5} more publications*\n\n"

        # Footer
        output += "\n---\n\n"
        output += f"*Generated with [SheetQuerySkill](https://github.com/monarch-initiative/MicroGrowAgents)*\n"

        return output.strip()

"""
Search Literature Skill.

Wraps LiteratureAgent to search scientific literature.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from microgrowagents.skills.base_skill import BaseSkill, SkillMetadata, SkillParameter
from microgrowagents.agents.literature_agent import LiteratureAgent


class SearchLiteratureSkill(BaseSkill):
    """
    Search scientific literature (PubMed + web).

    Uses LiteratureAgent to search for:
    - PubMed articles
    - Web resources
    - DOI/PMID lookups

    Examples:
        >>> skill = SearchLiteratureSkill()
        >>> result = skill.run(query="glucose fermentation", output_format="markdown")
        >>> "pubmed" in result.lower() or "doi" in result.lower()
        True
    """

    def __init__(self):
        """Initialize skill."""
        super().__init__()
        self._agent = None

    def get_metadata(self) -> SkillMetadata:
        """
        Get skill metadata.

        Returns:
            SkillMetadata with parameters and examples
        """
        return SkillMetadata(
            name="search-literature",
            description="Search scientific literature (PubMed and web)",
            category="simple",
            parameters=[
                SkillParameter(
                    name="query",
                    type="str",
                    description="Search query (keywords, DOI, PMID)",
                    required=True,
                ),
                SkillParameter(
                    name="max_results",
                    type="int",
                    description="Maximum results to return",
                    required=False,
                    default=10,
                ),
            ],
            examples=[
                "search-literature 'glucose fermentation'",
                "search-literature 'iron toxicity bacteria'",
                "search-literature '10.1021/acs.jced.8b00201'",
            ],
            requires_database=False,
            requires_internet=True,
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute literature search.

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            Result dictionary with literature results
        """
        # Get parameters
        query = kwargs.get("query")
        if not query:
            return {
                "success": False,
                "error": "Missing required parameter: query",
            }

        max_results = kwargs.get("max_results", 10)

        # Initialize agent if needed
        if self._agent is None:
            self._agent = LiteratureAgent()

        # Run search
        try:
            result = self._agent.run(query=query, max_results=max_results)

            if not result.get("success", False):
                return result

            # Transform result for skill output
            transformed = self._transform_result(result)
            return transformed

        except Exception as e:
            return {
                "success": False,
                "error": f"Literature search failed: {str(e)}",
            }

    def _transform_result(self, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform agent result to skill output format.

        Args:
            agent_result: Result from LiteratureAgent

        Returns:
            Transformed result with formatted data
        """
        data = agent_result.get("data", {})
        articles = data.get("articles", [])

        # Format as table rows
        table_rows = []
        evidence_list = []

        for i, article in enumerate(articles, 1):
            title = article.get("title", "No title")
            authors = article.get("authors", "")
            pmid = article.get("pmid", "")
            doi = article.get("doi", "")
            year = article.get("year", "")

            # Truncate title
            title_short = title[:60] + "..." if len(title) > 60 else title

            # Truncate authors
            authors_short = authors[:30] + "..." if len(authors) > 30 else authors

            table_rows.append({
                "#": str(i),
                "Title": title_short,
                "Authors": authors_short,
                "Year": year,
                "PMID/DOI": pmid if pmid else doi[:20] if doi else "-",
            })

            # Add to evidence
            if doi:
                evidence_list.append({"doi": doi})
            elif pmid:
                evidence_list.append({"pmid": pmid})

        return {
            "success": True,
            "data": table_rows,
            "evidence": evidence_list,
            "metadata": {
                "results_count": len(articles),
                "query": data.get("query", ""),
            },
        }

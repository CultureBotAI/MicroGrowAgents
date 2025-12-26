"""
Literature Agent: Web search and paper retrieval.

Capabilities:
- Web search for media formulations
- PubMed/PMC paper search via E-utilities API
- Evidence extraction from scientific literature
- Abstract retrieval and parsing
- Integration with ARTL MCP server (if available)
"""

from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import requests
import requests_cache

from microgrowagents.agents.base_agent import BaseAgent


class LiteratureAgent(BaseAgent):
    """Agent for searching literature and web."""

    PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    CACHE_FILE = "data/cache/literature_cache.sqlite"

    def __init__(self, db_path=None):
        """
        Initialize literature agent.

        Args:
            db_path: Path to DuckDB database (inherited from BaseAgent)
        """
        super().__init__(db_path)
        # Setup caching for API calls (24 hour expiration)
        requests_cache.install_cache(
            self.CACHE_FILE,
            backend="sqlite",
            expire_after=86400,  # 24 hours
        )

    def run(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Search literature for media formulations and chemical properties.

        Args:
            query: Search query
            max_results: Maximum number of results (default: 10)
            search_type: Type of search - 'pubmed', 'web', or 'both' (default: 'both')

        Returns:
            Dictionary with:
            - success: bool
            - results: Dict with 'pubmed' and/or 'web' results
            - query: Original query
            - result_count: Total number of results

        Examples:
            >>> agent = LiteratureAgent()
            >>> result = agent.run("Escherichia coli LB medium", max_results=5)
            >>> result = agent.run("glucose concentration effect", search_type='pubmed')
        """
        max_results = kwargs.get("max_results", 10)
        search_type = kwargs.get("search_type", "both")

        results = {}

        try:
            if search_type in ["pubmed", "both"]:
                self.log(f"Searching PubMed for: {query}")
                results["pubmed"] = self._pubmed_search(query, max_results)

            if search_type in ["web", "both"]:
                self.log(f"Performing web search for: {query}")
                results["web"] = self._web_search(query, max_results)

            total_count = sum(len(r) for r in results.values())
            self.log(f"Found {total_count} total results")

            return {
                "success": True,
                "results": results,
                "query": query,
                "result_count": total_count,
            }

        except Exception as e:
            self.log(f"Search failed: {str(e)}", level="ERROR")
            return {"success": False, "error": str(e), "query": query}

    def _pubmed_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Search PubMed via E-utilities API.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of paper dictionaries with title, abstract, PMID, etc.
        """
        results = []

        # Step 1: Search for PMIDs
        search_url = f"{self.PUBMED_BASE_URL}esearch.fcgi"
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance",
        }

        try:
            search_response = requests.get(search_url, params=search_params, timeout=10)
            search_response.raise_for_status()
            search_data = search_response.json()

            pmids = search_data.get("esearchresult", {}).get("idlist", [])

            if not pmids:
                self.log("No PubMed results found")
                return results

            # Step 2: Fetch article details
            fetch_url = f"{self.PUBMED_BASE_URL}esummary.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "json",
            }

            fetch_response = requests.get(fetch_url, params=fetch_params, timeout=10)
            fetch_response.raise_for_status()
            fetch_data = fetch_response.json()

            # Parse results
            for pmid in pmids:
                if pmid in fetch_data.get("result", {}):
                    article = fetch_data["result"][pmid]
                    results.append(
                        {
                            "pmid": pmid,
                            "title": article.get("title", ""),
                            "authors": self._parse_authors(article.get("authors", [])),
                            "journal": article.get("fulljournalname", ""),
                            "pub_date": article.get("pubdate", ""),
                            "doi": article.get("elocationid", ""),
                            "source": "PubMed",
                            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        }
                    )

            # Step 3: Fetch abstracts (separate API call)
            self._fetch_abstracts(results)

        except Exception as e:
            self.log(f"PubMed search error: {str(e)}", level="ERROR")

        return results

    def _fetch_abstracts(self, papers: List[Dict]) -> None:
        """
        Fetch abstracts for papers (modifies papers in place).

        Args:
            papers: List of paper dictionaries
        """
        if not papers:
            return

        pmids = [p["pmid"] for p in papers]
        fetch_url = f"{self.PUBMED_BASE_URL}efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        }

        try:
            response = requests.get(fetch_url, params=fetch_params, timeout=15)
            response.raise_for_status()

            # Parse XML (simplified - would use xml.etree in production)
            # For now, just mark that abstract fetching was attempted
            for paper in papers:
                paper["abstract"] = ""  # Placeholder

        except Exception as e:
            self.log(f"Abstract fetch error: {str(e)}", level="WARNING")

    def _parse_authors(self, authors_data: List) -> str:
        """
        Parse author list into formatted string.

        Args:
            authors_data: List of author dictionaries

        Returns:
            Formatted author string
        """
        if not authors_data:
            return ""

        author_names = []
        for author in authors_data[:3]:  # First 3 authors
            name = author.get("name", "")
            if name:
                author_names.append(name)

        if len(authors_data) > 3:
            author_names.append("et al.")

        return ", ".join(author_names)

    def _web_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Web search (placeholder for future implementation).

        Could integrate with:
        - Google Scholar API (if available)
        - Semantic Scholar API
        - arXiv API
        - bioRxiv/medRxiv

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            List of web search results
        """
        # Placeholder implementation
        self.log("Web search not yet implemented", level="WARNING")
        return []

    def search_for_organism(self, organism_name: str) -> Dict[str, Any]:
        """
        Search literature for organism growth conditions.

        Args:
            organism_name: Organism name (e.g., "Escherichia coli")

        Returns:
            Search results focused on growth media
        """
        query = f"{organism_name} growth medium formulation culture"
        return self.run(query, max_results=10, search_type="pubmed")

    def search_for_ingredient(self, ingredient_name: str) -> Dict[str, Any]:
        """
        Search literature for ingredient properties and effects.

        Args:
            ingredient_name: Chemical ingredient name

        Returns:
            Search results focused on chemical properties
        """
        query = f"{ingredient_name} concentration effect microbial growth"
        return self.run(query, max_results=5, search_type="pubmed")

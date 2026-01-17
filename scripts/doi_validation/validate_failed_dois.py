#!/usr/bin/env python
"""
Validate failed DOIs by checking if they exist and retrieving metadata.

This script validates DOIs that failed PDF download by:
1. Checking if the DOI exists (Crossref API)
2. Retrieving abstract and metadata
3. Categorizing failures as:
   - Invalid DOI (doesn't exist)
   - Valid DOI but no abstract/metadata
   - Valid DOI with metadata (paper exists, just unavailable)
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class DOIValidator:
    """Validate DOIs by checking metadata and abstract availability."""

    def __init__(self, email: str = "MJoachimiak@lbl.gov"):
        """Initialize validator.

        Args:
            email: Email for API politeness
        """
        self.email = email
        self.session = self._create_session()

        # API endpoints
        self.crossref_base = "https://api.crossref.org/works/"
        self.unpaywall_base = "https://api.unpaywall.org/v2/"
        self.semantic_scholar_base = "https://api.semanticscholar.org/graph/v1/paper/"

        # Statistics
        self.stats = {
            "total": 0,
            "invalid_doi": 0,
            "valid_no_metadata": 0,
            "valid_with_abstract": 0,
            "valid_no_abstract": 0,
            "api_errors": 0,
        }

    def _create_session(self) -> requests.Session:
        """Create session with retry logic."""
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _normalize_doi(self, doi: str) -> str:
        """Normalize DOI to just the identifier.

        Args:
            doi: DOI string (may have https://doi.org/ prefix)

        Returns:
            Normalized DOI identifier
        """
        if doi.startswith("https://doi.org/"):
            return doi.replace("https://doi.org/", "")
        elif doi.startswith("http://doi.org/"):
            return doi.replace("http://doi.org/", "")
        return doi

    def validate_via_crossref(self, doi: str) -> Dict[str, Any]:
        """Validate DOI via Crossref API.

        Args:
            doi: DOI identifier

        Returns:
            Dictionary with validation results
        """
        doi_normalized = self._normalize_doi(doi)
        url = f"{self.crossref_base}{doi_normalized}"

        try:
            response = self.session.get(
                url,
                headers={"User-Agent": f"DOIValidator/1.0 (mailto:{self.email})"},
                timeout=10,
            )

            if response.status_code == 404:
                return {
                    "valid": False,
                    "source": "crossref",
                    "error": "DOI not found in Crossref",
                    "metadata": None,
                }

            response.raise_for_status()
            data = response.json()

            metadata = data.get("message", {})
            abstract = metadata.get("abstract")

            return {
                "valid": True,
                "source": "crossref",
                "title": metadata.get("title", [None])[0] if metadata.get("title") else None,
                "authors": self._extract_authors(metadata),
                "year": self._extract_year(metadata),
                "abstract": abstract,
                "type": metadata.get("type"),
                "publisher": metadata.get("publisher"),
                "container_title": metadata.get("container-title", [None])[0]
                if metadata.get("container-title")
                else None,
            }

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return {
                    "valid": False,
                    "source": "crossref",
                    "error": "DOI not found",
                    "metadata": None,
                }
            return {
                "valid": None,
                "source": "crossref",
                "error": f"HTTP error: {e}",
                "metadata": None,
            }
        except Exception as e:
            return {
                "valid": None,
                "source": "crossref",
                "error": f"Error: {e}",
                "metadata": None,
            }

    def validate_via_semantic_scholar(self, doi: str) -> Dict[str, Any]:
        """Validate DOI via Semantic Scholar API.

        Args:
            doi: DOI identifier

        Returns:
            Dictionary with validation results
        """
        doi_normalized = self._normalize_doi(doi)
        url = f"{self.semantic_scholar_base}DOI:{doi_normalized}"

        try:
            response = self.session.get(
                url,
                params={"fields": "title,authors,year,abstract,publicationTypes"},
                timeout=10,
            )

            if response.status_code == 404:
                return {
                    "valid": False,
                    "source": "semantic_scholar",
                    "error": "DOI not found in Semantic Scholar",
                }

            response.raise_for_status()
            data = response.json()

            return {
                "valid": True,
                "source": "semantic_scholar",
                "title": data.get("title"),
                "authors": [a.get("name") for a in data.get("authors", [])],
                "year": data.get("year"),
                "abstract": data.get("abstract"),
                "type": ", ".join(data.get("publicationTypes", [])),
            }

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return {"valid": False, "source": "semantic_scholar", "error": "DOI not found"}
            return {"valid": None, "source": "semantic_scholar", "error": f"HTTP error: {e}"}
        except Exception as e:
            return {"valid": None, "source": "semantic_scholar", "error": f"Error: {e}"}

    def validate_via_unpaywall(self, doi: str) -> Dict[str, Any]:
        """Validate DOI via Unpaywall API.

        Args:
            doi: DOI identifier

        Returns:
            Dictionary with validation results
        """
        doi_normalized = self._normalize_doi(doi)
        url = f"{self.unpaywall_base}{doi_normalized}"

        try:
            response = self.session.get(url, params={"email": self.email}, timeout=10)

            if response.status_code == 404:
                return {
                    "valid": False,
                    "source": "unpaywall",
                    "error": "DOI not found in Unpaywall",
                }

            response.raise_for_status()
            data = response.json()

            return {
                "valid": True,
                "source": "unpaywall",
                "title": data.get("title"),
                "authors": self._extract_unpaywall_authors(data),
                "year": data.get("year"),
                "is_oa": data.get("is_oa"),
                "journal": data.get("journal_name"),
            }

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return {"valid": False, "source": "unpaywall", "error": "DOI not found"}
            return {"valid": None, "source": "unpaywall", "error": f"HTTP error: {e}"}
        except Exception as e:
            return {"valid": None, "source": "unpaywall", "error": f"Error: {e}"}

    def _extract_authors(self, metadata: Dict) -> List[str]:
        """Extract author names from Crossref metadata."""
        authors = []
        for author in metadata.get("author", []):
            given = author.get("given", "")
            family = author.get("family", "")
            if given and family:
                authors.append(f"{given} {family}")
            elif family:
                authors.append(family)
        return authors[:3]  # First 3 authors

    def _extract_unpaywall_authors(self, data: Dict) -> List[str]:
        """Extract author names from Unpaywall metadata."""
        z_authors = data.get("z_authors", [])
        return [a.get("family", "") for a in z_authors[:3] if a.get("family")]

    def _extract_year(self, metadata: Dict) -> Optional[int]:
        """Extract publication year from Crossref metadata."""
        published = metadata.get("published-print") or metadata.get("published-online")
        if published and "date-parts" in published:
            date_parts = published["date-parts"][0]
            if date_parts:
                return date_parts[0]
        return None

    def validate_doi(self, doi: str) -> Dict[str, Any]:
        """Validate a DOI using multiple sources.

        Args:
            doi: DOI to validate

        Returns:
            Validation result dictionary
        """
        self.stats["total"] += 1
        doi_normalized = self._normalize_doi(doi)

        print(f"\n[{self.stats['total']}] Validating {doi_normalized}...")

        # Try Crossref first (most comprehensive)
        result = self.validate_via_crossref(doi)

        if result["valid"] is False:
            # Try Semantic Scholar
            print(f"  ✗ Not in Crossref, trying Semantic Scholar...")
            result = self.validate_via_semantic_scholar(doi)

            if result["valid"] is False:
                # Try Unpaywall
                print(f"  ✗ Not in Semantic Scholar, trying Unpaywall...")
                result = self.validate_via_unpaywall(doi)

                if result["valid"] is False:
                    print(f"  ✗ INVALID DOI - not found in any database")
                    self.stats["invalid_doi"] += 1
                    return {
                        "doi": doi,
                        "valid": False,
                        "category": "INVALID_DOI",
                        "sources_checked": ["crossref", "semantic_scholar", "unpaywall"],
                        "metadata": None,
                    }

        if result["valid"] is None:
            # API error
            print(f"  ⚠️  API error: {result.get('error', 'Unknown')}")
            self.stats["api_errors"] += 1
            return {
                "doi": doi,
                "valid": None,
                "category": "API_ERROR",
                "error": result.get("error"),
                "metadata": result,
            }

        # DOI is valid
        has_abstract = bool(result.get("abstract"))
        has_metadata = bool(result.get("title"))

        if has_abstract:
            print(f"  ✓ VALID - has abstract ({len(result['abstract'])} chars)")
            self.stats["valid_with_abstract"] += 1
            category = "VALID_WITH_ABSTRACT"
        elif has_metadata:
            print(f"  ✓ VALID - has metadata but no abstract")
            self.stats["valid_no_abstract"] += 1
            category = "VALID_NO_ABSTRACT"
        else:
            print(f"  ✓ VALID - minimal metadata")
            self.stats["valid_no_metadata"] += 1
            category = "VALID_MINIMAL_METADATA"

        return {
            "doi": doi,
            "valid": True,
            "category": category,
            "source": result["source"],
            "metadata": result,
        }

    def validate_failed_dois(self, results_file: Path) -> Dict[str, Any]:
        """Validate all failed DOIs from results file.

        Args:
            results_file: Path to CSV all DOIs results JSON

        Returns:
            Validation results dictionary
        """
        # Load results
        with open(results_file) as f:
            data = json.load(f)

        # Extract failed DOIs
        failed_dois = []
        for result in data.get("results", []):
            if not result.get("success", False):
                failed_dois.append(result["doi"])

        print(f"Found {len(failed_dois)} failed DOIs to validate")
        print("=" * 70)

        # Validate each DOI
        validation_results = []
        for i, doi in enumerate(failed_dois, 1):
            result = self.validate_doi(doi)
            validation_results.append(result)

            # Rate limiting - be polite to APIs
            if i < len(failed_dois):
                time.sleep(0.5)  # 500ms between requests

        return {
            "total_failed": len(failed_dois),
            "validation_results": validation_results,
            "statistics": self.stats,
        }

    def generate_report(self, validation_data: Dict[str, Any], output_path: Path) -> None:
        """Generate validation report.

        Args:
            validation_data: Validation results
            output_path: Path to output markdown file
        """
        results = validation_data["validation_results"]
        stats = validation_data["statistics"]

        # Categorize results
        invalid_dois = [r for r in results if r["category"] == "INVALID_DOI"]
        valid_with_abstract = [r for r in results if r["category"] == "VALID_WITH_ABSTRACT"]
        valid_no_abstract = [r for r in results if r["category"] == "VALID_NO_ABSTRACT"]
        valid_minimal = [r for r in results if r["category"] == "VALID_MINIMAL_METADATA"]
        api_errors = [r for r in results if r["category"] == "API_ERROR"]

        # Generate markdown report
        report = []
        report.append("# DOI Validation Report")
        report.append("")
        report.append("## Summary")
        report.append("")
        report.append(f"- **Total failed DOIs validated**: {stats['total']}")
        report.append(f"- **Invalid DOIs** (not found in any database): {stats['invalid_doi']} ({stats['invalid_doi']/stats['total']*100:.1f}%)")
        report.append(f"- **Valid DOIs with abstract**: {stats['valid_with_abstract']} ({stats['valid_with_abstract']/stats['total']*100:.1f}%)")
        report.append(f"- **Valid DOIs without abstract**: {stats['valid_no_abstract']} ({stats['valid_no_abstract']/stats['total']*100:.1f}%)")
        report.append(f"- **Valid DOIs with minimal metadata**: {stats['valid_no_metadata']} ({stats['valid_no_metadata']/stats['total']*100:.1f}%)")
        report.append(f"- **API errors**: {stats['api_errors']} ({stats['api_errors']/stats['total']*100:.1f}%)")
        report.append("")

        # Invalid DOIs section
        if invalid_dois:
            report.append(f"## Invalid DOIs ({len(invalid_dois)})")
            report.append("")
            report.append("These DOIs do not exist in Crossref, Semantic Scholar, or Unpaywall:")
            report.append("")
            for r in invalid_dois:
                report.append(f"- `{r['doi']}`")
            report.append("")

        # Valid DOIs with abstracts
        if valid_with_abstract:
            report.append(f"## Valid DOIs with Abstracts ({len(valid_with_abstract)})")
            report.append("")
            report.append("These are real papers with abstracts - PDF just unavailable:")
            report.append("")
            for r in valid_with_abstract:
                meta = r["metadata"]
                report.append(f"### {r['doi']}")
                report.append(f"- **Title**: {meta.get('title', 'N/A')}")
                if meta.get("authors"):
                    report.append(f"- **Authors**: {', '.join(meta['authors'])}")
                if meta.get("year"):
                    report.append(f"- **Year**: {meta['year']}")
                if meta.get("container_title") or meta.get("journal"):
                    journal = meta.get("container_title") or meta.get("journal")
                    report.append(f"- **Journal**: {journal}")
                if meta.get("abstract"):
                    abstract_preview = meta["abstract"][:200] + "..." if len(meta["abstract"]) > 200 else meta["abstract"]
                    report.append(f"- **Abstract**: {abstract_preview}")
                report.append(f"- **Source**: {r['source']}")
                report.append("")

        # Valid DOIs without abstracts
        if valid_no_abstract:
            report.append(f"## Valid DOIs without Abstracts ({len(valid_no_abstract)})")
            report.append("")
            report.append("These are real papers but abstract not available:")
            report.append("")
            for r in valid_no_abstract:
                meta = r["metadata"]
                report.append(f"- `{r['doi']}` - {meta.get('title', 'N/A')} ({meta.get('year', 'N/A')})")
            report.append("")

        # API errors
        if api_errors:
            report.append(f"## API Errors ({len(api_errors)})")
            report.append("")
            report.append("Could not validate due to API errors (may need retry):")
            report.append("")
            for r in api_errors:
                report.append(f"- `{r['doi']}` - {r.get('error', 'Unknown error')}")
            report.append("")

        # Write report
        with open(output_path, "w") as f:
            f.write("\n".join(report))

        print(f"\n✓ Report written to {output_path}")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate failed DOIs")
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("csv_all_dois_results.json"),
        help="Path to results JSON file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("doi_validation_report.md"),
        help="Output report path",
    )
    parser.add_argument("--email", default="MJoachimiak@lbl.gov", help="Email for APIs")

    args = parser.parse_args()

    # Create validator
    validator = DOIValidator(email=args.email)

    # Validate failed DOIs
    print("DOI Validation")
    print("=" * 70)
    validation_data = validator.validate_failed_dois(args.results)

    # Generate report
    validator.generate_report(validation_data, args.output)

    # Save detailed JSON results
    json_output = args.output.with_suffix(".json")
    with open(json_output, "w") as f:
        json.dump(validation_data, f, indent=2)
    print(f"✓ Detailed results written to {json_output}")

    # Print summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    stats = validation_data["statistics"]
    print(f"Total validated: {stats['total']}")
    print(f"Invalid DOIs: {stats['invalid_doi']} ({stats['invalid_doi']/stats['total']*100:.1f}%)")
    print(f"Valid with abstract: {stats['valid_with_abstract']} ({stats['valid_with_abstract']/stats['total']*100:.1f}%)")
    print(f"Valid without abstract: {stats['valid_no_abstract']} ({stats['valid_no_abstract']/stats['total']*100:.1f}%)")
    print(f"API errors: {stats['api_errors']}")


if __name__ == "__main__":
    main()

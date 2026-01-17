#!/usr/bin/env python
"""
Find correct DOIs for invalid entries.

This script attempts to find the correct DOIs for the 21 invalid entries
by parsing metadata from the invalid DOI patterns and searching Crossref.
"""

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class DOIMetadata:
    """Metadata extracted from invalid DOI pattern."""

    invalid_doi: str
    publisher_prefix: str
    journal_code: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    page_start: Optional[str] = None
    page_end: Optional[str] = None
    year: Optional[str] = None
    article_id: Optional[str] = None


class DOICorrector:
    """Find correct DOIs for invalid entries."""

    def __init__(self, email: str = "your@email.com"):
        """Initialize DOI corrector.

        Args:
            email: Email for Crossref API (polite pool)
        """
        self.email = email
        self.crossref_base = "https://api.crossref.org/works/"

        # Setup session with retries
        self.session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Load invalid DOIs from validation results
        validation_path = Path("doi_validation_report.json")
        with open(validation_path) as f:
            validation_data = json.load(f)

        self.invalid_dois = self._extract_invalid_dois(validation_data)
        print(f"Loaded {len(self.invalid_dois)} invalid DOIs")

    def _extract_invalid_dois(self, validation_data: Dict) -> List[str]:
        """Extract list of invalid DOIs from validation results."""
        invalid = []
        for result in validation_data["validation_results"]:
            if result["category"] == "INVALID_DOI":
                doi = result["doi"]
                # Normalize to bare DOI (no URL prefix)
                if doi.startswith("https://doi.org/"):
                    doi = doi.replace("https://doi.org/", "")
                invalid.append(doi)
        return invalid

    def parse_asm_doi(self, doi: str) -> Optional[DOIMetadata]:
        """Parse ASM journal DOI pattern.

        Patterns:
        - 10.1128/JB.182.5.1346-1349.2000 (volume.issue.page-page.year)
        - 10.1128/jb.149.1.163-170.1982 (same, lowercase)
        - 10.1128/jb.183.16.4806 (volume.issue.page - incomplete?)
        - 10.1128/JB.01349-08 (article-year)
        - 10.1128/CMR.00010-10 (article-year)
        """
        match = re.match(
            r"10\.1128/([A-Za-z]+)\.(\d+)\.(\d+)\.(\d+)(?:-(\d+))?(?:\.(\d{4}))?",
            doi,
        )
        if match:
            return DOIMetadata(
                invalid_doi=doi,
                publisher_prefix="10.1128",
                journal_code=match.group(1),
                volume=match.group(2),
                issue=match.group(3),
                page_start=match.group(4),
                page_end=match.group(5),
                year=match.group(6),
            )

        # Try article-year pattern
        match = re.match(
            r"10\.1128/([A-Za-z]+)\.(\d+)-(\d{2})",
            doi,
        )
        if match:
            return DOIMetadata(
                invalid_doi=doi,
                publisher_prefix="10.1128",
                journal_code=match.group(1),
                article_id=match.group(2),
                year=f"20{match.group(3)}",  # Assume 20xx
            )

        return None

    def parse_elsevier_doi(self, doi: str) -> Optional[DOIMetadata]:
        """Parse Elsevier DOI pattern.

        Patterns:
        - 10.1016/S0006-2979(97)90180-5 (SXXXX-XXXX(YY)NNNNN-N)
        - 10.1016/S0304386X23001494 (seems malformed)
        """
        match = re.match(
            r"10\.1016/S(\d{4})-?(\d{4})\((\d{2})\)(\d+)-(\d+)",
            doi,
        )
        if match:
            year = match.group(3)
            # Assume 19xx or 20xx based on value
            if int(year) > 50:
                year = f"19{year}"
            else:
                year = f"20{year}"

            return DOIMetadata(
                invalid_doi=doi,
                publisher_prefix="10.1016",
                journal_code=f"{match.group(1)}-{match.group(2)}",
                year=year,
                page_start=match.group(4),
                page_end=match.group(5),
            )

        return None

    def search_crossref_by_metadata(
        self, metadata: DOIMetadata
    ) -> List[Dict[str, any]]:
        """Search Crossref for papers matching metadata.

        Args:
            metadata: Parsed DOI metadata

        Returns:
            List of potential matches from Crossref
        """
        # Build query
        query_parts = []

        if metadata.journal_code:
            query_parts.append(metadata.journal_code)

        if metadata.volume:
            query_parts.append(f"volume:{metadata.volume}")

        if metadata.year:
            query_parts.append(f"year:{metadata.year}")

        if not query_parts:
            return []

        query = " ".join(query_parts)
        print(f"  Searching Crossref: {query}")

        # Search Crossref
        url = "https://api.crossref.org/works"
        params = {
            "query": query,
            "rows": 10,
            "mailto": self.email,
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            items = data.get("message", {}).get("items", [])

            # Filter by additional criteria
            matches = []
            for item in items:
                # Check volume match
                if metadata.volume:
                    if str(item.get("volume", "")) != metadata.volume:
                        continue

                # Check year match
                if metadata.year:
                    pub_year = item.get("published-print", {}).get("date-parts", [[None]])[0][0]
                    if pub_year and str(pub_year) != metadata.year:
                        continue

                # Check page match (if available)
                if metadata.page_start:
                    page = item.get("page", "")
                    if metadata.page_start not in page:
                        continue

                matches.append(item)

            return matches

        except Exception as e:
            print(f"  Error searching Crossref: {e}")
            return []

    def suggest_correction(self, invalid_doi: str) -> Optional[Dict[str, any]]:
        """Suggest correction for an invalid DOI.

        Args:
            invalid_doi: The invalid DOI to correct

        Returns:
            Dictionary with suggested correction or None
        """
        print(f"\nProcessing: {invalid_doi}")

        # Parse metadata from DOI pattern
        metadata = None

        if invalid_doi.startswith("10.1128"):
            metadata = self.parse_asm_doi(invalid_doi)
        elif invalid_doi.startswith("10.1016"):
            metadata = self.parse_elsevier_doi(invalid_doi)

        if not metadata:
            print("  Unable to parse metadata from DOI pattern")
            return None

        print(f"  Parsed metadata: {metadata}")

        # Search Crossref
        matches = self.search_crossref_by_metadata(metadata)

        if not matches:
            print("  No matches found in Crossref")
            return None

        print(f"  Found {len(matches)} potential matches")

        # Return top match
        top_match = matches[0]

        return {
            "invalid_doi": invalid_doi,
            "suggested_doi": top_match.get("DOI"),
            "title": top_match.get("title", [None])[0],
            "year": top_match.get("published-print", {}).get("date-parts", [[None]])[0][0],
            "journal": top_match.get("container-title", [None])[0],
            "volume": top_match.get("volume"),
            "page": top_match.get("page"),
            "score": top_match.get("score"),
            "confidence": "high" if len(matches) == 1 else "medium",
        }

    def process_all(self) -> List[Dict[str, any]]:
        """Process all invalid DOIs and suggest corrections.

        Returns:
            List of suggestion dictionaries
        """
        suggestions = []

        for doi in self.invalid_dois:
            suggestion = self.suggest_correction(doi)
            if suggestion:
                suggestions.append(suggestion)

            # Be polite to Crossref API
            time.sleep(1)

        return suggestions

    def generate_report(
        self, suggestions: List[Dict[str, any]], output_path: Path
    ) -> None:
        """Generate report of suggested corrections.

        Args:
            suggestions: List of suggestion dictionaries
            output_path: Path for output report
        """
        report = []
        report.append("# DOI Correction Suggestions")
        report.append("")
        report.append(f"**Total invalid DOIs:** {len(self.invalid_dois)}")
        report.append(f"**Suggestions found:** {len(suggestions)}")
        report.append(f"**Needs manual review:** {len(self.invalid_dois) - len(suggestions)}")
        report.append("")

        # Suggestions
        if suggestions:
            report.append("## Suggested Corrections")
            report.append("")

            for s in suggestions:
                report.append(f"### {s['invalid_doi']}")
                report.append("")
                report.append(f"**Suggested DOI:** {s['suggested_doi']}")
                report.append(f"**Title:** {s['title']}")
                report.append(f"**Journal:** {s['journal']}")
                report.append(f"**Year:** {s['year']}")
                report.append(f"**Volume:** {s['volume']}")
                report.append(f"**Pages:** {s['page']}")
                report.append(f"**Confidence:** {s['confidence']}")
                report.append("")

        # DOIs without suggestions
        suggested_dois = {s["invalid_doi"] for s in suggestions}
        needs_manual = [doi for doi in self.invalid_dois if doi not in suggested_dois]

        if needs_manual:
            report.append("## Needs Manual Review")
            report.append("")
            report.append("These DOIs could not be automatically corrected:")
            report.append("")
            for doi in needs_manual:
                report.append(f"- {doi}")
            report.append("")

        with open(output_path, "w") as f:
            f.write("\n".join(report))

        print(f"\n✓ Report written to {output_path}")

    def save_suggestions_json(
        self, suggestions: List[Dict[str, any]], output_path: Path
    ) -> None:
        """Save suggestions as JSON.

        Args:
            suggestions: List of suggestion dictionaries
            output_path: Path for JSON output
        """
        with open(output_path, "w") as f:
            json.dump(suggestions, f, indent=2)

        print(f"✓ JSON saved to {output_path}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Find correct DOIs for invalid entries")
    parser.add_argument(
        "--email",
        type=str,
        default="MJoachimiak@lbl.gov",
        help="Email for Crossref API",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("doi_correction_suggestions.md"),
        help="Output report path",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=Path("doi_correction_suggestions.json"),
        help="Output JSON path",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("DOI Corrector")
    print("=" * 70)

    corrector = DOICorrector(email=args.email)

    print("\nSearching for corrections...")
    print("-" * 70)

    suggestions = corrector.process_all()

    print("\n" + "=" * 70)
    print(f"Found {len(suggestions)} suggestions")
    print("=" * 70)

    # Generate reports
    corrector.generate_report(suggestions, args.report)
    corrector.save_suggestions_json(suggestions, args.json)

    print("\nNext steps:")
    print(f"1. Review suggestions in {args.report}")
    print("2. Manually verify each suggestion")
    print("3. Update CSV with corrected DOIs")
    print("4. Re-run PDF download for corrected DOIs")


if __name__ == "__main__":
    main()

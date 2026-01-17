#!/usr/bin/env python
"""
Generate search links for manual DOI correction.

This script creates direct search URLs for each invalid DOI to facilitate
manual correction.
"""

import json
import re
from pathlib import Path
from typing import Dict, List
from urllib.parse import quote


class SearchLinkGenerator:
    """Generate search links for invalid DOIs."""

    def __init__(self, validation_path: Path):
        """Initialize generator.

        Args:
            validation_path: Path to DOI validation JSON
        """
        # Load invalid DOIs
        with open(validation_path) as f:
            validation_data = json.load(f)

        self.invalid_dois = []
        for result in validation_data["validation_results"]:
            if result["category"] == "INVALID_DOI":
                doi = result["doi"]
                if doi.startswith("https://doi.org/"):
                    doi = doi.replace("https://doi.org/", "")
                self.invalid_dois.append(doi)

        print(f"Loaded {len(self.invalid_dois)} invalid DOIs")

    def generate_google_scholar_url(self, doi: str) -> str:
        """Generate Google Scholar search URL."""
        query = doi
        return f"https://scholar.google.com/scholar?q={quote(query)}"

    def generate_pubmed_url(self, search_terms: str) -> str:
        """Generate PubMed search URL."""
        return f"https://pubmed.ncbi.nlm.nih.gov/?term={quote(search_terms)}"

    def generate_crossref_search_url(self, doi: str) -> str:
        """Generate Crossref search URL."""
        return f"https://search.crossref.org/?q={quote(doi)}"

    def generate_asm_journal_url(self, doi: str) -> str:
        """Generate ASM journals search URL for specific citation."""
        # Parse ASM DOI pattern
        match = re.match(
            r"10\.1128/([A-Za-z]+)\.(\d+)\.(\d+)\.(\d+)(?:-(\d+))?(?:\.(\d{4}))?",
            doi,
        )
        if match:
            journal = match.group(1).upper()
            volume = match.group(2)
            issue = match.group(3)
            page_start = match.group(4)
            year = match.group(6)

            if year and volume:
                # Search for specific volume and year
                search = f"{journal} {year} volume {volume}"
                return f"https://journals.asm.org/search/{quote(search)}"

        # Fallback: generic ASM search
        return f"https://journals.asm.org/search/{quote(doi)}"

    def parse_asm_citation(self, doi: str) -> Dict[str, str]:
        """Parse ASM DOI into citation components."""
        match = re.match(
            r"10\.1128/([A-Za-z]+)\.(\d+)\.(\d+)\.(\d+)(?:-(\d+))?(?:\.(\d{4}))?",
            doi,
        )
        if match:
            return {
                "journal": match.group(1).upper(),
                "volume": match.group(2),
                "issue": match.group(3),
                "page_start": match.group(4),
                "page_end": match.group(5) or "",
                "year": match.group(6) or "unknown",
            }
        return {}

    def generate_links_for_doi(self, doi: str) -> Dict[str, str]:
        """Generate all relevant search links for a DOI."""
        links = {
            "google_scholar": self.generate_google_scholar_url(doi),
            "crossref": self.generate_crossref_search_url(doi),
        }

        # Add journal-specific links
        if doi.startswith("10.1128"):
            links["asm_journals"] = self.generate_asm_journal_url(doi)
            citation = self.parse_asm_citation(doi)
            if citation:
                # PubMed search with citation details
                search_terms = f"{citation.get('journal', '')} {citation.get('year', '')} {citation.get('volume', '')}"
                links["pubmed"] = self.generate_pubmed_url(search_terms)

        elif doi.startswith("10.1074/jbc"):
            # JBC specific
            links["jbc"] = f"https://www.jbc.org/search/{quote(doi)}"

        elif doi.startswith("10.1073/pnas"):
            # PNAS specific
            links["pnas"] = f"https://www.pnas.org/search/{quote(doi)}"

        return links

    def generate_html_report(self, output_path: Path) -> None:
        """Generate HTML report with clickable search links.

        Args:
            output_path: Path for HTML output
        """
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("  <title>DOI Correction Search Links</title>")
        html.append("  <style>")
        html.append("    body { font-family: Arial, sans-serif; margin: 40px; }")
        html.append("    h1 { color: #333; }")
        html.append("    .doi-section { margin: 30px 0; padding: 20px; border: 1px solid #ddd; }")
        html.append("    .doi-code { font-family: monospace; font-size: 14px; background: #f5f5f5; padding: 5px; }")
        html.append("    .links { margin: 15px 0; }")
        html.append("    .link-button { ")
        html.append("      display: inline-block; margin: 5px; padding: 10px 15px; ")
        html.append("      background: #007bff; color: white; text-decoration: none; ")
        html.append("      border-radius: 4px; ")
        html.append("    }")
        html.append("    .link-button:hover { background: #0056b3; }")
        html.append("    .citation { font-style: italic; color: #666; }")
        html.append("  </style>")
        html.append("</head>")
        html.append("<body>")
        html.append("  <h1>DOI Correction Search Links</h1>")
        html.append(f"  <p>Total invalid DOIs: {len(self.invalid_dois)}</p>")
        html.append("  <p>Click the search links below to find the correct papers manually.</p>")
        html.append("  <hr>")

        for doi in sorted(self.invalid_dois):
            html.append(f'  <div class="doi-section">')
            html.append(f'    <h2 class="doi-code">{doi}</h2>')

            # Add citation info for ASM journals
            if doi.startswith("10.1128"):
                citation = self.parse_asm_citation(doi)
                if citation:
                    journal = citation.get("journal", "")
                    year = citation.get("year", "")
                    volume = citation.get("volume", "")
                    issue = citation.get("issue", "")
                    pages = f"{citation.get('page_start', '')}"
                    if citation.get("page_end"):
                        pages += f"-{citation.get('page_end')}"

                    html.append(f'    <p class="citation">')
                    html.append(f'      Parsed citation: {journal} ({year}) Vol {volume}({issue}): {pages}')
                    html.append(f'    </p>')

            # Search links
            links = self.generate_links_for_doi(doi)
            html.append(f'    <div class="links">')
            html.append(f'      <strong>Search in:</strong><br>')

            for link_name, link_url in links.items():
                display_name = link_name.replace("_", " ").title()
                html.append(f'      <a href="{link_url}" target="_blank" class="link-button">{display_name}</a>')

            html.append(f'    </div>')
            html.append(f'  </div>')

        html.append("</body>")
        html.append("</html>")

        with open(output_path, "w") as f:
            f.write("\n".join(html))

        print(f"\n✓ HTML report with search links: {output_path}")
        print(f"  Open this file in your browser to access clickable search links")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate search links for DOI correction")
    parser.add_argument(
        "--validation",
        type=Path,
        default=Path("doi_validation_report.json"),
        help="DOI validation JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("doi_search_links.html"),
        help="Output HTML path",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Search Link Generator")
    print("=" * 70)

    generator = SearchLinkGenerator(validation_path=args.validation)

    print("\nGenerating search links...")
    generator.generate_html_report(args.output)

    print("\n" + "=" * 70)
    print("Complete!")
    print("=" * 70)
    print(f"\nOpen {args.output} in your browser to start searching")


if __name__ == "__main__":
    main()

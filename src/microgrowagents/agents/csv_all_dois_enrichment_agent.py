"""CSV All-DOIs Enrichment Agent.

This agent processes ALL DOI columns in the MP medium ingredient properties CSV,
downloading PDFs for all 146 unique DOIs across 20 citation columns.
"""

import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd

from microgrowagents.agents.base_agent import BaseAgent
from microgrowagents.agents.pdf_evidence_extractor import PDFEvidenceExtractor


class CSVAllDOIsEnrichmentAgent(BaseAgent):
    """Agent for downloading all PDFs referenced in CSV DOI columns.

    This agent processes all 20 DOI citation columns in the MP medium ingredient
    properties CSV file, downloading PDFs for all unique DOIs using a cascading
    source approach.

    Sources tried (in order):
    1. Direct publisher access
    2. PubMed Central (PMC)
    3. Unpaywall API
    4. Semantic Scholar
    5. Web search (arXiv, bioRxiv, Sci-Hub, etc.)

    Examples:
        >>> agent = CSVAllDOIsEnrichmentAgent(
        ...     csv_path=Path("data/raw/mp_medium_ingredient_properties.csv"),
        ...     email="MJoachimiak@lbl.gov"
        ... )
        >>> result = agent.run(limit=10, dry_run=False)
        >>> print(f"Downloaded {result['stats']['successful']} PDFs")
    """

    def __init__(
        self,
        csv_path: Path,
        email: str = "your@email.com",
        pdf_cache_dir: Optional[Path] = None,
        db_path: Optional[Path] = None,
        use_fallback_pdf: bool = True,
    ):
        """Initialize the CSV All-DOIs Enrichment Agent.

        Args:
            csv_path: Path to MP medium ingredient properties CSV
            email: Academic email for Unpaywall API
            pdf_cache_dir: Directory to cache downloaded PDFs (default: /tmp/microgrow_pdfs)
            db_path: Path to DuckDB database (optional, not used for this agent)
            use_fallback_pdf: Whether to use fallback PDF sources for paywalled papers (default: True)
        """
        super().__init__(db_path)
        self.csv_path = Path(csv_path)
        self.email = email
        self.use_fallback_pdf = use_fallback_pdf

        # Set up PDF cache directory
        if pdf_cache_dir is None:
            self.pdf_cache_dir = Path("/tmp/microgrow_pdfs")
        else:
            self.pdf_cache_dir = Path(pdf_cache_dir)

        self.pdf_cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize PDF extractor with custom cache dir and fallback PDF setting
        self.pdf_extractor = PDFEvidenceExtractor(email=email, use_fallback_pdf=use_fallback_pdf)
        # Override the pdf_extractor's cache directory
        self.pdf_extractor.pdf_cache_dir = self.pdf_cache_dir

        # DOI pattern for extraction
        self.doi_pattern = re.compile(r"https?://doi\.org/[^\s,;]+")

    def get_doi_columns(self) -> List[str]:
        """Get list of all DOI citation columns from CSV.

        Returns:
            List of column names containing 'DOI'
        """
        df = pd.read_csv(self.csv_path)
        return [col for col in df.columns if "DOI" in col]

    def extract_dois_from_text(self, text: str) -> List[str]:
        """Extract all DOIs from a text string.

        Args:
            text: Text potentially containing DOIs

        Returns:
            List of DOI URLs found in text
        """
        if pd.isna(text) or not str(text).strip():
            return []

        matches = self.doi_pattern.findall(str(text))
        return [self.normalize_doi(doi) for doi in matches]

    def normalize_doi(self, doi: str) -> str:
        """Normalize DOI to standard HTTPS URL format.

        Args:
            doi: DOI in any format (URL or bare DOI)

        Returns:
            Normalized DOI as https://doi.org/... URL
        """
        # Strip whitespace
        doi = doi.strip()

        # If already a full URL, convert http to https
        if doi.startswith("http://doi.org/"):
            return doi.replace("http://", "https://")
        elif doi.startswith("https://doi.org/"):
            return doi
        # If bare DOI (starts with 10.), add https://doi.org/
        elif doi.startswith("10."):
            return f"https://doi.org/{doi}"
        else:
            return doi

    def extract_all_dois(self) -> Set[str]:
        """Extract all unique DOIs from all DOI columns in CSV.

        Returns:
            Set of unique DOI URLs
        """
        df = pd.read_csv(self.csv_path)
        doi_columns = self.get_doi_columns()

        all_dois = set()

        for col in doi_columns:
            for value in df[col]:
                dois = self.extract_dois_from_text(value)
                all_dois.update(dois)

        return all_dois

    def extract_dois_by_column(self) -> Dict[str, Set[str]]:
        """Extract DOIs grouped by column.

        Returns:
            Dictionary mapping column name to set of DOIs
        """
        df = pd.read_csv(self.csv_path)
        doi_columns = self.get_doi_columns()

        dois_by_column = {}

        for col in doi_columns:
            column_dois = set()
            for value in df[col]:
                dois = self.extract_dois_from_text(value)
                column_dois.update(dois)
            dois_by_column[col] = column_dois

        return dois_by_column

    def download_doi_pdf(self, doi: str) -> Dict[str, Any]:
        """Download PDF for a single DOI.

        Uses the PDFEvidenceExtractor with cascading source lookup.

        Args:
            doi: DOI URL to download

        Returns:
            Dictionary with keys:
                - success: bool
                - doi: str
                - source: str (if successful)
                - pdf_path: Path (if successful)
                - error: str (if failed)
        """
        # Check cache first
        doi_safe = doi.replace("https://doi.org/", "").replace(
            "http://doi.org/", ""
        )
        doi_safe = doi_safe.replace("/", "_").replace(".", "_")
        cached_pdf = self.pdf_cache_dir / f"{doi_safe}.pdf"

        if cached_pdf.exists():
            return {
                "success": True,
                "doi": doi,
                "source": "cache",
                "pdf_path": cached_pdf,
            }

        # Try downloading with cascading sources
        try:
            # Use the PDF extractor's method but without requiring ingredient_id
            pdf_url = None
            source = None

            # Try 1: Publisher
            pdf_url = self.pdf_extractor._get_pdf_url_from_publisher(doi)
            if pdf_url:
                source = "publisher"

            # Try 2: PMC
            if not pdf_url:
                pdf_url = self.pdf_extractor._get_pdf_url_from_pmc(doi)
                if pdf_url:
                    source = "pmc"

            # Try 3: Unpaywall
            if not pdf_url:
                pdf_url = self.pdf_extractor._get_pdf_url_from_unpaywall(doi)
                if pdf_url:
                    source = "unpaywall"

            # Try 4: Semantic Scholar
            if not pdf_url:
                pdf_url = self.pdf_extractor._get_pdf_url_from_semantic_scholar(doi)
                if pdf_url:
                    source = "semantic_scholar"

            # Try 5: Web search
            if not pdf_url:
                pdf_url = self.pdf_extractor._get_pdf_url_from_web_search(doi)
                if pdf_url:
                    source = "web_search"

            if not pdf_url:
                return {
                    "success": False,
                    "doi": doi,
                    "error": "No PDF source found",
                }

            # Download the PDF
            pdf_path = self.pdf_extractor._download_pdf(pdf_url, doi)

            if pdf_path and pdf_path.exists():
                return {
                    "success": True,
                    "doi": doi,
                    "source": source,
                    "pdf_path": pdf_path,
                }
            else:
                return {
                    "success": False,
                    "doi": doi,
                    "error": "PDF download failed",
                }

        except Exception as e:
            return {"success": False, "doi": doi, "error": str(e)}

    def run(
        self, limit: Optional[int] = None, dry_run: bool = False
    ) -> Dict[str, Any]:
        """Process all DOIs from CSV and download PDFs.

        Args:
            limit: Maximum number of DOIs to process (for testing)
            dry_run: If True, only extract DOIs without downloading

        Returns:
            Dictionary with keys:
                - success: bool
                - stats: dict with statistics
                - results: list of download results
                - dois_by_column: dict mapping columns to DOIs
        """
        print("=" * 70)
        print("CSV All-DOIs Enrichment Agent")
        print("=" * 70)

        # Extract all DOIs
        all_dois = self.extract_all_dois()
        dois_by_column = self.extract_dois_by_column()

        print(f"\nTotal unique DOIs found: {len(all_dois)}")
        print(f"DOI columns: {len(self.get_doi_columns())}")

        if dry_run:
            print("\n[DRY RUN] Not downloading PDFs")
            return {
                "success": True,
                "stats": {
                    "total_dois": len(all_dois),
                    "doi_columns": len(self.get_doi_columns()),
                    "pdfs_downloaded": 0,
                },
                "results": [],
                "dois_by_column": {
                    col: list(dois) for col, dois in dois_by_column.items()
                },
            }

        # Download PDFs
        dois_to_process = sorted(all_dois)
        if limit:
            dois_to_process = dois_to_process[:limit]
            print(f"\n[LIMIT] Processing first {limit} DOIs only")

        results = []
        successful = 0
        failed = 0

        print(f"\nDownloading {len(dois_to_process)} PDFs...")
        print("-" * 70)

        for i, doi in enumerate(dois_to_process, 1):
            print(f"\n[{i}/{len(dois_to_process)}] {doi}")

            result = self.download_doi_pdf(doi)
            results.append(result)

            if result["success"]:
                successful += 1
                print(f"  ✓ Downloaded from {result['source']}")
            else:
                failed += 1
                print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")

        # Generate statistics
        stats = self.generate_statistics(results)

        print("\n" + "=" * 70)
        print("Summary")
        print("=" * 70)
        print(f"Total DOIs: {stats['total']}")
        print(f"Successful: {stats['successful']} ({stats['success_rate']:.1f}%)")
        print(f"Failed: {stats['failed']}")
        print("\nSources:")
        for source, count in stats["sources"].items():
            print(f"  {source}: {count}")

        return {
            "success": True,
            "stats": stats,
            "results": results,
            "dois_by_column": {
                col: list(dois) for col, dois in dois_by_column.items()
            },
        }

    def generate_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate statistics from download results.

        Args:
            results: List of download result dictionaries

        Returns:
            Dictionary with summary statistics
        """
        total = len(results)
        successful = sum(1 for r in results if r["success"])
        failed = total - successful

        # Count by source
        sources = defaultdict(int)
        for r in results:
            if r["success"]:
                sources[r["source"]] += 1

        # Count by error type
        errors = defaultdict(int)
        for r in results:
            if not r["success"]:
                error = r.get("error", "Unknown error")
                # Simplify error messages
                if "403" in error or "Forbidden" in error:
                    errors["403 Forbidden (Paywall)"] += 1
                elif "404" in error or "Not Found" in error:
                    errors["404 Not Found"] += 1
                elif "No PDF source" in error:
                    errors["No source found"] += 1
                else:
                    errors[error] += 1

        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "sources": dict(sources),
            "errors": dict(errors),
        }

    def generate_report(
        self, results: List[Dict[str, Any]], output_path: Path
    ) -> None:
        """Generate a markdown report of download results.

        Args:
            results: List of download result dictionaries
            output_path: Path to save markdown report
        """
        stats = self.generate_statistics(results)

        report = []
        report.append("# PDF Download Report")
        report.append("")
        report.append(f"**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**CSV Source:** `{self.csv_path}`")
        report.append("")

        # Summary
        report.append("## Summary")
        report.append("")
        report.append(f"- **Total DOIs:** {stats['total']}")
        report.append(
            f"- **Successful Downloads:** {stats['successful']} ({stats['success_rate']:.1f}%)"
        )
        report.append(f"- **Failed Downloads:** {stats['failed']}")
        report.append("")

        # Sources breakdown
        report.append("## Downloads by Source")
        report.append("")
        report.append("| Source | Count |")
        report.append("|--------|-------|")
        for source, count in sorted(
            stats["sources"].items(), key=lambda x: x[1], reverse=True
        ):
            report.append(f"| {source} | {count} |")
        report.append("")

        # Errors breakdown
        if stats["errors"]:
            report.append("## Errors")
            report.append("")
            report.append("| Error Type | Count |")
            report.append("|------------|-------|")
            for error, count in sorted(
                stats["errors"].items(), key=lambda x: x[1], reverse=True
            ):
                report.append(f"| {error} | {count} |")
            report.append("")

        # Successful downloads
        successful_results = [r for r in results if r["success"]]
        if successful_results:
            report.append("## Successful Downloads")
            report.append("")
            for r in successful_results:
                doi_short = r["doi"].replace("https://doi.org/", "")
                report.append(f"- [{doi_short}]({r['doi']}) - {r['source']}")
            report.append("")

        # Failed downloads
        failed_results = [r for r in results if not r["success"]]
        if failed_results:
            report.append("## Failed Downloads")
            report.append("")
            for r in failed_results:
                doi_short = r["doi"].replace("https://doi.org/", "")
                error = r.get("error", "Unknown error")
                report.append(f"- [{doi_short}]({r['doi']}) - {error}")
            report.append("")

        # Write report
        output_path.write_text("\n".join(report))
        print(f"\n✓ Report saved to: {output_path}")

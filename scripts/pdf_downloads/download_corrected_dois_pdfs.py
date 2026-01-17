#!/usr/bin/env python
"""
Download PDFs for corrected DOIs.

This script reads the corrections file and downloads PDFs for all
successfully corrected DOIs.
"""

from pathlib import Path
from typing import Dict, List

import yaml

from microgrowagents.agents.pdf_evidence_extractor import PDFEvidenceExtractor


def load_corrections(corrections_file: Path) -> List[str]:
    """Load corrected DOIs from YAML file.

    Args:
        corrections_file: Path to corrections YAML file

    Returns:
        List of corrected DOIs (only non-empty ones)
    """
    with open(corrections_file) as f:
        data = yaml.safe_load(f)

    corrected_dois = []

    if "corrections" in data:
        for item in data["corrections"]:
            corrected_doi = item.get("corrected_doi", "")

            if corrected_doi and corrected_doi.strip():
                # Normalize to full URL
                if not corrected_doi.startswith("https://doi.org/"):
                    corrected_doi = f"https://doi.org/{corrected_doi}"

                corrected_dois.append(corrected_doi)

    return corrected_dois


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Download PDFs for corrected DOIs"
    )
    parser.add_argument(
        "--corrections",
        type=Path,
        default=Path("doi_corrections.yaml"),
        help="Corrections YAML file",
    )
    parser.add_argument(
        "--email",
        type=str,
        default="MJoachimiak@lbl.gov",
        help="Email for Unpaywall API",
    )
    parser.add_argument(
        "--use-fallback-pdf",
        action="store_true",
        default=True,
        help="Use fallback PDF sources",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Download PDFs for Corrected DOIs")
    print("=" * 70)

    # Load corrected DOIs
    print(f"\nLoading corrections from: {args.corrections}")
    corrected_dois = load_corrections(args.corrections)

    if not corrected_dois:
        print("\nNo corrected DOIs found in the corrections file.")
        print("Please fill in the corrected_doi fields in doi_corrections.yaml")
        return

    print(f"Found {len(corrected_dois)} corrected DOIs")

    # Create PDF extractor
    extractor = PDFEvidenceExtractor(
        email=args.email,
        use_fallback_pdf=args.use_fallback_pdf,
    )

    # Download PDFs
    results = []
    successful = 0
    failed = 0

    print(f"\nDownloading {len(corrected_dois)} PDFs...")
    print("-" * 70)

    for i, doi in enumerate(corrected_dois, 1):
        print(f"\n[{i}/{len(corrected_dois)}] {doi}")

        # Download PDF
        result = extractor.download_pdf(doi)

        if result["success"]:
            successful += 1
            print(f"  ✓ Downloaded from {result.get('source', 'unknown')}")
        else:
            failed += 1
            print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")

        results.append(result)

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Total corrected DOIs: {len(corrected_dois)}")
    print(f"Successful downloads: {successful} ({successful/len(corrected_dois)*100:.1f}%)")
    print(f"Failed downloads: {failed}")

    # Source breakdown
    sources = {}
    for r in results:
        if r["success"]:
            source = r.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1

    if sources:
        print("\nSources:")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count}")


if __name__ == "__main__":
    main()

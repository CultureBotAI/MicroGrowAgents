#!/usr/bin/env python3
"""
Automated PDF downloader for all CSV DOIs using Unpaywall + fallback sources.

This script uses the "aurelian method" - Unpaywall API with fallback PDF sources
to download all 158 unique DOIs from the CSV file.
"""

import csv
import json
import time
from pathlib import Path

from microgrowagents.agents.pdf_evidence_extractor import PDFEvidenceExtractor


def extract_all_dois_from_csv(csv_path: Path) -> list[str]:
    """Extract all unique DOIs from CSV file."""
    all_dois = []

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

        # Find all DOI columns
        if rows:
            doi_columns = [col for col in rows[0].keys() if 'DOI' in col or 'Citation' in col]

            # Extract DOIs
            for row in rows:
                for col in doi_columns:
                    doi = row.get(col, '').strip()
                    if doi and doi.startswith('https://doi.org/'):
                        doi_clean = doi.replace('https://doi.org/', '')
                        all_dois.append(doi_clean)

    return sorted(set(all_dois))


def main():
    """Download all PDFs using automated method."""
    print("\n" + "=" * 80)
    print("Automated PDF Downloader - Aurelian Method")
    print("Using: Unpaywall API + Fallback PDF Sources")
    print("=" * 80)

    # Configuration
    csv_path = Path("data/raw/mp_medium_ingredient_properties.csv")
    email = "MJoachimiak@lbl.gov"
    pdf_cache_dir = Path("data/pdfs")
    pdf_cache_dir.mkdir(exist_ok=True, parents=True)

    # Extract DOIs
    print(f"\n📄 Extracting DOIs from: {csv_path}")
    unique_dois = extract_all_dois_from_csv(csv_path)
    print(f"✓ Found {len(unique_dois)} unique DOIs")

    # Check existing PDFs
    existing_pdfs = set()
    for pdf_file in pdf_cache_dir.glob("*.pdf"):
        # Extract DOI from filename
        doi = pdf_file.stem.replace('_', '/')
        existing_pdfs.add(doi)

    print(f"✓ Already downloaded: {len(existing_pdfs)} PDFs")

    # Filter to missing DOIs
    missing_dois = [doi for doi in unique_dois if doi not in existing_pdfs]
    print(f"✓ Need to download: {len(missing_dois)} PDFs")

    if not missing_dois:
        print("\n✅ All PDFs already downloaded!")
        return

    # Auto-proceed (comment out for interactive mode)
    print(f"\n📥 Starting download of {len(missing_dois)} PDFs")
    print(f"   Target directory: {pdf_cache_dir}")
    print(f"   Method: Unpaywall API + Fallback sources")
    print(f"   Email: {email}")
    print("\n✓ Auto-proceeding with download...")

    # Initialize PDF extractor with fallback enabled
    print("\n🚀 Initializing PDF extractor...")
    extractor = PDFEvidenceExtractor(email=email, use_fallback_pdf=True)
    # Override cache directory to use data/pdfs
    extractor.cache_dir = pdf_cache_dir
    print(f"✓ PDF cache directory: {extractor.cache_dir}")

    # Download stats
    stats = {
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "errors": []
    }

    results = []

    # Download each DOI
    print(f"\n📥 Downloading {len(missing_dois)} PDFs...\n")

    for i, doi in enumerate(missing_dois, 1):
        print(f"[{i}/{len(missing_dois)}] {doi}")

        try:
            # Check if PDF already exists (double-check)
            pdf_filename = doi.replace('/', '_') + '.pdf'
            pdf_path = pdf_cache_dir / pdf_filename

            if pdf_path.exists():
                print(f"  ⏭️  Already exists")
                stats["skipped"] += 1
                continue

            # Attempt download
            result = extractor._download_pdf(doi)

            if result and result.get("success"):
                print(f"  ✅ Downloaded successfully")
                stats["success"] += 1
                results.append({
                    "doi": doi,
                    "status": "success",
                    "source": result.get("source", "unknown"),
                    "pdf_path": str(pdf_path)
                })
            else:
                error_msg = result.get("error", "Unknown error") if result else "No result"
                print(f"  ❌ Failed: {error_msg}")
                stats["failed"] += 1
                stats["errors"].append({
                    "doi": doi,
                    "error": error_msg
                })
                results.append({
                    "doi": doi,
                    "status": "failed",
                    "error": error_msg
                })

            # Rate limiting - be polite to servers
            time.sleep(2)

        except Exception as e:
            print(f"  ⚠️  Error: {str(e)}")
            stats["failed"] += 1
            stats["errors"].append({
                "doi": doi,
                "error": str(e)
            })
            results.append({
                "doi": doi,
                "status": "error",
                "error": str(e)
            })
            time.sleep(2)

    # Summary
    print("\n" + "=" * 80)
    print("Download Summary")
    print("=" * 80)
    print(f"✅ Successful: {stats['success']}")
    print(f"⏭️  Skipped:    {stats['skipped']}")
    print(f"❌ Failed:     {stats['failed']}")
    print(f"📊 Total:      {len(missing_dois)}")

    success_rate = (stats['success'] / len(missing_dois) * 100) if missing_dois else 0
    print(f"\n📈 Success rate: {success_rate:.1f}%")

    # Save results
    results_file = Path("pdf_download_results.json")
    with open(results_file, 'w') as f:
        json.dump({
            "stats": stats,
            "results": results
        }, f, indent=2)

    print(f"\n✓ Results saved to: {results_file}")

    # Show failed DOIs if any
    if stats["errors"]:
        print(f"\n⚠️  {len(stats['errors'])} DOIs failed to download:")
        for error in stats["errors"][:10]:  # Show first 10
            print(f"  - {error['doi']}: {error['error']}")

        if len(stats["errors"]) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more")

        print(f"\nSee {results_file} for full error details")

    print("\n✅ Done!")
    print(f"\nPDFs saved to: {pdf_cache_dir}")


if __name__ == "__main__":
    main()

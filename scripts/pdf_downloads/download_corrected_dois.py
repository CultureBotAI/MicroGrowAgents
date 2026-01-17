#!/usr/bin/env python3
"""
Download PDFs for the 7 corrected DOIs using the existing PDFEvidenceExtractor
which includes unpaywall and fallback PDF sources (Aurelian method).
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from microgrowagents.agents.pdf_evidence_extractor import PDFEvidenceExtractor


# The 7 corrected DOIs from our correction work
CORRECTED_DOIS = [
    {
        "doi": "https://doi.org/10.1016/S0969-2126(96)00095-0",
        "title": "Molecular dynamics study of unbinding of the avidin-biotin complex",
        "correction": "Biotin - Avidin Binding",
        "ingredient": "Biotin"
    },
    {
        "doi": "https://doi.org/10.1074/jbc.RA119.010023",
        "title": "Zinc excess increases cellular demand for iron...",
        "correction": "Zinc Antagonistic Effects",
        "ingredient": "ZnSO₄·7H₂O"
    },
    {
        "doi": "https://doi.org/10.1016/S0168-6445(03)00052-4",
        "title": "Emerging themes in manganese transport...",
        "correction": "Manganese Transport",
        "ingredient": "MnCl₂·4H₂O"
    },
    {
        "doi": "https://doi.org/10.1074/jbc.R116.742023",
        "title": "Bacterial Strategies to Maintain Zinc Metallostasis...",
        "correction": "Zinc Metalloproteins Review",
        "ingredient": "ZnSO₄·7H₂O"
    },
    {
        "doi": "https://doi.org/10.1016/j.colsurfb.2006.04.014",
        "title": "Selective accumulation of light or heavy rare earth elements...",
        "correction": "Neodymium Bacteria",
        "ingredient": "Neodymium (III) chloride hexahydrate"
    },
    {
        "doi": "https://doi.org/10.1021/ja00485a018",
        "title": "Coordination chemistry of microbial iron transport compounds...",
        "correction": "Enterobactin Iron",
        "ingredient": "FeSO₄·7H₂O"
    },
    {
        "doi": "https://doi.org/10.1093/nar/gkg900",
        "title": "Coenzyme B12 riboswitches...",
        "correction": "B12 Riboswitch",
        "ingredient": "CoCl₂·6H₂O"
    }
]


def get_pdf_filename(doi: str) -> str:
    """Generate PDF filename from DOI."""
    clean_doi = doi.replace('https://doi.org/', '').replace('http://doi.org/', '')
    safe_name = clean_doi.replace('/', '_').replace('\\', '_')
    return f"{safe_name}.pdf"


def check_pdf_exists(doi: str, pdf_dir: Path) -> bool:
    """Check if PDF already exists."""
    filename = get_pdf_filename(doi)
    pdf_path = pdf_dir / filename
    return pdf_path.exists()


def main():
    """Download PDFs for corrected DOIs using PDFEvidenceExtractor."""

    # Setup
    pdf_dir = Path('data/pdfs')
    pdf_dir.mkdir(parents=True, exist_ok=True)

    # Initialize PDF extractor with fallback enabled
    email = "microgrow@example.com"
    extractor = PDFEvidenceExtractor(email=email, use_fallback_pdf=True)

    print("Downloading PDFs for 7 corrected DOIs")
    print("Using PDFEvidenceExtractor with fallback PDF sources")
    print(f"Fallback mirrors: {extractor.fallback_pdf_urls}")
    print("="*70)

    results = []
    existing_count = 0
    downloaded_count = 0
    failed_count = 0

    for doi_info in CORRECTED_DOIS:
        doi = doi_info['doi']
        print(f"\n{doi_info['correction']}")
        print(f"DOI: {doi}")
        print(f"Title: {doi_info['title'][:60]}...")

        # Check if PDF already exists
        if check_pdf_exists(doi, pdf_dir):
            print(f"  ✓ PDF already exists")
            existing_count += 1
            results.append({
                'doi': doi,
                'correction': doi_info['correction'],
                'ingredient': doi_info['ingredient'],
                'status': 'exists',
                'method': None
            })
            continue

        # Try to download using the extractor
        print(f"  Attempting download via PDFEvidenceExtractor...")
        try:
            # Use extract_from_doi which handles the full cascade
            result = extractor.extract_from_doi(
                doi=doi,
                ingredient_id=doi_info['ingredient'],
                concentration_low=None,
                concentration_high=None,
                toxicity_value=None
            )

            if result.get('pdf_path'):
                # PDF was downloaded, move it to our pdfs directory
                src_path = Path(result['pdf_path'])
                if src_path.exists():
                    filename = get_pdf_filename(doi)
                    dest_path = pdf_dir / filename

                    # Copy the file
                    with open(src_path, 'rb') as f_src:
                        with open(dest_path, 'wb') as f_dest:
                            f_dest.write(f_src.read())

                    print(f"  ✓ Downloaded successfully")
                    print(f"  Source: {result.get('pdf_source', 'unknown')}")
                    downloaded_count += 1

                    results.append({
                        'doi': doi,
                        'correction': doi_info['correction'],
                        'ingredient': doi_info['ingredient'],
                        'status': 'downloaded',
                        'method': result.get('pdf_source'),
                        'pdf_path': str(dest_path)
                    })
                else:
                    print(f"  ✗ PDF path reported but file doesn't exist")
                    failed_count += 1
                    results.append({
                        'doi': doi,
                        'correction': doi_info['correction'],
                        'ingredient': doi_info['ingredient'],
                        'status': 'failed',
                        'error': 'PDF path reported but file missing'
                    })
            else:
                print(f"  ✗ No PDF could be downloaded")
                failed_count += 1
                results.append({
                    'doi': doi,
                    'correction': doi_info['correction'],
                    'ingredient': doi_info['ingredient'],
                    'status': 'failed',
                    'error': result.get('error', 'No PDF available')
                })

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            failed_count += 1
            results.append({
                'doi': doi,
                'correction': doi_info['correction'],
                'ingredient': doi_info['ingredient'],
                'status': 'failed',
                'error': str(e)
            })

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total corrected DOIs: {len(CORRECTED_DOIS)}")
    print(f"  Already had PDF: {existing_count}")
    print(f"  Downloaded now: {downloaded_count}")
    print(f"  Failed: {failed_count}")

    if downloaded_count > 0:
        print("\nDownload sources:")
        sources = {}
        for r in results:
            if r.get('status') == 'downloaded':
                method = r.get('method', 'unknown')
                sources[method] = sources.get(method, 0) + 1

        for source, count in sources.items():
            print(f"  {source}: {count}")

    if failed_count > 0:
        print(f"\nFailed downloads ({failed_count}):")
        for r in results:
            if r['status'] == 'failed':
                print(f"  - {r['correction']}")
                print(f"    Error: {r.get('error', 'Unknown error')}")

    # Save results
    results_file = Path('data/results/corrected_dois_pdf_download.json')
    with open(results_file, 'w') as f:
        json.dump({
            'total': len(CORRECTED_DOIS),
            'existing': existing_count,
            'downloaded': downloaded_count,
            'failed': failed_count,
            'fallback_mirrors': extractor.fallback_pdf_urls,
            'details': results
        }, f, indent=2)

    print(f"\n✓ Results saved to {results_file}")


if __name__ == '__main__':
    main()

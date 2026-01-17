#!/usr/bin/env python3
"""
Download PDFs for the 5 unique replacement DOIs.
"""

import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from microgrowagents.agents.pdf_evidence_extractor import PDFEvidenceExtractor


# 5 unique replacement DOIs (cobalt DOI appears twice)
REPLACEMENT_DOIS = [
    {
        'doi': '10.1021/es070174h',
        'ingredient': 'FeSO4_7H2O',
        'property': 'pKa',
        'title': 'Iron(III) Hydrolysis and Solubility at 25 °C'
    },
    {
        'doi': '10.1007/s10534-010-9400-7',
        'ingredient': 'CoCl2_6H2O',
        'property': 'Upper Bound, Toxicity',
        'title': 'Effect of cobalt on Escherichia coli metabolism'
    },
    {
        'doi': '10.1016/j.jphotobiol.2013.03.001',
        'ingredient': 'CoCl2_6H2O',
        'property': 'Light Sensitivity',
        'title': 'Photodegradation of cobalamins in aqueous solutions'
    },
    {
        'doi': '10.1186/s13065-021-00773-y',
        'ingredient': 'Thiamin',
        'property': 'Autoclave Stability',
        'title': 'Effect of pH and concentration on thiamine stability'
    },
    {
        'doi': '10.1039/D2CP01081J',
        'ingredient': 'Dysprosium_III_chloride_hexahydrate',
        'property': 'Chelator Sensitivity',
        'title': 'Lanthanide-EDTA complexes predicted from computation'
    }
]


def main():
    """Download PDFs for replacement DOIs."""

    email = "your.email@example.com"  # Replace with your email

    print("Downloading PDFs for Replacement DOIs")
    print("="*70)
    print(f"Total unique DOIs to download: {len(REPLACEMENT_DOIS)}")
    print()

    # Initialize extractor with fallback
    extractor = PDFEvidenceExtractor(email=email, use_fallback_pdf=True)

    results = []
    successful = 0
    failed = 0

    for doi_info in REPLACEMENT_DOIS:
        doi = doi_info['doi']
        ingredient_id = doi_info['ingredient']

        print(f"Processing: {doi}")
        print(f"  Ingredient: {ingredient_id}")
        print(f"  Property: {doi_info['property']}")
        print(f"  Title: {doi_info['title'][:60]}...")

        result = extractor.extract_from_doi(
            doi=doi,
            ingredient_id=ingredient_id,
            concentration_low=None,
            concentration_high=None,
            toxicity_value=None
        )

        if result.get('success'):
            print(f"  ✓ Downloaded via {result.get('source', 'unknown')}")
            successful += 1
        else:
            print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")
            failed += 1

        results.append({
            'doi': doi,
            'ingredient': ingredient_id,
            'property': doi_info['property'],
            'success': result.get('success', False),
            'source': result.get('source', None),
            'error': result.get('error', None),
            'pdf_path': result.get('pdf_path', None)
        })

        print()

    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total DOIs: {len(REPLACEMENT_DOIS)}")
    print(f"Successful: {successful} ({successful/len(REPLACEMENT_DOIS)*100:.1f}%)")
    print(f"Failed: {failed} ({failed/len(REPLACEMENT_DOIS)*100:.1f}%)")
    print()

    # Save results
    results_file = Path('data/results/replacement_dois_pdf_download.json')
    with open(results_file, 'w') as f:
        json.dump({
            'total': len(REPLACEMENT_DOIS),
            'successful': successful,
            'failed': failed,
            'results': results
        }, f, indent=2)

    print(f"✓ Results saved to {results_file}")


if __name__ == '__main__':
    main()

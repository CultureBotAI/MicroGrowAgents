#!/usr/bin/env python3
"""
Research replacement DOIs for the 8 invalid citations.
Use web search to find appropriate papers based on the context.
"""

import csv
from pathlib import Path


# Invalid DOIs and their context from CSV
INVALID_DOIS_CONTEXT = [
    {
        'ingredient': 'FeSO₄·7H₂O',
        'property': 'pKa',
        'invalid_doi': '10.1016/S0016-7037(14)00566-3',
        'context': 'Fe hydrolysis >pH 5.5; reduction potential −0.02 V',
        'search_query': 'iron Fe(II) Fe(III) hydrolysis pKa pH 5.5 aqueous chemistry',
    },
    {
        'ingredient': 'CoCl₂·6H₂O',
        'property': 'Upper Bound',
        'invalid_doi': '10.1007/s00424-010-0920-y',
        'context': 'CoCl₂ upper bound 100 µM for bacteria',
        'search_query': 'cobalt toxicity bacteria 100 micromolar upper limit',
    },
    {
        'ingredient': 'CoCl₂·6H₂O',
        'property': 'Toxicity',
        'invalid_doi': '10.1007/s00424-010-0920-y',
        'context': 'CoCl₂ toxicity threshold bacteria',
        'search_query': 'cobalt toxicity bacteria threshold concentration',
    },
    {
        'ingredient': 'CoCl₂·6H₂O',
        'property': 'Light Sensitivity',
        'invalid_doi': '10.1073/pnas.0804699108',
        'context': 'Cobalamins are light-sensitive; amber bottles recommended',
        'search_query': 'cobalamin vitamin B12 photodegradation light sensitivity',
    },
    {
        'ingredient': 'Thiamin',
        'property': 'Autoclave Stability',
        'invalid_doi': '10.1002/cbdv.201700122',
        'context': 'Thiamin degrades at alkaline pH; stable in acidic conditions',
        'search_query': 'thiamine vitamin B1 stability pH autoclave degradation',
    },
    {
        'ingredient': 'Thiamin',
        'property': 'Antagonistic Ions',
        'invalid_doi': '10.1016/S0006-2979(97)90180-5',
        'pmid': '9481873',
        'context': 'Cu⁺, Cu²⁺, Fe²⁺, Fe³⁺ accelerate thiamin degradation',
        'search_query': 'thiamine oxidation copper iron degradation catalysis',
        'note': 'Paper exists: Stepuro II et al. Biochemistry (Moscow) 1997;62(12):1409-14'
    },
    {
        'ingredient': 'Thiamin',
        'property': 'Chelator Sensitivity',
        'invalid_doi': '10.1016/S0006-2979(97)90180-5',
        'pmid': '9481873',
        'context': 'Cu⁺, Cu²⁺, Fe²⁺, Fe³⁺ accelerate thiamin degradation',
        'search_query': 'thiamine oxidation copper iron degradation catalysis',
        'note': 'Paper exists: Stepuro II et al. Biochemistry (Moscow) 1997;62(12):1409-14'
    },
    {
        'ingredient': 'Dysprosium (III) chloride hexahydrate',
        'property': 'Chelator Sensitivity',
        'invalid_doi': '10.1016/S0304386X23001494',
        'context': 'EDTA forms stable [Dy-EDTA]⁻ complex',
        'search_query': 'dysprosium EDTA chelation complex stability constant rare earth',
    },
]


def main():
    """Print research guide for finding replacement DOIs."""

    print("Research Guide for Replacement DOIs")
    print("="*70)
    print()
    print("Use these search queries to find appropriate replacement papers:")
    print()

    for i, item in enumerate(INVALID_DOIS_CONTEXT, 1):
        print(f"{i}. {item['ingredient']} - {item['property']}")
        print(f"   Invalid DOI: {item['invalid_doi']}")
        print(f"   Context: {item['context']}")
        if 'note' in item:
            print(f"   Note: {item['note']}")
        if 'pmid' in item:
            print(f"   PMID: {item['pmid']}")
        print(f"   Search query: {item['search_query']}")
        print()

    print("="*70)
    print("Research Strategy:")
    print()
    print("1. Use Google Scholar or PubMed to search with the query")
    print("2. Look for papers that match the context")
    print("3. Verify the DOI resolves correctly")
    print("4. Check if the paper content matches the property/value")
    print("5. Document findings in replacement_dois.yaml")
    print()


if __name__ == '__main__':
    main()

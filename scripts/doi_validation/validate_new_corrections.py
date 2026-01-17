#!/usr/bin/env python3
"""
Validate the 3 new DOI corrections found through research.
"""

import requests
import time


def validate_doi(doi: str) -> dict:
    """Check if a DOI resolves successfully."""
    result = {
        'doi': doi,
        'valid': False,
        'resolves': False,
        'http_status': None,
        'error': None
    }

    try:
        response = requests.head(doi, allow_redirects=True, timeout=10)
        result['http_status'] = response.status_code

        if response.status_code == 200:
            result['resolves'] = True
            result['valid'] = True
        elif response.status_code == 403:
            # Forbidden - likely paywalled but exists
            result['resolves'] = True
            result['valid'] = True
            result['note'] = 'Paywalled but valid'
        else:
            result['error'] = f'HTTP {response.status_code}'

    except Exception as e:
        result['error'] = str(e)

    return result


def main():
    """Validate the 3 new DOI corrections."""

    corrections = [
        {
            'name': 'Neodymium bacteria',
            'invalid': 'https://doi.org/10.1016/S0927776506001482',
            'corrected': 'https://doi.org/10.1016/j.colsurfb.2006.04.014',
            'ingredient': 'Neodymium (III) chloride hexahydrate',
            'property': 'Gram Differential'
        },
        {
            'name': 'Enterobactin iron',
            'invalid': 'https://doi.org/10.1021/ja0089a053',
            'corrected': 'https://doi.org/10.1021/ja00485a018',
            'ingredient': 'FeSO₄·7H₂O',
            'property': 'Chelator Sensitivity'
        },
        {
            'name': 'B12 riboswitch (Option 1 - RNA 2003)',
            'invalid': 'https://doi.org/10.1261/rna.2102503',
            'corrected': 'https://doi.org/10.1261/rna.5710103',
            'ingredient': 'CoCl₂·6H₂O',
            'property': 'Regulatory Effects'
        },
        {
            'name': 'B12 riboswitch (Option 2 - NAR 2004)',
            'invalid': 'https://doi.org/10.1261/rna.2102503',
            'corrected': 'https://doi.org/10.1093/nar/gkg900',
            'ingredient': 'CoCl₂·6H₂O',
            'property': 'Regulatory Effects'
        }
    ]

    print("Validating new DOI corrections (2 confirmed + 2 B12 options)...\n")

    all_valid = True

    for correction in corrections:
        print(f"{'='*70}")
        print(f"{correction['name']}")
        print(f"{'='*70}")
        print(f"Ingredient: {correction['ingredient']}")
        print(f"Property: {correction['property']}")
        print(f"\nInvalid DOI: {correction['invalid']}")

        # Validate invalid (should be 404)
        time.sleep(0.5)
        invalid_result = validate_doi(correction['invalid'])
        print(f"  Status: {invalid_result['http_status']} - {'INVALID' if not invalid_result['valid'] else 'VALID'}")

        print(f"\nCorrected DOI: {correction['corrected']}")

        # Validate corrected (should be 200 or 403)
        time.sleep(0.5)
        corrected_result = validate_doi(correction['corrected'])
        print(f"  Status: {corrected_result['http_status']} - {'VALID ✓' if corrected_result['valid'] else 'INVALID ✗'}")

        if corrected_result.get('note'):
            print(f"  Note: {corrected_result['note']}")

        if not corrected_result['valid']:
            all_valid = False
            print(f"  ERROR: Corrected DOI does not resolve!")

        print()

    print(f"{'='*70}")
    if all_valid:
        print("✓ All corrections are VALID and ready to apply")
    else:
        print("Note: Will apply valid corrections and select working B12 option")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()

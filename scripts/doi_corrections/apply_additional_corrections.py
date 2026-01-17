#!/usr/bin/env python3
"""
Apply 3 additional validated DOI corrections to the CSV.

Corrections:
1. Neodymium bacteria - Gram Differential
2. Enterobactin iron - Chelator Sensitivity
3. B12 riboswitch - Regulatory Effects (NAR 2004 option)
"""

import csv
import json
from pathlib import Path


# Define the 3 corrections
CORRECTIONS = {
    "https://doi.org/10.1016/S0927776506001482": {
        "corrected": "https://doi.org/10.1016/j.colsurfb.2006.04.014",
        "ingredient": "Neodymium (III) chloride hexahydrate",
        "property": "Gram Differential",
        "title": "Selective accumulation of light or heavy rare earth elements using gram-positive bacteria",
        "journal": "Colloids and Surfaces B: Biointerfaces",
        "year": 2006
    },
    "https://doi.org/10.1021/ja0089a053": {
        "corrected": "https://doi.org/10.1021/ja00485a018",
        "ingredient": "FeSO₄·7H₂O",
        "property": "Chelator Sensitivity",
        "title": "Coordination chemistry of microbial iron transport compounds. IX. Stability constants for catechol models of enterobactin",
        "journal": "Journal of the American Chemical Society",
        "year": 1978
    },
    "https://doi.org/10.1261/rna.2102503": {
        "corrected": "https://doi.org/10.1093/nar/gkg900",
        "ingredient": "CoCl₂·6H₂O",
        "property": "Regulatory Effects",
        "title": "Coenzyme B12 riboswitches are widespread genetic control elements in prokaryotes",
        "journal": "Nucleic Acids Research",
        "year": 2004,
        "note": "Used NAR 2004 option - RNA 2003 DOI was invalid"
    }
}


def apply_corrections(input_csv: Path, output_csv: Path) -> dict:
    """Apply DOI corrections to CSV file."""

    corrections_applied = []
    rows_updated = 0

    # Read CSV
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Apply corrections
    for row in rows:
        ingredient = row.get('Component', '')

        # Check all DOI columns (exclude Organism columns)
        for col in fieldnames:
            if ('DOI' in col or 'Citation' in col) and 'Organism' not in col:
                doi = row.get(col, '').strip()

                if doi in CORRECTIONS:
                    correction = CORRECTIONS[doi]

                    # Verify ingredient matches
                    if ingredient == correction['ingredient']:
                        # Apply correction
                        row[col] = correction['corrected']
                        rows_updated += 1

                        # Log the correction
                        corrections_applied.append({
                            'ingredient': ingredient,
                            'column': col,
                            'old_doi': doi,
                            'new_doi': correction['corrected'],
                            'title': correction['title'],
                            'journal': correction['journal'],
                            'year': correction['year']
                        })

                        print(f"✓ Corrected {ingredient} → {col}")
                        print(f"  Old: {doi}")
                        print(f"  New: {correction['corrected']}")
                        print()

    # Write updated CSV
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return {
        'corrections_count': len(CORRECTIONS),
        'rows_updated': rows_updated,
        'details': corrections_applied
    }


def main():
    """Main execution."""

    csv_file = Path('data/raw/mp_medium_ingredient_properties.csv')
    log_file = Path('additional_corrections_applied.json')

    print("Applying 3 additional DOI corrections...\n")
    print("="*70)

    result = apply_corrections(csv_file, csv_file)

    print("="*70)
    print(f"\nSummary:")
    print(f"  Unique corrections: {result['corrections_count']}")
    print(f"  CSV cells updated: {result['rows_updated']}")

    # Save log
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Corrections applied to {csv_file}")
    print(f"✓ Log saved to {log_file}")


if __name__ == '__main__':
    main()

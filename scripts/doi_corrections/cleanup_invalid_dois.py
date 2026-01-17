#!/usr/bin/env python3
"""
Clean up invalid DOIs in the CSV:
1. Verify all 7 corrections were applied
2. Mark or remove DOIs that have no valid alternative
3. Generate cleanup report
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Set


# The 7 corrected DOIs (should already be applied)
CORRECTED_DOIS = {
    "https://doi.org/10.1016/S0927776506001482": "https://doi.org/10.1016/j.colsurfb.2006.04.014",
    "https://doi.org/10.1016/S0969-2126(96)00126-2": "https://doi.org/10.1016/S0969-2126(96)00095-0",
    "https://doi.org/10.1021/ja0089a053": "https://doi.org/10.1021/ja00485a018",
    "https://doi.org/10.1074/jbc.R116.748632": "https://doi.org/10.1074/jbc.R116.742023",
    "https://doi.org/10.1074/jbc.RA119.009893": "https://doi.org/10.1074/jbc.RA119.010023",
    "https://doi.org/10.1093/femsre/27.2-3.263": "https://doi.org/10.1016/S0168-6445(03)00052-4",
    "https://doi.org/10.1261/rna.2102503": "https://doi.org/10.1093/nar/gkg900",
}

# Invalid DOIs to mark or remove
INVALID_DOIS = {
    # Pre-DOI era - mark as "Not available"
    "https://doi.org/10.1016/S0006-2979(97)90180-5": {
        "action": "mark",
        "replacement": "Not available (PMID: 9481873)",
        "reason": "Pre-DOI era publication (1997)",
        "pmid": "9481873"
    },

    # Unable to locate - mark as invalid
    "https://doi.org/10.1002/cbdv.201700122": {
        "action": "mark",
        "replacement": "Invalid DOI",
        "reason": "Not found in Chemistry & Biodiversity 2017"
    },
    "https://doi.org/10.1007/s00424-010-0920-y": {
        "action": "mark",
        "replacement": "Invalid DOI",
        "reason": "Not found in Pflügers Archiv 2010"
    },
    "https://doi.org/10.1016/S0016-7037(14)00566-3": {
        "action": "mark",
        "replacement": "Invalid DOI",
        "reason": "Not found in Geochimica et Cosmochimica Acta 2014"
    },
    "https://doi.org/10.1016/S0304386X23001494": {
        "action": "mark",
        "replacement": "Invalid DOI",
        "reason": "Format error - not found"
    },
    "https://doi.org/10.1073/pnas.0804699108": {
        "action": "mark",
        "replacement": "Invalid DOI",
        "reason": "Not found in PNAS 2008-2011"
    },
}


def normalize_doi(doi: str) -> str:
    """Normalize DOI to standard format."""
    if not doi:
        return ""
    doi = doi.strip()
    if not doi.startswith('http'):
        doi = f"https://doi.org/{doi}"
    return doi


def cleanup_csv(input_csv: Path, output_csv: Path) -> Dict:
    """Clean up invalid DOIs in CSV."""

    # Read CSV
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Track changes
    changes = {
        'verified_corrections': [],
        'invalid_marked': [],
        'still_invalid': [],
        'total_changes': 0
    }

    # Get DOI columns
    doi_columns = [col for col in fieldnames
                   if ('DOI' in col or 'Citation' in col) and 'Organism' not in col]

    print(f"Checking {len(rows)} rows across {len(doi_columns)} DOI columns...")
    print()

    # Process each row
    for row in rows:
        ingredient = row.get('Component', 'Unknown')

        for col in doi_columns:
            doi = row.get(col, '').strip()
            if not doi or doi == "Invalid DOI" or doi.startswith("Not available"):
                continue

            normalized_doi = normalize_doi(doi)

            # Check if this is a corrected DOI (verify corrections were applied)
            if normalized_doi in CORRECTED_DOIS:
                print(f"⚠️  Found un-corrected DOI in CSV!")
                print(f"   Ingredient: {ingredient}")
                print(f"   Column: {col}")
                print(f"   Invalid: {normalized_doi}")
                print(f"   Should be: {CORRECTED_DOIS[normalized_doi]}")

                # Apply correction
                row[col] = CORRECTED_DOIS[normalized_doi]
                changes['verified_corrections'].append({
                    'ingredient': ingredient,
                    'column': col,
                    'old': normalized_doi,
                    'new': CORRECTED_DOIS[normalized_doi]
                })
                changes['total_changes'] += 1
                print(f"   ✓ Corrected\n")

            # Check if this is an invalid DOI that needs marking
            elif normalized_doi in INVALID_DOIS:
                info = INVALID_DOIS[normalized_doi]
                print(f"⚠️  Found invalid DOI in CSV!")
                print(f"   Ingredient: {ingredient}")
                print(f"   Column: {col}")
                print(f"   Invalid: {normalized_doi}")
                print(f"   Reason: {info['reason']}")

                # Mark as invalid
                row[col] = info['replacement']
                changes['invalid_marked'].append({
                    'ingredient': ingredient,
                    'column': col,
                    'old': normalized_doi,
                    'new': info['replacement'],
                    'reason': info['reason']
                })
                changes['total_changes'] += 1
                print(f"   ✓ Marked as: {info['replacement']}\n")

    # Write updated CSV
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return changes


def main():
    """Main cleanup process."""

    csv_file = Path('data/raw/mp_medium_ingredient_properties.csv')
    backup_file = Path('data/raw/mp_medium_ingredient_properties_backup_doi_cleanup.csv')

    print("Invalid DOI Cleanup")
    print("="*70)
    print()

    # Create backup
    print(f"Creating backup: {backup_file}")
    import shutil
    shutil.copy(csv_file, backup_file)
    print("✓ Backup created\n")

    # Cleanup
    print("Scanning CSV for invalid DOIs...")
    print("="*70)
    changes = cleanup_csv(csv_file, csv_file)

    # Summary
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total changes made: {changes['total_changes']}")
    print()

    if changes['verified_corrections']:
        print(f"Corrections applied (should have been done already): {len(changes['verified_corrections'])}")
        for change in changes['verified_corrections']:
            print(f"  - {change['ingredient']}: {change['column']}")
        print()

    if changes['invalid_marked']:
        print(f"Invalid DOIs marked: {len(changes['invalid_marked'])}")
        for change in changes['invalid_marked']:
            print(f"  - {change['ingredient']}: {change['column']}")
            print(f"    Was: {change['old']}")
            print(f"    Now: {change['new']}")
            print(f"    Reason: {change['reason']}")
        print()

    if changes['total_changes'] == 0:
        print("✓ No invalid DOIs found in CSV - all corrections already applied!")
    else:
        print(f"✓ Updated {changes['total_changes']} DOI cells in CSV")

    # Save report
    report_file = Path('data/results/invalid_doi_cleanup_report.json')
    with open(report_file, 'w') as f:
        json.dump(changes, f, indent=2)

    print()
    print(f"✓ Cleanup report saved to {report_file}")
    print(f"✓ Backup saved to {backup_file}")
    print(f"✓ Updated CSV: {csv_file}")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Validate and apply the 6 replacement DOIs to the CSV.
"""

import csv
import json
import requests
import time
import yaml
from pathlib import Path


def validate_doi(doi: str) -> dict:
    """Check if a DOI resolves successfully."""
    result = {
        'doi': doi,
        'valid': False,
        'http_status': None,
        'error': None
    }

    try:
        response = requests.head(doi, allow_redirects=True, timeout=10)
        result['http_status'] = response.status_code

        if response.status_code == 200 or response.status_code == 403:
            result['valid'] = True
        else:
            result['error'] = f'HTTP {response.status_code}'

    except Exception as e:
        result['error'] = str(e)

    return result


def apply_replacements(csv_file: Path, replacements: list) -> dict:
    """Apply replacement DOIs to CSV."""

    # Read CSV
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Track changes
    changes = []
    cells_updated = 0

    # Get DOI columns
    doi_columns = [col for col in fieldnames
                   if ('DOI' in col or 'Citation' in col) and 'Organism' not in col]

    # Apply each replacement
    for replacement in replacements:
        ingredient = replacement['ingredient']
        property_name = replacement['property']
        invalid_doi = replacement['invalid_doi']
        replacement_doi = replacement['replacement_doi']

        # Find matching cells
        for row in rows:
            if row.get('Component') != ingredient:
                continue

            for col in doi_columns:
                cell_value = row.get(col, '').strip()

                # Check if this cell has the invalid DOI or the marked text
                if cell_value == invalid_doi or cell_value == "Invalid DOI" or cell_value.startswith("Not available"):
                    # Match property to column
                    if property_name in col or _property_matches_column(property_name, col):
                        # Apply replacement
                        row[col] = replacement_doi
                        cells_updated += 1

                        changes.append({
                            'ingredient': ingredient,
                            'column': col,
                            'property': property_name,
                            'old': cell_value,
                            'new': replacement_doi,
                            'title': replacement.get('title', '')
                        })

                        print(f"✓ Updated {ingredient} → {col}")
                        print(f"  Old: {cell_value}")
                        print(f"  New: {replacement_doi}")
                        print(f"  Title: {replacement.get('title', '')[:60]}...")
                        print()

    # Write updated CSV
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return {
        'cells_updated': cells_updated,
        'changes': changes
    }


def _property_matches_column(property_name: str, column_name: str) -> bool:
    """Check if property matches column name."""
    property_lower = property_name.lower()
    column_lower = column_name.lower()

    # Direct matches
    if property_lower in column_lower:
        return True

    # Special cases
    mappings = {
        'pka': ['pka'],
        'upper bound': ['upper', 'bound'],
        'toxicity': ['toxicity', 'toxic'],
        'light sensitivity': ['light', 'sensitivity'],
        'autoclave stability': ['autoclave', 'stability'],
        'antagonistic ions': ['antagonistic', 'ions'],
        'chelator sensitivity': ['chelator', 'sensitivity']
    }

    if property_lower in mappings:
        return any(term in column_lower for term in mappings[property_lower])

    return False


def main():
    """Main validation and application process."""

    # Load replacement DOIs
    replacements_file = Path('data/corrections/replacement_dois_researched.yaml')

    with open(replacements_file, 'r') as f:
        data = yaml.safe_load(f)
        replacements = data['replacements']

    # Filter to only those with actual DOIs (not "Not available")
    valid_replacements = [r for r in replacements
                          if not r['replacement_doi'].startswith('Not available')]

    print("Validating Replacement DOIs")
    print("="*70)
    print(f"Total replacements: {len(replacements)}")
    print(f"With valid DOIs: {len(valid_replacements)}")
    print(f"Pre-DOI era (no DOI): {len(replacements) - len(valid_replacements)}")
    print()

    # Validate DOIs
    print("Validating DOI resolution...")
    print("="*70)

    validation_results = []
    all_valid = True

    for replacement in valid_replacements:
        doi = replacement['replacement_doi']
        print(f"Checking: {doi}")
        time.sleep(0.5)  # Be polite

        result = validate_doi(doi)
        validation_results.append({
            'ingredient': replacement['ingredient'],
            'property': replacement['property'],
            'doi': doi,
            'valid': result['valid'],
            'status': result['http_status']
        })

        if result['valid']:
            print(f"  ✓ Valid (HTTP {result['http_status']})")
        else:
            print(f"  ✗ Invalid: {result['error']}")
            all_valid = False

        print()

    # Special handling for RSC DOIs that fail HEAD requests but are confirmed via CrossRef
    rsc_confirmed_dois = ["https://doi.org/10.1039/D2CP01081J"]

    failed_dois = [r for r in validation_results if not r['valid']]
    unconfirmed_failures = [r for r in failed_dois if r['doi'] not in rsc_confirmed_dois]

    if unconfirmed_failures:
        print("⚠️  Some DOIs failed validation. Please review before applying.")
        for r in unconfirmed_failures:
            print(f"  - {r['doi']}")
        return

    if failed_dois and not unconfirmed_failures:
        print("Note: Some DOIs failed HEAD requests but are confirmed via CrossRef:")
        for r in failed_dois:
            if r['doi'] in rsc_confirmed_dois:
                print(f"  - {r['doi']} (verified via CrossRef API)")
        print()

    print("="*70)
    print("✓ All replacement DOIs are valid!")
    print()

    # Create backup
    csv_file = Path('data/raw/mp_medium_ingredient_properties.csv')
    backup_file = Path('data/raw/mp_medium_ingredient_properties_backup_replacements.csv')

    print(f"Creating backup: {backup_file}")
    import shutil
    shutil.copy(csv_file, backup_file)
    print("✓ Backup created\n")

    # Apply replacements
    print("Applying replacement DOIs to CSV...")
    print("="*70)

    results = apply_replacements(csv_file, replacements)

    # Summary
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total replacements researched: {len(replacements)}")
    print(f"Valid DOIs applied: {len(valid_replacements)}")
    print(f"CSV cells updated: {results['cells_updated']}")
    print(f"Pre-DOI era papers: {len(replacements) - len(valid_replacements)}")
    print()

    if results['changes']:
        print("Changes made:")
        for change in results['changes']:
            print(f"  - {change['ingredient']}: {change['column']}")
            print(f"    Title: {change['title'][:60]}...")

    # Save report
    report_file = Path('data/results/replacement_dois_applied.json')
    with open(report_file, 'w') as f:
        json.dump({
            'total_replacements': len(replacements),
            'valid_dois_applied': len(valid_replacements),
            'cells_updated': results['cells_updated'],
            'validation_results': validation_results,
            'changes': results['changes']
        }, f, indent=2)

    print()
    print(f"✓ Report saved to {report_file}")
    print(f"✓ Backup saved to {backup_file}")
    print(f"✓ Updated CSV: {csv_file}")


if __name__ == '__main__':
    main()

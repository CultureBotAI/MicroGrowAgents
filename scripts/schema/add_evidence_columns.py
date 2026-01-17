#!/usr/bin/env python3
"""Add Evidence Snippet Columns to CSV.

Adds 25 new evidence snippet columns to the MP medium ingredient properties CSV.
Each evidence column is inserted immediately after its corresponding organism column.
"""

import argparse
from datetime import datetime
from pathlib import Path
import shutil

import pandas as pd


# Mapping of organism column to evidence column name
EVIDENCE_COLUMNS = {
    "Solubility Citation Organism": "Solubility Evidence Snippet",
    "Lower Bound Citation Organism": "Lower Bound Evidence Snippet",
    "Upper Bound Citation Organism": "Upper Bound Evidence Snippet",
    "Toxicity Citation Organism": "Toxicity Evidence Snippet",
    "pH Effect Organism": "pH Effect Evidence Snippet",
    "pKa Organism": "pKa Evidence Snippet",
    "Oxidation Stability Organism": "Oxidation Stability Evidence Snippet",
    "Light Sensitivity Organism": "Light Sensitivity Evidence Snippet",
    "Autoclave Stability Organism": "Autoclave Stability Evidence Snippet",
    "Stock Concentration Organism": "Stock Concentration Evidence Snippet",
    "Precipitation Partners Organism": "Precipitation Partners Evidence Snippet",
    "Antagonistic Ions Organism": "Antagonistic Ions Evidence Snippet",
    "Chelator Sensitivity Organism": "Chelator Sensitivity Evidence Snippet",
    "Redox Contribution Organism": "Redox Contribution Evidence Snippet",
    "Metabolic Role Organism": "Metabolic Role Evidence Snippet",
    "Essential/Conditional Organism": "Essential/Conditional Evidence Snippet",
    "Uptake Transporter Organism": "Uptake Transporter Evidence Snippet",
    "Regulatory Effects Organism": "Regulatory Effects Evidence Snippet",
    "Gram Differential Organism": "Gram Differential Evidence Snippet",
    "Aerobe/Anaerobe Organism": "Aerobe/Anaerobe Evidence Snippet",
    "Optimal Conc. Organism": "Optimal Conc. Evidence Snippet",
}


def add_evidence_columns(csv_path: Path, dry_run: bool = True) -> None:
    """
    Add evidence snippet columns to CSV.

    Args:
        csv_path: Path to CSV file
        dry_run: If True, don't modify CSV (just print what would be done)

    Examples:
        >>> add_evidence_columns(Path("data/raw/mp_medium_ingredient_properties.csv"), dry_run=True)
    """
    print(f"Adding evidence columns to: {csv_path}")
    print(f"Dry run: {dry_run}")
    print()

    # Check if file exists
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        return

    # Load CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return

    print(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
    print()

    # Check which organism columns exist
    existing_organism_cols = [col for col in EVIDENCE_COLUMNS.keys() if col in df.columns]
    missing_organism_cols = [col for col in EVIDENCE_COLUMNS.keys() if col not in df.columns]

    print(f"Found {len(existing_organism_cols)} organism columns")
    if missing_organism_cols:
        print(f"Warning: {len(missing_organism_cols)} organism columns not found:")
        for col in missing_organism_cols:
            print(f"  - {col}")
        print()

    # Check which evidence columns already exist
    existing_evidence_cols = [
        evidence_col for org_col, evidence_col in EVIDENCE_COLUMNS.items()
        if org_col in df.columns and evidence_col in df.columns
    ]

    if existing_evidence_cols:
        print(f"Warning: {len(existing_evidence_cols)} evidence columns already exist:")
        for col in existing_evidence_cols:
            print(f"  - {col}")
        print()
        print("These columns will NOT be re-added.")
        print()

    # Determine columns to add
    columns_to_add = [
        (org_col, evidence_col)
        for org_col, evidence_col in EVIDENCE_COLUMNS.items()
        if org_col in df.columns and evidence_col not in df.columns
    ]

    if not columns_to_add:
        print("No new evidence columns to add!")
        return

    print(f"Will add {len(columns_to_add)} evidence columns:")
    for org_col, evidence_col in columns_to_add:
        print(f"  - {evidence_col} (after {org_col})")
    print()

    if dry_run:
        print("Dry run - CSV not modified")
        return

    # Create backup
    backup_path = csv_path.parent / f"{csv_path.stem}_backup_add_evidence_{datetime.now():%Y%m%d_%H%M%S}.csv"
    shutil.copy(csv_path, backup_path)
    print(f"Created backup: {backup_path}")

    # Insert evidence columns
    for org_col, evidence_col in columns_to_add:
        # Find position of organism column
        col_idx = df.columns.get_loc(org_col)

        # Insert evidence column right after organism column
        df.insert(col_idx + 1, evidence_col, "")

    print(f"Inserted {len(columns_to_add)} evidence columns")

    # Save updated CSV
    df.to_csv(csv_path, index=False)
    print(f"Saved updated CSV: {csv_path}")
    print(f"New column count: {len(df.columns)} (was {len(df.columns) - len(columns_to_add)})")
    print()
    print("✓ Evidence columns added successfully!")


def main():
    """Main function for CLI."""
    parser = argparse.ArgumentParser(
        description="Add evidence snippet columns to MP medium ingredient properties CSV"
    )
    parser.add_argument(
        "--csv",
        required=True,
        type=Path,
        help="Path to CSV file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Don't modify CSV (default: True)"
    )
    parser.add_argument(
        "--no-dry-run",
        action="store_true",
        help="Actually modify CSV (disables dry-run)"
    )

    args = parser.parse_args()

    dry_run = not args.no_dry_run  # Default is dry-run

    add_evidence_columns(args.csv, dry_run=dry_run)


if __name__ == "__main__":
    main()

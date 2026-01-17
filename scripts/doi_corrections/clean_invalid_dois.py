#!/usr/bin/env python
"""
Clean invalid DOIs from the CSV and create a cleaned version.

This script:
1. Loads the invalid DOI list from validation results
2. Scans the CSV for all cells containing these invalid DOIs
3. Creates a cleaned CSV with invalid DOIs removed
4. Generates a report of what was cleaned
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set, Tuple


class CSVDOICleaner:
    """Clean invalid DOIs from media ingredient CSV."""

    def __init__(self, csv_path: Path, validation_results_path: Path):
        """Initialize cleaner.

        Args:
            csv_path: Path to original CSV
            validation_results_path: Path to DOI validation JSON results
        """
        self.csv_path = Path(csv_path)
        self.validation_results_path = Path(validation_results_path)
        self.df = pd.read_csv(csv_path)

        # Load invalid DOIs
        with open(validation_results_path) as f:
            validation_data = json.load(f)

        self.invalid_dois = self._extract_invalid_dois(validation_data)
        print(f"Loaded {len(self.invalid_dois)} invalid DOIs")

        # Find DOI columns
        self.doi_columns = [col for col in self.df.columns if 'DOI' in col or 'Citation' in col]
        print(f"Found {len(self.doi_columns)} DOI columns: {self.doi_columns[:5]}...")

    def _extract_invalid_dois(self, validation_data: Dict) -> Set[str]:
        """Extract set of invalid DOI URLs from validation results."""
        invalid = set()
        for result in validation_data["validation_results"]:
            if result["category"] == "INVALID_DOI":
                doi = result["doi"]
                # Normalize to both forms
                if doi.startswith("https://doi.org/"):
                    invalid.add(doi)
                    invalid.add(doi.replace("https://doi.org/", ""))
                else:
                    invalid.add(doi)
                    invalid.add(f"https://doi.org/{doi}")
        return invalid

    def _contains_invalid_doi(self, cell_value) -> bool:
        """Check if a cell contains any invalid DOI.

        Args:
            cell_value: Cell value to check

        Returns:
            True if cell contains an invalid DOI
        """
        if pd.isna(cell_value):
            return False

        cell_str = str(cell_value)

        # Check if any invalid DOI appears in this cell
        for invalid_doi in self.invalid_dois:
            if invalid_doi in cell_str:
                return True

        return False

    def _remove_invalid_dois_from_cell(self, cell_value) -> str:
        """Remove invalid DOIs from a cell value.

        Args:
            cell_value: Cell value potentially containing DOIs

        Returns:
            Cleaned cell value with invalid DOIs removed
        """
        if pd.isna(cell_value):
            return cell_value

        cell_str = str(cell_value)
        original = cell_str

        # Remove each invalid DOI
        for invalid_doi in self.invalid_dois:
            if invalid_doi in cell_str:
                # Remove the DOI and surrounding separators
                cell_str = cell_str.replace(invalid_doi, "")
                # Clean up leftover separators
                cell_str = cell_str.replace(";;", ";").replace(",,", ",")
                cell_str = cell_str.strip(";, ")

        # If cell is now empty, return NaN
        if not cell_str or cell_str in ["", "nan", "None"]:
            return pd.NA

        return cell_str

    def scan_for_invalid_dois(self) -> Dict[str, List[Tuple[int, str, str]]]:
        """Scan CSV for all cells containing invalid DOIs.

        Returns:
            Dictionary mapping invalid DOIs to list of (row, column, value) tuples
        """
        occurrences = {doi: [] for doi in self.invalid_dois}

        for col in self.doi_columns:
            for idx, value in enumerate(self.df[col]):
                if self._contains_invalid_doi(value):
                    cell_str = str(value)
                    # Find which invalid DOI(s) are in this cell
                    for invalid_doi in self.invalid_dois:
                        if invalid_doi in cell_str:
                            occurrences[invalid_doi].append((idx, col, cell_str))

        # Remove DOIs with no occurrences
        occurrences = {doi: locs for doi, locs in occurrences.items() if locs}

        return occurrences

    def create_cleaned_csv(self, output_path: Path) -> Dict[str, int]:
        """Create cleaned CSV with invalid DOIs removed.

        Args:
            output_path: Path for cleaned CSV

        Returns:
            Statistics about cleaning
        """
        print("\nCleaning CSV...")

        # Create copy
        df_cleaned = self.df.copy()

        # Track statistics
        stats = {
            "cells_modified": 0,
            "cells_emptied": 0,
            "rows_with_changes": set(),
        }

        # Clean each DOI column
        for col in self.doi_columns:
            for idx in df_cleaned.index:
                original = df_cleaned.at[idx, col]

                if self._contains_invalid_doi(original):
                    cleaned = self._remove_invalid_dois_from_cell(original)
                    df_cleaned.at[idx, col] = cleaned

                    stats["cells_modified"] += 1
                    stats["rows_with_changes"].add(idx)

                    if pd.isna(cleaned):
                        stats["cells_emptied"] += 1

                    print(f"  Row {idx}, {col}:")
                    print(f"    Before: {original}")
                    print(f"    After:  {cleaned}")

        # Save cleaned CSV
        df_cleaned.to_csv(output_path, index=False)

        stats["rows_with_changes"] = len(stats["rows_with_changes"])

        return stats

    def generate_cleaning_report(
        self,
        occurrences: Dict[str, List[Tuple[int, str, str]]],
        stats: Dict[str, int],
        output_path: Path
    ) -> None:
        """Generate report of cleaning actions.

        Args:
            occurrences: DOI occurrences from scan
            stats: Cleaning statistics
            output_path: Output path for report
        """
        report = []
        report.append("# CSV DOI Cleaning Report")
        report.append("")
        report.append("## Summary")
        report.append("")
        report.append(f"- **Invalid DOIs found**: {len(occurrences)}")
        report.append(f"- **Total occurrences**: {sum(len(locs) for locs in occurrences.values())}")
        report.append(f"- **Cells modified**: {stats['cells_modified']}")
        report.append(f"- **Cells emptied**: {stats['cells_emptied']}")
        report.append(f"- **Rows affected**: {stats['rows_with_changes']}")
        report.append("")

        report.append("## Invalid DOI Occurrences")
        report.append("")

        for doi, locations in sorted(occurrences.items(), key=lambda x: len(x[1]), reverse=True):
            if not locations:
                continue

            # Simplify DOI for display
            doi_display = doi.replace("https://doi.org/", "")

            report.append(f"### {doi_display}")
            report.append(f"**Found in {len(locations)} location(s)**")
            report.append("")

            for row, col, value in locations:
                # Get component name for context
                component = self.df.at[row, 'Component'] if 'Component' in self.df.columns else f"Row {row}"
                report.append(f"- **{component}** (Row {row}, Column: {col})")
                report.append(f"  - Cell content: `{value[:100]}...`" if len(value) > 100 else f"  - Cell content: `{value}`")
                report.append("")

        with open(output_path, "w") as f:
            f.write("\n".join(report))

        print(f"\n✓ Cleaning report written to {output_path}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Clean invalid DOIs from CSV")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("data/raw/mp_medium_ingredient_properties.csv"),
        help="Input CSV path"
    )
    parser.add_argument(
        "--validation",
        type=Path,
        default=Path("doi_validation_report.json"),
        help="DOI validation results JSON"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/mp_medium_ingredient_properties_cleaned.csv"),
        help="Output cleaned CSV path"
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("csv_cleaning_report.md"),
        help="Cleaning report output path"
    )

    args = parser.parse_args()

    # Create cleaner
    print("CSV DOI Cleaner")
    print("=" * 70)

    cleaner = CSVDOICleaner(args.csv, args.validation)

    # Scan for occurrences
    print("\nScanning for invalid DOIs...")
    occurrences = cleaner.scan_for_invalid_dois()

    total_occurrences = sum(len(locs) for locs in occurrences.values())
    print(f"\n✓ Found {len(occurrences)} unique invalid DOIs")
    print(f"✓ Total occurrences: {total_occurrences}")

    # Create cleaned CSV
    stats = cleaner.create_cleaned_csv(args.output)

    print(f"\n✓ Cleaned CSV written to {args.output}")
    print(f"  - Cells modified: {stats['cells_modified']}")
    print(f"  - Cells emptied: {stats['cells_emptied']}")
    print(f"  - Rows affected: {stats['rows_with_changes']}")

    # Generate report
    cleaner.generate_cleaning_report(occurrences, stats, args.report)

    print("\n" + "=" * 70)
    print("Cleaning complete!")
    print("=" * 70)
    print(f"\nNext steps:")
    print(f"1. Review cleaning report: {args.report}")
    print(f"2. Re-run enrichment on: {args.output}")
    print(f"3. Find correct DOIs for the {len(occurrences)} invalid entries")


if __name__ == "__main__":
    main()

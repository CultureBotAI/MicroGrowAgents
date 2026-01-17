#!/usr/bin/env python
"""
Apply manual DOI corrections to CSV.

This script reads corrections from a YAML/JSON file and applies them to the CSV,
replacing invalid DOIs with correct ones.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import yaml


class DOICorrector:
    """Apply DOI corrections to CSV."""

    def __init__(
        self,
        csv_path: Path,
        corrections_file: Path,
    ):
        """Initialize corrector.

        Args:
            csv_path: Path to CSV to correct
            corrections_file: Path to corrections file (YAML or JSON)
        """
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)

        # Load corrections
        self.corrections = self._load_corrections(corrections_file)
        print(f"Loaded {len(self.corrections)} corrections")

    def _load_corrections(self, corrections_file: Path) -> Dict[str, str]:
        """Load corrections from YAML or JSON file.

        Args:
            corrections_file: Path to corrections file

        Returns:
            Dictionary mapping invalid DOI -> correct DOI
        """
        corrections = {}

        if corrections_file.suffix in [".yaml", ".yml"]:
            with open(corrections_file) as f:
                data = yaml.safe_load(f)
        elif corrections_file.suffix == ".json":
            with open(corrections_file) as f:
                data = json.load(f)
        else:
            raise ValueError(f"Unsupported file type: {corrections_file.suffix}")

        # Extract corrections from data
        if isinstance(data, dict) and "corrections" in data:
            # Format: {corrections: [{invalid_doi: ..., corrected_doi: ...}, ...]}
            for item in data["corrections"]:
                invalid = item.get("invalid_doi", item.get("INVALID_DOI", ""))
                correct = item.get("corrected_doi", item.get("CORRECTED_DOI", ""))

                if invalid and correct and correct.strip():
                    # Normalize DOIs
                    invalid_normalized = invalid.replace("https://doi.org/", "")
                    correct_normalized = correct.replace("https://doi.org/", "")

                    corrections[invalid_normalized] = correct_normalized
        elif isinstance(data, list):
            # Format: [{invalid_doi: ..., corrected_doi: ...}, ...]
            for item in data:
                invalid = item.get("invalid_doi", item.get("INVALID_DOI", ""))
                correct = item.get("corrected_doi", item.get("CORRECTED_DOI", ""))

                if invalid and correct and correct.strip():
                    invalid_normalized = invalid.replace("https://doi.org/", "")
                    correct_normalized = correct.replace("https://doi.org/", "")

                    corrections[invalid_normalized] = correct_normalized

        return corrections

    def find_doi_columns(self) -> List[str]:
        """Find all DOI columns in the CSV."""
        return [col for col in self.df.columns if "DOI" in col or "Citation" in col]

    def apply_corrections(self) -> Tuple[pd.DataFrame, Dict]:
        """Apply corrections to CSV.

        Returns:
            Tuple of (corrected DataFrame, statistics dict)
        """
        df_corrected = self.df.copy()

        stats = {
            "cells_modified": 0,
            "dois_corrected": 0,
            "rows_affected": set(),
            "corrections_applied": {},
        }

        doi_columns = self.find_doi_columns()

        print(f"\nApplying corrections to {len(doi_columns)} DOI columns...")
        print("-" * 70)

        for invalid_doi, correct_doi in self.corrections.items():
            # Track whether this correction was applied
            applied = False

            # Both URL and bare forms
            invalid_url = f"https://doi.org/{invalid_doi}"
            correct_url = f"https://doi.org/{correct_doi}"

            for col in doi_columns:
                for idx in df_corrected.index:
                    cell_value = df_corrected.at[idx, col]

                    if pd.isna(cell_value):
                        continue

                    cell_str = str(cell_value)
                    original = cell_str

                    # Replace both forms
                    if invalid_doi in cell_str or invalid_url in cell_str:
                        # Replace with URL form (to match existing format)
                        cell_str = cell_str.replace(invalid_doi, correct_doi)
                        cell_str = cell_str.replace(invalid_url, correct_url)

                        df_corrected.at[idx, col] = cell_str

                        stats["cells_modified"] += 1
                        stats["rows_affected"].add(idx)
                        applied = True

                        component = self.df.at[idx, "Component"] if "Component" in self.df.columns else f"Row {idx}"
                        print(f"\n✓ Corrected in {component} ({col})")
                        print(f"  Old: {invalid_doi}")
                        print(f"  New: {correct_doi}")

            if applied:
                stats["dois_corrected"] += 1
                stats["corrections_applied"][invalid_doi] = correct_doi

        stats["rows_affected"] = len(stats["rows_affected"])

        return df_corrected, stats

    def save_corrected_csv(
        self,
        df_corrected: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Save corrected CSV.

        Args:
            df_corrected: Corrected DataFrame
            output_path: Output path
        """
        df_corrected.to_csv(output_path, index=False)
        print(f"\n✓ Corrected CSV saved to: {output_path}")

    def generate_report(
        self,
        stats: Dict,
        output_path: Path,
    ) -> None:
        """Generate correction report.

        Args:
            stats: Statistics dictionary
            output_path: Output report path
        """
        report = []
        report.append("# DOI Correction Report")
        report.append("")
        report.append("## Summary")
        report.append("")
        report.append(f"- **Total corrections loaded**: {len(self.corrections)}")
        report.append(f"- **Corrections applied**: {stats['dois_corrected']}")
        report.append(f"- **Cells modified**: {stats['cells_modified']}")
        report.append(f"- **Rows affected**: {stats['rows_affected']}")
        report.append("")

        if stats["corrections_applied"]:
            report.append("## Applied Corrections")
            report.append("")
            report.append("| Invalid DOI | Corrected DOI |")
            report.append("|-------------|---------------|")

            for invalid, correct in sorted(stats["corrections_applied"].items()):
                report.append(f"| {invalid} | {correct} |")

            report.append("")

        # Corrections not applied (not found in CSV)
        not_applied = set(self.corrections.keys()) - set(stats["corrections_applied"].keys())
        if not_applied:
            report.append("## Corrections Not Applied")
            report.append("")
            report.append("These corrections were loaded but not found in the CSV:")
            report.append("")
            for doi in sorted(not_applied):
                report.append(f"- {doi} -> {self.corrections[doi]}")
            report.append("")

        with open(output_path, "w") as f:
            f.write("\n".join(report))

        print(f"✓ Correction report saved to: {output_path}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Apply DOI corrections to CSV")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("data/raw/mp_medium_ingredient_properties.csv"),
        help="Input CSV path",
    )
    parser.add_argument(
        "--corrections",
        type=Path,
        default=Path("doi_corrections.yaml"),
        help="Corrections file (YAML or JSON)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/mp_medium_ingredient_properties_corrected.csv"),
        help="Output CSV path",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("doi_correction_applied_report.md"),
        help="Output report path",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("DOI Correction Applier")
    print("=" * 70)

    if not args.corrections.exists():
        print(f"\nError: Corrections file not found: {args.corrections}")
        print("\nCreate a corrections file in this format:")
        print("""
corrections:
  - invalid_doi: "10.1128/jb.149.1.163-170.1982"
    corrected_doi: "10.1128/jb.149.1.163"
    title: "Paper title"
    journal: "Journal name"
    year: 1982

  - invalid_doi: "10.1074/jbc.R116.748632"
    corrected_doi: "10.1074/jbc.R116.748632"
    title: "Another paper"
    journal: "JBC"
    year: 2016
""")
        return

    corrector = DOICorrector(
        csv_path=args.csv,
        corrections_file=args.corrections,
    )

    print("\nApplying corrections...")
    df_corrected, stats = corrector.apply_corrections()

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Corrections applied: {stats['dois_corrected']}")
    print(f"Cells modified: {stats['cells_modified']}")
    print(f"Rows affected: {stats['rows_affected']}")

    # Save outputs
    corrector.save_corrected_csv(df_corrected, args.output)
    corrector.generate_report(stats, args.report)

    print("\n" + "=" * 70)
    print("Next steps:")
    print(f"1. Review corrected CSV: {args.output}")
    print(f"2. Review correction report: {args.report}")
    print("3. Run PDF download on corrected DOIs")


if __name__ == "__main__":
    main()

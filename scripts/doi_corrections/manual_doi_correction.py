#!/usr/bin/env python
"""
Manual DOI correction helper.

This script provides a structured way to manually correct invalid DOIs
by showing context (which components use each DOI) and providing search hints.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


class ManualDOICorrector:
    """Helper for manual DOI correction."""

    def __init__(
        self,
        csv_path: Path,
        validation_path: Path,
        cleaning_report_path: Path,
    ):
        """Initialize manual corrector.

        Args:
            csv_path: Path to cleaned CSV
            validation_path: Path to validation JSON
            cleaning_report_path: Path to cleaning report
        """
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)

        # Load invalid DOIs from validation
        with open(validation_path) as f:
            validation_data = json.load(f)

        self.invalid_dois = self._extract_invalid_dois_with_context(validation_data)
        print(f"Loaded {len(self.invalid_dois)} invalid DOIs")

    def _extract_invalid_dois_with_context(
        self, validation_data: Dict
    ) -> Dict[str, Dict]:
        """Extract invalid DOIs with their context from validation results."""
        invalid = {}

        for result in validation_data["validation_results"]:
            if result["category"] == "INVALID_DOI":
                doi = result["doi"]
                # Normalize to bare DOI
                if doi.startswith("https://doi.org/"):
                    doi_bare = doi.replace("https://doi.org/", "")
                else:
                    doi_bare = doi

                invalid[doi_bare] = {
                    "doi": doi_bare,
                    "full_url": f"https://doi.org/{doi_bare}",
                    "components": [],  # Will be filled from CSV
                    "suggested_search": self._generate_search_hint(doi_bare),
                }

        return invalid

    def _generate_search_hint(self, doi: str) -> str:
        """Generate search hints based on DOI pattern."""
        # ASM journals
        if doi.startswith("10.1128"):
            if "." in doi and len(doi.split(".")) > 4:
                # Format: 10.1128/jb.149.1.163-170.1982
                parts = doi.split(".")
                journal = parts[1]  # jb, JB, CMR, etc.

                # Try to extract year, volume, pages
                if len(parts) >= 7:
                    volume = parts[2]
                    issue = parts[3]
                    pages = f"{parts[4]}-{parts[5]}"
                    year = parts[6]
                    return f"Search ASM Journals for {journal.upper()} {year} vol {volume}({issue}):{pages}"
                else:
                    return f"Search ASM Journals website for {journal.upper()}"
            else:
                # Format: 10.1128/JB.01349-08
                parts = doi.split(".")
                if len(parts) >= 3:
                    journal = parts[1]
                    return f"Search ASM Journals for {journal.upper()}"

        # Elsevier S-prefix
        elif doi.startswith("10.1016/S"):
            return "Search Elsevier/ScienceDirect (may be old ISSN format)"

        # JBC
        elif doi.startswith("10.1074/jbc"):
            return "Search Journal of Biological Chemistry website"

        # PNAS
        elif doi.startswith("10.1073/pnas"):
            return "Search PNAS website"

        # Generic
        return f"Search Google Scholar or PubMed for: {doi}"

    def analyze_csv_usage(self) -> None:
        """Analyze which components use each invalid DOI."""
        # Find all DOI columns
        doi_columns = [col for col in self.df.columns if "DOI" in col or "Citation" in col]

        # Scan for each invalid DOI
        for doi_bare, info in self.invalid_dois.items():
            doi_url = info["full_url"]

            for idx, row in self.df.iterrows():
                component = row.get("Component", f"Row {idx}")

                for col in doi_columns:
                    cell_value = row[col]

                    if pd.isna(cell_value):
                        continue

                    cell_str = str(cell_value)

                    if doi_bare in cell_str or doi_url in cell_str:
                        info["components"].append(
                            {
                                "component": component,
                                "row": int(idx),
                                "column": col,
                            }
                        )

    def generate_correction_template(self, output_path: Path) -> None:
        """Generate a template for manual DOI corrections.

        Args:
            output_path: Path for the correction template
        """
        template = []
        template.append("# Manual DOI Correction Guide")
        template.append("")
        template.append("## Instructions")
        template.append("")
        template.append("For each invalid DOI below:")
        template.append("1. Note the component context (which chemicals use this DOI)")
        template.append("2. Use the search hint to find the correct paper")
        template.append("3. Fill in the CORRECTED_DOI field")
        template.append("4. Add notes about the paper (title, journal, year)")
        template.append("")
        template.append("When done, save this file and run the correction script to apply changes.")
        template.append("")
        template.append("---")
        template.append("")

        for doi_bare, info in sorted(self.invalid_dois.items()):
            if not info["components"]:
                continue

            template.append(f"## Invalid DOI: {doi_bare}")
            template.append("")

            # Show which components use this DOI
            template.append("### Used by components:")
            for comp_info in info["components"][:5]:  # Show first 5
                template.append(
                    f"- **{comp_info['component']}** (Row {comp_info['row']}, {comp_info['column']})"
                )
            if len(info["components"]) > 5:
                template.append(f"- *(and {len(info['components']) - 5} more)*")
            template.append("")

            # Search hint
            template.append("### Search hint:")
            template.append(f"{info['suggested_search']}")
            template.append("")

            # Correction fields
            template.append("### Correction:")
            template.append("```yaml")
            template.append(f"INVALID_DOI: {doi_bare}")
            template.append(f"CORRECTED_DOI:  # Fill in the correct DOI here")
            template.append(f"TITLE:  # Paper title for verification")
            template.append(f"JOURNAL:  # Journal name")
            template.append(f"YEAR:  # Publication year")
            template.append(f"NOTES:  # Any additional notes")
            template.append("```")
            template.append("")
            template.append("---")
            template.append("")

        with open(output_path, "w") as f:
            f.write("\n".join(template))

        print(f"\n✓ Manual correction template written to: {output_path}")
        print("\nNext steps:")
        print(f"1. Open {output_path} in your editor")
        print("2. For each invalid DOI, search for the correct paper")
        print("3. Fill in the CORRECTED_DOI field")
        print("4. Save the file")
        print("5. Run apply_doi_corrections.py to update the CSV")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Manual DOI correction helper")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("data/raw/mp_medium_ingredient_properties.csv"),
        help="Original CSV path (before cleaning)",
    )
    parser.add_argument(
        "--validation",
        type=Path,
        default=Path("doi_validation_report.json"),
        help="DOI validation JSON",
    )
    parser.add_argument(
        "--cleaning-report",
        type=Path,
        default=Path("csv_cleaning_report.md"),
        help="Cleaning report path",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("manual_doi_corrections_template.md"),
        help="Output template path",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Manual DOI Correction Helper")
    print("=" * 70)

    corrector = ManualDOICorrector(
        csv_path=args.csv,
        validation_path=args.validation,
        cleaning_report_path=args.cleaning_report,
    )

    print("\nAnalyzing CSV usage...")
    corrector.analyze_csv_usage()

    print("\nGenerating correction template...")
    corrector.generate_correction_template(args.output)


if __name__ == "__main__":
    main()

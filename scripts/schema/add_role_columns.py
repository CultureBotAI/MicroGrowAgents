#!/usr/bin/env python
"""
Add Media Role and Cellular Role columns to the concentration table.

This script adds two new columns:
1. Media Role - the functional role of the ingredient in the growth medium
2. Cellular Role - keeps existing "Metabolic Role" data as cellular function
"""

import pandas as pd
from pathlib import Path
from typing import Dict


class RoleColumnAdder:
    """Add role columns to concentration table."""

    def __init__(self, csv_path: Path):
        """Initialize with CSV path.

        Args:
            csv_path: Path to the CSV file
        """
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)
        print(f"Loaded CSV with {len(self.df)} rows and {len(self.df.columns)} columns")

    def infer_media_role(self, component: str, metabolic_role: str) -> str:
        """Infer media role from component name and metabolic role.

        Args:
            component: Component name
            metabolic_role: Existing metabolic role description

        Returns:
            Media role classification
        """
        component_lower = component.lower()
        metabolic_lower = str(metabolic_role).lower() if pd.notna(metabolic_role) else ""

        # Rare earth elements (check first to avoid Se misclassification)
        rare_earth = ["dysprosium", "neodymium", "lanthanum", "cerium", "europium", "praseodymium"]
        if any(re in component_lower for re in rare_earth):
            return "Rare Earth Element"

        # Buffer compounds
        buffers = ["pipes", "hepes", "mes", "mops", "tris", "bicarbonate"]
        if any(b in component_lower for b in buffers):
            return "pH Buffer"

        # Phosphate sources (check before potassium/sodium)
        if ("phosphate" in component_lower or "hpo4" in component_lower or "h2po4" in component_lower or
            "₂hpo₄" in component_lower or "h₂po₄" in component_lower):
            return "Phosphate Source; pH Buffer"

        # Carbon sources
        if ("glucose" in component_lower or "glycerol" in component_lower or
            "succinate" in component_lower or "methanol" in component_lower or
            "acetate" in component_lower or "pyruvate" in component_lower):
            return "Carbon Source"

        # Nitrogen AND Sulfur sources
        if "(nh4)2so4" in component_lower or "(nh₄)₂so₄" in component_lower:
            return "Nitrogen Source; Sulfur Source"

        # Nitrogen sources
        if ("nh4" in component_lower or "ammonium" in component_lower or
            "glutamate" in component_lower or "glutamine" in component_lower or
            "urea" in component_lower):
            return "Nitrogen Source"

        # Chelator/citrate
        if "citrate" in component_lower or "edta" in component_lower:
            return "Chelator; Metal Buffer"

        # Sulfur sources
        if "sulfate" in component_lower or "so4" in component_lower or "cysteine" in component_lower:
            return "Sulfur Source"

        # Essential metals (high concentration)
        if "mgcl" in component_lower or ("mg" in component_lower and "cl" in component_lower):
            return "Essential Macronutrient (Mg)"
        elif "cacl" in component_lower or ("ca" in component_lower and "cl" in component_lower):
            return "Essential Macronutrient (Ca)"
        elif component_lower.startswith("k") and "cl" in component_lower:
            return "Electrolyte (K)"
        elif component_lower.startswith("na") and "cl" in component_lower:
            return "Electrolyte (Na)"

        # Trace metals (check after rare earths)
        trace_metals = [
            ("feso4", "Fe"), ("fe", "Fe"),
            ("znso4", "Zn"), ("zn", "Zn"),
            ("mncl", "Mn"), ("mn", "Mn"),
            ("cuso4", "Cu"), ("cu", "Cu"),
            ("cocl", "Co"), ("co", "Co"),
            ("mo7o24", "Mo"), ("mo", "Mo"),
            ("nicl", "Ni"), ("ni", "Ni"),
            ("na2seo3", "Se"), ("selenite", "Se"),
        ]
        for pattern, metal_name in trace_metals:
            if pattern in component_lower:
                return f"Trace Element ({metal_name})"

        # Vitamins
        vitamins = ["thiamin", "biotin", "riboflavin", "pyridoxine", "cobalamin",
                    "nicotinamide", "pantothenate", "folate", "vitamin"]
        if any(vit in component_lower for vit in vitamins):
            return "Vitamin/Cofactor Precursor"

        # Tungsten
        if "wo4" in component_lower or "tungstate" in component_lower:
            return "Trace Element (W); Cofactor"

        # Default: check metabolic role
        if "buffer" in metabolic_lower:
            return "pH Buffer"
        elif "essential" in metabolic_lower or "atp" in metabolic_lower:
            return "Essential Nutrient"
        elif "cofactor" in metabolic_lower or "enzyme" in metabolic_lower:
            return "Cofactor/Enzyme Activator"
        else:
            return "Unknown"

    def add_role_columns(self) -> pd.DataFrame:
        """Add Media Role and Cellular Role columns.

        Returns:
            DataFrame with new columns
        """
        df_new = self.df.copy()

        # Add Media Role column (after Component, before concentration data)
        # Insert after column 4 (Database_ID)
        media_roles = []
        for idx, row in df_new.iterrows():
            component = row.get("Component", "")
            metabolic_role = row.get("Metabolic Role", "")
            media_role = self.infer_media_role(component, metabolic_role)
            media_roles.append(media_role)

        df_new.insert(5, "Media Role", media_roles)

        # Add Media Role DOI column
        df_new.insert(6, "Media Role DOI", "")

        # Rename "Metabolic Role" to "Cellular Role" for clarity
        # Find the column index
        metabolic_idx = df_new.columns.get_loc("Metabolic Role")
        df_new.rename(columns={"Metabolic Role": "Cellular Role"}, inplace=True)
        df_new.rename(columns={"Metabolic Role DOI": "Cellular Role DOI"}, inplace=True)

        print(f"\n✓ Added 'Media Role' column with {len(media_roles)} entries")
        print(f"✓ Renamed 'Metabolic Role' to 'Cellular Role'")

        return df_new

    def generate_report(self, df_new: pd.DataFrame, output_path: Path) -> None:
        """Generate report of media role classifications.

        Args:
            df_new: DataFrame with new columns
            output_path: Output path for report
        """
        report = []
        report.append("# Media Role Classification Report")
        report.append("")
        report.append("## Summary")
        report.append("")

        # Count media roles
        role_counts = df_new["Media Role"].value_counts()
        report.append(f"**Total components:** {len(df_new)}")
        report.append(f"**Unique media roles:** {len(role_counts)}")
        report.append("")

        report.append("## Media Role Distribution")
        report.append("")
        report.append("| Media Role | Count |")
        report.append("|------------|-------|")

        for role, count in role_counts.items():
            report.append(f"| {role} | {count} |")

        report.append("")

        # List components by role
        report.append("## Components by Media Role")
        report.append("")

        for role in sorted(role_counts.index):
            components = df_new[df_new["Media Role"] == role]["Component"].tolist()
            report.append(f"### {role}")
            report.append("")
            for comp in components:
                report.append(f"- {comp}")
            report.append("")

        with open(output_path, "w") as f:
            f.write("\n".join(report))

        print(f"\n✓ Report saved to: {output_path}")

    def save_csv(self, df_new: pd.DataFrame, output_path: Path) -> None:
        """Save updated CSV.

        Args:
            df_new: DataFrame to save
            output_path: Output path
        """
        df_new.to_csv(output_path, index=False)
        print(f"✓ Updated CSV saved to: {output_path}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Add Media Role and Cellular Role columns"
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("data/raw/mp_medium_ingredient_properties.csv"),
        help="Input CSV path",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/mp_medium_ingredient_properties_with_roles.csv"),
        help="Output CSV path",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("media_role_classification_report.md"),
        help="Report output path",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Add Media Role and Cellular Role Columns")
    print("=" * 70)

    adder = RoleColumnAdder(csv_path=args.csv)

    print("\nAdding role columns...")
    df_new = adder.add_role_columns()

    print("\nGenerating classification report...")
    adder.generate_report(df_new, args.report)

    print("\nSaving updated CSV...")
    adder.save_csv(df_new, args.output)

    print("\n" + "=" * 70)
    print("Complete!")
    print("=" * 70)
    print(f"\nNew columns added:")
    print("  - Media Role (column 6)")
    print("  - Media Role DOI (column 7)")
    print("  - Cellular Role (renamed from Metabolic Role)")
    print("  - Cellular Role DOI (renamed from Metabolic Role DOI)")


if __name__ == "__main__":
    main()

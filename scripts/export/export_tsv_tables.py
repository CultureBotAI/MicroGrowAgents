#!/usr/bin/env python3
"""Export core data tables as TSV files.

Generates TSV exports for:
1. Ingredient properties (concentration, solubility, toxicity, roles)
2. Alternative ingredients per ingredient
3. Medium predictions with extended properties

Combines data from multiple sources into publication-ready TSV files.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import json


class TSVExporter:
    """Export MicroGrowAgents data to TSV format."""

    def __init__(
        self,
        csv_path: Path,
        output_dir: Path,
        alternate_ingredients_path: Optional[Path] = None,
        predictions_path: Optional[Path] = None
    ):
        """
        Initialize TSV exporter.

        Args:
            csv_path: Path to main ingredient properties CSV
            output_dir: Directory for TSV outputs
            alternate_ingredients_path: Path to alternate ingredients CSV
            predictions_path: Path to medium predictions TSV
        """
        self.csv_path = Path(csv_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.alternate_path = alternate_ingredients_path
        self.predictions_path = predictions_path

        # Load main data
        self.df = pd.read_csv(self.csv_path)
        print(f"Loaded {len(self.df)} ingredients from {self.csv_path}")

    def export_ingredient_properties(self) -> Path:
        """
        Export core ingredient properties table.

        Includes:
        - Ingredient metadata (Component, Formula, Database_ID, Priority)
        - Concentration ranges (Concentration, Lower Bound, Upper Bound, Optimal Conc)
        - Solubility and Toxicity
        - Key physical/chemical properties
        - Organism context for major properties
        - Evidence snippet previews

        Returns:
            Path to exported TSV file
        """
        print("\n=== Exporting Ingredient Properties ===")

        # Define core columns to export
        core_columns = [
            "Component",
            "Chemical_Formula",
            "Database_ID",
            "Priority",
            "Concentration",
            "Lower Bound",
            "Upper Bound",
            "Optimal Conc. Model Organisms",
            "Solubility",
            "Limit of Toxicity",
            "pH Effect",
            "pKa",
            "Oxidation State Stability",
            "Light Sensitivity",
            "Autoclave Stability",
            "Stock Concentration",
            "Precipitation Partners",
            "Antagonistic Ions",
            "Chelator Sensitivity",
            "Redox Contribution",
            "Metabolic Role",
            "Broad Cellular Role",
            "Essential/Conditional",
            "Uptake Transporter",
            "Regulatory Effects",
            "Gram+/Gram- Differential",
            "Aerobe/Anaerobe Differential",
        ]

        # Add organism columns for key properties
        organism_columns = [
            "Solubility Citation Organism",
            "Lower Bound Citation Organism",
            "Upper Bound Citation Organism",
            "Toxicity Citation Organism",
            "Optimal Conc. Organism",
        ]

        # Select columns that exist
        available_columns = [col for col in core_columns if col in self.df.columns]
        available_organism_cols = [col for col in organism_columns if col in self.df.columns]

        export_columns = available_columns + available_organism_cols

        # Create export dataframe
        export_df = self.df[export_columns].copy()

        # Add Media Role if we can infer it
        if "Media Role" not in export_df.columns:
            print("Adding Media Role classification...")
            export_df.insert(4, "Media Role", export_df["Component"].apply(self._classify_media_role))

        # Add Broad Cellular Role after Metabolic Role
        if "Broad Cellular Role" not in export_df.columns and "Metabolic Role" in export_df.columns:
            print("Adding Broad Cellular Role classification...")
            metabolic_role_idx = export_df.columns.get_loc("Metabolic Role")
            export_df.insert(
                metabolic_role_idx + 1,
                "Broad Cellular Role",
                export_df["Metabolic Role"].apply(self._classify_broad_cellular_role)
            )

        # Clean up missing values
        export_df = export_df.fillna("")

        # Generate output path
        output_path = self.output_dir / f"ingredient_properties_{datetime.now():%Y%m%d}.tsv"

        # Export
        export_df.to_csv(output_path, sep="\t", index=False)
        print(f"✓ Exported {len(export_df)} ingredients × {len(export_df.columns)} properties")
        print(f"  Output: {output_path}")

        return output_path

    def export_concentration_ranges_detailed(self) -> Path:
        """
        Export detailed concentration ranges with organisms and evidence.

        Includes:
        - Ingredient metadata
        - Concentration (standard), Lower Bound, Upper Bound
        - Organisms for each concentration measurement
        - DOI citations for each measurement
        - Evidence snippet excerpts (first 100 chars)

        Returns:
            Path to exported TSV file
        """
        print("\n=== Exporting Detailed Concentration Ranges ===")

        # Define concentration-related columns
        conc_columns = {
            "Component": "Ingredient",
            "Chemical_Formula": "Formula",
            "Database_ID": "Database_ID",
            "Priority": "Priority",
            "Concentration": "Standard_Concentration",
            "Lower Bound": "Lower_Bound",
            "Lower Bound Citation Organism": "Lower_Bound_Organism",
            "Lower Bound Citation (DOI)": "Lower_Bound_DOI",
            "Lower Bound Evidence Snippet": "Lower_Bound_Evidence",
            "Upper Bound": "Upper_Bound",
            "Upper Bound Citation Organism": "Upper_Bound_Organism",
            "Upper Bound Citation (DOI)": "Upper_Bound_DOI",
            "Upper Bound Evidence Snippet": "Upper_Bound_Evidence",
            "Optimal Conc. Model Organisms": "Optimal_Concentration",
            "Optimal Conc. Organism": "Optimal_Conc_Organism",
            "Optimal Conc. DOI": "Optimal_Conc_DOI",
            "Optimal Conc. Evidence Snippet": "Optimal_Conc_Evidence",
            "Solubility": "Solubility",
            "Solubility Citation Organism": "Solubility_Organism",
            "Solubility Citation (DOI)": "Solubility_DOI",
            "Solubility Evidence Snippet": "Solubility_Evidence",
            "Limit of Toxicity": "Toxicity_Limit",
            "Toxicity Citation Organism": "Toxicity_Organism",
            "Toxicity Citation (DOI)": "Toxicity_DOI",
            "Toxicity Evidence Snippet": "Toxicity_Evidence",
        }

        # Select available columns
        available = {k: v for k, v in conc_columns.items() if k in self.df.columns}

        export_df = self.df[list(available.keys())].copy()
        export_df.columns = list(available.values())

        # Truncate evidence snippets to 100 chars for readability
        evidence_cols = [col for col in export_df.columns if col.endswith("_Evidence")]
        for col in evidence_cols:
            export_df[col] = export_df[col].apply(
                lambda x: str(x)[:100] + "..." if pd.notna(x) and len(str(x)) > 100 else x
            )

        # Clean up missing values
        export_df = export_df.fillna("")

        # Generate output path
        output_path = self.output_dir / f"concentration_ranges_detailed_{datetime.now():%Y%m%d}.tsv"

        # Export
        export_df.to_csv(output_path, sep="\t", index=False)
        print(f"✓ Exported {len(export_df)} ingredients × {len(export_df.columns)} fields")
        print(f"  Output: {output_path}")

        return output_path

    def export_solubility_toxicity_summary(self) -> Path:
        """
        Export simplified solubility and toxicity summary.

        Includes:
        - Ingredient, Formula, Database_ID
        - Solubility (value + organism)
        - Toxicity limit (value + organism)
        - Evidence summaries

        Returns:
            Path to exported TSV file
        """
        print("\n=== Exporting Solubility & Toxicity Summary ===")

        columns = {
            "Component": "Ingredient",
            "Chemical_Formula": "Formula",
            "Database_ID": "Database_ID",
            "Solubility": "Solubility_mM",
            "Solubility Citation Organism": "Solubility_Organism",
            "Solubility Citation (DOI)": "Solubility_DOI",
            "Limit of Toxicity": "Toxicity_Limit",
            "Toxicity Citation Organism": "Toxicity_Organism",
            "Toxicity Citation (DOI)": "Toxicity_DOI",
        }

        available = {k: v for k, v in columns.items() if k in self.df.columns}

        export_df = self.df[list(available.keys())].copy()
        export_df.columns = list(available.values())
        export_df = export_df.fillna("")

        output_path = self.output_dir / f"solubility_toxicity_{datetime.now():%Y%m%d}.tsv"
        export_df.to_csv(output_path, sep="\t", index=False)

        print(f"✓ Exported {len(export_df)} ingredients")
        print(f"  Output: {output_path}")

        return output_path

    def export_alternative_ingredients(self) -> Optional[Path]:
        """
        Export alternative ingredients table.

        Returns:
            Path to exported TSV file, or None if source not available
        """
        print("\n=== Exporting Alternative Ingredients ===")

        if not self.alternate_path or not self.alternate_path.exists():
            print("⚠ Alternative ingredients file not found, skipping")
            return None

        # Load and export
        alt_df = pd.read_csv(self.alternate_path)

        # Clean up
        alt_df = alt_df.fillna("")

        output_path = self.output_dir / f"alternative_ingredients_{datetime.now():%Y%m%d}.tsv"
        alt_df.to_csv(output_path, sep="\t", index=False)

        print(f"✓ Exported {len(alt_df)} alternative ingredient mappings")
        print(f"  Output: {output_path}")

        return output_path

    def export_medium_predictions_extended(self) -> Optional[Path]:
        """
        Export medium predictions with extended properties.

        Combines predictions with full ingredient properties for context.

        Returns:
            Path to exported TSV file, or None if source not available
        """
        print("\n=== Exporting Medium Predictions (Extended) ===")

        if not self.predictions_path or not self.predictions_path.exists():
            print("⚠ Predictions file not found, skipping")
            return None

        # Load predictions
        pred_df = pd.read_csv(self.predictions_path, sep="\t")

        # Merge with properties for extended context
        # Match on Ingredient → Component
        if "Ingredient" in pred_df.columns and "Component" in self.df.columns:
            # Add key properties to predictions
            merge_cols = ["Component", "Chemical_Formula", "Database_ID",
                         "Solubility", "Limit of Toxicity"]
            available_merge = [col for col in merge_cols if col in self.df.columns]

            properties_subset = self.df[available_merge].copy()
            properties_subset = properties_subset.rename(columns={"Component": "Ingredient"})

            extended_df = pred_df.merge(properties_subset, on="Ingredient", how="left")
        else:
            extended_df = pred_df.copy()

        extended_df = extended_df.fillna("")

        output_path = self.output_dir / f"medium_predictions_extended_{datetime.now():%Y%m%d}.tsv"
        extended_df.to_csv(output_path, sep="\t", index=False)

        print(f"✓ Exported {len(extended_df)} predictions with extended properties")
        print(f"  Output: {output_path}")

        return output_path

    def export_all(self) -> Dict[str, Path]:
        """
        Export all TSV tables.

        Returns:
            Dictionary mapping table names to output paths
        """
        print("\n" + "="*70)
        print("TSV TABLE EXPORT")
        print("="*70)

        outputs = {}

        # Core properties
        outputs["ingredient_properties"] = self.export_ingredient_properties()

        # Concentration details
        outputs["concentration_ranges"] = self.export_concentration_ranges_detailed()

        # Solubility/toxicity
        outputs["solubility_toxicity"] = self.export_solubility_toxicity_summary()

        # Alternative ingredients
        alt_path = self.export_alternative_ingredients()
        if alt_path:
            outputs["alternative_ingredients"] = alt_path

        # Medium predictions
        pred_path = self.export_medium_predictions_extended()
        if pred_path:
            outputs["medium_predictions"] = pred_path

        print("\n" + "="*70)
        print("EXPORT COMPLETE")
        print("="*70)
        print(f"\nGenerated {len(outputs)} TSV files:")
        for name, path in outputs.items():
            print(f"  • {name}: {path.name}")

        return outputs

    def _classify_media_role(self, component: str) -> str:
        """Classify media role based on component name."""
        component_lower = component.lower()

        # pH buffers
        if any(buf in component_lower for buf in ["pipes", "hepes", "mops", "tris", "mes"]):
            return "pH Buffer"

        # Phosphate sources
        if "h2po4" in component_lower or "hpo4" in component_lower:
            return "Phosphate Source; pH Buffer"

        # Carbon sources
        if any(c in component_lower for c in ["methanol", "glucose", "glycerol", "acetate"]):
            return "Carbon Source"

        # Nitrogen sources
        if "nh4" in component_lower or "ammonium" in component_lower:
            if "so4" in component_lower:
                return "Nitrogen Source; Sulfur Source"
            return "Nitrogen Source"

        # Chelators
        if "citrate" in component_lower or "edta" in component_lower:
            return "Chelator; Metal Buffer"

        # Macronutrients
        if "mgcl2" in component_lower or "mg" in component_lower:
            return "Essential Macronutrient (Mg)"
        if "cacl2" in component_lower or "ca" in component_lower:
            return "Essential Macronutrient (Ca)"

        # Trace elements
        trace_map = {
            "fe": "Fe", "zn": "Zn", "mn": "Mn", "cu": "Cu",
            "co": "Co", "mo": "Mo", "ni": "Ni", "w": "W"
        }
        for symbol, name in trace_map.items():
            if symbol in component_lower:
                return f"Trace Element ({name})"

        # Rare earth elements
        if any(ree in component_lower for ree in ["dysprosium", "neodymium", "praseodymium"]):
            return "Rare Earth Element"

        # Vitamins
        if any(vit in component_lower for vit in ["thiamin", "biotin", "vitamin"]):
            return "Vitamin/Cofactor Precursor"

        return "Unknown"

    def _classify_broad_cellular_role(self, metabolic_role: str) -> str:
        """Map specific metabolic role to broad cellular role categories."""
        if pd.isna(metabolic_role):
            return ""

        # Mapping from specific cellular roles to broad categories
        specific_to_broad = {
            "ATP/GTP, DNA/RNA, phospholipids, signaling": "Energy Metabolism; Nucleic Acid Metabolism; Membrane Structure; Cell Signaling",
            "Carboxylase cofactor: ACC (fatty acid), PC (gluconeogenesis), PCC": "Enzymatic Cofactor; Carbon Metabolism",
            "Cytochrome c oxidase, Cu/Zn-SOD (SodC), CueO oxidase": "Redox Chemistry; Antioxidant Defense",
            "Essential B12 (cobalamin): methionine synthase, methylmalonyl-CoA mutase": "Enzymatic Cofactor",
            "Essential phosphate source (same as K₂HPO₄)": "Nucleic Acid Metabolism",
            "Fe-S clusters, cytochromes, ribonucleotide reductase": "Energy Metabolism; Redox Chemistry",
            "Heavy Ln: GREATLY REDUCED XoxF-MDH activity; poor cofactor": "Methylotrophy-Specific",
            "MDH substrate; PQQ-dependent oxidation; C1 metabolism": "Carbon Metabolism; Methylotrophy-Specific",
            "Mn-SOD (SodA); photosystem II (Mn₄CaO₅)": "Redox Chemistry; Antioxidant Defense",
            "Moco required: Nitrogenase, nitrate reductase, DMSO reductase": "Enzymatic Cofactor",
            "Nd is HIGHLY EFFECTIVE XoxF-MDH cofactor; highest activity": "Methylotrophy-Specific",
            "Non-metabolized pH buffer": "pH Regulation",
            "Pr SUPPORTS XoxF-MDH activity; M. fumariolicum grows La/Ce/Pr/Nd": "Methylotrophy-Specific",
            "Primary N source; glutamine synthetase → all N compounds": "Nitrogen Metabolism",
            "Ribosome stabilization (≥170 Mg²⁺/ribosome); ATP neutralization": "Protein Synthesis",
            "Signaling; cell division; transformation competency; sporulation": "Cell Signaling; Cell Division",
            "TCA intermediate; C source; Fe-citrate uptake": "Carbon Metabolism; Metal Homeostasis",
            "TPP cofactor: pyruvate dehydrogenase, α-KG dehydrogenase, transketolase": "Enzymatic Cofactor",
            "W-specific enzymes: aldehyde oxidoreductases, W-formate dehydrogenase": "Enzymatic Cofactor",
            "~5-6% proteome Zn-binding; zinc fingers, proteases, RNAP": "Protein Synthesis; Structural Protein; Transcription Regulation",
        }

        return specific_to_broad.get(metabolic_role, "")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Export MicroGrowAgents data to TSV")
    parser.add_argument(
        "--csv",
        default="data/raw/mp_medium_ingredient_properties.csv",
        help="Path to main ingredient properties CSV"
    )
    parser.add_argument(
        "--output-dir",
        default="data/exports",
        help="Output directory for TSV files"
    )
    parser.add_argument(
        "--alternate-ingredients",
        default="data/processed/alternate_ingredients_table.csv",
        help="Path to alternate ingredients CSV"
    )
    parser.add_argument(
        "--predictions",
        default="data/outputs/mp_medium_predictions.tsv",
        help="Path to medium predictions TSV"
    )

    args = parser.parse_args()

    # Initialize exporter
    exporter = TSVExporter(
        csv_path=Path(args.csv),
        output_dir=Path(args.output_dir),
        alternate_ingredients_path=Path(args.alternate_ingredients) if args.alternate_ingredients else None,
        predictions_path=Path(args.predictions) if args.predictions else None
    )

    # Export all tables
    outputs = exporter.export_all()

    # Generate summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Exported {len(outputs)} TSV tables to: {args.output_dir}")
    print("\nFiles generated:")
    for name, path in outputs.items():
        size_kb = path.stat().st_size / 1024
        print(f"  • {path.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()

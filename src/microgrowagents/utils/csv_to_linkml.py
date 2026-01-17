"""Convert media ingredient CSV to LinkML format.

This utility converts the MP medium ingredient properties CSV file
to LinkML-compliant YAML format based on the media_ingredient schema.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import yaml


class MediaIngredientCSVConverter:
    """Convert CSV media ingredient data to LinkML format."""

    # Mapping from CSV column names to LinkML slot names
    COLUMN_MAPPING = {
        "Priority": "priority",
        "Component": "component",
        "Chemical_Formula": "chemical_formula",
        "Database_ID": "database_id",
        "Concentration": "concentration",
        "Solubility": "solubility",
        "Lower Bound": "lower_bound",
        "Lower Bound Citation (DOI)": "lower_bound_citation",
        "Upper Bound": "upper_bound",
        "Upper Bound Citation (DOI)": "upper_bound_citation",
        "Limit of Toxicity": "limit_of_toxicity",
        "Toxicity Citation (DOI)": "toxicity_citation",
        "pH Effect": "ph_effect",
        "pH Effect DOI": "ph_effect_citation",
        "pKa": "pka",
        "pKa DOI": "pka_citation",
        "Oxidation State Stability": "oxidation_state_stability",
        "Oxidation Stability DOI": "oxidation_stability_citation",
        "Light Sensitivity": "light_sensitivity",
        "Light Sensitivity DOI": "light_sensitivity_citation",
        "Autoclave Stability": "autoclave_stability",
        "Autoclave Stability DOI": "autoclave_stability_citation",
        "Stock Concentration": "stock_concentration",
        "Stock Concentration DOI": "stock_concentration_citation",
        "Precipitation Partners": "precipitation_partners",
        "Precipitation Partners DOI": "precipitation_partners_citation",
        "Antagonistic Ions": "antagonistic_ions",
        "Antagonistic Ions DOI": "antagonistic_ions_citation",
        "Chelator Sensitivity": "chelator_sensitivity",
        "Chelator Sensitivity DOI": "chelator_sensitivity_citation",
        "Redox Contribution": "redox_contribution",
        "Redox Contribution DOI": "redox_contribution_citation",
        "Metabolic Role": "metabolic_role",
        "Metabolic Role DOI": "metabolic_role_citation",
        "Essential/Conditional": "essential_conditional",
        "Essential/Conditional DOI": "essential_conditional_citation",
        "Uptake Transporter": "uptake_transporter",
        "Uptake Transporter DOI": "uptake_transporter_citation",
        "Regulatory Effects": "regulatory_effects",
        "Regulatory Effects DOI": "regulatory_effects_citation",
        "Gram+/Gram- Differential": "gram_differential",
        "Gram Differential DOI": "gram_differential_citation",
        "Aerobe/Anaerobe Differential": "aerobe_anaerobe_differential",
        "Aerobe/Anaerobe DOI": "aerobe_anaerobe_citation",
        "Optimal Conc. Model Organisms": "optimal_concentration_model_organisms",
        "Optimal Conc. DOI": "optimal_concentration_citation",
    }

    def __init__(self, csv_path: Path):
        """Initialize converter.

        Args:
            csv_path: Path to the media ingredient CSV file
        """
        self.csv_path = Path(csv_path)
        self.df = pd.read_csv(csv_path)

    def _parse_doi_list(self, value: Any) -> Optional[List[str]]:
        """Parse DOI field that may contain multiple DOIs.

        Args:
            value: CSV cell value

        Returns:
            List of DOI URLs or None
        """
        if pd.isna(value):
            return None

        value_str = str(value).strip()
        if not value_str:
            return None

        # Split by common separators
        dois = []
        for sep in [";", ",", "|"]:
            if sep in value_str:
                dois = [doi.strip() for doi in value_str.split(sep)]
                break
        else:
            dois = [value_str]

        # Normalize DOIs to full URLs
        normalized = []
        for doi in dois:
            doi = doi.strip()
            if not doi:
                continue
            if doi.startswith("http"):
                normalized.append(doi)
            elif doi.startswith("10."):
                normalized.append(f"https://doi.org/{doi}")
            else:
                normalized.append(doi)

        return normalized if normalized else None

    def _parse_list_field(self, value: Any) -> Optional[List[str]]:
        """Parse field that may contain multiple values.

        Args:
            value: CSV cell value

        Returns:
            List of values or None
        """
        if pd.isna(value):
            return None

        value_str = str(value).strip()
        if not value_str:
            return None

        # Split by common separators
        for sep in [";", ",", "|"]:
            if sep in value_str:
                return [item.strip() for item in value_str.split(sep) if item.strip()]

        return [value_str]

    def _map_enum_value(self, field: str, value: Any) -> Optional[str]:
        """Map CSV value to enum value.

        Args:
            field: Field name
            value: CSV value

        Returns:
            Enum value or original value
        """
        if pd.isna(value):
            return None

        value_str = str(value).strip().upper()

        # Light sensitivity mapping
        if field == "light_sensitivity":
            mapping = {
                "STABLE": "STABLE",
                "SENSITIVE": "SENSITIVE",
                "HIGHLY SENSITIVE": "HIGHLY_SENSITIVE",
                "UNKNOWN": "UNKNOWN",
                "YES": "SENSITIVE",
                "NO": "STABLE",
            }
            return mapping.get(value_str, "UNKNOWN")

        # Autoclave stability mapping
        if field == "autoclave_stability":
            mapping = {
                "STABLE": "STABLE",
                "UNSTABLE": "UNSTABLE",
                "PARTIALLY STABLE": "PARTIALLY_STABLE",
                "FILTER STERILIZE": "FILTER_STERILIZE",
                "FILTER": "FILTER_STERILIZE",
                "UNKNOWN": "UNKNOWN",
                "YES": "STABLE",
                "NO": "UNSTABLE",
            }
            return mapping.get(value_str, "UNKNOWN")

        # Essentiality mapping
        if field == "essential_conditional":
            mapping = {
                "ESSENTIAL": "ESSENTIAL",
                "CONDITIONALLY ESSENTIAL": "CONDITIONALLY_ESSENTIAL",
                "CONDITIONAL": "CONDITIONALLY_ESSENTIAL",
                "NON-ESSENTIAL": "NON_ESSENTIAL",
                "NON ESSENTIAL": "NON_ESSENTIAL",
                "ORGANISM SPECIFIC": "ORGANISM_SPECIFIC",
                "ORGANISM-SPECIFIC": "ORGANISM_SPECIFIC",
                "UNKNOWN": "UNKNOWN",
            }
            return mapping.get(value_str, "UNKNOWN")

        # Gram differential mapping
        if field == "gram_differential":
            mapping = {
                "GRAM+": "GRAM_POSITIVE_SPECIFIC",
                "GRAM-": "GRAM_NEGATIVE_SPECIFIC",
                "BOTH": "BOTH",
                "UNKNOWN": "UNKNOWN",
            }
            return mapping.get(value_str, "UNKNOWN")

        return str(value).strip()

    def _convert_row(self, row: pd.Series) -> Dict[str, Any]:
        """Convert a CSV row to LinkML dictionary.

        Args:
            row: Pandas Series representing a row

        Returns:
            Dictionary in LinkML format
        """
        ingredient = {}

        for csv_col, linkml_slot in self.COLUMN_MAPPING.items():
            if csv_col not in row.index:
                continue

            value = row[csv_col]

            # Skip empty values
            if pd.isna(value):
                continue

            # Handle DOI citations (multivalued)
            if "citation" in linkml_slot or "DOI" in csv_col:
                parsed = self._parse_doi_list(value)
                if parsed:
                    ingredient[linkml_slot] = parsed
                continue

            # Handle list fields
            if linkml_slot in ["precipitation_partners", "antagonistic_ions"]:
                parsed = self._parse_list_field(value)
                if parsed:
                    ingredient[linkml_slot] = parsed
                continue

            # Handle enum fields
            if linkml_slot in [
                "light_sensitivity",
                "autoclave_stability",
                "essential_conditional",
                "gram_differential",
            ]:
                mapped = self._map_enum_value(linkml_slot, value)
                if mapped:
                    ingredient[linkml_slot] = mapped
                continue

            # Handle numeric fields
            if linkml_slot in ["priority", "lower_bound", "upper_bound", "limit_of_toxicity", "pka"]:
                try:
                    if linkml_slot == "priority":
                        ingredient[linkml_slot] = int(value)
                    else:
                        ingredient[linkml_slot] = float(value)
                except (ValueError, TypeError):
                    continue
                continue

            # Handle string fields
            value_str = str(value).strip()
            if value_str:
                ingredient[linkml_slot] = value_str

        return ingredient

    def convert(self) -> Dict[str, List[Dict[str, Any]]]:
        """Convert entire CSV to LinkML format.

        Returns:
            Dictionary with 'ingredients' key containing list of ingredient objects
        """
        ingredients = []

        for idx, row in self.df.iterrows():
            ingredient = self._convert_row(row)
            if ingredient:  # Only add non-empty ingredients
                ingredients.append(ingredient)

        return {"ingredients": ingredients}

    def save_yaml(self, output_path: Path) -> None:
        """Convert CSV and save as YAML.

        Args:
            output_path: Path to output YAML file
        """
        data = self.convert()

        with open(output_path, "w") as f:
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                width=100,
            )

        print(f"Converted {len(data['ingredients'])} ingredients to {output_path}")

    def save_json(self, output_path: Path) -> None:
        """Convert CSV and save as JSON.

        Args:
            output_path: Path to output JSON file
        """
        import json

        data = self.convert()

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"Converted {len(data['ingredients'])} ingredients to {output_path}")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Convert media ingredient CSV to LinkML format")
    parser.add_argument("csv_path", type=Path, help="Path to input CSV file")
    parser.add_argument("-o", "--output", type=Path, help="Output file path (YAML or JSON)")
    parser.add_argument(
        "-f",
        "--format",
        choices=["yaml", "json"],
        default="yaml",
        help="Output format (default: yaml)",
    )

    args = parser.parse_args()

    # Create converter
    converter = MediaIngredientCSVConverter(args.csv_path)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_path = args.csv_path.with_suffix(f".{args.format}")

    # Convert and save
    if args.format == "yaml":
        converter.save_yaml(output_path)
    else:
        converter.save_json(output_path)


if __name__ == "__main__":
    main()

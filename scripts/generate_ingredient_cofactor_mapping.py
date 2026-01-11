"""
Generate ingredient-to-cofactor mapping from MP medium ingredient properties.

This script parses the MP medium CSV file and creates a mapping between
ingredients and the cofactors they provide.

Output: data/processed/ingredient_cofactor_mapping.csv
"""

import csv
import yaml
from pathlib import Path


def load_cofactor_hierarchy():
    """Load cofactor hierarchy from YAML."""
    yaml_path = Path("src/microgrowagents/data/cofactor_hierarchy.yaml")
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    return data["cofactor_hierarchy"]


def map_ingredient(component, chebi_id, cellular_role, media_role):
    """Map ingredient to cofactors based on component name and roles."""
    cofactors = set()
    component_lower = component.lower()

    # Vitamins
    if "thiamin" in component_lower:
        cofactors.add(("thiamine_pyrophosphate", "CHEBI:9532"))
    if "biotin" in component_lower:
        cofactors.add(("biotin", "CHEBI:15956"))
    if "cobalamin" in component_lower or "b12" in component_lower:
        cofactors.add(("cobalamin", "CHEBI:16335"))
    if "pyridoxine" in component_lower or "b6" in component_lower:
        cofactors.add(("pyridoxal_phosphate", "CHEBI:18405"))
    if "riboflavin" in component_lower:
        cofactors.add(("flavin_adenine_dinucleotide", "CHEBI:16238"))
    if "pantothen" in component_lower:
        cofactors.add(("coenzyme_a", "CHEBI:15346"))
    if "pqq" in component_lower:
        cofactors.add(("pyrroloquinoline_quinone", "CHEBI:18315"))

    # Metals
    if "fe" in component_lower or "iron" in component_lower or "ferr" in component_lower:
        cofactors.add(("iron_ion", "CHEBI:18248"))
        cofactors.add(("iron_sulfur_clusters", "CHEBI:30408"))
        cofactors.add(("heme", "CHEBI:30413"))
    if "zn" in component_lower or "zinc" in component_lower:
        cofactors.add(("zinc_ion", "CHEBI:27363"))
    if "cu" in component_lower or "copper" in component_lower or "cupr" in component_lower:
        cofactors.add(("copper_ion", "CHEBI:28694"))
    if "mg" in component_lower or "magnesium" in component_lower:
        cofactors.add(("magnesium_ion", "CHEBI:18420"))
    if "ca" in component_lower or "calcium" in component_lower:
        cofactors.add(("calcium_ion", "CHEBI:29108"))
    if "mn" in component_lower or "manganese" in component_lower:
        cofactors.add(("manganese_ion", "CHEBI:29035"))
    if "mo" in component_lower or "molybdenum" in component_lower or "molybdate" in component_lower:
        cofactors.add(("molybdenum_cofactor", "CHEBI:25374"))
    if "co" in component_lower or "cobalt" in component_lower:
        cofactors.add(("cobalt_ion", "CHEBI:48828"))
        cofactors.add(("cobalamin", "CHEBI:16335"))
    if "neodymium" in component_lower or "cerium" in component_lower or "praseodymium" in component_lower:
        cofactors.add(("lanthanides", "CHEBI:33319"))

    return list(cofactors)


def generate_mapping():
    """Generate ingredient-to-cofactor mapping CSV."""
    mp_csv_path = Path("data/raw/mp_medium_ingredient_properties.csv")

    if not mp_csv_path.exists():
        print(f"Error: {mp_csv_path} not found")
        return

    mapping_rows = []

    # Read MP medium CSV
    with open(mp_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            component = row.get("Component", "")
            chebi_id = row.get("Database_ID", "")
            cellular_role = row.get("Cellular_Role", "")
            media_role = row.get("Media Role", "")

            if not component:
                continue

            # Map to cofactors
            cofactor_matches = map_ingredient(component, chebi_id, cellular_role, media_role)

            if cofactor_matches:
                cofactor_keys = [cf[0] for cf in cofactor_matches]
                cofactor_ids = [cf[1] for cf in cofactor_matches]

                mapping_rows.append({
                    "Component": component,
                    "CHEBI_ID": chebi_id,
                    "Cofactors_Provided": ";".join(cofactor_keys),
                    "Cofactor_IDs": ";".join(cofactor_ids),
                    "Bioavailability": "Variable",
                    "Notes": f"Provides: {', '.join(cofactor_keys)}"
                })

    # Write output CSV
    output_path = Path("data/processed/ingredient_cofactor_mapping.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["Component", "CHEBI_ID", "Cofactors_Provided", "Cofactor_IDs", "Bioavailability", "Notes"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(mapping_rows)

    print(f"Generated mapping for {len(mapping_rows)} ingredients")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    generate_mapping()

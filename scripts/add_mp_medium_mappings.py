"""Add CHEBI/PubChem/CAS-RN mappings to MP medium ingredient properties CSV."""

import pandas as pd
import re
from pathlib import Path


# Manual mappings for compounds not in the mappings file
MANUAL_MAPPINGS = {
    "Dysprosium (III) chloride hexahydrate": ("CHEBI:30443", "Cl3Dy.6H2O"),  # dysprosium trichloride hexahydrate
    "Neodymium (III) chloride hexahydrate": ("CHEBI:52501", "Cl3Nd.6H2O"),  # neodymium trichloride hexahydrate
    "Praseodymium (III) chloride hexahydrate": ("CHEBI:52503", "Cl3Pr.6H2O"),  # praseodymium trichloride hexahydrate
    "K₂HPO₄·3H₂O": ("CHEBI:131527", "K2HPO4.3H2O"),  # dipotassium hydrogen phosphate trihydrate
    "NaH₂PO₄·H₂O": ("CHEBI:37586", "NaH2PO4.H2O"),  # sodium dihydrogen phosphate monohydrate
    "MgCl₂·6H₂O": ("CHEBI:86345", "MgCl2.6H2O"),  # magnesium dichloride hexahydrate
    "(NH₄)₂SO₄": ("CHEBI:62946", "(NH4)2SO4"),  # ammonium sulfate
    "CaCl₂·2H₂O": ("CHEBI:86158", "CaCl2.2H2O"),  # calcium chloride dihydrate
    "ZnSO₄·7H₂O": ("CHEBI:32312", "ZnSO4.7H2O"),  # zinc sulfate heptahydrate
    "MnCl₂·4H₂O": ("CHEBI:86345", "MnCl2.4H2O"),  # manganese dichloride tetrahydrate
    "FeSO₄·7H₂O": ("CHEBI:75832", "FeSO4.7H2O"),  # iron(II) sulfate heptahydrate
    "(NH₄)₆Mo₇O₂₄·4H₂O": ("CHEBI:75211", "(NH4)6Mo7O24.4H2O"),  # ammonium heptamolybdate tetrahydrate
    "CuSO₄·5H₂O": ("CHEBI:31440", "CuSO4.5H2O"),  # copper(II) sulfate pentahydrate
    "CoCl₂·6H₂O": ("CHEBI:86134", "CoCl2.6H2O"),  # cobalt dichloride hexahydrate
    "Na₂WO₄·2H₂O": ("CHEBI:86714", "Na2WO4.2H2O"),  # sodium tungstate dihydrate
    "Thiamin": ("CHEBI:49105", "C12H17N4OS+"),  # thiamin(1+)
}


def extract_chemical_formula(component_name: str) -> str:
    """
    Extract chemical formula from component name.

    Examples:
        K₂HPO₄·3H₂O -> K₂HPO₄·3H₂O
        PIPES -> (extracted from mappings if available)
        Sodium citrate -> (extracted from mappings if available)
    """
    # Check if component name contains chemical formula symbols
    formula_pattern = r'[A-Z][a-z]?[₀-₉0-9]*'
    if re.search(r'[₀-₉₂₃₄₅₆₇]|·|[A-Z][a-z]?[₀-₉0-9]*[A-Z]', component_name):
        # Already contains formula notation
        return component_name
    return ""


def normalize_component_name(name: str) -> str:
    """Normalize component name for matching."""
    # Remove hydration notation
    name = re.sub(r'[·\s]*[x×]?\s*\d+\s*H[₂2]O', '', name, flags=re.IGNORECASE)
    # Remove punctuation and normalize spaces
    name = re.sub(r'[·\s\-()]+', '', name.lower().strip())
    return name


def find_best_mapping(component: str, mappings_df: pd.DataFrame) -> tuple[str, str]:
    """
    Find best ID mapping for a component in preference order: CHEBI → PubChem → CAS-RN.

    Returns:
        Tuple of (id_value, formula)
    """
    # Check manual mappings first
    if component in MANUAL_MAPPINGS:
        return MANUAL_MAPPINGS[component]

    # Normalize component name for matching
    component_normalized = component.lower().strip()
    component_base = normalize_component_name(component)

    # Try exact match on original field
    exact_match = mappings_df[mappings_df['original'].str.lower() == component_normalized]

    if not exact_match.empty:
        row = exact_match.iloc[0]

        # Get formula
        formula = row.get('chebi_formula', '')
        if pd.isna(formula):
            formula = ''

        # Preference order: CHEBI → PubChem → CAS-RN
        chebi_id = row.get('chebi_id', '')
        if pd.notna(chebi_id) and chebi_id and chebi_id != '':
            return str(chebi_id), formula

        # Check mapped field for PubChem or CAS-RN
        mapped = row.get('mapped', '')
        if pd.notna(mapped) and mapped:
            if mapped.startswith('PubChem:'):
                return mapped, formula
            elif mapped.startswith('CAS-RN:'):
                return mapped, formula

    # Try fuzzy matching on chebi_label
    label_match = mappings_df[mappings_df['chebi_label'].str.lower() == component_normalized]
    if not label_match.empty:
        row = label_match.iloc[0]
        formula = row.get('chebi_formula', '')
        if pd.isna(formula):
            formula = ''

        chebi_id = row.get('chebi_id', '')
        if pd.notna(chebi_id) and chebi_id:
            return str(chebi_id), formula

    # Try matching normalized names (without hydration)
    for _, row in mappings_df.iterrows():
        original = str(row.get('original', ''))
        label = str(row.get('chebi_label', ''))

        original_base = normalize_component_name(original)
        label_base = normalize_component_name(label)

        if component_base and (component_base == original_base or component_base == label_base):
            formula = row.get('chebi_formula', '')
            if pd.isna(formula):
                formula = ''

            chebi_id = row.get('chebi_id', '')
            if pd.notna(chebi_id) and chebi_id:
                return str(chebi_id), formula

            mapped = row.get('mapped', '')
            if pd.notna(mapped) and mapped:
                return mapped, formula

    return '', ''


def main():
    """Main function to add mappings to MP medium CSV."""
    # Paths
    data_dir = Path(__file__).parent.parent / 'data' / 'raw'
    mp_csv = data_dir / 'mp_medium_ingredient_properties.csv'
    mappings_tsv = data_dir / 'compound_mappings_strict_final.tsv'
    output_csv = data_dir / 'mp_medium_ingredient_properties_with_ids.csv'

    # Load data
    print(f"Loading MP medium CSV from {mp_csv}...")
    mp_df = pd.read_csv(mp_csv)

    print(f"Loading compound mappings from {mappings_tsv}...")
    mappings_df = pd.read_csv(mappings_tsv, sep='\t', low_memory=False)

    print(f"Found {len(mp_df)} ingredients in MP medium")
    print(f"Found {len(mappings_df)} mappings in compound mappings file")

    # Process each component
    formulas = []
    ids = []

    for idx, row in mp_df.iterrows():
        component = row.get('Component', '')
        if pd.isna(component):
            formulas.append('')
            ids.append('')
            continue

        print(f"\nProcessing: {component}")

        # Find mapping
        id_value, formula = find_best_mapping(component, mappings_df)

        if not formula:
            # Try to extract from component name
            formula = extract_chemical_formula(component)

        formulas.append(formula)
        ids.append(id_value)

        if id_value:
            print(f"  → ID: {id_value}")
            if formula:
                print(f"  → Formula: {formula}")
        else:
            print(f"  → No mapping found")

    # Find position to insert columns (after "Component" which should be column 1)
    component_col_idx = mp_df.columns.get_loc('Component') + 1

    # Create new dataframe with inserted columns
    new_columns = list(mp_df.columns)
    new_columns.insert(component_col_idx, 'Chemical_Formula')
    new_columns.insert(component_col_idx + 1, 'Database_ID')

    # Create new dataframe
    new_df = pd.DataFrame(columns=new_columns)

    # Copy data
    for col in mp_df.columns:
        new_df[col] = mp_df[col]

    new_df['Chemical_Formula'] = formulas
    new_df['Database_ID'] = ids

    # Reorder columns
    cols_order = (
        list(mp_df.columns[:component_col_idx]) +
        ['Chemical_Formula', 'Database_ID'] +
        list(mp_df.columns[component_col_idx:])
    )
    new_df = new_df[cols_order]

    # Save
    print(f"\nSaving to {output_csv}...")
    new_df.to_csv(output_csv, index=False)
    print(f"✓ Saved {len(new_df)} rows")

    # Print summary
    mapped_count = sum(1 for id_val in ids if id_val)
    print(f"\n=== Summary ===")
    print(f"Total ingredients: {len(ids)}")
    print(f"Mapped: {mapped_count}")
    print(f"Unmapped: {len(ids) - mapped_count}")

    # Print unmapped
    unmapped = [mp_df.iloc[i]['Component'] for i, id_val in enumerate(ids) if not id_val]
    if unmapped:
        print(f"\nUnmapped ingredients:")
        for ing in unmapped:
            print(f"  - {ing}")


if __name__ == '__main__':
    main()

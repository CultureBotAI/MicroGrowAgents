"""
Molecular weight calculations with hydrate support.

Adapted from MicroMediaParam:
https://github.com/CultureBotAI/MicroMediaParam/blob/main/src/quality/calculate_molecular_weights.py

Enhancements:
- Integration with compound normalizer
- Support for complex formulas
- Hydration state corrections
"""

import re
from typing import Dict, Optional, Tuple

# Atomic weights (IUPAC 2021 standard atomic weights)
ATOMIC_WEIGHTS = {
    "H": 1.008,
    "He": 4.003,
    "Li": 6.941,
    "Be": 9.012,
    "B": 10.81,
    "C": 12.011,
    "N": 14.007,
    "O": 15.999,
    "F": 18.998,
    "Ne": 20.180,
    "Na": 22.990,
    "Mg": 24.305,
    "Al": 26.982,
    "Si": 28.085,
    "P": 30.974,
    "S": 32.06,
    "Cl": 35.45,
    "Ar": 39.948,
    "K": 39.098,
    "Ca": 40.078,
    "Sc": 44.956,
    "Ti": 47.867,
    "V": 50.942,
    "Cr": 51.996,
    "Mn": 54.938,
    "Fe": 55.845,
    "Co": 58.933,
    "Ni": 58.693,
    "Cu": 63.546,
    "Zn": 65.38,
    "Ga": 69.723,
    "Ge": 72.630,
    "As": 74.922,
    "Se": 78.971,
    "Br": 79.904,
    "Kr": 83.798,
    "Rb": 85.468,
    "Sr": 87.62,
    "Y": 88.906,
    "Zr": 91.224,
    "Nb": 92.906,
    "Mo": 95.95,
    "Tc": 98.0,
    "Ru": 101.07,
    "Rh": 102.91,
    "Pd": 106.42,
    "Ag": 107.87,
    "Cd": 112.41,
    "In": 114.82,
    "Sn": 118.71,
    "Sb": 121.76,
    "Te": 127.60,
    "I": 126.90,
    "Xe": 131.29,
    "Cs": 132.91,
    "Ba": 137.33,
    "La": 138.91,
    "Ce": 140.12,
    "Pr": 140.91,
    "Nd": 144.24,
    "Pm": 145.0,
    "Sm": 150.36,
    "Eu": 151.96,
    "Gd": 157.25,
    "Tb": 158.93,
    "Dy": 162.50,
    "Ho": 164.93,
    "Er": 167.26,
    "Tm": 168.93,
    "Yb": 173.05,
    "Lu": 174.97,
    "Hf": 178.49,
    "Ta": 180.95,
    "W": 183.84,
    "Re": 186.21,
    "Os": 190.23,
    "Ir": 192.22,
    "Pt": 195.08,
    "Au": 196.97,
    "Hg": 200.59,
    "Tl": 204.38,
    "Pb": 207.2,
    "Bi": 208.98,
    "Po": 209.0,
    "At": 210.0,
    "Rn": 222.0,
    "Fr": 223.0,
    "Ra": 226.0,
    "Ac": 227.0,
    "Th": 232.04,
    "Pa": 231.04,
    "U": 238.03,
}

# Common compounds lookup table (from MicroMediaParam)
COMMON_COMPOUNDS_MW = {
    "glucose": 180.16,
    "nacl": 58.44,
    "kcl": 74.55,
    "cacl2": 110.98,
    "mgso4": 120.37,
    "na2hpo4": 141.96,
    "kh2po4": 136.09,
    "nh4cl": 53.49,
    "(nh4)2so4": 132.14,
    "feso4": 151.91,
    "mnso4": 151.00,
    "znso4": 161.47,
    "cuso4": 159.61,
    "h3bo3": 61.83,
    "coso4": 154.996,
    "namoo4": 205.92,
    "edta": 292.24,
    "tris": 121.14,
    "hepes": 238.30,
    "mes": 195.24,
    "mops": 209.26,
    "pipes": 302.37,
    "tricine": 179.17,
    "glycine": 75.07,
    "alanine": 89.09,
    "valine": 117.15,
    "leucine": 131.17,
    "isoleucine": 131.17,
    "serine": 105.09,
    "threonine": 119.12,
    "cysteine": 121.16,
    "methionine": 149.21,
    "asparagine": 132.12,
    "glutamine": 146.15,
    "lysine": 146.19,
    "arginine": 174.20,
    "histidine": 155.15,
    "phenylalanine": 165.19,
    "tyrosine": 181.19,
    "tryptophan": 204.23,
    "proline": 115.13,
    "aspartic acid": 133.10,
    "glutamic acid": 147.13,
    "adenine": 135.13,
    "guanine": 151.13,
    "cytosine": 111.10,
    "thymine": 126.11,
    "uracil": 112.09,
}

# Water molecular weight for hydrate calculations
WATER_MW = 18.015


def calculate_molecular_weight(
    formula: str, hydration_number: int = 0
) -> Optional[float]:
    """
    Calculate molecular weight from chemical formula.

    Handles:
    - Simple formulas: H2O, NaCl, CaCl2
    - Complex formulas: Ca(OH)2, (NH4)2SO4
    - Hydrates: automatic correction if hydration_number provided

    Args:
        formula: Chemical formula (e.g., "CaCl2", "Ca(OH)2")
        hydration_number: Number of water molecules (default: 0)

    Returns:
        Molecular weight in g/mol, or None if parsing fails

    Examples:
        >>> calculate_molecular_weight("H2O")
        18.015
        >>> calculate_molecular_weight("CaCl2", hydration_number=2)
        147.015  # 110.98 + 2*18.015
        >>> calculate_molecular_weight("Ca(OH)2")
        74.093
    """
    # Try common compounds first (fast lookup)
    normalized = formula.lower().strip()
    if normalized in COMMON_COMPOUNDS_MW:
        base_mw = COMMON_COMPOUNDS_MW[normalized]
        if hydration_number > 0:
            return base_mw + (hydration_number * WATER_MW)
        return base_mw

    # Parse formula element by element
    base_mw = parse_formula(formula)

    if base_mw is None:
        return None

    # Add hydration water
    if hydration_number > 0:
        return base_mw + (hydration_number * WATER_MW)

    return base_mw


def parse_formula(formula: str) -> Optional[float]:
    """
    Parse chemical formula and calculate molecular weight.

    Handles parentheses and complex formulas.

    Args:
        formula: Chemical formula

    Returns:
        Molecular weight or None if parsing fails
    """
    # Remove spaces
    formula = formula.replace(" ", "")

    # Handle parentheses recursively
    while "(" in formula:
        # Find innermost parentheses
        match = re.search(r"\(([^()]+)\)(\d*)", formula)
        if not match:
            break

        inner_formula = match.group(1)
        multiplier = int(match.group(2)) if match.group(2) else 1

        # Calculate weight of inner formula
        inner_weight = parse_formula(inner_formula)
        if inner_weight is None:
            return None

        # Replace with a placeholder that won't interfere
        # We'll use a dummy element symbol that doesn't exist
        placeholder = f"X{inner_weight * multiplier}"
        formula = formula[: match.start()] + placeholder + formula[match.end() :]

    # Parse element counts
    total_weight = 0.0

    # Pattern: Element (uppercase + optional lowercase) followed by optional number
    pattern = r"([A-Z][a-z]?)(\d*)"

    for match in re.finditer(pattern, formula):
        element = match.group(1)
        count_str = match.group(2)
        count = int(count_str) if count_str else 1

        # Check for placeholder (X followed by number)
        if element == "X":
            # Extract the weight from the full match
            remaining = formula[match.start() :]
            weight_match = re.match(r"X([\d.]+)", remaining)
            if weight_match:
                weight = float(weight_match.group(1))
                total_weight += weight
                continue

        if element not in ATOMIC_WEIGHTS:
            # Unknown element
            return None

        total_weight += ATOMIC_WEIGHTS[element] * count

    return round(total_weight, 3)


def calculate_hydrated_weight(
    base_weight: float, hydration_number: int
) -> float:
    """
    Calculate hydrated molecular weight.

    Args:
        base_weight: Molecular weight of anhydrous compound
        hydration_number: Number of water molecules

    Returns:
        Hydrated molecular weight

    Example:
        >>> calculate_hydrated_weight(120.37, 7)  # MgSO4·7H2O
        246.475
    """
    return base_weight + (hydration_number * WATER_MW)


def extract_hydration_number(compound_name: str) -> Tuple[str, int]:
    """
    Extract hydration number from compound name.

    Args:
        compound_name: Compound name (may include hydration)

    Returns:
        Tuple of (base_name, hydration_number)

    Examples:
        >>> extract_hydration_number("CaCl2·2H2O")
        ("CaCl2", 2)
        >>> extract_hydration_number("MgSO4 7-hydrate")
        ("MgSO4", 7)
        >>> extract_hydration_number("glucose")
        ("glucose", 0)
    """
    # Patterns from MicroMediaParam
    patterns = [
        r"(.+?)[·.\s]+(\d+)\s*H2O",  # CaCl2·2H2O, CaCl2.2H2O, CaCl2 2H2O
        r"(.+?)\s+(\d+)-hydrate",  # MgSO4 7-hydrate
        r"(.+?)\s+monohydrate",  # MgSO4 monohydrate
        r"(.+?)\s+dihydrate",  # CaCl2 dihydrate
        r"(.+?)\s+trihydrate",  # Na2HPO4 trihydrate
        r"(.+?)\s+tetrahydrate",  # FeSO4 tetrahydrate
        r"(.+?)\s+pentahydrate",  # CuSO4 pentahydrate
        r"(.+?)\s+hexahydrate",  # MgCl2 hexahydrate
        r"(.+?)\s+heptahydrate",  # MgSO4 heptahydrate
        r"(.+?)\s+octahydrate",  # Ba(OH)2 octahydrate
        r"(.+?)\s+nonahydrate",  # Na2HPO4 nonahydrate
        r"(.+?)\s+decahydrate",  # Na2SO4 decahydrate
    ]

    hydration_numbers = {
        "monohydrate": 1,
        "dihydrate": 2,
        "trihydrate": 3,
        "tetrahydrate": 4,
        "pentahydrate": 5,
        "hexahydrate": 6,
        "heptahydrate": 7,
        "octahydrate": 8,
        "nonahydrate": 9,
        "decahydrate": 10,
    }

    for pattern in patterns:
        match = re.search(pattern, compound_name, re.IGNORECASE)
        if match:
            base_name = match.group(1).strip()
            if len(match.groups()) == 2 and match.group(2).isdigit():
                # Pattern with explicit number
                hydration_num = int(match.group(2))
            else:
                # Pattern with text (monohydrate, etc.)
                hydrate_text = match.group(0).split()[-1].lower()
                hydration_num = hydration_numbers.get(hydrate_text, 0)

            return (base_name, hydration_num)

    # No hydration found
    return (compound_name, 0)

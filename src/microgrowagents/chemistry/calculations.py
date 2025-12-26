"""
Chemistry calculations for media analysis.

Implements:
- pH calculation for multi-component mixtures (Henderson-Hasselbalch)
- Ionic strength calculation (Debye-Hückel)
- Buffer capacity
- Salinity estimation
- pKa estimation (from MicroMediaParam + extensions)

References:
- MicroMediaParam property_extractor.py for pKa patterns
- Standard physical chemistry equations
"""

import math
import re
from typing import Dict, List, Optional, Tuple

import numpy as np

# pKa values for common compounds (from MicroMediaParam + literature)
PKA_DATABASE = {
    # Buffers
    "tris": [8.06],
    "hepes": [7.48],
    "mes": [6.15],
    "mops": [7.20],
    "pipes": [6.76],
    "tricine": [8.15],
    "bicine": [8.35],
    "tes": [7.40],
    "mobs": [7.60],
    # Phosphates
    "phosphate": [2.15, 7.20, 12.35],
    "h3po4": [2.15, 7.20, 12.35],
    "h2po4": [7.20, 12.35],
    "hpo4": [12.35],
    # Carbonates
    "carbonate": [6.35, 10.33],
    "h2co3": [6.35, 10.33],
    "hco3": [10.33],
    # Organic acids
    "acetic acid": [4.76],
    "acetate": [4.76],
    "citric acid": [3.13, 4.76, 6.40],
    "citrate": [3.13, 4.76, 6.40],
    "lactic acid": [3.86],
    "lactate": [3.86],
    "pyruvic acid": [2.49],
    "pyruvate": [2.49],
    "succinic acid": [4.21, 5.64],
    "succinate": [4.21, 5.64],
    "formic acid": [3.75],
    "formate": [3.75],
    # Amino acids (alpha-carboxyl, alpha-amino, side chain if applicable)
    "glycine": [2.34, 9.60],
    "alanine": [2.34, 9.69],
    "aspartic acid": [1.88, 3.65, 9.60],
    "glutamic acid": [2.19, 4.25, 9.67],
    "histidine": [1.82, 6.00, 9.17],
    "lysine": [2.18, 8.95, 10.53],
    "arginine": [2.17, 9.04, 12.48],
    "cysteine": [1.96, 8.18, 10.28],
    # Common inorganic acids/bases
    "hcl": [-6.0],  # Strong acid
    "naoh": [14.0],  # Strong base
    "h2so4": [-3.0, 1.99],  # Strong acid + weak
    "hno3": [-1.4],  # Strong acid
    "nh3": [9.25],
    "nh4": [9.25],
}

# Functional group pKa patterns (SMILES-based, from MicroMediaParam)
FUNCTIONAL_GROUP_PKA = {
    "carboxylic_acid": 4.75,
    "primary_amine": 10.8,
    "secondary_amine": 11.0,
    "tertiary_amine": 9.8,
    "phenol": 10.0,
    "thiol": 8.5,
    "phosphate": 7.2,
    "sulfonic_acid": -2.8,
}


def calculate_mixture_ph(
    ingredients: List[Dict[str, float]],
    temperature: float = 25.0,
    ionic_strength: Optional[float] = None,
) -> Dict[str, float]:
    """
    Calculate pH of ingredient mixture using Henderson-Hasselbalch equation.

    Handles multi-component mixtures with buffers, acids, and bases.

    Args:
        ingredients: List of ingredient dicts with:
            - name: str
            - concentration: float (mol/L)
            - pka: float or List[float] (optional, will estimate if missing)
            - is_acid: bool (optional)
            - charge: int (optional)
        temperature: Temperature in Celsius (default: 25)
        ionic_strength: Ionic strength (mol/L), will calculate if None

    Returns:
        Dictionary with:
        - ph: float
        - ionic_strength: float
        - buffer_capacity: float (if buffered)
        - dominant_buffer: str (if applicable)

    Example:
        >>> ingredients = [
        ...     {"name": "phosphate", "concentration": 0.05, "pka": [2.15, 7.20, 12.35]},
        ...     {"name": "NaCl", "concentration": 0.15, "charge": 1}
        ... ]
        >>> calculate_mixture_ph(ingredients)
        {"ph": 7.2, "ionic_strength": 0.2, ...}
    """
    if not ingredients:
        return {"ph": 7.0, "ionic_strength": 0.0}

    # Calculate ionic strength if not provided
    if ionic_strength is None:
        ionic_strength = calculate_ionic_strength(ingredients)

    # Separate components by type
    buffers = []
    acids = []
    bases = []

    for ing in ingredients:
        conc = ing.get("concentration", 0.0)
        if conc <= 0:
            continue

        # Get pKa values
        pka_values = ing.get("pka")
        if pka_values is None:
            # Try to estimate
            pka_values = estimate_pka(ing.get("name", ""))

        if not pka_values:
            continue

        if not isinstance(pka_values, list):
            pka_values = [pka_values]

        # Classify as buffer, acid, or base
        for pka in pka_values:
            if 3.0 < pka < 11.0:  # Buffering range
                buffers.append({"name": ing["name"], "pka": pka, "concentration": conc})
            elif pka < 3.0:
                acids.append({"name": ing["name"], "pka": pka, "concentration": conc})
            else:
                bases.append({"name": ing["name"], "pka": pka, "concentration": conc})

    # Calculate pH based on dominant component
    if buffers:
        # Use Henderson-Hasselbalch for buffer
        dominant_buffer = max(buffers, key=lambda x: x["concentration"])
        pka = dominant_buffer["pka"]

        # Activity coefficient correction (Davies equation)
        log_gamma = -0.51 * (math.sqrt(ionic_strength) / (1 + math.sqrt(ionic_strength)) - 0.3 * ionic_strength)
        pka_corrected = pka - log_gamma

        # Assume equal acid/base form for simplicity (can be refined)
        ph = pka_corrected

        # Calculate buffer capacity
        buffer_capacity = calculate_buffer_capacity(
            dominant_buffer["concentration"], pka_corrected, ph
        )

        return {
            "ph": round(ph, 2),
            "ionic_strength": round(ionic_strength, 3),
            "buffer_capacity": round(buffer_capacity, 3),
            "dominant_buffer": dominant_buffer["name"],
            "pka_effective": round(pka_corrected, 2),
        }

    elif acids:
        # Acidic solution
        total_h = sum(ing["concentration"] * 10 ** (-ing["pka"]) for ing in acids)
        ph = -math.log10(total_h) if total_h > 0 else 7.0
        return {
            "ph": round(ph, 2),
            "ionic_strength": round(ionic_strength, 3),
            "buffer_capacity": 0.0,
        }

    elif bases:
        # Basic solution
        total_oh = sum(ing["concentration"] * 10 ** (-(14 - ing["pka"])) for ing in bases)
        poh = -math.log10(total_oh) if total_oh > 0 else 7.0
        ph = 14 - poh
        return {
            "ph": round(ph, 2),
            "ionic_strength": round(ionic_strength, 3),
            "buffer_capacity": 0.0,
        }

    else:
        # Neutral
        return {"ph": 7.0, "ionic_strength": round(ionic_strength, 3)}


def calculate_ionic_strength(ingredients: List[Dict[str, float]]) -> float:
    """
    Calculate ionic strength of solution.

    I = 0.5 * Σ(c_i * z_i^2)

    Args:
        ingredients: List of ingredient dicts with:
            - concentration: float (mol/L)
            - charge: int (ionic charge)

    Returns:
        Ionic strength in mol/L

    Example:
        >>> ingredients = [
        ...     {"concentration": 0.15, "charge": 1},  # Na+
        ...     {"concentration": 0.15, "charge": -1}, # Cl-
        ... ]
        >>> calculate_ionic_strength(ingredients)
        0.15
    """
    ionic_strength = 0.0

    for ing in ingredients:
        conc = ing.get("concentration", 0.0)
        charge = ing.get("charge", 0)

        if conc > 0 and charge != 0:
            ionic_strength += 0.5 * conc * (charge ** 2)

    return ionic_strength


def calculate_buffer_capacity(
    concentration: float, pka: float, ph: float
) -> float:
    """
    Calculate buffer capacity (β) in mol/(L·pH).

    β = 2.303 * C * ([H+] * Ka) / (Ka + [H+])^2

    Args:
        concentration: Buffer concentration (mol/L)
        pka: Buffer pKa
        ph: Solution pH

    Returns:
        Buffer capacity

    Example:
        >>> calculate_buffer_capacity(0.1, 7.2, 7.2)  # Phosphate at pH = pKa
        0.058
    """
    ka = 10 ** (-pka)
    h_conc = 10 ** (-ph)

    if (ka + h_conc) == 0:
        return 0.0

    beta = 2.303 * concentration * (h_conc * ka) / ((ka + h_conc) ** 2)
    return beta


def calculate_salinity(ingredients: List[Dict]) -> float:
    """
    Calculate Total Dissolved Solids (TDS) in g/L.

    Note: This is often called "salinity" but technically measures TDS,
    which includes ALL dissolved compounds (salts, organics, buffers, etc.),
    not just ionic salts. For charge-weighted ionic concentration, use
    calculate_ionic_strength() instead.

    Args:
        ingredients: List of ingredient dicts with:
            - grams_per_liter: float

    Returns:
        Total dissolved solids (TDS) in g/L

    Example:
        >>> ingredients = [
        ...     {"grams_per_liter": 10.0},  # NaCl
        ...     {"grams_per_liter": 5.0},   # Glucose
        ... ]
        >>> calculate_salinity(ingredients)
        15.0
    """
    tds = sum(ing.get("grams_per_liter", 0.0) for ing in ingredients)
    return round(tds, 2)


def calculate_tds(ingredients: List[Dict]) -> float:
    """
    Calculate Total Dissolved Solids (TDS) in g/L.

    Alias for calculate_salinity() with clearer naming.

    Args:
        ingredients: List of ingredient dicts with grams_per_liter

    Returns:
        Total dissolved solids (TDS) in g/L
    """
    return calculate_salinity(ingredients)


def calculate_nacl_salinity(ingredients: List[Dict]) -> float:
    """
    Calculate NaCl-equivalent salinity from ionic salts only (g/L).

    Sums contribution from inorganic ionic salts (chlorides, sulfates, nitrates)
    excluding organic compounds, buffers, and non-ionic compounds. This represents
    the traditional "salinity" concept used in microbiology.

    Common ionic salts included:
    - Chlorides: NaCl, KCl, CaCl2, MgCl2, NH4Cl, FeCl2, FeCl3, etc.
    - Sulfates: (NH4)2SO4, MgSO4, FeSO4, K2SO4, Na2SO4, etc.
    - Nitrates: NaNO3, KNO3, Ca(NO3)2, etc.
    - Other salts: NaBr, KBr, NaI, etc.

    Excludes:
    - Organic buffers (PIPES, HEPES, MES, MOPS, Tris, etc.)
    - Phosphate buffers (often act as buffers, not just salts)
    - Organic compounds (glucose, vitamins, amino acids, etc.)
    - Non-ionic compounds

    Args:
        ingredients: List of ingredient dicts with:
            - name: str (ingredient name)
            - grams_per_liter: float

    Returns:
        NaCl-equivalent salinity in g/L (sum of ionic salt masses)

    Example:
        >>> ingredients = [
        ...     {"name": "NaCl", "grams_per_liter": 5.0},
        ...     {"name": "glucose", "grams_per_liter": 10.0},
        ...     {"name": "MgSO4", "grams_per_liter": 2.0},
        ...     {"name": "PIPES", "grams_per_liter": 3.0}
        ... ]
        >>> calculate_nacl_salinity(ingredients)
        7.0
    """
    # Patterns for ionic salts (case-insensitive)
    ionic_salt_patterns = [
        # Chlorides
        r"(Na|K|Ca|Mg|Fe|Mn|Zn|Cu|NH4|Li|Rb|Cs|Ba|Sr|Al|Co|Ni)Cl\d?",
        # Sulfates
        r"(Na|K|Ca|Mg|Fe|Mn|Zn|Cu|NH4|Li|Al|Co|Ni)[\d_()]*SO4",
        # Nitrates
        r"(Na|K|Ca|Mg|Fe|Mn|NH4|Li|Ba|Sr)[\d_()]*NO3",
        # Bromides, Iodides
        r"(Na|K|Ca|Mg|NH4|Li)(Br|I)\d?",
        # Carbonates and bicarbonates (ionic salts, though also pH-active)
        r"(Na|K|Ca|Mg)[\d_()]*CO3",
        r"(Na|K|Ca|Mg)HCO3",
    ]

    # Excluded patterns (buffers and non-salts)
    excluded_patterns = [
        r"PIPES", r"HEPES", r"MES", r"MOPS", r"TES", r"TRICINE", r"BICINE",
        r"Tris", r"TRIS", r"MOBS", r"ADA", r"BES", r"CAPS", r"CHES",
        r"glucose", r"glycerol", r"sucrose", r"fructose",
        r"vitamin", r"thiamine", r"biotin", r"pantothenate",
        r"amino acid", r"alanine", r"glycine", r"leucine",
        # Phosphate buffers are excluded (act as buffers, not just salts)
        r".*PO4", r"phosphate", r"buffer",
    ]

    nacl_salinity = 0.0

    for ing in ingredients:
        name = ing.get("name", "")
        gpl = ing.get("grams_per_liter", 0.0)

        if gpl <= 0:
            continue

        # Check if excluded
        is_excluded = any(re.search(pattern, name, re.IGNORECASE) for pattern in excluded_patterns)
        if is_excluded:
            continue

        # Check if it matches ionic salt patterns
        is_ionic_salt = any(re.search(pattern, name, re.IGNORECASE) for pattern in ionic_salt_patterns)
        if is_ionic_salt:
            nacl_salinity += gpl

    return round(nacl_salinity, 2)


def estimate_pka(compound_name: str, smiles: Optional[str] = None) -> Optional[List[float]]:
    """
    Estimate pKa values from compound name or SMILES.

    Uses lookup table and pattern matching (from MicroMediaParam).

    Args:
        compound_name: Compound name
        smiles: SMILES string (optional, for pattern matching)

    Returns:
        List of pKa values, or None if cannot estimate

    Example:
        >>> estimate_pka("phosphate")
        [2.15, 7.20, 12.35]
        >>> estimate_pka("tris")
        [8.06]
    """
    # Normalize name
    normalized = compound_name.lower().strip()

    # Check database
    if normalized in PKA_DATABASE:
        return PKA_DATABASE[normalized]

    # Check for partial matches
    for key, pka_values in PKA_DATABASE.items():
        if key in normalized or normalized in key:
            return pka_values

    # SMILES-based estimation (if provided)
    if smiles:
        return estimate_pka_from_smiles(smiles)

    # Formula-based estimation
    if re.search(r"PO4|H\d?PO4", compound_name, re.IGNORECASE):
        return [2.15, 7.20, 12.35]  # Phosphate
    elif re.search(r"CO3|HCO3", compound_name, re.IGNORECASE):
        return [6.35, 10.33]  # Carbonate
    elif re.search(r"NH\d|NH4", compound_name, re.IGNORECASE):
        return [9.25]  # Ammonium

    return None


def estimate_pka_from_smiles(smiles: str) -> Optional[List[float]]:
    """
    Estimate pKa from SMILES patterns (from MicroMediaParam).

    Args:
        smiles: SMILES string

    Returns:
        List of estimated pKa values
    """
    pka_values = []

    # Carboxylic acid: C(=O)O
    if "C(=O)O" in smiles or "C(O)=O" in smiles:
        pka_values.append(FUNCTIONAL_GROUP_PKA["carboxylic_acid"])

    # Primary amine: N (not in ring, not quaternary)
    if re.search(r"[^N]N[^N]", smiles):
        pka_values.append(FUNCTIONAL_GROUP_PKA["primary_amine"])

    # Phosphate: P(=O)(O)O
    if "P(=O)" in smiles or "P(O)" in smiles:
        pka_values.append(FUNCTIONAL_GROUP_PKA["phosphate"])

    # Phenol: c-O (aromatic-OH)
    if "cO" in smiles or "c-O" in smiles:
        pka_values.append(FUNCTIONAL_GROUP_PKA["phenol"])

    # Thiol: S
    if "S" in smiles and "S(=O)" not in smiles:  # Not sulfone
        pka_values.append(FUNCTIONAL_GROUP_PKA["thiol"])

    return pka_values if pka_values else None


def compare_media_chemistry(
    media1: List[Dict], media2: List[Dict]
) -> Dict[str, any]:
    """
    Compare chemical properties of two media formulations.

    Args:
        media1: Ingredients list for medium 1
        media2: Ingredients list for medium 2

    Returns:
        Dictionary with comparison results:
        - ph_diff: pH difference
        - ionic_strength_diff: Ionic strength difference
        - unique_to_media1: Ingredients only in media1
        - unique_to_media2: Ingredients only in media2
        - concentration_diffs: Concentration differences for shared ingredients

    Example:
        >>> media1 = [{"name": "glucose", "concentration": 0.1}]
        >>> media2 = [{"name": "glucose", "concentration": 0.05}]
        >>> compare_media_chemistry(media1, media2)
        {...}
    """
    # Calculate properties for each medium
    props1 = calculate_mixture_ph(media1)
    props2 = calculate_mixture_ph(media2)

    # Find unique and shared ingredients
    names1 = {ing["name"] for ing in media1}
    names2 = {ing["name"] for ing in media2}

    unique_to_media1 = names1 - names2
    unique_to_media2 = names2 - names1
    shared = names1 & names2

    # Calculate concentration differences for shared ingredients
    conc_diffs = {}
    for name in shared:
        conc1 = next((ing["concentration"] for ing in media1 if ing["name"] == name), 0)
        conc2 = next((ing["concentration"] for ing in media2 if ing["name"] == name), 0)
        if conc1 != conc2:
            conc_diffs[name] = {
                "media1": conc1,
                "media2": conc2,
                "diff": conc1 - conc2,
                "percent_diff": ((conc1 - conc2) / max(conc1, conc2) * 100) if max(conc1, conc2) > 0 else 0,
            }

    return {
        "ph_diff": round(props1["ph"] - props2["ph"], 2),
        "ionic_strength_diff": round(
            props1["ionic_strength"] - props2["ionic_strength"], 3
        ),
        "media1_properties": props1,
        "media2_properties": props2,
        "unique_to_media1": list(unique_to_media1),
        "unique_to_media2": list(unique_to_media2),
        "concentration_differences": conc_diffs,
        "ingredient_overlap": len(shared) / max(len(names1), len(names2)) if max(len(names1), len(names2)) > 0 else 0,
    }

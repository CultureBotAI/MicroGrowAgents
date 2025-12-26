"""
Nutrient ratio calculations for microbial growth media.

This module provides functions to calculate C:N:P ratios, trace metal ratios,
and identify limiting nutrients. These ratios are critical for predicting
nutrient limitation and optimizing media formulations.

Key functions:
    - calculate_cnp_ratios: Calculate C:N:P molar ratios and limiting nutrients
    - calculate_trace_metal_ratios: Calculate Fe:P, Mn:P, Zn:P ratios
    - parse_elemental_composition: Parse elemental composition from formula

Examples:
    >>> ingredients = [
    ...     {"name": "glucose", "concentration": 10.0, "formula": "C6H12O6"},
    ...     {"name": "NH4Cl", "concentration": 5.0, "formula": "NH4Cl"},
    ...     {"name": "KH2PO4", "concentration": 1.0, "formula": "KH2PO4"}
    ... ]
    >>> result = calculate_cnp_ratios(ingredients)  # doctest: +SKIP
    >>> result["limiting_nutrient"]
    'N'
"""

from typing import Dict, List, Optional, Any
import re


# Redfield ratio (marine microorganisms): C:N:P = 106:16:1
REDFIELD_RATIO = {
    "C": 106.0,
    "N": 16.0,
    "P": 1.0
}

# Typical trace metal requirements relative to P
# Values from literature (e.g., Morel & Price 2003, Anderson & Morel 1982)
TRACE_METAL_REQUIREMENTS = {
    "Fe": {"min": 0.02, "max": 0.2, "typical": 0.1},  # Fe:P ratio
    "Mn": {"min": 0.001, "max": 0.01, "typical": 0.005},  # Mn:P ratio
    "Zn": {"min": 0.001, "max": 0.01, "typical": 0.003},  # Zn:P ratio
    "Cu": {"min": 0.0001, "max": 0.001, "typical": 0.0005},
    "Co": {"min": 0.00001, "max": 0.0001, "typical": 0.00005},
    "Mo": {"min": 0.00001, "max": 0.0001, "typical": 0.00005}
}


def parse_elemental_composition(formula: str) -> Dict[str, int]:
    """
    Parse elemental composition from chemical formula.

    Uses regex to extract element symbols and counts, handling:
    - Simple formulas: C6H12O6
    - Formulas with parentheses: Ca(NO3)2
    - Multi-character elements: Mg, Ca, Fe, etc.

    Args:
        formula: Chemical formula string

    Returns:
        Dictionary mapping element symbol → count

    Examples:
        >>> parse_elemental_composition("C6H12O6")
        {'C': 6, 'H': 12, 'O': 6}

        >>> parse_elemental_composition("K2HPO4")
        {'K': 2, 'H': 1, 'P': 1, 'O': 4}

        >>> parse_elemental_composition("Ca(NO3)2")
        {'Ca': 1, 'N': 2, 'O': 6}
    """
    if not formula:
        return {}

    composition = {}

    # Expand parentheses first: Ca(NO3)2 → CaN2O6
    # Pattern: (group)number
    while '(' in formula:
        match = re.search(r'\(([^\)]+)\)(\d+)', formula)
        if not match:
            break

        group = match.group(1)
        multiplier = int(match.group(2))

        # Parse group and multiply counts
        expanded = ""
        for elem_match in re.finditer(r'([A-Z][a-z]?)(\d*)', group):
            elem = elem_match.group(1)
            count = int(elem_match.group(2)) if elem_match.group(2) else 1
            new_count = count * multiplier
            expanded += elem + (str(new_count) if new_count > 1 else "")

        formula = formula[:match.start()] + expanded + formula[match.end():]

    # Parse elements and counts
    # Pattern: Uppercase letter, optional lowercase letter, optional digits
    for match in re.finditer(r'([A-Z][a-z]?)(\d*)', formula):
        element = match.group(1)
        count = int(match.group(2)) if match.group(2) else 1

        composition[element] = composition.get(element, 0) + count

    return composition


def calculate_cnp_ratios(
    ingredients: List[Dict]
) -> Dict[str, Any]:
    """
    Calculate C:N:P molar ratios and identify limiting nutrients.

    Calculates total molar concentrations of C, N, and P from all ingredients
    and compares to the Redfield ratio (106:16:1) and other thresholds.

    Limiting nutrient determination:
    - P-limited: C:P > 106 AND N:P > 16
    - N-limited: C:N > 6.6 AND N:P < 16
    - C-limited: C:N < 6.6
    - Balanced: Near Redfield ratio

    Args:
        ingredients: List of ingredient dictionaries with keys:
            - name: Compound name
            - concentration: Molar concentration (mM)
            - formula: Chemical formula [optional]

    Returns:
        Dictionary with keys:
            - c_mol: Total carbon (mM)
            - n_mol: Total nitrogen (mM)
            - p_mol: Total phosphorus (mM)
            - c_n_ratio: C:N molar ratio
            - c_p_ratio: C:P molar ratio
            - n_p_ratio: N:P molar ratio
            - limiting_nutrient: "C", "N", "P", "balanced", or "all"
            - redfield_deviation: % deviation from Redfield ratio
            - confidence: Confidence score (0.0 to 1.0)

    Raises:
        ValueError: If negative concentrations provided

    Examples:
        >>> ingredients = [
        ...     {"name": "glucose", "concentration": 10.0, "formula": "C6H12O6"},
        ...     {"name": "NH4Cl", "concentration": 5.0, "formula": "NH4Cl"},
        ...     {"name": "KH2PO4", "concentration": 1.0, "formula": "KH2PO4"}
        ... ]
        >>> result = calculate_cnp_ratios(ingredients)  # doctest: +SKIP
        >>> result["c_mol"] > 0
        True
    """
    # Validate inputs
    for ing in ingredients:
        conc = ing.get("concentration", 0)
        if conc < 0:
            raise ValueError(f"Negative concentration for {ing.get('name', 'unknown')}: {conc}")

    # Accumulate elemental molar concentrations
    c_mol = 0.0
    n_mol = 0.0
    p_mol = 0.0

    for ing in ingredients:
        formula = ing.get("formula", "")
        concentration = ing.get("concentration", 0.0)  # mM

        if not formula or concentration == 0:
            continue

        # Parse elemental composition
        composition = parse_elemental_composition(formula)

        # Add to totals
        c_mol += composition.get("C", 0) * concentration
        n_mol += composition.get("N", 0) * concentration
        p_mol += composition.get("P", 0) * concentration

    # Calculate ratios
    c_n_ratio = c_mol / n_mol if n_mol > 0 else float('inf')
    c_p_ratio = c_mol / p_mol if p_mol > 0 else float('inf')
    n_p_ratio = n_mol / p_mol if p_mol > 0 else float('inf')

    # Determine limiting nutrient
    if c_mol == 0 and n_mol == 0 and p_mol == 0:
        limiting_nutrient = "all"
    elif c_n_ratio < 6.6:
        # C:N below threshold → C-limited
        limiting_nutrient = "C"
    elif c_p_ratio > 150 or n_p_ratio > 20:
        # High C:P or high N:P → P-limited
        # Check P first because P-limited conditions also show high C:N
        limiting_nutrient = "P"
    elif c_n_ratio > 20 or n_p_ratio < 10:
        # High C:N or low N:P → N-limited
        limiting_nutrient = "N"
    else:
        # Near balanced
        limiting_nutrient = "balanced"

    # Calculate Redfield deviation
    # Compare actual N:P and C:P ratios to Redfield
    if p_mol > 0:
        actual_c_p = c_p_ratio
        actual_n_p = n_p_ratio
        redfield_c_p = REDFIELD_RATIO["C"] / REDFIELD_RATIO["P"]
        redfield_n_p = REDFIELD_RATIO["N"] / REDFIELD_RATIO["P"]

        # Average percent deviation
        dev_c_p = abs(actual_c_p - redfield_c_p) / redfield_c_p * 100 if redfield_c_p > 0 else 0
        dev_n_p = abs(actual_n_p - redfield_n_p) / redfield_n_p * 100 if redfield_n_p > 0 else 0
        redfield_deviation = (dev_c_p + dev_n_p) / 2
    else:
        redfield_deviation = 100.0  # Max deviation if no P

    # Confidence score
    # High confidence if formulas provided and parsed successfully
    confidence = 0.8 if all(ing.get("formula") for ing in ingredients) else 0.5

    return {
        "c_mol": c_mol,
        "n_mol": n_mol,
        "p_mol": p_mol,
        "c_n_ratio": c_n_ratio,
        "c_p_ratio": c_p_ratio,
        "n_p_ratio": n_p_ratio,
        "limiting_nutrient": limiting_nutrient,
        "redfield_deviation": redfield_deviation,
        "confidence": confidence
    }


def calculate_trace_metal_ratios(
    ingredients: List[Dict]
) -> Dict[str, Any]:
    """
    Calculate trace metal ratios relative to phosphorus.

    Trace metals (Fe, Mn, Zn, Cu, Co, Mo) are essential micronutrients for
    microbial growth. Their requirements are typically expressed relative
    to phosphorus concentration.

    Args:
        ingredients: List of ingredient dictionaries with keys:
            - name: Compound name
            - concentration: Molar concentration (mM)
            - formula: Chemical formula [optional]

    Returns:
        Dictionary with keys:
            - fe_p_ratio: Fe:P molar ratio
            - mn_p_ratio: Mn:P molar ratio
            - zn_p_ratio: Zn:P molar ratio
            - cu_p_ratio: Cu:P molar ratio
            - co_p_ratio: Co:P molar ratio
            - mo_p_ratio: Mo:P molar ratio
            - deficiencies: List of deficient metals
            - excesses: List of excess metals
            - confidence: Confidence score

    Examples:
        >>> ingredients = [
        ...     {"name": "FeSO4", "concentration": 0.02, "formula": "FeSO4"},
        ...     {"name": "KH2PO4", "concentration": 1.0, "formula": "KH2PO4"}
        ... ]
        >>> result = calculate_trace_metal_ratios(ingredients)  # doctest: +SKIP
        >>> 0.01 <= result["fe_p_ratio"] <= 0.03
        True
    """
    # Parse elemental concentrations
    elements = {}

    for ing in ingredients:
        formula = ing.get("formula", "")
        concentration = ing.get("concentration", 0.0)  # mM

        if not formula or concentration == 0:
            continue

        composition = parse_elemental_composition(formula)

        for elem, count in composition.items():
            elements[elem] = elements.get(elem, 0.0) + count * concentration

    # Extract metals and phosphorus
    fe = elements.get("Fe", 0.0)
    mn = elements.get("Mn", 0.0)
    zn = elements.get("Zn", 0.0)
    cu = elements.get("Cu", 0.0)
    co = elements.get("Co", 0.0)
    mo = elements.get("Mo", 0.0)
    p = elements.get("P", 0.0)

    # Calculate ratios
    if p > 0:
        fe_p_ratio = fe / p
        mn_p_ratio = mn / p
        zn_p_ratio = zn / p
        cu_p_ratio = cu / p
        co_p_ratio = co / p
        mo_p_ratio = mo / p
    else:
        # No phosphorus - ratios undefined
        fe_p_ratio = None
        mn_p_ratio = None
        zn_p_ratio = None
        cu_p_ratio = None
        co_p_ratio = None
        mo_p_ratio = None

    # Identify deficiencies and excesses
    deficiencies = []
    excesses = []

    metals = {
        "Fe": fe_p_ratio,
        "Mn": mn_p_ratio,
        "Zn": zn_p_ratio,
        "Cu": cu_p_ratio,
        "Co": co_p_ratio,
        "Mo": mo_p_ratio
    }

    for metal, ratio in metals.items():
        if ratio is None:
            continue

        req = TRACE_METAL_REQUIREMENTS.get(metal, {})
        min_req = req.get("min", 0)
        max_req = req.get("max", float('inf'))

        if ratio < min_req:
            deficiencies.append(metal)
        elif ratio > max_req:
            excesses.append(metal)

    # Confidence
    confidence = 0.8 if p > 0 else 0.3

    return {
        "fe_p_ratio": fe_p_ratio if fe_p_ratio is not None else 0.0,
        "mn_p_ratio": mn_p_ratio if mn_p_ratio is not None else 0.0,
        "zn_p_ratio": zn_p_ratio if zn_p_ratio is not None else 0.0,
        "cu_p_ratio": cu_p_ratio if cu_p_ratio is not None else 0.0,
        "co_p_ratio": co_p_ratio if co_p_ratio is not None else 0.0,
        "mo_p_ratio": mo_p_ratio if mo_p_ratio is not None else 0.0,
        "deficiencies": deficiencies,
        "excesses": excesses,
        "confidence": confidence
    }

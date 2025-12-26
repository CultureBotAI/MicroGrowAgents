"""
Osmotic property calculations for microbial growth media.

This module provides functions to calculate osmotic properties of chemical mixtures,
including osmolarity, osmolality, water activity, and van't Hoff dissociation factors.
These properties are critical for understanding osmoregulation, halotolerance, and
microbial survival in different salinity conditions.

Key functions:
    - calculate_osmolarity: Calculate osmotic concentration (mOsm/L)
    - calculate_water_activity: Calculate water activity (aw)
    - estimate_van_hoff_factor: Estimate dissociation factor for compounds

Examples:
    >>> # Calculate osmolarity of simple NaCl solution
    >>> ingredients = [{
    ...     "name": "NaCl",
    ...     "concentration": 150.0,  # mM
    ...     "molecular_weight": 58.44,
    ...     "formula": "NaCl",
    ...     "charge": 0,
    ...     "grams_per_liter": 8.77
    ... }]
    >>> result = calculate_osmolarity(ingredients, temperature=25.0)
    >>> 280 <= result["osmolarity"] <= 290
    True
    >>> result["confidence"] >= 0.9
    True
"""

from typing import Dict, List, Optional, Tuple
import math
import re


# Van't Hoff factor database (experimental values at 25°C, typical concentrations)
# Format: {formula: (factor, confidence)}
VAN_HOFF_DATABASE = {
    # Strong 1:1 electrolytes (incomplete dissociation due to ion pairing)
    "NaCl": (1.9, 1.0),
    "KCl": (1.9, 1.0),
    "LiCl": (1.9, 1.0),
    "NaBr": (1.9, 1.0),
    "KBr": (1.9, 1.0),
    "NH4Cl": (1.9, 1.0),

    # Strong 1:2 and 2:1 electrolytes
    "CaCl2": (2.7, 1.0),
    "MgCl2": (2.7, 1.0),
    "BaCl2": (2.7, 1.0),
    "Na2SO4": (2.7, 1.0),
    "K2SO4": (2.7, 1.0),

    # Strong 2:2 electrolytes (significant ion pairing)
    "MgSO4": (1.3, 1.0),
    "CaSO4": (1.3, 1.0),
    "ZnSO4": (1.3, 1.0),

    # Weak electrolytes and buffers
    "NaH2PO4": (1.8, 0.9),
    "Na2HPO4": (2.5, 0.9),
    "K2HPO4": (2.5, 0.9),
    "KH2PO4": (1.8, 0.9),

    # Non-dissociating compounds
    "C6H12O6": (1.0, 1.0),  # glucose
    "C12H22O11": (1.0, 1.0),  # sucrose
    "C2H6O2": (1.0, 1.0),  # ethylene glycol
    "C3H8O3": (1.0, 1.0),  # glycerol
    "C6H8O7": (1.0, 1.0),  # citric acid (non-ionized form)

    # Common buffers (pH-dependent, typical values at pH 7)
    "C8H18N2O4S": (1.0, 0.9),  # HEPES (zwitterionic)
    "C8H18N2O6S2": (1.0, 0.9),  # PIPES (zwitterionic)
    "C4H11NO3S": (1.0, 0.9),  # TES (zwitterionic)
    "C6H13NO4S": (1.0, 0.9),  # MES (zwitterionic)
    "C8H20N2O4S": (1.0, 0.9),  # MOPS (zwitterionic)
}


def estimate_van_hoff_factor(
    formula: Optional[str] = None,
    charge: int = 0,
    name: Optional[str] = None,
    smiles: Optional[str] = None
) -> Tuple[float, float]:
    """
    Estimate van't Hoff dissociation factor for a compound.

    The van't Hoff factor (i) represents the number of particles a compound
    dissociates into in solution. For strong electrolytes, i approaches the
    theoretical ion count but is reduced by ion pairing effects.

    Estimation hierarchy:
    1. Database lookup (experimental values)
    2. Formula-based estimation (ion counting)
    3. Charge-based estimation
    4. Fallback to 1.0

    Args:
        formula: Chemical formula (e.g., "NaCl", "CaCl2")
        charge: Net charge of the compound
        name: Common name (for database lookup)
        smiles: SMILES string (for future estimation methods)

    Returns:
        Tuple of (van_hoff_factor, confidence)
        - van_hoff_factor: Estimated i value (typically 1.0 to 3.0)
        - confidence: Confidence score (0.0 to 1.0)

    Examples:
        >>> estimate_van_hoff_factor(formula="NaCl", charge=0, name="sodium chloride")
        (1.9, 1.0)

        >>> estimate_van_hoff_factor(formula="C6H12O6", charge=0, name="glucose")
        (1.0, 1.0)

        >>> estimate_van_hoff_factor(formula="CaCl2", charge=0, name="calcium chloride")
        (2.7, 1.0)
    """
    # 1. Database lookup by formula
    if formula and formula in VAN_HOFF_DATABASE:
        return VAN_HOFF_DATABASE[formula]

    # 2. Database lookup by name (case-insensitive partial match)
    if name:
        name_lower = name.lower()
        for db_formula, (factor, conf) in VAN_HOFF_DATABASE.items():
            # Check if name contains key terms
            if "nacl" in name_lower or "sodium chloride" in name_lower:
                if db_formula == "NaCl":
                    return (factor, conf)
            elif "cacl2" in name_lower or "calcium chloride" in name_lower:
                if db_formula == "CaCl2":
                    return (factor, conf)
            elif "mgso4" in name_lower or "magnesium sulfate" in name_lower:
                if db_formula == "MgSO4":
                    return (factor, conf)
            elif "glucose" in name_lower:
                if db_formula == "C6H12O6":
                    return (factor, conf)

    # 3. Formula-based estimation (ion counting with ion pairing correction)
    if formula:
        ion_count = _estimate_ion_count_from_formula(formula)
        if ion_count > 1:
            # Apply ion pairing correction (empirical)
            # Strong 1:1 electrolytes: i ≈ 1.9 (not 2.0)
            # Strong 1:2 electrolytes: i ≈ 2.7 (not 3.0)
            # Strong 2:2 electrolytes: i ≈ 1.3 (significant pairing)
            if ion_count == 2:
                return (1.9, 0.7)
            elif ion_count == 3:
                return (2.7, 0.7)
            else:
                # For higher ion counts, use conservative estimate
                return (float(ion_count) * 0.85, 0.6)

    # 4. Charge-based estimation
    if charge != 0:
        # Charged species likely dissociate
        return (2.0, 0.5)

    # 5. Fallback: assume non-dissociating
    return (1.0, 0.5)


def _estimate_ion_count_from_formula(formula: str) -> int:
    """
    Estimate the number of ions from a chemical formula.

    Uses simple heuristics:
    - Alkali metals (Na, K, Li) + halides/anions → 2 ions
    - Alkaline earth (Ca, Mg, Ba) + halides → 3 ions
    - Sulfates/phosphates with divalent cations → check stoichiometry

    Args:
        formula: Chemical formula string

    Returns:
        Estimated number of ions (1 for non-electrolytes)

    Examples:
        >>> _estimate_ion_count_from_formula("NaCl")
        2
        >>> _estimate_ion_count_from_formula("CaCl2")
        3
        >>> _estimate_ion_count_from_formula("C6H12O6")
        1
    """
    # Remove numbers and count unique metal/halide elements
    formula_clean = re.sub(r'\d+', '', formula)

    # Alkali metals (1+ charge)
    alkali = ["Na", "K", "Li", "Rb", "Cs"]
    # Alkaline earth metals (2+ charge)
    alkaline_earth = ["Ca", "Mg", "Ba", "Sr"]
    # Halides and common anions
    anions = ["Cl", "Br", "I", "F"]
    # Polyatomic anions
    polyatomic = ["SO4", "PO4", "NO3", "CO3"]

    # Check for alkali metal salts (1:1 typically)
    for metal in alkali:
        if metal in formula:
            # Check for anions
            for anion in anions:
                if anion in formula:
                    return 2  # M+ + X- = 2 ions
            for poly in polyatomic:
                if poly in formula:
                    # Na2SO4 → 3 ions, NaNO3 → 2 ions
                    # Count metal atoms
                    match = re.search(rf"{metal}(\d*)", formula)
                    if match:
                        count = int(match.group(1)) if match.group(1) else 1
                        return count + 1
            return 2  # default for alkali salt

    # Check for alkaline earth salts (1:2 typically)
    for metal in alkaline_earth:
        if metal in formula:
            # MgCl2 → 3 ions, MgSO4 → 2 ions (but high pairing, effective ~1.3)
            for anion in anions:
                if anion in formula:
                    return 3  # M2+ + 2X- = 3 ions
            for poly in polyatomic:
                if poly in formula:
                    return 2  # M2+ + SO4(2-) = 2 ions (nominal)
            return 2

    # Ammonium salts
    if "NH4" in formula:
        return 2

    # Default: non-electrolyte
    return 1


def calculate_osmolarity(
    ingredients: List[Dict],
    temperature: float = 25.0
) -> Dict:
    """
    Calculate osmolarity (mOsm/L) and osmolality (mOsm/kg) of a solution.

    Osmolarity represents the osmotic pressure of a solution and is calculated
    as the sum of molar concentrations weighted by van't Hoff factors:

        Osmolarity (mOsm/L) = Σ(concentration_i × van_hoff_factor_i)

    Osmolality accounts for solution density and is more accurate for
    concentrated solutions:

        Osmolality (mOsm/kg) = Osmolarity / solution_density

    Args:
        ingredients: List of ingredient dictionaries with keys:
            - name: Compound name
            - concentration: Molar concentration (mM)
            - formula: Chemical formula (optional)
            - charge: Net charge (optional)
            - molecular_weight: MW in g/mol (optional)
            - grams_per_liter: Mass concentration (optional)
        temperature: Temperature in °C (default 25.0)

    Returns:
        Dictionary with keys:
            - osmolarity: Total osmolarity (mOsm/L)
            - osmolality: Total osmolality (mOsm/kg)
            - van_hoff_factors: Dict mapping ingredient names to factors
            - confidence: Overall confidence score (0.0 to 1.0)
            - warnings: List of warning messages

    Examples:
        >>> ingredients = [{
        ...     "name": "NaCl",
        ...     "concentration": 150.0,
        ...     "molecular_weight": 58.44,
        ...     "formula": "NaCl",
        ...     "charge": 0,
        ...     "grams_per_liter": 8.77
        ... }]
        >>> result = calculate_osmolarity(ingredients, temperature=25.0)
        >>> 280 <= result["osmolarity"] <= 290
        True
    """
    if not ingredients:
        return {
            "osmolarity": 0.0,
            "osmolality": 0.0,
            "van_hoff_factors": {},
            "confidence": 1.0,
            "warnings": []
        }

    total_osmolarity = 0.0
    van_hoff_factors = {}
    confidences = []
    warnings = []
    total_mass = 0.0  # g/L for density estimation

    for ingredient in ingredients:
        name = ingredient.get("name", "unknown")
        concentration = ingredient.get("concentration", 0.0)  # mM
        formula = ingredient.get("formula")
        charge = ingredient.get("charge", 0)
        grams_per_liter = ingredient.get("grams_per_liter", 0.0)

        if concentration == 0.0:
            van_hoff_factors[name] = 1.0
            continue

        # Estimate van't Hoff factor
        factor, confidence = estimate_van_hoff_factor(
            formula=formula,
            charge=charge,
            name=name
        )

        # Calculate contribution to osmolarity
        osmolarity_contribution = concentration * factor
        total_osmolarity += osmolarity_contribution

        # Track
        van_hoff_factors[name] = factor
        confidences.append(confidence)
        total_mass += grams_per_liter

        # Warnings for low confidence
        if confidence < 0.7:
            warnings.append(
                f"Low confidence ({confidence:.2f}) for van't Hoff factor "
                f"of {name} (estimated as {factor:.2f})"
            )

    # Calculate overall confidence (geometric mean)
    if confidences:
        overall_confidence = math.exp(sum(math.log(c) for c in confidences) / len(confidences))
    else:
        overall_confidence = 1.0

    # Estimate solution density for osmolality
    # Approximation: density (g/mL) ≈ 1.0 + 0.0008 × total_mass (g/L)
    # This accounts for dissolved solids; coefficient slightly higher for electrolytes
    density_g_ml = 1.0 + 0.0008 * total_mass
    density_kg_L = density_g_ml  # 1 g/mL = 1 kg/L

    osmolality = total_osmolarity / density_kg_L

    return {
        "osmolarity": total_osmolarity,
        "osmolality": osmolality,
        "van_hoff_factors": van_hoff_factors,
        "confidence": overall_confidence,
        "warnings": warnings
    }


def calculate_water_activity(
    ingredients: List[Dict],
    temperature: float = 25.0,
    method: str = "raoult"
) -> Dict:
    """
    Calculate water activity (aw) of a solution.

    Water activity represents the availability of water for microbial growth
    and chemical reactions. It's defined as the ratio of vapor pressure of
    water in the solution to pure water:

        aw = P_solution / P_pure_water

    Methods:
        - "raoult": Raoult's law (ideal, best for dilute solutions)
            aw ≈ 1 - (osmolality / 55.5)
            where 55.5 is the molality of pure water (mol/kg)

        - "robinson_stokes": Robinson-Stokes equation (concentrated solutions)
            ln(aw) = -ν × m × φ × (M_water / 1000)
            where ν is ion count, m is molality, φ is osmotic coefficient

        - "bromley": Bromley equation (ionic solutions)
            Accounts for specific ion interactions

    Growth categories based on water activity:
        - aw > 0.98: Most bacteria, fungi
        - aw 0.93-0.98: Halotolerant bacteria
        - aw 0.90-0.93: Halophilic bacteria
        - aw 0.75-0.90: Xerophilic fungi, extreme halophiles
        - aw < 0.75: Limited microbial growth

    Args:
        ingredients: List of ingredient dictionaries (see calculate_osmolarity)
        temperature: Temperature in °C (default 25.0)
        method: Calculation method - "raoult", "robinson_stokes", or "bromley"

    Returns:
        Dictionary with keys:
            - water_activity: Calculated aw (0.0 to 1.0)
            - method: Method used
            - growth_category: Microbial growth category
            - osmolality: Solution osmolality (mOsm/kg)
            - confidence: Confidence score (0.0 to 1.0)
            - warnings: List of warning messages

    Examples:
        >>> ingredients = [{
        ...     "name": "NaCl",
        ...     "concentration": 100.0,
        ...     "molecular_weight": 58.44,
        ...     "formula": "NaCl",
        ...     "charge": 0,
        ...     "grams_per_liter": 5.84
        ... }]
        >>> result = calculate_water_activity(ingredients, temperature=25.0)
        >>> 0.995 <= result["water_activity"] <= 0.999
        True
        >>> result["growth_category"]
        'most_bacteria'
    """
    # Calculate osmolarity first
    osm_result = calculate_osmolarity(ingredients, temperature)
    osmolality = osm_result["osmolality"]  # mOsm/kg
    confidence = osm_result["confidence"]
    warnings = osm_result["warnings"].copy()

    # Pure water case
    if osmolality == 0.0:
        return {
            "water_activity": 1.0,
            "method": method,
            "growth_category": "most_bacteria",
            "osmolality": 0.0,
            "confidence": 1.0,
            "warnings": []
        }

    # Calculate water activity
    if method == "raoult":
        # Raoult's law: aw = 1 - (osmolality / 55.5)
        # 55.5 mol/kg is the molality of pure water
        molality = osmolality / 1000.0

        # For moderate to high concentrations, apply small activity correction
        # to account for non-ideal behavior
        if molality > 0.5:
            # Empirical correction factor for electrolytes (non-ideal behavior)
            correction = 1.0 + 0.095 * (molality - 0.5)
            aw = 1.0 - (molality * correction) / 55.5
        else:
            aw = 1.0 - molality / 55.5

        # Adjust confidence for concentrated solutions
        if osmolality > 500.0:  # > 0.5 Osm/kg
            confidence *= 0.8
            warnings.append(
                f"Raoult's law may be inaccurate for concentrated solutions "
                f"(osmolality = {osmolality:.1f} mOsm/kg). "
                f"Consider method='robinson_stokes'."
            )

    elif method == "robinson_stokes":
        # Robinson-Stokes with osmotic coefficient
        # ln(aw) = -(osmolality × φ) / 55.5
        # where 55.5 mol/kg is the molality of pure water

        # Estimate osmotic coefficient (empirical for NaCl-like solutions)
        molality = osmolality / 1000.0  # Convert to Osm/kg
        osmotic_coefficient = _estimate_osmotic_coefficient(molality)

        # 55.5 mol/kg is the molality of water
        ln_aw = -(molality * osmotic_coefficient) / 55.5
        aw = math.exp(ln_aw)

        # This method is better for concentrated solutions
        if osmolality < 200.0:
            confidence *= 0.9
            warnings.append(
                f"Robinson-Stokes method is designed for concentrated solutions. "
                f"Consider method='raoult' for dilute solutions."
            )

    elif method == "bromley":
        # Bromley equation (more complex, ionic-specific)
        # For now, use Robinson-Stokes as approximation
        warnings.append(
            "Bromley method not fully implemented, using Robinson-Stokes approximation."
        )
        molality = osmolality / 1000.0
        osmotic_coefficient = _estimate_osmotic_coefficient(molality)
        ln_aw = -(molality * osmotic_coefficient) / 55.5
        aw = math.exp(ln_aw)

    else:
        raise ValueError(f"Unknown method: {method}. Use 'raoult', 'robinson_stokes', or 'bromley'.")

    # Clamp to valid range
    aw = max(0.0, min(1.0, aw))

    # Determine growth category
    growth_category = _classify_growth_category(aw)

    # Temperature adjustment confidence
    if temperature < 0 or temperature > 50:
        confidence *= 0.7
        warnings.append(
            f"Water activity calculations are less accurate at extreme temperatures "
            f"({temperature}°C). Standard temperature is 25°C."
        )

    return {
        "water_activity": aw,
        "method": method,
        "growth_category": growth_category,
        "osmolality": osmolality,
        "confidence": confidence,
        "warnings": warnings
    }


def _estimate_osmotic_coefficient(molality: float) -> float:
    """
    Estimate osmotic coefficient for aqueous solutions.

    Uses empirical correlation for NaCl-like electrolytes based on
    experimental data. The osmotic coefficient increases with concentration
    due to ion-ion interactions.

    Experimental reference values for NaCl:
    - 0.1 m: φ ≈ 0.93
    - 0.5 m: φ ≈ 0.93
    - 1.0 m: φ ≈ 0.94
    - 2.0 m: φ ≈ 0.97
    - 4.0 m: φ ≈ 1.05

    Args:
        molality: Solution molality (Osm/kg or mol/kg)

    Returns:
        Estimated osmotic coefficient (typically 0.9 to 1.3)
    """
    # Empirical fit to NaCl osmotic coefficient data
    # φ = a + b × sqrt(m) + c × m

    if molality < 0.01:
        # Very dilute: ideal behavior
        phi = 1.0
    elif molality < 3.0:
        # Moderate to concentrated: fitted polynomial
        # This gives φ ≈ 0.93 at 0.1-1 m, rising to ~1.0 at 3 m
        phi = 0.90 + 0.02 * math.sqrt(molality) + 0.03 * molality
    else:
        # Very concentrated: coefficient increases more rapidly
        phi = 0.85 + 0.05 * math.sqrt(molality) + 0.05 * molality

    return max(0.85, min(1.5, phi))


def _classify_growth_category(aw: float) -> str:
    """
    Classify microbial growth category based on water activity.

    Args:
        aw: Water activity (0.0 to 1.0)

    Returns:
        Growth category string

    Examples:
        >>> _classify_growth_category(0.99)
        'most_bacteria'
        >>> _classify_growth_category(0.95)
        'halotolerant'
        >>> _classify_growth_category(0.85)
        'halophiles'
    """
    if aw > 0.98:
        return "most_bacteria"
    elif aw > 0.93:
        return "halotolerant"
    elif aw > 0.75:
        return "halophiles"
    else:
        return "extreme_halophiles"

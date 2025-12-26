"""
Redox property calculations for microbial growth media.

This module provides functions to calculate redox potential (Eh), electron
balance, and pE for chemical mixtures. These properties are critical for
understanding anaerobic growth, electron transport chains, and metabolic
energy generation.

Key functions:
    - calculate_redox_potential: Calculate Eh and pE using Nernst equation
    - calculate_electron_balance: Calculate electron donor/acceptor balance

Examples:
    >>> ingredients = [{
    ...     "name": "O2",
    ...     "concentration": 8.0,
    ...     "redox_couple": "O2/H2O"
    ... }]
    >>> result = calculate_redox_potential(ingredients, ph=7.0)  # doctest: +SKIP
    >>> result["eh"] > 200  # Aerobic conditions
    True
"""

from typing import Dict, List, Optional, Any
import math


# Physical constants
GAS_CONSTANT = 8.314  # J/(mol·K)
FARADAY_CONSTANT = 96485  # C/mol

# Standard redox potentials (E0' at pH 7, 25°C)
# Format: {couple: {e0: mV, n_electrons: int, ph_dependent: bool}}
STANDARD_POTENTIALS = {
    # Aerobic respiration
    "O2/H2O": {
        "e0": 820,  # mV at pH 7
        "n_electrons": 4,
        "ph_dependent": True,
        "oxidized": "O2",
        "reduced": "H2O"
    },

    # Nitrate reduction
    "NO3-/NO2-": {
        "e0": 420,
        "n_electrons": 2,
        "ph_dependent": True,
        "oxidized": "NO3-",
        "reduced": "NO2-"
    },
    "NO2-/NO": {
        "e0": 350,
        "n_electrons": 1,
        "ph_dependent": True,
        "oxidized": "NO2-",
        "reduced": "NO"
    },
    "NO3-/N2": {
        "e0": 750,
        "n_electrons": 5,
        "ph_dependent": True,
        "oxidized": "NO3-",
        "reduced": "N2"
    },

    # Iron reduction/oxidation
    "Fe3+/Fe2+": {
        "e0": 770,
        "n_electrons": 1,
        "ph_dependent": False,
        "oxidized": "Fe3+",
        "reduced": "Fe2+"
    },

    # Sulfate reduction
    "SO42-/H2S": {
        "e0": -220,
        "n_electrons": 8,
        "ph_dependent": True,
        "oxidized": "SO42-",
        "reduced": "H2S"
    },
    "SO42-/S0": {
        "e0": -100,
        "n_electrons": 6,
        "ph_dependent": True,
        "oxidized": "SO42-",
        "reduced": "S0"
    },

    # Manganese reduction
    "MnO2/Mn2+": {
        "e0": 500,
        "n_electrons": 2,
        "ph_dependent": True,
        "oxidized": "MnO2",
        "reduced": "Mn2+"
    },

    # Hydrogen/proton
    "H+/H2": {
        "e0": -420,
        "n_electrons": 2,
        "ph_dependent": True,
        "oxidized": "H+",
        "reduced": "H2"
    },

    # Carbon dioxide reduction (methanogenesis)
    "CO2/CH4": {
        "e0": -240,
        "n_electrons": 8,
        "ph_dependent": True,
        "oxidized": "CO2",
        "reduced": "CH4"
    },

    # Fumarate reduction
    "Fumarate/Succinate": {
        "e0": 30,
        "n_electrons": 2,
        "ph_dependent": False,
        "oxidized": "Fumarate",
        "reduced": "Succinate"
    }
}

# Electron donor/acceptor classification
# Approximate electron equivalents per mole of compound
ELECTRON_EQUIVALENTS = {
    # Electron donors (reduced organic compounds)
    "glucose": 24,  # C6H12O6 → 6 CO2 + 24 H+ + 24 e-
    "C6H12O6": 24,
    "lactate": 12,  # C3H6O3 → 3 CO2 + 12 H+ + 12 e-
    "C3H6O3": 12,
    "acetate": 8,  # C2H4O2 → 2 CO2 + 8 H+ + 8 e-
    "C2H4O2": 8,
    "ethanol": 12,  # C2H6O → 2 CO2 + 12 H+ + 12 e-
    "C2H6O": 12,
    "pyruvate": 10,  # C3H4O3 → 3 CO2 + 10 H+ + 10 e-
    "C3H4O3": 10,
    "H2": 2,  # H2 → 2 H+ + 2 e-
    "Fe2+": 1,  # Fe2+ → Fe3+ + e-
    "NH4+": 8,  # NH4+ → NO3- + 8 H+ + 8 e-

    # Electron acceptors (oxidized compounds)
    "O2": 4,  # O2 + 4 H+ + 4 e- → 2 H2O
    "NO3-": 5,  # NO3- + 6 H+ + 5 e- → 0.5 N2 + 3 H2O
    "NO3": 5,
    "SO42-": 8,  # SO42- + 9 H+ + 8 e- → HS- + 4 H2O
    "SO4": 8,
    "Fe3+": 1,  # Fe3+ + e- → Fe2+
    "CO2": 8,  # CO2 + 8 H+ + 8 e- → CH4 + 2 H2O
}


def calculate_redox_potential(
    ingredients: List[Dict],
    ph: float = 7.0,
    temperature: float = 25.0
) -> Dict[str, Any]:
    """
    Calculate redox potential (Eh) and pE for a solution.

    Uses the Nernst equation:
        Eh = E0' + (59.16/n) × log([oxidized]/[reduced])  (at 25°C)

    For pH-dependent reactions:
        Eh = E0 - 59.16 × pH + (59.16/n) × log([oxidized]/[reduced])

    pE (electron activity) is calculated as:
        pE = Eh / 59.16  (at 25°C)

    Args:
        ingredients: List of ingredient dictionaries with keys:
            - name: Compound name
            - concentration: Molar concentration (mM)
            - redox_couple: Redox couple name (e.g., "O2/H2O") [optional]
        ph: pH value (default: 7.0)
        temperature: Temperature in °C (default: 25.0)

    Returns:
        Dictionary with keys:
            - eh: Redox potential in mV
            - pe: Electron activity (dimensionless)
            - redox_couples: List of identified redox couples
            - redox_state: "oxidizing", "reducing", or "intermediate"
            - confidence: Confidence score (0.0 to 1.0)
            - warnings: List of warning messages

    Examples:
        >>> ingredients = [{"name": "O2", "concentration": 8.0, "redox_couple": "O2/H2O"}]
        >>> result = calculate_redox_potential(ingredients, ph=7.0)  # doctest: +SKIP
        >>> result["eh"] > 200  # Aerobic
        True
        >>> result["redox_state"]
        'oxidizing'
    """
    warnings = []
    temp_kelvin = temperature + 273.15

    # Check for extreme conditions
    if ph < 0 or ph > 14:
        warnings.append(f"Extreme pH value ({ph}) - results may be inaccurate")
    if temperature < 0 or temperature > 80:
        warnings.append(f"Extreme temperature ({temperature}°C) - results may be inaccurate")

    # Validate concentrations
    for ing in ingredients:
        conc = ing.get("concentration", 0)
        if conc < 0:
            raise ValueError(f"Negative concentration for {ing.get('name', 'unknown')}: {conc}")

    # Calculate RT/F factor (mV) - varies with temperature
    # RT/F = (R × T) / F = (8.314 J/(mol·K) × T(K)) / 96485 C/mol
    # Convert to mV: multiply by 1000
    rt_over_f = (GAS_CONSTANT * temp_kelvin / FARADAY_CONSTANT) * 1000  # mV
    # At 25°C: RT/F ≈ 25.7 mV
    # Natural log to log10 conversion: 2.303 × RT/F ≈ 59.16 mV at 25°C
    nernst_factor = 2.303 * rt_over_f

    # Find redox couples in ingredients
    identified_couples = []
    eh_values = []

    for ing in ingredients:
        redox_couple = ing.get("redox_couple")
        if redox_couple and redox_couple in STANDARD_POTENTIALS:
            couple_data = STANDARD_POTENTIALS[redox_couple]
            e0 = couple_data["e0"]  # mV
            n_electrons = couple_data["n_electrons"]
            ph_dependent = couple_data["ph_dependent"]

            # Apply pH correction if pH-dependent
            if ph_dependent:
                # Eh = E0 - (59.16 mV / n) × pH (at 25°C, or nernst_factor/n at temp T)
                e0_corrected = e0 - (nernst_factor / n_electrons) * ph
            else:
                e0_corrected = e0

            # Nernst equation with concentration
            # Eh = E0' + (nernst_factor / n) × log([ox]/[red])
            # Simplified: assume concentration represents [ox], and [red] = 1 (or ratio)
            # For dissolved oxygen: [O2] is measurable, [H2O] is constant (55.5 M)
            conc_mM = ing.get("concentration", 1.0)
            conc_M = conc_mM / 1000.0

            # Avoid log(0)
            if conc_M <= 0:
                conc_M = 1e-9

            # Simplified Nernst: Eh = E0' + (nernst_factor / n) × log(conc)
            # This assumes [reduced] is in excess or constant
            eh_couple = e0_corrected + (nernst_factor / n_electrons) * math.log10(conc_M)

            eh_values.append(eh_couple)
            identified_couples.append({
                "couple": redox_couple,
                "eh": eh_couple,
                "e0": e0,
                "n_electrons": n_electrons
            })

    # Calculate overall Eh
    if eh_values:
        # Use weighted average or dominant couple
        eh = sum(eh_values) / len(eh_values)
        confidence = 0.9
    else:
        # No redox couples identified - use default estimate
        # Neutral Eh around 0 mV for undefined systems
        eh = 0.0
        confidence = 0.3
        warnings.append("No redox couples identified - using default estimate")

    # Calculate pE
    pe = eh / nernst_factor if nernst_factor > 0 else 0.0

    # Classify redox state
    if eh > 200:
        redox_state = "oxidizing"
    elif eh < -100:
        redox_state = "reducing"
    else:
        redox_state = "intermediate"

    # Adjust confidence based on warnings
    if warnings:
        confidence *= 0.8

    return {
        "eh": eh,
        "pe": pe,
        "redox_couples": identified_couples,
        "redox_state": redox_state,
        "confidence": confidence,
        "warnings": warnings
    }


def calculate_electron_balance(
    ingredients: List[Dict]
) -> Dict[str, Any]:
    """
    Calculate electron donor/acceptor balance for a solution.

    Determines the total electron-donating capacity (e- donors) and
    electron-accepting capacity (e- acceptors) based on ingredient
    composition and redox roles.

    Args:
        ingredients: List of ingredient dictionaries with keys:
            - name: Compound name
            - concentration: Molar concentration (mM)
            - formula: Chemical formula [optional]
            - role: "electron_donor" or "electron_acceptor" [optional]

    Returns:
        Dictionary with keys:
            - total_donors: Total electron-donating capacity (meq/L)
            - total_acceptors: Total electron-accepting capacity (meq/L)
            - balance: (donors - acceptors) / donors × 100 (%)
            - donor_list: List of electron donors with details
            - acceptor_list: List of electron acceptors with details

    Examples:
        >>> ingredients = [
        ...     {"name": "glucose", "concentration": 10.0, "formula": "C6H12O6", "role": "electron_donor"},
        ...     {"name": "O2", "concentration": 60.0, "formula": "O2", "role": "electron_acceptor"}
        ... ]
        >>> result = calculate_electron_balance(ingredients)  # doctest: +SKIP
        >>> result["total_donors"] > 0
        True
        >>> result["total_acceptors"] > 0
        True
    """
    total_donors = 0.0
    total_acceptors = 0.0
    donor_list = []
    acceptor_list = []

    for ing in ingredients:
        name = ing.get("name", "").lower()
        formula = ing.get("formula", "").upper()
        concentration = ing.get("concentration", 0.0)  # mM
        role = ing.get("role", "")

        # Determine electron equivalents
        electrons = 0
        for key in [name, formula]:
            if key in ELECTRON_EQUIVALENTS:
                electrons = ELECTRON_EQUIVALENTS[key]
                break

        if electrons == 0:
            # Try to infer from formula or role
            if role == "electron_donor":
                electrons = 4  # Default estimate
            elif role == "electron_acceptor":
                electrons = 2  # Default estimate

        # Calculate electron capacity (meq/L = mM × electrons)
        electron_capacity = concentration * electrons

        # Classify as donor or acceptor
        if role == "electron_donor" or (electrons > 0 and name in ELECTRON_EQUIVALENTS and electrons >= 8):
            total_donors += electron_capacity
            donor_list.append({
                "name": ing["name"],
                "concentration": concentration,
                "electrons": electrons,
                "capacity": electron_capacity
            })
        elif role == "electron_acceptor" or name in ["o2", "no3-", "no3", "so42-", "so4", "fe3+", "co2"]:
            total_acceptors += electron_capacity
            acceptor_list.append({
                "name": ing["name"],
                "concentration": concentration,
                "electrons": electrons,
                "capacity": electron_capacity
            })

    # Calculate balance as percentage deviation
    if total_donors > 0:
        balance = ((total_donors - total_acceptors) / total_donors) * 100
    else:
        balance = 0.0

    return {
        "total_donors": total_donors,
        "total_acceptors": total_acceptors,
        "balance": balance,
        "donor_list": donor_list,
        "acceptor_list": acceptor_list
    }

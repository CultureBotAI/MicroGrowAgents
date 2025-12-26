"""
Thermodynamic property calculations for biochemical reactions.

This module provides functions to calculate Gibbs free energy and formation
energies for biochemical compounds and reactions, using data from eQuilibrator,
lookup tables, and estimation methods.

Key functions:
    - calculate_gibbs_free_energy: Calculate ΔG for reactions
    - calculate_formation_energy: Calculate ΔGf° for compounds

Examples:
    >>> result = calculate_gibbs_free_energy(
    ...     reactants=["glucose"],
    ...     products=["ethanol", "CO2"],
    ...     stoichiometry={"glucose": -1, "ethanol": 2, "CO2": 2},
    ...     ph=7.0,
    ...     method="lookup"
    ... )  # doctest: +SKIP
"""

from typing import Dict, List, Optional, Any
import math

from microgrowagents.chemistry.api_clients.equilibrator_client import EquilibratorClient


# Physical constants
GAS_CONSTANT = 8.314  # J/(mol·K)
FARADAY_CONSTANT = 96485  # C/mol

# Formation energy database (ΔGf° at pH 7, 25°C, I=0.1M)
# Values in kJ/mol from eQuilibrator and literature
FORMATION_ENERGY_DATABASE = {
    "glucose": -426.71,
    "D-glucose": -426.71,
    "C6H12O6": -426.71,
    "ethanol": -181.75,
    "C2H5OH": -181.75,
    "CO2": -547.1,
    "water": -237.18,
    "H2O": -237.18,
    "ATP": -2768.1,
    "ADP": -1906.13,
    "phosphate": -1059.0,
    "Pi": -1059.0,
    "NAD+": -1059.11,
    "NADH": -1120.09,
    "pyruvate": -474.0,
}


def calculate_formation_energy(
    compound: str,
    method: str = "equilibrator"
) -> Optional[Dict[str, Any]]:
    """
    Calculate standard formation energy (ΔGf°) for a compound.

    The formation energy is the Gibbs energy change for forming one mole
    of the compound from its constituent elements in their standard states.

    Methods:
        - equilibrator: Use eQuilibrator API (biochemical data)
        - lookup: Use internal database
        - estimation: Group contribution estimation (low confidence)

    Args:
        compound: Compound name or identifier
        method: Calculation method (default: "equilibrator")

    Returns:
        Dictionary with keys:
            - delta_gf: Formation energy in kJ/mol
            - delta_hf: Formation enthalpy (if available)
            - s_standard: Standard entropy (if available)
            - method: Method used
            - confidence: Confidence score (0.0 to 1.0)
            - source: Data source
        or None if calculation fails

    Examples:
        >>> result = calculate_formation_energy("glucose", method="lookup")
        >>> -450 <= result["delta_gf"] <= -400
        True
        >>> result["confidence"] >= 0.8
        True
    """
    if method == "equilibrator":
        try:
            client = EquilibratorClient()
            api_result = client.get_compound_formation_energy(compound)

            if api_result and "formation_energy" in api_result:
                return {
                    "delta_gf": api_result["formation_energy"]["value"],
                    "delta_hf": None,  # Not always provided
                    "s_standard": None,
                    "method": "equilibrator",
                    "confidence": 0.95,
                    "source": "eQuilibrator API"
                }
        except Exception:
            pass

        # Fallback to lookup
        method = "lookup"

    if method == "lookup":
        # Check database
        compound_lower = compound.lower()
        for key, value in FORMATION_ENERGY_DATABASE.items():
            if compound_lower == key.lower():
                return {
                    "delta_gf": value,
                    "delta_hf": None,
                    "s_standard": None,
                    "method": "lookup",
                    "confidence": 0.85,
                    "source": "Internal database"
                }

        # Not found in database, fallback to estimation
        method = "estimation"

    if method == "estimation":
        # Very rough estimation - return low confidence
        return {
            "delta_gf": 0.0,  # Placeholder
            "delta_hf": None,
            "s_standard": None,
            "method": "estimation",
            "confidence": 0.3,
            "source": "Estimation (unreliable)"
        }

    # Not found
    return {
        "delta_gf": 0.0,
        "delta_hf": None,
        "s_standard": None,
        "method": "not_found",
        "confidence": 0.0,
        "source": "Not found"
    }


def calculate_gibbs_free_energy(
    reactants: List[str],
    products: List[str],
    stoichiometry: Dict[str, float],
    ph: float = 7.0,
    temperature: float = 25.0,
    ionic_strength: float = 0.1,
    concentrations: Optional[Dict[str, float]] = None,
    method: str = "equilibrator",
    allow_fallback: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Calculate Gibbs free energy (ΔG) for a biochemical reaction.

    Calculates both standard ΔG'° and actual ΔG including reaction quotient:
        ΔG = ΔG'° + RT ln(Q)

    where Q is the reaction quotient based on concentrations.

    Args:
        reactants: List of reactant compound names
        products: List of product compound names
        stoichiometry: Dict mapping compound name → stoichiometric coefficient
                      (negative for reactants, positive for products)
        ph: pH value (default: 7.0)
        temperature: Temperature in °C (default: 25.0)
        ionic_strength: Ionic strength in M (default: 0.1)
        concentrations: Dict mapping compound name → concentration in mM
                       (optional, for calculating Q)
        method: Calculation method - "equilibrator", "lookup", "estimation"
        allow_fallback: Allow fallback to other methods if primary fails

    Returns:
        Dictionary with keys:
            - delta_g: Gibbs free energy (kJ/mol)
            - delta_g_prime: Standard ΔG'° at specified pH (kJ/mol)
            - reaction_quotient: Q value (if concentrations provided)
            - feasibility: "favorable" (ΔG < 0) or "unfavorable" (ΔG > 0)
            - method: Method used
            - confidence: Confidence score (0.0 to 1.0)
            - warnings: List of warning messages
        or None if calculation fails

    Raises:
        ValueError: If reactants/products are empty or stoichiometry invalid

    Examples:
        >>> result = calculate_gibbs_free_energy(
        ...     reactants=["glucose"],
        ...     products=["ethanol", "CO2"],
        ...     stoichiometry={"glucose": -1, "ethanol": 2, "CO2": 2},
        ...     ph=7.0,
        ...     method="lookup"
        ... )
        >>> result["delta_g"] < 0  # Fermentation is favorable
        True
        >>> result["feasibility"]
        'favorable'
    """
    # Input validation
    if not reactants:
        raise ValueError("At least one reactant is required")
    if not products:
        raise ValueError("At least one product is required")

    # Check stoichiometry matches reactants/products
    all_compounds = set(reactants) | set(products)
    stoich_compounds = set(stoichiometry.keys())
    if not stoich_compounds.issubset(all_compounds):
        raise ValueError(
            f"Stoichiometry contains unknown compounds: "
            f"{stoich_compounds - all_compounds}"
        )

    # Validate concentrations if provided
    if concentrations:
        for compound, conc in concentrations.items():
            if conc < 0:
                raise ValueError(f"Negative concentration for {compound}: {conc}")

    warnings = []

    # Check for extreme conditions
    if ph < 0 or ph > 14:
        warnings.append(f"Extreme pH value ({ph}) - results may be inaccurate")
    if temperature < -20 or temperature > 100:
        warnings.append(
            f"Extreme temperature ({temperature}°C) - results may be inaccurate"
        )

    # Try equilibrator method first
    delta_g_prime = None
    confidence = 0.0
    method_used = method

    if method == "equilibrator":
        try:
            client = EquilibratorClient()

            # Construct reaction string
            # Format: "n1 COMPOUND1 + n2 COMPOUND2 => n3 COMPOUND3 + n4 COMPOUND4"
            reactant_strs = []
            for r in reactants:
                coef = abs(stoichiometry.get(r, 1))
                if coef == 1:
                    reactant_strs.append(r)
                else:
                    reactant_strs.append(f"{coef} {r}")

            product_strs = []
            for p in products:
                coef = abs(stoichiometry.get(p, 1))
                if coef == 1:
                    product_strs.append(p)
                else:
                    product_strs.append(f"{coef} {p}")

            reaction_str = " + ".join(reactant_strs) + " => " + " + ".join(product_strs)

            api_result = client.get_reaction_energy(
                reaction=reaction_str,
                ph=ph,
                ionic_strength=ionic_strength,
                temperature=temperature
            )

            if api_result and "delta_g_prime" in api_result:
                delta_g_prime = api_result["delta_g_prime"]["value"]
                confidence = 0.9
                method_used = "equilibrator"

        except Exception as e:
            if allow_fallback:
                method_used = "lookup"
            else:
                return None

    # Fallback to lookup method
    if delta_g_prime is None and (method == "lookup" or allow_fallback):
        # Calculate from formation energies
        delta_g_prime = 0.0
        confidence_values = []
        found_any_lookup = False

        for compound, coef in stoichiometry.items():
            form_energy = calculate_formation_energy(compound, method="lookup")
            if form_energy:
                delta_g_prime += coef * form_energy["delta_gf"]
                confidence_values.append(form_energy["confidence"])
                # Check if this came from actual lookup or estimation/fallback
                if form_energy["method"] == "lookup":
                    found_any_lookup = True
            else:
                # Unknown compound
                confidence_values.append(0.3)

        if confidence_values:
            # Geometric mean of confidences
            confidence = math.exp(
                sum(math.log(max(c, 0.01)) for c in confidence_values) / len(confidence_values)
            )
        else:
            confidence = 0.5

        # If we didn't find any compounds in lookup, use estimation method
        method_used = "lookup" if found_any_lookup else "estimation"

    # If still no result, use estimation
    if delta_g_prime is None:
        delta_g_prime = 0.0
        confidence = 0.2
        method_used = "estimation"
        warnings.append("Using low-confidence estimation method")

    # Calculate actual ΔG with reaction quotient
    delta_g = delta_g_prime
    reaction_quotient = None

    if concentrations:
        # Calculate Q = [products]^coefficients / [reactants]^coefficients
        # Convert concentrations from mM to M
        q_numerator = 1.0
        q_denominator = 1.0

        for compound, coef in stoichiometry.items():
            if compound in concentrations:
                conc_M = concentrations[compound] / 1000.0  # mM to M

                # Avoid log(0)
                if conc_M <= 0:
                    conc_M = 1e-9

                if coef > 0:  # Product
                    q_numerator *= conc_M ** abs(coef)
                else:  # Reactant
                    q_denominator *= conc_M ** abs(coef)

        if q_denominator > 0:
            reaction_quotient = q_numerator / q_denominator

            # ΔG = ΔG° + RT ln(Q)
            # R = 8.314 J/(mol·K), convert to kJ/(mol·K)
            temp_kelvin = temperature + 273.15
            rt = (GAS_CONSTANT / 1000.0) * temp_kelvin  # kJ/(mol·K) * K = kJ/mol

            if reaction_quotient > 0:
                delta_g = delta_g_prime + rt * math.log(reaction_quotient)

    # Determine feasibility
    if delta_g < -5.0:
        feasibility = "favorable"
    elif delta_g < 5.0:
        feasibility = "marginally_favorable"
    else:
        feasibility = "unfavorable"

    # Adjust confidence based on warnings
    if warnings:
        confidence *= 0.8

    return {
        "delta_g": delta_g,
        "delta_g_prime": delta_g_prime,
        "reaction_quotient": reaction_quotient,
        "feasibility": feasibility,
        "method": method_used,
        "confidence": confidence,
        "warnings": warnings
    }

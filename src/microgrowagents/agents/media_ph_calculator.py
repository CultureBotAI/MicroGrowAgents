"""Media pH calculator for predicting pH effects of ingredient concentrations.

This module provides functionality to calculate the pH of media formulations
based on ingredient concentrations, pKa values, and buffering capacity.
"""

import math
from typing import Dict, List, Optional, Tuple
import pandas as pd


class MediaPhCalculator:
    """
    Calculator for media pH based on ingredient compositions.

    Uses Henderson-Hasselbalch equation for weak acids/bases and
    accounts for strong acids/bases, metal salts, and buffer systems.
    """

    # pKa values for common buffer systems (at 25°C)
    PKA_VALUES = {
        # Buffers
        "PIPES": 6.76,
        "HEPES": 7.48,
        "MES": 6.15,
        "MOPS": 7.20,
        "Tris": 8.06,

        # Phosphates
        "H3PO4": [2.15, 7.20, 12.35],  # pKa1, pKa2, pKa3
        "phosphate": 7.20,  # Typical working pKa

        # Organic acids
        "citrate": [3.13, 4.76, 6.40],  # pKa1, pKa2, pKa3
        "acetate": 4.76,

        # Amino acids
        "glycine": [2.34, 9.60],

        # Vitamins
        "thiamin": 4.8,
        "biotin": 4.5,
    }

    # Acidic/basic character of metal salts
    SALT_PH_EFFECTS = {
        # Neutral salts
        "NaCl": 0.0,
        "KCl": 0.0,
        "NaH2PO4": -0.3,  # Slightly acidic
        "KH2PO4": -0.3,   # Slightly acidic
        "K2HPO4": 0.3,    # Slightly basic

        # Acidic salts (metal cations from weak bases)
        "NH4Cl": -0.5,
        "FeSO4": -0.5,
        "FeCl2": -0.5,
        "CuSO4": -0.4,
        "CuCl2": -0.4,
        "ZnSO4": -0.4,
        "ZnCl2": -0.4,
        "MnCl2": -0.3,
        "CoCl2": -0.3,
        "NiCl2": -0.3,
        "MgCl2": -0.2,
        "MgSO4": -0.2,
        "CaCl2": -0.1,
        "CaCl₂": -0.1,   # Unicode variation

        # Basic salts (anions from weak acids)
        "Na2WO4": 0.4,
        "Na2MoO4": 0.4,
        "Na2SeO3": 0.3,
    }

    def __init__(self):
        """Initialize pH calculator."""
        pass

    def calculate_ph(
        self,
        ingredients: List[Dict],
        volume_ml: float = 1000.0,
        temperature_c: float = 25.0,
    ) -> Tuple[float, Dict]:
        """
        Calculate pH of media formulation.

        Args:
            ingredients: List of ingredient dictionaries with:
                - name: Ingredient name
                - concentration: Concentration value
                - unit: Unit (mM, g/L, etc.)
                - pka: pKa value (optional)
            volume_ml: Total volume in mL
            temperature_c: Temperature in Celsius

        Returns:
            Tuple of (pH value, details dict with buffering info)

        Examples:
            >>> calc = MediaPhCalculator()
            >>> ingredients = [
            ...     {"name": "PIPES", "concentration": 30, "unit": "mM"},
            ...     {"name": "NaCl", "concentration": 100, "unit": "mM"}
            ... ]
            >>> ph, details = calc.calculate_ph(ingredients)
            >>> 6.0 < ph < 7.5
            True
        """
        # Separate ingredients by type
        buffers = []
        weak_acids = []
        weak_bases = []
        strong_acids = []
        strong_bases = []
        salts = []

        for ing in ingredients:
            name = ing.get("name", "")
            conc_mM = self._convert_to_mM(ing)

            if conc_mM <= 0:
                continue

            # Classify ingredient
            if self._is_buffer(name):
                pka = self._get_pka(name, ing)
                buffers.append({
                    "name": name,
                    "concentration": conc_mM,
                    "pka": pka,
                })
            elif self._is_weak_acid(name):
                pka = self._get_pka(name, ing)
                weak_acids.append({
                    "name": name,
                    "concentration": conc_mM,
                    "pka": pka,
                })
            elif self._is_salt(name):
                ph_effect = self._get_salt_ph_effect(name)
                salts.append({
                    "name": name,
                    "concentration": conc_mM,
                    "ph_effect": ph_effect,
                })

        # Calculate pH based on dominant components
        # Initialize pH to neutral (water) as default
        ph = 7.0
        details = {"system_type": "water"}

        if buffers:
            # Buffer-dominated system
            ph = self._calculate_buffer_ph(buffers, weak_acids, salts)
            dominant_buffer = max(buffers, key=lambda x: x["concentration"])
            details = {
                "system_type": "buffered",
                "dominant_buffer": dominant_buffer["name"],
                "buffer_concentration": dominant_buffer["concentration"],
                "buffer_pka": dominant_buffer["pka"],
            }
        elif weak_acids:
            # Weak acid dominated
            ph = self._calculate_weak_acid_ph(weak_acids, salts)
            details = {
                "system_type": "weak_acid",
                "dominant_acid": weak_acids[0]["name"],
            }
        elif salts:
            # Salt-only solution
            ph = self._calculate_salt_ph(salts)
            details = {
                "system_type": "salt_solution",
            }

        # Apply salt corrections
        if salts:
            salt_correction = sum(s["ph_effect"] * math.log10(1 + s["concentration"]/100)
                                 for s in salts) / max(len(salts), 1)
            if ph is not None:
                ph += salt_correction
        else:
            salt_correction = 0.0

        # Clamp to reasonable range
        ph = max(2.0, min(12.0, ph))

        details["salt_correction"] = salt_correction
        details["n_buffers"] = len(buffers)
        details["n_salts"] = len(salts)

        return ph, details

    def predict_ph_at_concentrations(
        self,
        base_formulation: List[Dict],
        variable_ingredient: str,
        concentrations: List[float],
        volume_ml: float = 1000.0,
    ) -> List[Dict]:
        """
        Predict pH at different concentrations of a single ingredient.

        Args:
            base_formulation: Base formulation with default concentrations
            variable_ingredient: Name of ingredient to vary
            concentrations: List of concentrations to test
            volume_ml: Total volume in mL

        Returns:
            List of dicts with concentration and predicted pH

        Examples:
            >>> calc = MediaPhCalculator()
            >>> base = [{"name": "PIPES", "concentration": 30, "unit": "mM"}]
            >>> results = calc.predict_ph_at_concentrations(base, "PIPES", [10, 30, 100])
            >>> len(results) == 3
            True
        """
        results = []

        for conc in concentrations:
            # Create modified formulation
            modified = []
            found = False

            for ing in base_formulation:
                if ing["name"] == variable_ingredient:
                    # Replace with new concentration
                    modified.append({
                        **ing,
                        "concentration": conc,
                    })
                    found = True
                else:
                    modified.append(ing)

            # If ingredient not in base, add it
            if not found:
                # Try to find it in original formulation for pKa info
                modified.append({
                    "name": variable_ingredient,
                    "concentration": conc,
                    "unit": "mM",
                })

            # Calculate pH
            ph, details = self.calculate_ph(modified, volume_ml)

            results.append({
                "concentration": conc,
                "unit": "mM",
                "ph": round(ph, 2),
                "details": details,
            })

        return results

    def _convert_to_mM(self, ingredient: Dict) -> float:
        """Convert concentration to mM."""
        conc = ingredient.get("concentration", 0)
        unit = ingredient.get("unit", "mM")

        if unit in ["mM", "mmol/L"]:
            return conc
        elif unit in ["M", "mol/L"]:
            return conc * 1000
        elif unit in ["µM", "uM", "umol/L"]:
            return conc / 1000
        elif unit == "g/L":
            # Would need molecular weight - use approximation
            mw = ingredient.get("molecular_weight", 100)
            return (conc / mw) * 1000
        else:
            return conc

    def _is_buffer(self, name: str) -> bool:
        """Check if ingredient is a buffer."""
        buffer_keywords = ["PIPES", "HEPES", "MES", "MOPS", "Tris", "TRIS"]
        return any(kw.lower() in name.lower() for kw in buffer_keywords)

    def _is_weak_acid(self, name: str) -> bool:
        """Check if ingredient is a weak acid."""
        acid_keywords = ["citrate", "acetate", "phosphate", "HPO4", "H2PO4"]
        return any(kw.lower() in name.lower() for kw in acid_keywords)

    def _is_salt(self, name: str) -> bool:
        """Check if ingredient is a salt."""
        # Most ingredients containing Cl, SO4, etc are salts
        salt_indicators = ["Cl", "SO4", "NO3", "WO4", "MoO4", "SeO3"]

        # Common salt name patterns
        if any(ind in name for ind in salt_indicators):
            return True

        # Metal cation patterns (e.g., FeCl2, CaCl2, etc.)
        metal_cations = ["Fe", "Ca", "Mg", "Mn", "Zn", "Cu", "Co", "Ni", "Na", "K", "NH4"]
        if any(metal in name for metal in metal_cations):
            return True

        return False

    def _get_pka(self, name: str, ingredient: Dict) -> float:
        """Get pKa value for ingredient."""
        # Check if provided in ingredient (and not None)
        if "pka" in ingredient and ingredient["pka"] is not None:
            return ingredient["pka"]

        # Look up in database
        name_lower = name.lower()
        for key, value in self.PKA_VALUES.items():
            if key.lower() in name_lower:
                if isinstance(value, list):
                    # Return middle pKa for polyprotic acids
                    return value[len(value) // 2]
                return value

        # Default to neutral
        return 7.0

    def _get_salt_ph_effect(self, name: str) -> float:
        """Get pH effect of salt."""
        # Normalize name by removing hydration info
        # E.g., "FeCl2 x 4 H2O" -> "FeCl2"
        normalized = name.split(" x ")[0].split(" · ")[0].strip()

        for salt_name, effect in self.SALT_PH_EFFECTS.items():
            if salt_name.lower() in normalized.lower():
                return effect

        # Fallback: Check original name
        for salt_name, effect in self.SALT_PH_EFFECTS.items():
            if salt_name.lower() in name.lower():
                return effect

        # Default: assume slightly acidic for metal salts, neutral otherwise
        # Most metal chlorides/sulfates are slightly acidic
        if any(metal in name for metal in ["Fe", "Cu", "Zn", "Mn", "Co", "Ni", "Al"]):
            return -0.3
        return 0.0

    def _calculate_buffer_ph(
        self,
        buffers: List[Dict],
        weak_acids: List[Dict],
        salts: List[Dict],
    ) -> float:
        """Calculate pH for buffered system using Henderson-Hasselbalch."""
        # Use dominant buffer
        dominant = max(buffers, key=lambda x: x["concentration"])

        # Henderson-Hasselbalch: pH = pKa + log([A-]/[HA])
        pka = dominant["pka"]
        buffer_conc = dominant["concentration"]

        # Calculate net acid/base from salts
        # Acidic salts increase [HA], basic salts increase [A-]
        net_acid_mM = 0.0
        for salt in salts:
            # Acidic salts (negative pH effect) add H+
            # Basic salts (positive pH effect) add OH-
            net_acid_mM += salt["ph_effect"] * salt["concentration"] * 0.01  # Scale factor

        # Calculate ratio of conjugate base to acid
        # Start with equal amounts (1:1 ratio at pKa)
        # Then shift based on net acid/base added
        if buffer_conc > 0:
            ratio = (buffer_conc/2 + net_acid_mM) / (buffer_conc/2 - net_acid_mM) if abs(net_acid_mM) < buffer_conc/2 else 1.0
            ratio = max(0.01, min(100, ratio))  # Clamp to reasonable range
            ph = pka + math.log10(ratio)
        else:
            ph = pka

        return ph

    def _calculate_weak_acid_ph(
        self,
        weak_acids: List[Dict],
        salts: List[Dict],
    ) -> float:
        """Calculate pH for weak acid system."""
        dominant = weak_acids[0]

        # For weak acid: pH ≈ (pKa1 + pKa2) / 2 for intermediate salts
        pka = dominant["pka"]

        return pka

    def _calculate_salt_ph(self, salts: List[Dict]) -> float:
        """Calculate pH for salt-only solution."""
        if not salts:
            return 7.0  # Pure water

        # Weighted average of salt effects
        total_conc = sum(s["concentration"] for s in salts)
        if total_conc == 0:
            return 7.0

        weighted_effect = sum(s["concentration"] * s["ph_effect"] for s in salts) / total_conc

        return 7.0 + weighted_effect

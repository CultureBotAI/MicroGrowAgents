"""Tests for osmotic property calculations."""

import pytest
from microgrowagents.chemistry.osmotic_properties import (
    calculate_osmolarity,
    calculate_water_activity,
    estimate_van_hoff_factor,
    VAN_HOFF_DATABASE
)


class TestVanHoffFactor:
    """Test van't Hoff factor estimation."""

    def test_nacl_lookup(self):
        """Test NaCl van't Hoff factor from database."""
        factor, confidence = estimate_van_hoff_factor(
            formula="NaCl",
            charge=0,
            name="sodium chloride"
        )
        assert factor == pytest.approx(1.9, abs=0.1)
        assert confidence == 1.0

    def test_glucose_nondissociating(self):
        """Test glucose (non-dissociating) factor."""
        factor, confidence = estimate_van_hoff_factor(
            formula="C6H12O6",
            charge=0,
            name="glucose"
        )
        assert factor == 1.0
        assert confidence == 1.0

    def test_cacl2_polyelectrolyte(self):
        """Test CaCl2 (1:2 electrolyte) factor."""
        factor, confidence = estimate_van_hoff_factor(
            formula="CaCl2",
            charge=0,
            name="calcium chloride"
        )
        assert 2.5 <= factor <= 3.0
        assert confidence >= 0.9

    def test_mgso4_ion_pairing(self):
        """Test MgSO4 (strong ion pairing) factor."""
        factor, confidence = estimate_van_hoff_factor(
            formula="MgSO4",
            charge=0,
            name="magnesium sulfate"
        )
        # MgSO4 shows strong ion pairing, i ≈ 1.3
        assert 1.2 <= factor <= 1.5
        assert confidence >= 0.9

    def test_unknown_compound_estimation(self):
        """Test estimation for unknown compound."""
        factor, confidence = estimate_van_hoff_factor(
            formula="XYZ123",
            charge=0,
            name="unknown compound"
        )
        # Should return fallback value
        assert factor == 1.0
        assert confidence == 0.5

    def test_charged_compound_estimation(self):
        """Test estimation for charged compound."""
        factor, confidence = estimate_van_hoff_factor(
            formula="NH4Cl",
            charge=0,
            name="ammonium chloride"
        )
        # NH4Cl is a strong electrolyte
        assert 1.8 <= factor <= 2.0
        assert confidence >= 0.9


class TestOsmolarity:
    """Test osmolarity calculations."""

    def test_simple_nacl_solution(self):
        """Test osmolarity of simple NaCl solution."""
        ingredients = [
            {
                "name": "NaCl",
                "concentration": 150.0,  # mM
                "molecular_weight": 58.44,
                "formula": "NaCl",
                "charge": 0,
                "grams_per_liter": 8.77
            }
        ]

        result = calculate_osmolarity(ingredients, temperature=25.0)

        # 150 mM NaCl → ~285 mOsm (factor ~1.9)
        assert 280 <= result["osmolarity"] <= 290
        assert result["confidence"] >= 0.9
        assert "van_hoff_factors" in result
        assert result["van_hoff_factors"]["NaCl"] == pytest.approx(1.9, abs=0.1)

    def test_pure_glucose_solution(self):
        """Test osmolarity of pure glucose solution."""
        ingredients = [
            {
                "name": "glucose",
                "concentration": 100.0,  # mM
                "molecular_weight": 180.16,
                "formula": "C6H12O6",
                "charge": 0,
                "grams_per_liter": 18.016
            }
        ]

        result = calculate_osmolarity(ingredients, temperature=25.0)

        # 100 mM glucose → 100 mOsm (factor = 1.0)
        assert 99 <= result["osmolarity"] <= 101
        assert result["confidence"] >= 0.9
        assert result["van_hoff_factors"]["glucose"] == 1.0

    def test_mixed_solution(self):
        """Test osmolarity of mixed electrolyte + non-electrolyte."""
        ingredients = [
            {
                "name": "NaCl",
                "concentration": 100.0,
                "molecular_weight": 58.44,
                "formula": "NaCl",
                "charge": 0,
                "grams_per_liter": 5.84
            },
            {
                "name": "glucose",
                "concentration": 50.0,
                "molecular_weight": 180.16,
                "formula": "C6H12O6",
                "charge": 0,
                "grams_per_liter": 9.008
            }
        ]

        result = calculate_osmolarity(ingredients, temperature=25.0)

        # 100 mM NaCl (~190 mOsm) + 50 mM glucose (50 mOsm) = ~240 mOsm
        assert 235 <= result["osmolarity"] <= 245
        assert result["confidence"] >= 0.9

    def test_empty_ingredient_list(self):
        """Test osmolarity with empty ingredient list."""
        ingredients = []

        result = calculate_osmolarity(ingredients, temperature=25.0)

        assert result["osmolarity"] == 0.0
        assert result["osmolality"] == 0.0
        assert result["confidence"] == 1.0

    def test_osmolality_calculation(self):
        """Test osmolality (mOsm/kg) vs osmolarity (mOsm/L)."""
        ingredients = [
            {
                "name": "NaCl",
                "concentration": 150.0,
                "molecular_weight": 58.44,
                "formula": "NaCl",
                "charge": 0,
                "grams_per_liter": 8.77
            }
        ]

        result = calculate_osmolarity(ingredients, temperature=25.0)

        # For dilute solutions, osmolality ≈ osmolarity
        assert result["osmolality"] == pytest.approx(result["osmolarity"], abs=5)


class TestWaterActivity:
    """Test water activity calculations."""

    def test_dilute_solution_raoult(self):
        """Test water activity via Raoult's law (dilute)."""
        ingredients = [
            {
                "name": "NaCl",
                "concentration": 100.0,
                "molecular_weight": 58.44,
                "formula": "NaCl",
                "charge": 0,
                "grams_per_liter": 5.84
            }
        ]

        result = calculate_water_activity(
            ingredients,
            temperature=25.0,
            method="raoult"
        )

        # aw ≈ 1 - (osmolality / 55.5)
        # ~190 mOsm/kg → aw ≈ 0.997
        assert 0.995 <= result["water_activity"] <= 0.999
        assert result["growth_category"] == "most_bacteria"
        assert result["method"] == "raoult"
        assert result["confidence"] >= 0.8

    def test_concentrated_solution(self):
        """Test water activity in concentrated solution."""
        ingredients = [
            {
                "name": "NaCl",
                "concentration": 1000.0,
                "molecular_weight": 58.44,
                "formula": "NaCl",
                "charge": 0,
                "grams_per_liter": 58.44
            }
        ]

        result = calculate_water_activity(
            ingredients,
            temperature=25.0,
            method="robinson_stokes"
        )

        # High salt → low aw
        assert 0.90 <= result["water_activity"] <= 0.97
        assert result["growth_category"] in ["halotolerant", "halophiles"]
        assert result["method"] == "robinson_stokes"

    def test_very_concentrated_halophile_range(self):
        """Test water activity in halophile range."""
        ingredients = [
            {
                "name": "NaCl",
                "concentration": 3000.0,
                "molecular_weight": 58.44,
                "formula": "NaCl",
                "charge": 0,
                "grams_per_liter": 175.32
            }
        ]

        result = calculate_water_activity(
            ingredients,
            temperature=25.0,
            method="robinson_stokes"
        )

        # Very high salt → very low aw
        assert result["water_activity"] < 0.90
        assert result["growth_category"] == "halophiles"

    def test_pure_water(self):
        """Test water activity of pure water."""
        ingredients = []

        result = calculate_water_activity(
            ingredients,
            temperature=25.0,
            method="raoult"
        )

        assert result["water_activity"] == pytest.approx(1.0, abs=0.001)
        assert result["growth_category"] == "most_bacteria"

    def test_temperature_dependence(self):
        """Test water activity at different temperatures."""
        ingredients = [
            {
                "name": "NaCl",
                "concentration": 500.0,
                "molecular_weight": 58.44,
                "formula": "NaCl",
                "charge": 0,
                "grams_per_liter": 29.22
            }
        ]

        result_25 = calculate_water_activity(ingredients, temperature=25.0)
        result_37 = calculate_water_activity(ingredients, temperature=37.0)

        # Water activity changes slightly with temperature
        assert abs(result_25["water_activity"] - result_37["water_activity"]) < 0.05


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_typical_bacterial_medium(self):
        """Test osmotic properties of typical bacterial growth medium."""
        # LB-like medium composition
        ingredients = [
            {"name": "NaCl", "concentration": 170.0, "molecular_weight": 58.44,
             "formula": "NaCl", "charge": 0, "grams_per_liter": 10.0},
            {"name": "glucose", "concentration": 20.0, "molecular_weight": 180.16,
             "formula": "C6H12O6", "charge": 0, "grams_per_liter": 3.6},
            {"name": "K2HPO4", "concentration": 10.0, "molecular_weight": 174.18,
             "formula": "K2HPO4", "charge": 0, "grams_per_liter": 1.74}
        ]

        osm_result = calculate_osmolarity(ingredients, temperature=37.0)
        aw_result = calculate_water_activity(ingredients, temperature=37.0)

        # Typical bacterial medium
        assert 300 <= osm_result["osmolarity"] <= 400
        assert aw_result["water_activity"] > 0.98
        assert aw_result["growth_category"] == "most_bacteria"

    def test_marine_medium(self):
        """Test osmotic properties of marine bacterial medium."""
        # Marine medium with high salt
        ingredients = [
            {"name": "NaCl", "concentration": 500.0, "molecular_weight": 58.44,
             "formula": "NaCl", "charge": 0, "grams_per_liter": 29.22},
            {"name": "MgCl2", "concentration": 50.0, "molecular_weight": 95.21,
             "formula": "MgCl2", "charge": 0, "grams_per_liter": 4.76},
        ]

        osm_result = calculate_osmolarity(ingredients, temperature=25.0)
        aw_result = calculate_water_activity(ingredients, temperature=25.0)

        # Marine medium - higher osmolarity
        assert osm_result["osmolarity"] > 900
        assert 0.90 <= aw_result["water_activity"] <= 0.98
        assert aw_result["growth_category"] in ["most_bacteria", "halotolerant"]


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_zero_concentration(self):
        """Test handling of zero concentration."""
        ingredients = [
            {"name": "NaCl", "concentration": 0.0, "molecular_weight": 58.44,
             "formula": "NaCl", "charge": 0, "grams_per_liter": 0.0}
        ]

        result = calculate_osmolarity(ingredients, temperature=25.0)
        assert result["osmolarity"] == 0.0

    def test_missing_formula(self):
        """Test handling of missing formula."""
        ingredients = [
            {"name": "unknown", "concentration": 100.0, "molecular_weight": 100.0,
             "charge": 0, "grams_per_liter": 10.0}
        ]

        result = calculate_osmolarity(ingredients, temperature=25.0)
        # Should use fallback van't Hoff factor = 1.0
        assert result["osmolarity"] == pytest.approx(100.0, abs=5)
        assert result["confidence"] < 1.0

    def test_extreme_temperature(self):
        """Test behavior at extreme temperatures."""
        ingredients = [
            {"name": "NaCl", "concentration": 150.0, "molecular_weight": 58.44,
             "formula": "NaCl", "charge": 0, "grams_per_liter": 8.77}
        ]

        # Should still calculate, though accuracy may decrease
        result = calculate_water_activity(ingredients, temperature=80.0)
        assert 0.0 < result["water_activity"] < 1.0
        # Confidence should be lower at extreme temperatures
        assert result["confidence"] < 0.9

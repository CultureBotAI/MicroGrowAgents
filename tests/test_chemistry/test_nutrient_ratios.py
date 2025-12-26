"""Tests for nutrient ratio calculations."""

import pytest
from microgrowagents.chemistry.nutrient_ratios import (
    calculate_cnp_ratios,
    calculate_trace_metal_ratios,
    parse_elemental_composition,
    REDFIELD_RATIO
)


class TestConstants:
    """Test constants and reference values."""

    def test_redfield_ratio_exists(self):
        """Test Redfield ratio constant exists."""
        assert "C" in REDFIELD_RATIO
        assert "N" in REDFIELD_RATIO
        assert "P" in REDFIELD_RATIO

    def test_redfield_ratio_values(self):
        """Test Redfield ratio values are reasonable."""
        # Marine Redfield: C:N:P = 106:16:1
        assert REDFIELD_RATIO["C"] == pytest.approx(106, abs=5)
        assert REDFIELD_RATIO["N"] == pytest.approx(16, abs=2)
        assert REDFIELD_RATIO["P"] == pytest.approx(1, abs=0.1)


class TestElementalComposition:
    """Test elemental composition parsing."""

    def test_simple_formula(self):
        """Test parsing simple formula."""
        comp = parse_elemental_composition("C6H12O6")  # glucose
        assert comp["C"] == 6
        assert comp["H"] == 12
        assert comp["O"] == 6
        assert comp.get("N", 0) == 0
        assert comp.get("P", 0) == 0

    def test_formula_with_parentheses(self):
        """Test parsing formula with parentheses."""
        comp = parse_elemental_composition("Ca(NO3)2")  # calcium nitrate
        assert comp["Ca"] == 1
        assert comp["N"] == 2
        assert comp["O"] == 6

    def test_formula_with_phosphate(self):
        """Test parsing phosphate formula."""
        comp = parse_elemental_composition("K2HPO4")  # dipotassium phosphate
        assert comp["K"] == 2
        assert comp["H"] == 1
        assert comp["P"] == 1
        assert comp["O"] == 4

    def test_complex_buffer_formula(self):
        """Test parsing complex buffer formula."""
        comp = parse_elemental_composition("C8H18N2O4S")  # HEPES
        assert comp["C"] == 8
        assert comp["H"] == 18
        assert comp["N"] == 2
        assert comp["O"] == 4
        assert comp["S"] == 1

    def test_hydrated_compound(self):
        """Test parsing hydrated compound."""
        # CaCl2·2H2O or MgSO4.7H2O
        comp = parse_elemental_composition("MgSO4")  # Ignore hydration for now
        assert comp["Mg"] == 1
        assert comp["S"] == 1
        assert comp["O"] == 4

    def test_empty_formula(self):
        """Test handling empty formula."""
        comp = parse_elemental_composition("")
        assert comp == {}

    def test_invalid_formula(self):
        """Test handling invalid formula."""
        comp = parse_elemental_composition("INVALID123XYZ")
        # Should return empty or partial result
        assert isinstance(comp, dict)


class TestCNPRatios:
    """Test C:N:P ratio calculations."""

    def test_balanced_medium(self):
        """Test balanced medium near Redfield ratio."""
        ingredients = [
            {"name": "glucose", "concentration": 10.0, "formula": "C6H12O6"},  # 60 mM C
            {"name": "NH4Cl", "concentration": 9.0, "formula": "NH4Cl"},  # 9 mM N
            {"name": "KH2PO4", "concentration": 0.6, "formula": "KH2PO4"}  # 0.6 mM P
        ]

        result = calculate_cnp_ratios(ingredients)

        assert result is not None
        # C:N:P should be 60:9:0.6 = 100:15:1 (close to Redfield 106:16:1)
        assert 6 <= result["c_n_ratio"] <= 7  # C:N = 60/9 = 6.67
        assert 90 <= result["c_p_ratio"] <= 110  # C:P = 60/0.6 = 100
        assert 14 <= result["n_p_ratio"] <= 16  # N:P = 9/0.6 = 15
        assert result["limiting_nutrient"] in ["balanced", "N"]

    def test_carbon_limited(self):
        """Test carbon-limited medium."""
        ingredients = [
            {"name": "glucose", "concentration": 1.0, "formula": "C6H12O6"},  # Low C
            {"name": "NH4Cl", "concentration": 10.0, "formula": "NH4Cl"},  # High N
            {"name": "KH2PO4", "concentration": 2.0, "formula": "KH2PO4"}  # High P
        ]

        result = calculate_cnp_ratios(ingredients)

        assert result is not None
        assert result["limiting_nutrient"] == "C"
        assert result["c_n_ratio"] < 6.6  # Below threshold

    def test_nitrogen_limited(self):
        """Test nitrogen-limited medium."""
        ingredients = [
            {"name": "glucose", "concentration": 20.0, "formula": "C6H12O6"},  # High C
            {"name": "NH4Cl", "concentration": 1.0, "formula": "NH4Cl"},  # Low N
            {"name": "KH2PO4", "concentration": 2.0, "formula": "KH2PO4"}  # High P
        ]

        result = calculate_cnp_ratios(ingredients)

        assert result is not None
        assert result["limiting_nutrient"] == "N"
        assert result["c_n_ratio"] > 20  # Above threshold

    def test_phosphorus_limited(self):
        """Test phosphorus-limited medium."""
        ingredients = [
            {"name": "glucose", "concentration": 20.0, "formula": "C6H12O6"},  # 120 mM C
            {"name": "NH4Cl", "concentration": 5.0, "formula": "NH4Cl"},  # 5 mM N
            {"name": "KH2PO4", "concentration": 0.1, "formula": "KH2PO4"}  # 0.1 mM P
        ]

        result = calculate_cnp_ratios(ingredients)

        assert result is not None
        assert result["limiting_nutrient"] == "P"
        assert result["c_p_ratio"] > 1000  # 120/0.1 = 1200 (very high)
        assert result["n_p_ratio"] > 40  # 5/0.1 = 50 (above Redfield 16)

    def test_organic_nitrogen_source(self):
        """Test with organic nitrogen source."""
        ingredients = [
            {"name": "glucose", "concentration": 10.0, "formula": "C6H12O6"},
            {"name": "peptone", "concentration": 5.0, "formula": "C5H9NO4"},  # Simplified
            {"name": "KH2PO4", "concentration": 1.0, "formula": "KH2PO4"}
        ]

        result = calculate_cnp_ratios(ingredients)

        assert result is not None
        assert result["c_mol"] > 0
        assert result["n_mol"] > 0
        assert result["p_mol"] > 0

    def test_no_nutrients(self):
        """Test with no C, N, or P."""
        ingredients = [
            {"name": "NaCl", "concentration": 100.0, "formula": "NaCl"}
        ]

        result = calculate_cnp_ratios(ingredients)

        assert result is not None
        assert result["c_mol"] == 0
        assert result["n_mol"] == 0
        assert result["p_mol"] == 0
        assert result["limiting_nutrient"] == "all"

    def test_redfield_deviation(self):
        """Test Redfield ratio deviation calculation."""
        ingredients = [
            {"name": "glucose", "concentration": 17.67, "formula": "C6H12O6"},  # 106 mM C
            {"name": "NH4Cl", "concentration": 16.0, "formula": "NH4Cl"},  # 16 mM N
            {"name": "KH2PO4", "concentration": 1.0, "formula": "KH2PO4"}  # 1 mM P
        ]

        result = calculate_cnp_ratios(ingredients)

        assert result is not None
        # Should be very close to Redfield (C:N:P = 106:16:1)
        assert result["redfield_deviation"] < 5  # % deviation


class TestTraceMetalRatios:
    """Test trace metal ratio calculations."""

    def test_adequate_trace_metals(self):
        """Test medium with adequate trace metals."""
        ingredients = [
            {"name": "FeSO4", "concentration": 0.02, "formula": "FeSO4"},  # Fe
            {"name": "MnCl2", "concentration": 0.005, "formula": "MnCl2"},  # Mn
            {"name": "ZnSO4", "concentration": 0.003, "formula": "ZnSO4"},  # Zn
            {"name": "KH2PO4", "concentration": 1.0, "formula": "KH2PO4"}  # P
        ]

        result = calculate_trace_metal_ratios(ingredients)

        assert result is not None
        # Fe:P should be around 0.02
        assert 0.01 <= result["fe_p_ratio"] <= 0.03
        # Mn:P should be around 0.005
        assert 0.003 <= result["mn_p_ratio"] <= 0.007
        # Zn:P should be around 0.003
        assert 0.002 <= result["zn_p_ratio"] <= 0.005

        # No deficiencies for provided metals (Fe, Mn, Zn)
        # Note: Cu, Co, Mo not provided so they will show as deficient
        provided_metals = {"Fe", "Mn", "Zn"}
        deficient_provided = [m for m in result["deficiencies"] if m in provided_metals]
        assert len(deficient_provided) == 0

    def test_iron_deficiency(self):
        """Test iron-deficient medium."""
        ingredients = [
            # No Fe
            {"name": "MnCl2", "concentration": 0.005, "formula": "MnCl2"},
            {"name": "ZnSO4", "concentration": 0.003, "formula": "ZnSO4"},
            {"name": "KH2PO4", "concentration": 1.0, "formula": "KH2PO4"}
        ]

        result = calculate_trace_metal_ratios(ingredients)

        assert result is not None
        assert result["fe_p_ratio"] == 0.0
        assert "Fe" in result["deficiencies"]

    def test_manganese_deficiency(self):
        """Test manganese-deficient medium."""
        ingredients = [
            {"name": "FeSO4", "concentration": 0.02, "formula": "FeSO4"},
            # No Mn
            {"name": "ZnSO4", "concentration": 0.003, "formula": "ZnSO4"},
            {"name": "KH2PO4", "concentration": 1.0, "formula": "KH2PO4"}
        ]

        result = calculate_trace_metal_ratios(ingredients)

        assert result is not None
        assert "Mn" in result["deficiencies"]

    def test_zinc_excess(self):
        """Test zinc excess."""
        ingredients = [
            {"name": "FeSO4", "concentration": 0.02, "formula": "FeSO4"},
            {"name": "MnCl2", "concentration": 0.005, "formula": "MnCl2"},
            {"name": "ZnSO4", "concentration": 0.5, "formula": "ZnSO4"},  # Very high Zn
            {"name": "KH2PO4", "concentration": 1.0, "formula": "KH2PO4"}
        ]

        result = calculate_trace_metal_ratios(ingredients)

        assert result is not None
        assert result["zn_p_ratio"] > 0.1  # Much higher than typical
        assert "Zn" in result["excesses"]

    def test_no_phosphorus(self):
        """Test handling when no phosphorus present."""
        ingredients = [
            {"name": "FeSO4", "concentration": 0.02, "formula": "FeSO4"},
            {"name": "MnCl2", "concentration": 0.005, "formula": "MnCl2"}
        ]

        result = calculate_trace_metal_ratios(ingredients)

        assert result is not None
        # Ratios should be None or inf
        assert result["fe_p_ratio"] in [None, float('inf'), 0]


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_ingredients(self):
        """Test with empty ingredients list."""
        result = calculate_cnp_ratios([])

        assert result is not None
        assert result["c_mol"] == 0
        assert result["n_mol"] == 0
        assert result["p_mol"] == 0

    def test_missing_formula(self):
        """Test ingredients without formula."""
        ingredients = [
            {"name": "unknown", "concentration": 10.0}  # No formula
        ]

        result = calculate_cnp_ratios(ingredients)

        assert result is not None
        # Should handle gracefully

    def test_zero_concentration(self):
        """Test with zero concentration."""
        ingredients = [
            {"name": "glucose", "concentration": 0.0, "formula": "C6H12O6"}
        ]

        result = calculate_cnp_ratios(ingredients)

        assert result is not None
        assert result["c_mol"] == 0

    def test_negative_concentration(self):
        """Test with negative concentration."""
        with pytest.raises(ValueError, match="concentration"):
            calculate_cnp_ratios([
                {"name": "glucose", "concentration": -10.0, "formula": "C6H12O6"}
            ])


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_complete_medium_analysis(self):
        """Test complete nutrient analysis for typical medium."""
        ingredients = [
            {"name": "glucose", "concentration": 10.0, "formula": "C6H12O6"},
            {"name": "NH4Cl", "concentration": 5.0, "formula": "NH4Cl"},
            {"name": "KH2PO4", "concentration": 1.0, "formula": "KH2PO4"},
            {"name": "FeSO4", "concentration": 0.01, "formula": "FeSO4"},
            {"name": "MnCl2", "concentration": 0.002, "formula": "MnCl2"},
            {"name": "ZnSO4", "concentration": 0.001, "formula": "ZnSO4"}
        ]

        cnp_result = calculate_cnp_ratios(ingredients)
        metal_result = calculate_trace_metal_ratios(ingredients)

        assert cnp_result is not None
        assert metal_result is not None

        # Both should provide useful information
        assert cnp_result["c_mol"] > 0
        assert cnp_result["n_mol"] > 0
        assert cnp_result["p_mol"] > 0
        assert metal_result["fe_p_ratio"] > 0

    def test_marine_medium(self):
        """Test analysis of marine medium composition."""
        # Marine media typically follow Redfield ratio more closely
        # Redfield: C:N:P = 106:16:1
        ingredients = [
            {"name": "glucose", "concentration": 17.67, "formula": "C6H12O6"},  # 106 mM C
            {"name": "NaNO3", "concentration": 16.0, "formula": "NaNO3"},  # 16 mM N
            {"name": "Na2HPO4", "concentration": 1.0, "formula": "Na2HPO4"},  # 1 mM P
            {"name": "FeCl3", "concentration": 0.02, "formula": "FeCl3"}
        ]

        result = calculate_cnp_ratios(ingredients)

        assert result is not None
        # Should be close to Redfield
        assert 6 <= result["c_n_ratio"] <= 7  # 106/16 = 6.625
        assert 100 <= result["c_p_ratio"] <= 110  # 106/1 = 106
        assert 14 <= result["n_p_ratio"] <= 18  # 16/1 = 16
        assert result["limiting_nutrient"] in ["balanced", "N", "C"]

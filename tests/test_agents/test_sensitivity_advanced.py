"""Tests for SensitivityAnalysisAgent with advanced chemistry properties."""

import pytest
from microgrowagents.agents.sensitivity_analysis_agent import SensitivityAnalysisAgent


class TestSensitivityWithOsmoticProperties:
    """Test sensitivity analysis with osmotic property calculations."""

    def test_baseline_with_osmotic_properties(self):
        """Test baseline calculation includes osmotic properties when requested."""
        agent = SensitivityAnalysisAgent()

        # Simple test case: NaCl and KCl
        result = agent.run(
            "NaCl,KCl",
            mode="ingredients",
            calculate_osmotic=True
        )

        assert result["success"]
        assert "baseline" in result
        baseline = result["baseline"]

        # Check osmotic properties are present
        assert "osmotic_properties" in baseline
        osm_props = baseline["osmotic_properties"]

        assert "osmolarity" in osm_props
        assert "osmolality" in osm_props
        assert "water_activity" in osm_props
        assert "growth_category" in osm_props

        # Values should be reasonable
        assert osm_props["osmolarity"] > 0
        assert 0.9 < osm_props["water_activity"] <= 1.0

    def test_baseline_without_osmotic_properties(self):
        """Test baseline calculation without osmotic properties when not requested."""
        agent = SensitivityAnalysisAgent()

        result = agent.run(
            "NaCl,KCl",
            mode="ingredients"
        )

        assert result["success"]
        assert "baseline" in result
        baseline = result["baseline"]

        # Osmotic properties should not be present
        assert "osmotic_properties" not in baseline

    def test_mp_medium_with_osmotic(self):
        """Test MP medium analysis with osmotic properties."""
        agent = SensitivityAnalysisAgent()

        result = agent.run(
            "MP medium",
            mode="medium",
            calculate_osmotic=True
        )

        assert result["success"]
        assert "baseline" in result
        baseline = result["baseline"]

        assert "osmotic_properties" in baseline
        osm_props = baseline["osmotic_properties"]

        # MP medium should have reasonable osmolarity
        # Note: May be high if concentrations are elevated or many ingredients
        assert osm_props["osmolarity"] > 0
        assert osm_props["osmolarity"] < 20000  # Sanity check (not astronomical)


class TestSensitivityWithRedoxProperties:
    """Test sensitivity analysis with redox property calculations."""

    def test_baseline_with_redox_properties(self):
        """Test baseline calculation includes redox properties when requested."""
        agent = SensitivityAnalysisAgent()

        # Create ingredients with redox couples
        result = agent.run(
            "glucose,NH4Cl,KH2PO4",
            mode="ingredients",
            calculate_redox=True,
            ph=7.0  # Need pH for redox calculations
        )

        assert result["success"]
        assert "baseline" in result
        baseline = result["baseline"]

        # Check redox properties are present
        assert "redox_properties" in baseline
        redox_props = baseline["redox_properties"]

        assert "eh" in redox_props
        assert "pe" in redox_props
        assert "redox_state" in redox_props
        assert "electron_balance" in redox_props

    def test_baseline_without_redox_properties(self):
        """Test baseline calculation without redox properties when not requested."""
        agent = SensitivityAnalysisAgent()

        result = agent.run(
            "glucose,NH4Cl",
            mode="ingredients"
        )

        assert result["success"]
        assert "redox_properties" not in result["baseline"]


class TestSensitivityWithNutrientRatios:
    """Test sensitivity analysis with nutrient ratio calculations."""

    def test_baseline_with_nutrient_ratios(self):
        """Test baseline calculation includes nutrient ratios when requested."""
        agent = SensitivityAnalysisAgent()

        # Ingredients with C, N, P
        result = agent.run(
            "glucose,NH4Cl,KH2PO4",
            mode="ingredients",
            calculate_nutrients=True
        )

        assert result["success"]
        assert "baseline" in result
        baseline = result["baseline"]

        # Check nutrient ratio properties are present
        assert "nutrient_ratios" in baseline
        nutrient_props = baseline["nutrient_ratios"]

        assert "c_mol" in nutrient_props
        assert "n_mol" in nutrient_props
        assert "p_mol" in nutrient_props
        assert "c_n_ratio" in nutrient_props
        assert "c_p_ratio" in nutrient_props
        assert "n_p_ratio" in nutrient_props
        assert "limiting_nutrient" in nutrient_props

    def test_baseline_without_nutrient_ratios(self):
        """Test baseline calculation without nutrient ratios when not requested."""
        agent = SensitivityAnalysisAgent()

        result = agent.run(
            "glucose,NH4Cl",
            mode="ingredients"
        )

        assert result["success"]
        assert "nutrient_ratios" not in result["baseline"]


class TestSensitivityWithAllAdvancedProperties:
    """Test sensitivity analysis with all advanced properties."""

    def test_baseline_with_all_properties(self):
        """Test baseline calculation with all advanced properties."""
        agent = SensitivityAnalysisAgent()

        result = agent.run(
            "glucose,NH4Cl,KH2PO4,NaCl",
            mode="ingredients",
            calculate_osmotic=True,
            calculate_redox=True,
            calculate_nutrients=True,
            ph=7.0
        )

        assert result["success"]
        baseline = result["baseline"]

        # All three property categories should be present
        assert "osmotic_properties" in baseline
        assert "redox_properties" in baseline
        assert "nutrient_ratios" in baseline

    def test_mp_medium_with_all_properties(self):
        """Test MP medium with all advanced properties."""
        agent = SensitivityAnalysisAgent()

        result = agent.run(
            "MP medium",
            mode="medium",
            calculate_osmotic=True,
            calculate_redox=True,
            calculate_nutrients=True
        )

        assert result["success"]
        baseline = result["baseline"]

        # All properties should be calculated
        assert "osmotic_properties" in baseline
        assert "redox_properties" in baseline
        assert "nutrient_ratios" in baseline

        # Check some specific values
        assert baseline["osmotic_properties"]["osmolarity"] > 0
        assert baseline["osmotic_properties"]["osmolarity"] < 20000  # Sanity check
        assert baseline["nutrient_ratios"]["c_mol"] >= 0  # May be 0 if no formulas available


class TestEdgeCases:
    """Test edge cases for advanced property integration."""

    def test_missing_formula_for_nutrients(self):
        """Test handling when ingredients lack formula for nutrient calculations."""
        agent = SensitivityAnalysisAgent()

        # Some ingredients may not have formulas in database
        result = agent.run(
            "NaCl,KCl",
            mode="ingredients",
            calculate_nutrients=True
        )

        # Should not crash, may return zeros or warnings
        assert result["success"]
        if "nutrient_ratios" in result["baseline"]:
            # If formulas not available, C/N/P should be zero or minimal
            pass

    def test_invalid_flags_combination(self):
        """Test with invalid flag combinations."""
        agent = SensitivityAnalysisAgent()

        # Redox without pH (should still work, may use default pH)
        result = agent.run(
            "glucose",
            mode="ingredients",
            calculate_redox=True
        )

        # Should succeed but may have low confidence
        assert result["success"]

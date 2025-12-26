"""Tests for SensitivityAnalysisAgent."""

import pytest
from pathlib import Path
from typing import Dict, List

# Import will fail initially - that's expected for TDD
try:
    from microgrowagents.agents.sensitivity_analysis_agent import SensitivityAnalysisAgent
except ImportError:
    SensitivityAnalysisAgent = None


# Test data fixtures
TEST_INGREDIENTS = [
    {
        "name": "PIPES",
        "low_conc": 10.0,
        "default_conc": 30.0,
        "high_conc": 100.0,
        "unit": "mM",
        "pka": [6.76],
        "molecular_weight": 302.37,
        "formula": "C8H18N2O6S2"
    },
    {
        "name": "NaCl",
        "low_conc": 10.0,
        "default_conc": 100.0,
        "high_conc": 500.0,
        "unit": "mM",
        "pka": None,
        "molecular_weight": 58.44,
        "formula": "NaCl"
    },
    {
        "name": "K₂HPO₄",
        "low_conc": 0.1,
        "default_conc": 1.45,
        "high_conc": 100.0,
        "unit": "mM",
        "pka": [2.15, 7.20, 12.35],
        "molecular_weight": 174.18,
        "formula": "K2HPO4"
    }
]

# Expected values for validation (approximate)
EXPECTED_BASELINE = {
    "ph": 7.0,  # Approximate, ±0.5
    "salinity": 7.0,  # Approximate total dissolved solids in g/L
    "ionic_strength": 0.1,  # Approximate
    "volume_ml": 1000.0,
}


@pytest.fixture
def test_ingredients():
    """Sample ingredient data for testing."""
    return TEST_INGREDIENTS.copy()


@pytest.fixture
def sensitivity_agent(tmp_path):
    """SensitivityAnalysisAgent for testing with temp database."""
    if SensitivityAnalysisAgent is None:
        pytest.skip("SensitivityAnalysisAgent not yet implemented")

    # Use temporary database path for isolated testing
    db_path = tmp_path / "test_sensitivity.duckdb"
    return SensitivityAnalysisAgent(db_path=db_path)


class TestSensitivityAnalysisAgentInit:
    """Test SensitivityAnalysisAgent initialization."""

    def test_init_default(self):
        """Test default initialization."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        agent = SensitivityAnalysisAgent()
        assert agent.db_path is not None
        assert hasattr(agent, 'sql_agent')
        assert hasattr(agent, 'ph_calculator')

    def test_init_with_db_path(self, tmp_path):
        """Test initialization with custom db_path."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        db_path = tmp_path / "custom.duckdb"
        agent = SensitivityAnalysisAgent(db_path=db_path)
        assert agent.db_path == db_path

    def test_init_with_chebi_owl(self, tmp_path):
        """Test initialization with ChEBI OWL file."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        db_path = tmp_path / "test.duckdb"
        chebi_path = tmp_path / "chebi.owl"
        chebi_path.touch()  # Create empty file for testing

        agent = SensitivityAnalysisAgent(db_path=db_path, chebi_owl_file=chebi_path)
        assert agent.chebi_owl_file == chebi_path


class TestGetIngredientData:
    """Test ingredient data retrieval."""

    def test_get_ingredient_data_with_list(self, sensitivity_agent, test_ingredients):
        """Test _get_ingredient_data with pre-provided list."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        # Directly provide ingredient data for testing
        result = sensitivity_agent._get_ingredient_data_from_list(test_ingredients)

        assert len(result) == 3
        assert all("name" in ing for ing in result)
        assert all("low_conc" in ing for ing in result)
        assert all("default_conc" in ing for ing in result)
        assert all("high_conc" in ing for ing in result)
        assert all("unit" in ing for ing in result)

    def test_ingredient_data_has_required_fields(self, sensitivity_agent, test_ingredients):
        """Test that ingredient data has all required fields."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        result = sensitivity_agent._get_ingredient_data_from_list(test_ingredients)

        required_fields = ["name", "low_conc", "default_conc", "high_conc", "unit", "molecular_weight"]
        for ing in result:
            for field in required_fields:
                assert field in ing, f"Missing field {field} in ingredient"

    def test_ingredient_data_validates_ranges(self, sensitivity_agent):
        """Test that ingredient concentration ranges are valid (low < default < high)."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        test_data = [
            {
                "name": "TestCompound",
                "low_conc": 1.0,
                "default_conc": 10.0,
                "high_conc": 100.0,
                "unit": "mM",
                "molecular_weight": 100.0
            }
        ]

        result = sensitivity_agent._get_ingredient_data_from_list(test_data)

        for ing in result:
            assert ing["low_conc"] <= ing["default_conc"], "Low should be <= default"
            assert ing["default_conc"] <= ing["high_conc"], "Default should be <= high"


class TestCalculateBaseline:
    """Test baseline calculation with all ingredients at DEFAULT."""

    def test_calculate_baseline_basic(self, sensitivity_agent, test_ingredients):
        """Test baseline calculation returns required fields."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        baseline = sensitivity_agent._calculate_baseline(test_ingredients, 1000.0)

        assert "ph" in baseline
        assert "salinity" in baseline
        assert "ionic_strength" in baseline
        assert "volume_ml" in baseline
        assert baseline["volume_ml"] == 1000.0

    def test_baseline_ph_in_valid_range(self, sensitivity_agent, test_ingredients):
        """Test that baseline pH is in valid range."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        baseline = sensitivity_agent._calculate_baseline(test_ingredients, 1000.0)

        assert 2.0 <= baseline["ph"] <= 12.0, f"pH {baseline['ph']} out of valid range"
        # For our test formulation with PIPES buffer, expect pH around 6-8
        assert 6.0 <= baseline["ph"] <= 8.0, f"pH {baseline['ph']} unexpected for PIPES buffer"

    def test_baseline_salinity_positive(self, sensitivity_agent, test_ingredients):
        """Test that baseline salinity is positive."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        baseline = sensitivity_agent._calculate_baseline(test_ingredients, 1000.0)

        assert baseline["salinity"] > 0, "Salinity should be positive"
        # Rough check: 3 ingredients at mM concentrations should give a few g/L
        assert baseline["salinity"] < 100, "Salinity seems too high"

    def test_baseline_with_different_volumes(self, sensitivity_agent, test_ingredients):
        """Test baseline calculation with different volumes."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        baseline_1000 = sensitivity_agent._calculate_baseline(test_ingredients, 1000.0)
        baseline_500 = sensitivity_agent._calculate_baseline(test_ingredients, 500.0)

        assert baseline_1000["volume_ml"] == 1000.0
        assert baseline_500["volume_ml"] == 500.0
        # pH should be similar regardless of volume (intensive property)
        assert abs(baseline_1000["ph"] - baseline_500["ph"]) < 0.5


class TestVolumeCalculations:
    """Test volume calculation logic."""

    def test_volume_totals_1000ml(self, sensitivity_agent, test_ingredients):
        """Test that total volume equals 1000ml."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        baseline = sensitivity_agent._calculate_baseline(test_ingredients, 1000.0)

        assert baseline["volume_ml"] == pytest.approx(1000.0, abs=0.1)

    def test_ingredient_volumes_calculated(self, sensitivity_agent, test_ingredients):
        """Test that ingredient volumes are calculated."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        baseline = sensitivity_agent._calculate_baseline(test_ingredients, 1000.0)

        # Should have formulation details
        assert "formulation" in baseline
        # Total ingredient volume should be small compared to 1000ml
        # (concentrations are in mM, so mass is small)
        assert baseline.get("ingredient_volume_ml", 0) < 50  # Should be < 5% of total


class TestPerformSensitivitySweep:
    """Test sensitivity sweep functionality."""

    def test_sweep_returns_correct_number_of_results(self, sensitivity_agent, test_ingredients):
        """Test that sweep returns low and high for each ingredient."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        results = sensitivity_agent._perform_sensitivity_sweep(test_ingredients, 1000.0)

        # Should have 2 results per ingredient (low + high)
        expected_count = 2 * len(test_ingredients)
        assert len(results) == expected_count

    def test_sweep_results_have_required_fields(self, sensitivity_agent, test_ingredients):
        """Test that each sweep result has required fields."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        results = sensitivity_agent._perform_sensitivity_sweep(test_ingredients, 1000.0)

        required_fields = [
            "ingredient", "concentration_level", "concentration_value",
            "unit", "ph", "salinity", "delta_ph", "delta_salinity"
        ]

        for result in results:
            for field in required_fields:
                assert field in result, f"Missing field {field}"

    def test_sweep_concentration_levels_correct(self, sensitivity_agent, test_ingredients):
        """Test that concentration levels are 'low' or 'high'."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        results = sensitivity_agent._perform_sensitivity_sweep(test_ingredients, 1000.0)

        for result in results:
            assert result["concentration_level"] in ["low", "high"]

    def test_sweep_delta_calculations(self, sensitivity_agent, test_ingredients):
        """Test that delta calculations are present and reasonable."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        results = sensitivity_agent._perform_sensitivity_sweep(test_ingredients, 1000.0)

        for result in results:
            # Deltas should be numeric
            assert isinstance(result["delta_ph"], (int, float))
            assert isinstance(result["delta_salinity"], (int, float))

            # pH delta should be reasonable (within ±5 pH units)
            assert abs(result["delta_ph"]) < 5.0


class TestRunMethodIntegration:
    """Test complete run() method integration."""

    def test_run_with_ingredient_list(self, sensitivity_agent):
        """Test run with comma-separated ingredient list."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        # This will require mocked database or test data
        # For now, test the structure
        result = sensitivity_agent.run(
            query="PIPES,NaCl,K2HPO4",
            mode="ingredients",
            volume_ml=1000.0
        )

        assert "success" in result
        if result["success"]:
            assert "data" in result
            assert "baseline" in result
            assert "summary" in result
            assert "metadata" in result

    def test_run_returns_proper_structure(self, sensitivity_agent):
        """Test that run() returns properly structured result."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        result = sensitivity_agent.run(
            query="PIPES,NaCl",
            mode="ingredients"
        )

        assert isinstance(result, dict)
        assert "success" in result
        assert isinstance(result["success"], bool)

    def test_run_error_handling(self, sensitivity_agent):
        """Test that run() handles errors gracefully."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        # Test with empty query
        result = sensitivity_agent.run(query="", mode="ingredients")

        # Should return error structure
        assert "success" in result
        if not result["success"]:
            assert "error" in result


class TestOutputFormatting:
    """Test output formatting functions."""

    def test_format_results_json(self, sensitivity_agent, test_ingredients):
        """Test JSON formatting."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        # Create mock results
        results = [
            {
                "ingredient": "PIPES",
                "concentration_level": "low",
                "concentration_value": 10.0,
                "unit": "mM",
                "ph": 6.5,
                "salinity": 1.0,
                "delta_ph": -0.5,
                "delta_salinity": -1.0
            }
        ]

        baseline = {"ph": 7.0, "salinity": 2.0}

        formatted = sensitivity_agent._format_results(
            results, baseline, output_format="json"
        )

        # Should be a string or dict
        assert formatted is not None

    def test_format_results_table(self, sensitivity_agent, test_ingredients):
        """Test table formatting."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        results = [
            {
                "ingredient": "PIPES",
                "concentration_level": "low",
                "ph": 6.5,
                "salinity": 1.0
            }
        ]

        baseline = {"ph": 7.0, "salinity": 2.0}

        formatted = sensitivity_agent._format_results(
            results, baseline, output_format="table"
        )

        # Should return something formatted
        assert formatted is not None


class TestSummaryStatistics:
    """Test summary statistics generation."""

    def test_summary_includes_ranges(self, sensitivity_agent, test_ingredients):
        """Test that summary includes pH and salinity ranges."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        result = sensitivity_agent.run(
            query="PIPES,NaCl",
            mode="ingredients"
        )

        if result["success"]:
            summary = result["summary"]
            assert "ph_range" in summary
            assert "salinity_range" in summary
            assert len(summary["ph_range"]) == 2  # [min, max]
            assert len(summary["salinity_range"]) == 2  # [min, max]

    def test_summary_identifies_most_sensitive(self, sensitivity_agent, test_ingredients):
        """Test that summary identifies most sensitive ingredients."""
        if SensitivityAnalysisAgent is None:
            pytest.skip("SensitivityAnalysisAgent not yet implemented")

        result = sensitivity_agent.run(
            query="PIPES,NaCl",
            mode="ingredients"
        )

        if result["success"]:
            summary = result["summary"]
            assert "most_sensitive_ph" in summary
            assert "most_sensitive_salinity" in summary

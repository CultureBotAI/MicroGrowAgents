"""Tests for ChemistryAgent."""

import pytest
from pathlib import Path

from microgrowagents.agents.chemistry_agent import ChemistryAgent


@pytest.fixture
def chemistry_agent():
    """Chemistry agent for testing."""
    return ChemistryAgent()


@pytest.fixture
def sample_owl_file():
    """Path to sample ChEBI OWL file."""
    return Path(__file__).parent.parent / "fixtures" / "chebi_sample.owl"


class TestChemistryAgentInit:
    """Test ChemistryAgent initialization."""

    def test_init_default(self):
        """Test default initialization."""
        agent = ChemistryAgent()
        assert agent.pubchem_client is not None
        assert agent.chebi_client is None  # Requires OWL file

    def test_init_with_chebi_owl(self, sample_owl_file):
        """Test initialization with ChEBI OWL file."""
        agent = ChemistryAgent(chebi_owl_file=sample_owl_file)
        assert agent.chebi_client is not None


class TestCompoundLookup:
    """Test compound information lookup."""

    def test_lookup_compound_pubchem(self, chemistry_agent):
        """Test PubChem compound lookup."""
        # Note: This requires internet connection
        result = chemistry_agent.run("lookup glucose", source="pubchem")

        assert result["success"] is True
        assert "data" in result
        assert "molecular_weight" in result["data"]

    def test_lookup_compound_chebi(self, sample_owl_file):
        """Test ChEBI compound lookup."""
        agent = ChemistryAgent(chebi_owl_file=sample_owl_file)
        result = agent.run("lookup glucose", source="chebi")

        assert result["success"] is True
        assert "data" in result
        assert result["data"]["chebi_id"] == "CHEBI:17234"

    def test_lookup_compound_unknown(self, chemistry_agent):
        """Test lookup of unknown compound."""
        result = chemistry_agent.run("lookup xyz_unknown_compound_123", source="pubchem")

        # Should handle gracefully
        assert "success" in result


class TestMolecularWeightCalculation:
    """Test molecular weight calculations."""

    def test_calculate_mw_simple(self, chemistry_agent):
        """Test MW calculation for simple formula."""
        result = chemistry_agent.run("calculate_mw H2O")

        assert result["success"] is True
        assert result["data"]["molecular_weight"] == pytest.approx(18.015, abs=0.01)
        assert result["data"]["formula"] == "H2O"

    def test_calculate_mw_with_hydrate(self, chemistry_agent):
        """Test MW calculation with hydration."""
        result = chemistry_agent.run("calculate_mw CaCl2 2")  # CaCl2·2H2O

        assert result["success"] is True
        # CaCl2 (110.98) + 2*H2O (2*18.015) = 147.01
        assert result["data"]["molecular_weight"] == pytest.approx(147.01, abs=0.1)

    def test_calculate_mw_complex_formula(self, chemistry_agent):
        """Test MW calculation for complex formula."""
        result = chemistry_agent.run("calculate_mw Ca(OH)2")

        assert result["success"] is True
        # Should parse parentheses correctly
        assert result["data"]["molecular_weight"] > 0


class TestPhCalculations:
    """Test pH calculations."""

    def test_calculate_ph_single_buffer(self, chemistry_agent):
        """Test pH calculation for single buffer."""
        ingredients = [
            {"name": "phosphate", "concentration": 0.05, "pka": [2.15, 7.20, 12.35]}
        ]

        result = chemistry_agent.run("calculate_ph", ingredients=ingredients)

        assert result["success"] is True
        assert "ph" in result["data"]
        assert "ionic_strength" in result["data"]
        assert "buffer_capacity" in result["data"]

    def test_calculate_ph_multiple_components(self, chemistry_agent):
        """Test pH calculation for mixture."""
        ingredients = [
            {"name": "tris", "concentration": 0.1, "pka": [8.06]},
            {"name": "NaCl", "concentration": 0.15, "charge": 1},
        ]

        result = chemistry_agent.run("calculate_ph", ingredients=ingredients)

        assert result["success"] is True
        assert result["data"]["ph"] > 7  # Tris is a base

    def test_calculate_ionic_strength(self, chemistry_agent):
        """Test ionic strength calculation."""
        ingredients = [
            {"concentration": 0.15, "charge": 1},  # Na+
            {"concentration": 0.15, "charge": -1},  # Cl-
        ]

        result = chemistry_agent.run("calculate_ionic_strength", ingredients=ingredients)

        assert result["success"] is True
        assert result["data"]["ionic_strength"] == pytest.approx(0.15, abs=0.01)


class TestMediaComparison:
    """Test media comparison functionality."""

    def test_compare_media(self, chemistry_agent):
        """Test media comparison."""
        media1 = [
            {"name": "glucose", "concentration": 0.1, "pka": [12.3]},
            {"name": "NaCl", "concentration": 0.15, "charge": 1},
        ]

        media2 = [
            {"name": "glucose", "concentration": 0.05, "pka": [12.3]},
            {"name": "KCl", "concentration": 0.15, "charge": 1},
        ]

        result = chemistry_agent.run("compare_media", media1=media1, media2=media2)

        assert result["success"] is True
        assert "unique_to_media1" in result["data"]
        assert "unique_to_media2" in result["data"]
        assert "concentration_differences" in result["data"]

    def test_compare_identical_media(self, chemistry_agent):
        """Test comparison of identical media."""
        media = [{"name": "glucose", "concentration": 0.1}]

        result = chemistry_agent.run("compare_media", media1=media, media2=media)

        assert result["success"] is True
        assert result["data"]["ph_diff"] == 0.0
        assert len(result["data"]["unique_to_media1"]) == 0


class TestCompoundAnalysis:
    """Test comprehensive compound analysis."""

    def test_analyze_compound_local(self, chemistry_agent):
        """Test analysis with local data only."""
        result = chemistry_agent.run("analyze NaCl")

        assert result["success"] is True
        assert "molecular_weight" in result["data"]

    def test_analyze_compound_with_apis(self, sample_owl_file):
        """Test analysis with API integration."""
        agent = ChemistryAgent(chebi_owl_file=sample_owl_file)
        result = agent.run("analyze glucose")

        assert result["success"] is True
        # Should have ChEBI data
        if "chebi_id" in result["data"]:
            assert result["data"]["chebi_id"] == "CHEBI:17234"


class TestPkaEstimation:
    """Test pKa estimation."""

    def test_estimate_pka_known_compound(self, chemistry_agent):
        """Test pKa estimation for known compound."""
        result = chemistry_agent.run("estimate_pka phosphate")

        assert result["success"] is True
        assert "pka_values" in result["data"]
        # Phosphate has 3 pKa values
        assert len(result["data"]["pka_values"]) == 3

    def test_estimate_pka_unknown_compound(self, chemistry_agent):
        """Test pKa estimation for unknown compound."""
        result = chemistry_agent.run("estimate_pka unknown_xyz")

        assert result["success"] is True
        # Should return None or empty list for unknown
        if result["data"]["pka_values"]:
            assert isinstance(result["data"]["pka_values"], list)


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_command(self, chemistry_agent):
        """Test with invalid command."""
        result = chemistry_agent.run("invalid_command_xyz")

        assert result["success"] is False
        assert "error" in result

    def test_missing_required_parameters(self, chemistry_agent):
        """Test with missing required parameters."""
        result = chemistry_agent.run("calculate_ph")  # Missing ingredients

        assert result["success"] is False
        assert "error" in result

    def test_invalid_formula(self, chemistry_agent):
        """Test MW calculation with invalid formula."""
        result = chemistry_agent.run("calculate_mw XYZ999")

        # Should handle gracefully
        assert "success" in result


class TestRunMethod:
    """Test the main run() method routing."""

    def test_run_with_operation_parameter(self, chemistry_agent):
        """Test run with explicit operation parameter."""
        result = chemistry_agent.run(
            "", operation="calculate_mw", formula="NaCl"
        )

        assert result["success"] is True
        assert result["data"]["molecular_weight"] == pytest.approx(58.44, abs=0.1)

    def test_run_parses_query_string(self, chemistry_agent):
        """Test that run() parses query strings."""
        result = chemistry_agent.run("calculate_mw H2O")

        assert result["success"] is True
        # Should extract operation and parameters from query


class TestIntegration:
    """Integration tests across multiple chemistry modules."""

    def test_full_compound_workflow(self, sample_owl_file):
        """Test complete compound analysis workflow."""
        agent = ChemistryAgent(chebi_owl_file=sample_owl_file)

        # 1. Look up compound in ChEBI
        chebi_result = agent.run("lookup glucose", source="chebi")
        assert chebi_result["success"] is True

        # 2. Calculate molecular weight
        mw_result = agent.run("calculate_mw C6H12O6")
        assert mw_result["success"] is True

        # 3. Estimate pKa
        pka_result = agent.run("estimate_pka glucose")
        assert pka_result["success"] is True

    def test_media_formulation_analysis(self, chemistry_agent):
        """Test analyzing a complete media formulation."""
        ingredients = [
            {"name": "glucose", "concentration": 0.1, "pka": [12.3]},
            {"name": "tris", "concentration": 0.05, "pka": [8.06]},
            {"name": "NaCl", "concentration": 0.15, "charge": 1},
            {"name": "MgSO4", "concentration": 0.002, "charge": 2},
        ]

        result = chemistry_agent.run("calculate_ph", ingredients=ingredients)

        assert result["success"] is True
        assert 7.0 < result["data"]["ph"] < 9.0  # Should be buffered by Tris
        assert result["data"]["ionic_strength"] > 0

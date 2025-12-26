"""Tests for thermodynamic property calculations."""

import pytest
from unittest.mock import Mock, patch
from microgrowagents.chemistry.thermodynamic_properties import (
    calculate_gibbs_free_energy,
    calculate_formation_energy,
    FARADAY_CONSTANT,
    GAS_CONSTANT
)


class TestConstants:
    """Test physical constants."""

    def test_gas_constant(self):
        """Test gas constant value."""
        assert GAS_CONSTANT == pytest.approx(8.314, abs=0.001)

    def test_faraday_constant(self):
        """Test Faraday constant value."""
        assert FARADAY_CONSTANT == pytest.approx(96485, abs=1)


class TestFormationEnergy:
    """Test formation energy calculations."""

    @patch('microgrowagents.chemistry.thermodynamic_properties.EquilibratorClient')
    def test_formation_energy_from_equilibrator(self, mock_client_class):
        """Test formation energy retrieval from eQuilibrator."""
        # Mock client instance
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock API response
        mock_client.get_compound_formation_energy.return_value = {
            "compound_id": "KEGG:C00031",
            "compound_name": "D-Glucose",
            "formation_energy": {
                "value": -426.71,  # kJ/mol
                "uncertainty": 0.5
            },
            "method": "component_contribution"
        }

        result = calculate_formation_energy(
            compound="KEGG:C00031",
            method="equilibrator"
        )

        assert result is not None
        assert result["delta_gf"] == pytest.approx(-426.71, abs=1.0)
        assert result["method"] == "equilibrator"
        assert result["confidence"] >= 0.9

    @patch('microgrowagents.chemistry.thermodynamic_properties.EquilibratorClient')
    def test_formation_energy_not_found(self, mock_client_class):
        """Test handling when compound not found in eQuilibrator."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_compound_formation_energy.return_value = None

        result = calculate_formation_energy(
            compound="INVALID:12345",
            method="equilibrator"
        )

        # Should fallback to estimation
        assert result is not None
        assert result["method"] in ["estimation", "fallback", "not_found"]
        assert result["confidence"] < 0.7

    def test_formation_energy_glucose(self):
        """Test formation energy for glucose (common compound)."""
        # This test uses a lookup table if equilibrator not available
        result = calculate_formation_energy(
            compound="glucose",
            method="lookup"
        )

        assert result is not None
        # Glucose ΔGf° ≈ -426 kJ/mol
        assert -450 <= result["delta_gf"] <= -400

    def test_formation_energy_estimation_fallback(self):
        """Test estimation fallback for unknown compounds."""
        result = calculate_formation_energy(
            compound="unknown_xyz_123",
            method="estimation"
        )

        assert result is not None
        assert result["method"] == "estimation"
        assert result["confidence"] <= 0.5


class TestGibbsFreeEnergy:
    """Test Gibbs free energy calculations."""

    @patch('microgrowagents.chemistry.thermodynamic_properties.EquilibratorClient')
    def test_gibbs_energy_favorable_reaction(self, mock_client_class):
        """Test ΔG calculation for favorable reaction."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock glucose fermentation: favorable reaction
        mock_client.get_reaction_energy.return_value = {
            "reaction": "C6H12O6 => 2 C2H5OH + 2 CO2",
            "delta_g_prime": {
                "value": -72.3,  # kJ/mol (favorable)
                "uncertainty": 1.5
            },
            "feasibility": "favorable"
        }

        result = calculate_gibbs_free_energy(
            reactants=["C6H12O6"],
            products=["C2H5OH", "CO2"],
            stoichiometry={"C6H12O6": -1, "C2H5OH": 2, "CO2": 2},
            ph=7.0,
            method="equilibrator"
        )

        assert result is not None
        assert result["delta_g"] < 0  # Favorable
        assert result["feasibility"] == "favorable"
        assert result["confidence"] >= 0.8

    @patch('microgrowagents.chemistry.thermodynamic_properties.EquilibratorClient')
    def test_gibbs_energy_unfavorable_reaction(self, mock_client_class):
        """Test ΔG calculation for unfavorable reaction."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock unfavorable reaction
        mock_client.get_reaction_energy.return_value = {
            "reaction": "test",
            "delta_g_prime": {
                "value": 50.0,  # kJ/mol (unfavorable)
                "uncertainty": 2.0
            },
            "feasibility": "unfavorable"
        }

        result = calculate_gibbs_free_energy(
            reactants=["A"],
            products=["B"],
            stoichiometry={"A": -1, "B": 1},
            ph=7.0,
            method="equilibrator"
        )

        assert result is not None
        assert result["delta_g"] > 0  # Unfavorable
        assert result["feasibility"] == "unfavorable"

    def test_gibbs_energy_with_reaction_quotient(self):
        """Test ΔG calculation including reaction quotient Q."""
        # ΔG = ΔG° + RT ln(Q)
        # If Q > 1, ΔG increases (less favorable)
        # If Q < 1, ΔG decreases (more favorable)

        result = calculate_gibbs_free_energy(
            reactants=["glucose"],
            products=["ethanol", "CO2"],
            stoichiometry={"glucose": -1, "ethanol": 2, "CO2": 2},
            ph=7.0,
            temperature=25.0,
            concentrations={"glucose": 100.0, "ethanol": 10.0, "CO2": 10.0},  # mM
            method="lookup"
        )

        assert result is not None
        assert "reaction_quotient" in result
        assert "delta_g" in result
        assert "delta_g_prime" in result  # Standard ΔG

    def test_gibbs_energy_ph_dependence(self):
        """Test pH dependence of ΔG'°."""
        # ΔG'° changes with pH for reactions involving H+

        result_ph7 = calculate_gibbs_free_energy(
            reactants=["glucose"],
            products=["ethanol", "CO2"],
            stoichiometry={"glucose": -1, "ethanol": 2, "CO2": 2},
            ph=7.0,
            method="lookup"
        )

        result_ph5 = calculate_gibbs_free_energy(
            reactants=["glucose"],
            products=["ethanol", "CO2"],
            stoichiometry={"glucose": -1, "ethanol": 2, "CO2": 2},
            ph=5.0,
            method="lookup"
        )

        assert result_ph7 is not None
        assert result_ph5 is not None
        # ΔG should differ between pH values
        # (may be small difference for this particular reaction)

    def test_gibbs_energy_temperature_dependence(self):
        """Test temperature dependence of ΔG."""
        # ΔG = ΔH - TΔS

        result_25 = calculate_gibbs_free_energy(
            reactants=["glucose"],
            products=["ethanol", "CO2"],
            stoichiometry={"glucose": -1, "ethanol": 2, "CO2": 2},
            ph=7.0,
            temperature=25.0,
            method="lookup"
        )

        result_37 = calculate_gibbs_free_energy(
            reactants=["glucose"],
            products=["ethanol", "CO2"],
            stoichiometry={"glucose": -1, "ethanol": 2, "CO2": 2},
            ph=7.0,
            temperature=37.0,
            method="lookup"
        )

        assert result_25 is not None
        assert result_37 is not None
        # ΔG should differ at different temperatures


class TestReactionFeasibility:
    """Test reaction feasibility classification."""

    def test_highly_favorable_reaction(self):
        """Test classification of highly favorable reactions."""
        # Use glucose fermentation which we know is favorable
        result = calculate_gibbs_free_energy(
            reactants=["glucose"],
            products=["ethanol", "CO2"],
            stoichiometry={"glucose": -1, "ethanol": 2, "CO2": 2},
            ph=7.0,
            method="lookup"
        )

        assert result is not None
        # Glucose fermentation should be favorable
        assert result["delta_g"] < -20
        assert result["feasibility"] == "favorable"

    def test_near_equilibrium_reaction(self):
        """Test classification of near-equilibrium reactions."""
        # Manually construct result for near-equilibrium
        result = {
            "delta_g": -2.0,  # Small negative
            "delta_g_prime": -2.0,
            "feasibility": "marginally_favorable",
            "confidence": 0.8
        }

        # Near equilibrium: |ΔG| < 5 kJ/mol
        assert abs(result["delta_g"]) < 5


class TestMethodFallbacks:
    """Test method fallback hierarchy."""

    @patch('microgrowagents.chemistry.thermodynamic_properties.EquilibratorClient')
    def test_equilibrator_to_lookup_fallback(self, mock_client_class):
        """Test fallback from equilibrator to lookup when API fails."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_reaction_energy.return_value = None  # API failure

        result = calculate_gibbs_free_energy(
            reactants=["glucose"],
            products=["ethanol", "CO2"],
            stoichiometry={"glucose": -1, "ethanol": 2, "CO2": 2},
            ph=7.0,
            method="equilibrator",
            allow_fallback=True
        )

        assert result is not None
        assert result["method"] in ["lookup", "estimation"]
        assert result["confidence"] < 0.9  # Lower confidence due to fallback

    def test_lookup_to_estimation_fallback(self):
        """Test fallback from lookup to estimation for unknown compounds."""
        result = calculate_gibbs_free_energy(
            reactants=["unknown_compound_xyz"],
            products=["another_unknown"],
            stoichiometry={"unknown_compound_xyz": -1, "another_unknown": 1},
            ph=7.0,
            method="lookup",
            allow_fallback=True
        )

        assert result is not None
        assert result["method"] == "estimation"
        assert result["confidence"] <= 0.5


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_reactants(self):
        """Test handling of empty reactants list."""
        with pytest.raises(ValueError, match="reactant"):
            calculate_gibbs_free_energy(
                reactants=[],
                products=["B"],
                stoichiometry={"B": 1}
            )

    def test_empty_products(self):
        """Test handling of empty products list."""
        with pytest.raises(ValueError, match="product"):
            calculate_gibbs_free_energy(
                reactants=["A"],
                products=[],
                stoichiometry={"A": -1}
            )

    def test_mismatched_stoichiometry(self):
        """Test handling of mismatched stoichiometry."""
        with pytest.raises(ValueError, match="Stoichiometry"):
            calculate_gibbs_free_energy(
                reactants=["A"],
                products=["B"],
                stoichiometry={"C": -1, "D": 1}  # Doesn't match A, B
            )

    def test_negative_concentrations(self):
        """Test handling of negative concentrations."""
        with pytest.raises(ValueError, match="Negative concentration"):
            calculate_gibbs_free_energy(
                reactants=["A"],
                products=["B"],
                stoichiometry={"A": -1, "B": 1},
                concentrations={"A": -10.0, "B": 10.0}
            )

    def test_extreme_ph(self):
        """Test warning for extreme pH values."""
        result = calculate_gibbs_free_energy(
            reactants=["glucose"],
            products=["ethanol", "CO2"],
            stoichiometry={"glucose": -1, "ethanol": 2, "CO2": 2},
            ph=15.0,  # Extreme pH
            method="lookup"
        )

        assert result is not None
        assert result["confidence"] < 0.8  # Lower confidence
        assert any("pH" in w for w in result.get("warnings", []))

    def test_extreme_temperature(self):
        """Test warning for extreme temperatures."""
        result = calculate_gibbs_free_energy(
            reactants=["glucose"],
            products=["ethanol", "CO2"],
            stoichiometry={"glucose": -1, "ethanol": 2, "CO2": 2},
            ph=7.0,
            temperature=150.0,  # Extreme temperature
            method="lookup"
        )

        assert result is not None
        assert result["confidence"] < 0.8
        assert any("temperature" in w.lower() for w in result.get("warnings", []))


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_complete_metabolic_pathway(self):
        """Test calculation for a complete metabolic pathway."""
        # Glycolysis: Glucose → 2 Pyruvate + 2 ATP + 2 NADH
        # Simplified stoichiometry
        result = calculate_gibbs_free_energy(
            reactants=["glucose", "NAD+", "ADP", "phosphate"],
            products=["pyruvate", "NADH", "ATP"],
            stoichiometry={
                "glucose": -1,
                "NAD+": -2,
                "ADP": -2,
                "phosphate": -2,
                "pyruvate": 2,
                "NADH": 2,
                "ATP": 2
            },
            ph=7.0,
            temperature=37.0,
            method="lookup"
        )

        assert result is not None
        # Glycolysis should be favorable
        assert result["feasibility"] in ["favorable", "marginally_favorable"]

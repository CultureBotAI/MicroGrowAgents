"""Tests for redox property calculations."""

import pytest
from microgrowagents.chemistry.redox_properties import (
    calculate_redox_potential,
    calculate_electron_balance,
    STANDARD_POTENTIALS,
    FARADAY_CONSTANT,
    GAS_CONSTANT
)


class TestConstants:
    """Test physical constants and database."""

    def test_gas_constant(self):
        """Test gas constant value."""
        assert GAS_CONSTANT == pytest.approx(8.314, abs=0.001)

    def test_faraday_constant(self):
        """Test Faraday constant value."""
        assert FARADAY_CONSTANT == pytest.approx(96485, abs=1)

    def test_standard_potentials_database(self):
        """Test standard potentials database exists and has key entries."""
        assert "O2/H2O" in STANDARD_POTENTIALS
        assert "NO3-/NO2-" in STANDARD_POTENTIALS
        assert "SO42-/H2S" in STANDARD_POTENTIALS

        # Check structure
        o2_entry = STANDARD_POTENTIALS["O2/H2O"]
        assert "e0" in o2_entry
        assert "n_electrons" in o2_entry
        assert "ph_dependent" in o2_entry

    def test_standard_potential_values(self):
        """Test standard potential values are reasonable."""
        # O2/H2O should be highly positive (oxidizing)
        assert STANDARD_POTENTIALS["O2/H2O"]["e0"] > 700

        # SO42-/H2S should be negative (reducing)
        assert STANDARD_POTENTIALS["SO42-/H2S"]["e0"] < 0


class TestRedoxPotential:
    """Test redox potential calculations."""

    def test_aerobic_conditions_high_eh(self):
        """Test high Eh under aerobic conditions."""
        result = calculate_redox_potential(
            ingredients=[
                {"name": "O2", "concentration": 8.0, "redox_couple": "O2/H2O"}  # Dissolved oxygen
            ],
            ph=7.0,
            temperature=25.0
        )

        assert result is not None
        # Aerobic: Eh should be positive and high
        assert result["eh"] > 200  # mV
        assert result["pe"] > 3
        assert result["redox_state"] == "oxidizing"

    def test_anaerobic_conditions_low_eh(self):
        """Test low Eh under anaerobic (sulfate-reducing) conditions."""
        result = calculate_redox_potential(
            ingredients=[
                {"name": "H2S", "concentration": 10.0, "redox_couple": "SO42-/H2S"}
            ],
            ph=7.0,
            temperature=25.0
        )

        assert result is not None
        # Anaerobic sulfate reduction: Eh should be negative
        assert result["eh"] < -150  # mV
        assert result["pe"] < -2
        assert result["redox_state"] == "reducing"

    def test_nitrate_reduction_intermediate_eh(self):
        """Test intermediate Eh for nitrate reduction."""
        result = calculate_redox_potential(
            ingredients=[
                {"name": "NO3-", "concentration": 20.0, "redox_couple": "NO3-/NO2-"}
            ],
            ph=7.0,
            temperature=25.0
        )

        assert result is not None
        # Nitrate reduction: intermediate Eh (lower than O2, higher than sulfate)
        assert 100 <= result["eh"] <= 500  # mV (relaxed lower bound)
        assert result["redox_state"] in ["oxidizing", "intermediate"]

    def test_ph_dependence(self):
        """Test pH dependence of redox potential."""
        # Eh decreases by ~59 mV / n_electrons per pH unit for H+-coupled reactions
        result_ph5 = calculate_redox_potential(
            ingredients=[{"name": "O2", "concentration": 8.0, "redox_couple": "O2/H2O"}],
            ph=5.0,
            temperature=25.0
        )

        result_ph9 = calculate_redox_potential(
            ingredients=[{"name": "O2", "concentration": 8.0, "redox_couple": "O2/H2O"}],
            ph=9.0,
            temperature=25.0
        )

        assert result_ph5 is not None
        assert result_ph9 is not None

        # pH 9 should have lower Eh than pH 5 (for pH-dependent couples)
        if STANDARD_POTENTIALS["O2/H2O"]["ph_dependent"]:
            assert result_ph9["eh"] < result_ph5["eh"]

            # O2/H2O has n=4, so slope is 59.16/4 = 14.79 mV/pH
            # 4 pH units → ~59 mV difference
            eh_diff = result_ph5["eh"] - result_ph9["eh"]
            assert 50 <= eh_diff <= 70

    def test_temperature_dependence(self):
        """Test temperature dependence of redox potential."""
        result_25 = calculate_redox_potential(
            ingredients=[{"name": "O2", "concentration": 8.0, "redox_couple": "O2/H2O"}],
            ph=7.0,
            temperature=25.0
        )

        result_37 = calculate_redox_potential(
            ingredients=[{"name": "O2", "concentration": 8.0, "redox_couple": "O2/H2O"}],
            ph=7.0,
            temperature=37.0
        )

        assert result_25 is not None
        assert result_37 is not None

        # Temperature affects Nernst equation (RT/nF term)
        # Higher temperature → different Eh, but effect is smaller than pH
        assert abs(result_37["eh"] - result_25["eh"]) < 50  # Should differ but not hugely

    def test_nernst_equation_concentration_effect(self):
        """Test Nernst equation concentration dependence."""
        # Higher oxidized form concentration → higher Eh
        result_low_o2 = calculate_redox_potential(
            ingredients=[{"name": "O2", "concentration": 1.0, "redox_couple": "O2/H2O"}],
            ph=7.0,
            temperature=25.0
        )

        result_high_o2 = calculate_redox_potential(
            ingredients=[{"name": "O2", "concentration": 10.0, "redox_couple": "O2/H2O"}],
            ph=7.0,
            temperature=25.0
        )

        assert result_low_o2 is not None
        assert result_high_o2 is not None

        # Higher O2 (oxidized form) → higher Eh
        assert result_high_o2["eh"] > result_low_o2["eh"]

    def test_multiple_redox_couples(self):
        """Test with multiple redox couples present."""
        result = calculate_redox_potential(
            ingredients=[
                {"name": "O2", "concentration": 2.0, "redox_couple": "O2/H2O"},
                {"name": "NO3-", "concentration": 10.0, "redox_couple": "NO3-/NO2-"}
            ],
            ph=7.0,
            temperature=25.0
        )

        assert result is not None
        assert "redox_couples" in result
        assert len(result["redox_couples"]) == 2

    def test_no_redox_couples(self):
        """Test handling when no redox couples present."""
        result = calculate_redox_potential(
            ingredients=[
                {"name": "glucose", "concentration": 100.0}  # No redox couple specified
            ],
            ph=7.0,
            temperature=25.0
        )

        # Should return a default or estimated Eh
        assert result is not None
        assert result["confidence"] < 0.5  # Low confidence without redox couples


class TestElectronBalance:
    """Test electron donor/acceptor balance calculations."""

    def test_aerobic_glucose_oxidation(self):
        """Test electron balance for aerobic glucose oxidation."""
        ingredients = [
            {"name": "glucose", "concentration": 10.0, "formula": "C6H12O6", "role": "electron_donor"},
            {"name": "O2", "concentration": 60.0, "formula": "O2", "role": "electron_acceptor"}
        ]

        result = calculate_electron_balance(ingredients)

        assert result is not None
        assert result["total_donors"] > 0
        assert result["total_acceptors"] > 0
        # Glucose oxidation requires 6 O2 per glucose
        # Balance should be close to stoichiometric
        assert abs(result["balance"]) < 50  # % deviation

    def test_anaerobic_fermentation(self):
        """Test electron balance for anaerobic fermentation."""
        ingredients = [
            {"name": "glucose", "concentration": 10.0, "formula": "C6H12O6", "role": "electron_donor"},
            # No external electron acceptor - glucose serves as both donor and acceptor
        ]

        result = calculate_electron_balance(ingredients)

        assert result is not None
        # In fermentation, internal balance (no external acceptors)
        assert result["total_donors"] > 0

    def test_nitrate_respiration(self):
        """Test electron balance for nitrate respiration."""
        ingredients = [
            {"name": "organic_carbon", "concentration": 10.0, "formula": "C6H12O6", "role": "electron_donor"},
            {"name": "NO3-", "concentration": 50.0, "formula": "NO3", "role": "electron_acceptor"}
        ]

        result = calculate_electron_balance(ingredients)

        assert result is not None
        assert result["total_donors"] > 0
        assert result["total_acceptors"] > 0

    def test_sulfate_reduction(self):
        """Test electron balance for sulfate reduction."""
        ingredients = [
            {"name": "lactate", "concentration": 10.0, "formula": "C3H6O3", "role": "electron_donor"},
            {"name": "SO42-", "concentration": 20.0, "formula": "SO4", "role": "electron_acceptor"}
        ]

        result = calculate_electron_balance(ingredients)

        assert result is not None
        assert result["total_donors"] > 0
        assert result["total_acceptors"] > 0

    def test_donor_acceptor_lists(self):
        """Test that donor and acceptor lists are populated."""
        ingredients = [
            {"name": "glucose", "concentration": 10.0, "formula": "C6H12O6", "role": "electron_donor"},
            {"name": "O2", "concentration": 60.0, "formula": "O2", "role": "electron_acceptor"},
            {"name": "NO3-", "concentration": 10.0, "formula": "NO3", "role": "electron_acceptor"}
        ]

        result = calculate_electron_balance(ingredients)

        assert result is not None
        assert len(result["donor_list"]) == 1
        assert len(result["acceptor_list"]) == 2

        # Check structure
        donor = result["donor_list"][0]
        assert "name" in donor
        assert "electrons" in donor

    def test_no_electron_transfer_compounds(self):
        """Test handling when no electron donors/acceptors present."""
        ingredients = [
            {"name": "buffer", "concentration": 10.0, "formula": "C8H18N2O4S"}  # HEPES
        ]

        result = calculate_electron_balance(ingredients)

        assert result is not None
        assert result["total_donors"] == 0
        assert result["total_acceptors"] == 0
        assert result["balance"] == 0


class TestRedoxStateClassification:
    """Test redox state classification."""

    def test_highly_oxidizing(self):
        """Test classification of highly oxidizing conditions."""
        result = calculate_redox_potential(
            ingredients=[{"name": "O2", "concentration": 10.0, "redox_couple": "O2/H2O"}],
            ph=7.0,
            temperature=25.0
        )

        assert result["redox_state"] == "oxidizing"
        assert result["eh"] > 300

    def test_highly_reducing(self):
        """Test classification of highly reducing conditions."""
        result = calculate_redox_potential(
            ingredients=[{"name": "H2S", "concentration": 10.0, "redox_couple": "SO42-/H2S"}],
            ph=7.0,
            temperature=25.0
        )

        assert result["redox_state"] == "reducing"
        assert result["eh"] < -100

    def test_intermediate_redox(self):
        """Test classification of intermediate redox conditions."""
        result = calculate_redox_potential(
            ingredients=[{"name": "NO3-", "concentration": 10.0, "redox_couple": "NO3-/NO2-"}],
            ph=7.0,
            temperature=25.0
        )

        # Nitrate reduction is oxidizing but less than O2
        assert result["redox_state"] in ["oxidizing", "intermediate"]


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_ingredients(self):
        """Test handling of empty ingredients list."""
        result = calculate_redox_potential(
            ingredients=[],
            ph=7.0,
            temperature=25.0
        )

        assert result is not None
        assert result["confidence"] < 0.5

    def test_extreme_ph(self):
        """Test handling of extreme pH values."""
        result = calculate_redox_potential(
            ingredients=[{"name": "O2", "concentration": 8.0, "redox_couple": "O2/H2O"}],
            ph=15.0,  # Extreme (beyond 14)
            temperature=25.0
        )

        assert result is not None
        assert len(result.get("warnings", [])) > 0
        assert result["confidence"] < 0.9

    def test_extreme_temperature(self):
        """Test handling of extreme temperatures."""
        result = calculate_redox_potential(
            ingredients=[{"name": "O2", "concentration": 8.0, "redox_couple": "O2/H2O"}],
            ph=7.0,
            temperature=95.0  # Near boiling
        )

        assert result is not None
        assert len(result.get("warnings", [])) > 0

    def test_negative_concentration(self):
        """Test handling of negative concentrations."""
        with pytest.raises(ValueError, match="concentration"):
            calculate_redox_potential(
                ingredients=[{"name": "O2", "concentration": -5.0, "redox_couple": "O2/H2O"}],
                ph=7.0,
                temperature=25.0
            )


class TestIntegration:
    """Integration tests combining redox potential and electron balance."""

    def test_complete_aerobic_system(self):
        """Test complete aerobic respiration system."""
        ingredients = [
            {"name": "glucose", "concentration": 10.0, "formula": "C6H12O6", "role": "electron_donor"},
            {"name": "O2", "concentration": 8.0, "formula": "O2", "role": "electron_acceptor", "redox_couple": "O2/H2O"}
        ]

        redox_result = calculate_redox_potential(ingredients, ph=7.0, temperature=37.0)
        balance_result = calculate_electron_balance(ingredients)

        assert redox_result is not None
        assert balance_result is not None

        # Aerobic conditions
        assert redox_result["eh"] > 200
        assert redox_result["redox_state"] == "oxidizing"

        # Balanced electron flow
        assert balance_result["total_donors"] > 0
        assert balance_result["total_acceptors"] > 0

    def test_complete_anaerobic_system(self):
        """Test complete anaerobic system with sulfate reduction."""
        ingredients = [
            {"name": "lactate", "concentration": 10.0, "formula": "C3H6O3", "role": "electron_donor"},
            {"name": "SO42-", "concentration": 20.0, "formula": "SO4", "role": "electron_acceptor", "redox_couple": "SO42-/H2S"}
        ]

        redox_result = calculate_redox_potential(ingredients, ph=7.0, temperature=30.0)
        balance_result = calculate_electron_balance(ingredients)

        assert redox_result is not None
        assert balance_result is not None

        # Anaerobic sulfate reduction
        assert redox_result["eh"] < 0
        assert redox_result["redox_state"] == "reducing"

        # Electron balance
        assert balance_result["total_donors"] > 0
        assert balance_result["total_acceptors"] > 0

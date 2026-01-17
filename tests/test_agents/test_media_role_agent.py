"""Test MediaRoleAgent class."""

import pytest
from pathlib import Path
import pandas as pd
import tempfile

from microgrowagents.agents.media_role_agent import MediaRoleAgent


class TestMediaRoleClassification:
    """Test media role classification patterns."""

    @pytest.fixture
    def agent(self):
        """Create MediaRoleAgent instance for testing."""
        return MediaRoleAgent()

    def test_rare_earth_element_dysprosium(self, agent):
        """Test rare earth element classification - dysprosium."""
        role, confidence = agent.infer_media_role("Dysprosium (III) chloride hexahydrate")
        assert role == "Rare Earth Element"
        assert confidence == "high"

    def test_rare_earth_element_neodymium(self, agent):
        """Test rare earth element classification - neodymium."""
        role, confidence = agent.infer_media_role("Neodymium (III) chloride hexahydrate")
        assert role == "Rare Earth Element"
        assert confidence == "high"

    def test_rare_earth_element_praseodymium(self, agent):
        """Test rare earth element classification - praseodymium."""
        role, confidence = agent.infer_media_role("Praseodymium (III) chloride hexahydrate")
        assert role == "Rare Earth Element"
        assert confidence == "high"

    def test_ph_buffer_pipes(self, agent):
        """Test pH buffer classification - PIPES."""
        role, confidence = agent.infer_media_role("PIPES")
        assert role == "pH Buffer"
        assert confidence == "high"

    def test_ph_buffer_hepes(self, agent):
        """Test pH buffer classification - HEPES."""
        role, confidence = agent.infer_media_role("HEPES")
        assert role == "pH Buffer"
        assert confidence == "high"

    def test_phosphate_source_k2hpo4(self, agent):
        """Test phosphate source - K2HPO4."""
        role, confidence = agent.infer_media_role("K₂HPO₄·3H₂O")
        assert role == "Phosphate Source; pH Buffer"
        assert confidence == "high"

    def test_phosphate_source_nah2po4(self, agent):
        """Test phosphate source - NaH2PO4."""
        role, confidence = agent.infer_media_role("NaH₂PO₄·H₂O")
        assert role == "Phosphate Source; pH Buffer"
        assert confidence == "high"

    def test_carbon_source_methanol(self, agent):
        """Test carbon source - methanol."""
        role, confidence = agent.infer_media_role("Methanol")
        assert role == "Carbon Source"
        assert confidence == "high"

    def test_carbon_source_glucose(self, agent):
        """Test carbon source - glucose."""
        role, confidence = agent.infer_media_role("Glucose")
        assert role == "Carbon Source"
        assert confidence == "high"

    def test_nitrogen_sulfur_source(self, agent):
        """Test nitrogen+sulfur dual source - ammonium sulfate."""
        role, confidence = agent.infer_media_role("(NH₄)₂SO₄")
        assert role == "Nitrogen Source; Sulfur Source"
        assert confidence == "high"

    def test_nitrogen_source_urea(self, agent):
        """Test nitrogen source - urea."""
        role, confidence = agent.infer_media_role("Urea")
        assert role == "Nitrogen Source"
        assert confidence == "high"

    def test_chelator_citrate(self, agent):
        """Test chelator - sodium citrate."""
        role, confidence = agent.infer_media_role("Sodium citrate")
        assert role == "Chelator; Metal Buffer"
        assert confidence == "high"

    def test_chelator_edta(self, agent):
        """Test chelator - EDTA."""
        role, confidence = agent.infer_media_role("EDTA")
        assert role == "Chelator; Metal Buffer"
        assert confidence == "high"

    def test_sulfur_source_cysteine(self, agent):
        """Test sulfur source - cysteine."""
        role, confidence = agent.infer_media_role("Cysteine")
        assert role == "Sulfur Source"
        assert confidence == "high"

    def test_essential_macronutrient_mg(self, agent):
        """Test essential macronutrient - magnesium."""
        role, confidence = agent.infer_media_role("MgCl₂·6H₂O")
        assert role == "Essential Macronutrient (Mg)"
        assert confidence == "high"

    def test_essential_macronutrient_ca(self, agent):
        """Test essential macronutrient - calcium."""
        role, confidence = agent.infer_media_role("CaCl₂·2H₂O")
        assert role == "Essential Macronutrient (Ca)"
        assert confidence == "high"

    def test_electrolyte_k(self, agent):
        """Test electrolyte - potassium chloride."""
        role, confidence = agent.infer_media_role("KCl")
        assert role == "Electrolyte (K)"
        assert confidence == "high"

    def test_electrolyte_na(self, agent):
        """Test electrolyte - sodium chloride."""
        role, confidence = agent.infer_media_role("NaCl")
        assert role == "Electrolyte (Na)"
        assert confidence == "high"

    def test_trace_element_fe(self, agent):
        """Test trace element - iron."""
        role, confidence = agent.infer_media_role("FeSO₄·7H₂O")
        assert role == "Trace Element (Fe)"
        assert confidence == "high"

    def test_trace_element_zn(self, agent):
        """Test trace element - zinc."""
        role, confidence = agent.infer_media_role("ZnSO₄·7H₂O")
        assert role == "Trace Element (Zn)"
        assert confidence == "high"

    def test_trace_element_mn(self, agent):
        """Test trace element - manganese."""
        role, confidence = agent.infer_media_role("MnCl₂·4H₂O")
        assert role == "Trace Element (Mn)"
        assert confidence == "high"

    def test_trace_element_cu(self, agent):
        """Test trace element - copper."""
        role, confidence = agent.infer_media_role("CuSO₄·5H₂O")
        assert role == "Trace Element (Cu)"
        assert confidence == "high"

    def test_trace_element_co(self, agent):
        """Test trace element - cobalt."""
        role, confidence = agent.infer_media_role("CoCl₂·6H₂O")
        assert role == "Trace Element (Co)"
        assert confidence == "high"

    def test_trace_element_mo(self, agent):
        """Test trace element - molybdenum."""
        role, confidence = agent.infer_media_role("(NH₄)₆Mo₇O₂₄·4H₂O")
        assert role == "Trace Element (Mo)"
        assert confidence == "high"

    def test_trace_element_w(self, agent):
        """Test trace element with cofactor - tungsten."""
        role, confidence = agent.infer_media_role("Na₂WO₄·2H₂O")
        assert role == "Trace Element (W); Cofactor"
        assert confidence == "high"

    def test_vitamin_thiamin(self, agent):
        """Test vitamin - thiamin."""
        role, confidence = agent.infer_media_role("Thiamin")
        assert role == "Vitamin/Cofactor Precursor"
        assert confidence == "high"

    def test_vitamin_biotin(self, agent):
        """Test vitamin - biotin."""
        role, confidence = agent.infer_media_role("Biotin")
        assert role == "Vitamin/Cofactor Precursor"
        assert confidence == "high"

    def test_unknown_compound(self, agent):
        """Test unknown compound classification."""
        role, confidence = agent.infer_media_role("XYZ123Unknown")
        assert role == "Unknown"
        assert confidence == "low"

    def test_metabolic_role_fallback_buffer(self, agent):
        """Test fallback to metabolic role - buffer."""
        role, confidence = agent.infer_media_role(
            "SomeCompound",
            metabolic_role="Non-metabolized pH buffer"
        )
        assert role == "pH Buffer"
        assert confidence == "medium"

    def test_metabolic_role_fallback_cofactor(self, agent):
        """Test fallback to metabolic role - cofactor."""
        role, confidence = agent.infer_media_role(
            "SomeCompound",
            metabolic_role="Enzyme cofactor for methyltransferases"
        )
        assert role == "Cofactor/Enzyme Activator"
        assert confidence == "medium"


class TestMediaRoleAgentQueryMode:
    """Test MediaRoleAgent query mode."""

    @pytest.fixture
    def agent(self):
        """Create MediaRoleAgent instance."""
        return MediaRoleAgent()

    def test_query_mode_single_ingredient(self, agent):
        """Test query mode with single ingredient."""
        result = agent.run("query", ingredient_name="FeSO₄·7H₂O")

        assert result["success"] is True
        assert "data" in result
        assert result["data"]["ingredient"] == "FeSO₄·7H₂O"
        assert result["data"]["media_role"] == "Trace Element (Fe)"
        assert result["data"]["confidence"] == "high"
        assert result["data"]["method"] == "pattern_match"

    def test_query_mode_with_metabolic_role(self, agent):
        """Test query mode with metabolic role provided."""
        result = agent.run(
            "query",
            ingredient_name="CustomBuffer",
            metabolic_role="Non-metabolized pH buffer"
        )

        assert result["success"] is True
        assert result["data"]["media_role"] == "pH Buffer"
        assert result["data"]["confidence"] == "medium"

    def test_query_mode_unknown_ingredient(self, agent):
        """Test query mode with unknown ingredient."""
        result = agent.run("query", ingredient_name="UnknownCompound123")

        assert result["success"] is True
        assert result["data"]["media_role"] == "Unknown"
        assert result["data"]["confidence"] == "low"

    def test_query_mode_missing_ingredient_name(self, agent):
        """Test query mode without ingredient_name parameter."""
        result = agent.run("query")

        assert result["success"] is False
        assert "error" in result
        assert "ingredient_name" in result["error"]


class TestMediaRoleAgentBatchMode:
    """Test MediaRoleAgent batch mode."""

    @pytest.fixture
    def agent(self):
        """Create MediaRoleAgent instance."""
        return MediaRoleAgent()

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create sample CSV for testing."""
        csv_path = tmp_path / "test_ingredients.csv"

        # Create test data with minimal required columns
        data = {
            "Component": [
                "FeSO₄·7H₂O",
                "MgCl₂·6H₂O",
                "Methanol",
                "PIPES",
                "K₂HPO₄·3H₂O"
            ],
            "Formula": [
                "FeSO4·7H2O",
                "MgCl2·6H2O",
                "CH3OH",
                "C8H18N2O6S2",
                "K2HPO4·3H2O"
            ],
            "Metabolic Role": [
                "Trace element",
                "Essential macronutrient",
                "Carbon source",
                "Non-metabolized pH buffer",
                "Phosphate source"
            ]
        }

        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        return csv_path

    def test_batch_mode_basic(self, agent, sample_csv, tmp_path):
        """Test batch mode with sample CSV."""
        output_path = tmp_path / "output_with_roles.csv"

        result = agent.run(
            "batch",
            csv_path=str(sample_csv),
            output_path=str(output_path)
        )

        assert result["success"] is True
        assert "data" in result
        assert result["data"]["total_ingredients"] == 5
        assert result["data"]["classified"] == 5
        assert result["data"]["unknown"] == 0
        assert Path(result["data"]["output_path"]).exists()

        # Verify output CSV has new columns
        df_output = pd.read_csv(output_path)
        assert "Media Role" in df_output.columns
        assert "Media Role DOI" in df_output.columns
        assert "Cellular Role" in df_output.columns  # Renamed from Metabolic Role
        assert "Cellular Role DOI" in df_output.columns

        # Verify some classifications
        assert df_output.loc[0, "Media Role"] == "Trace Element (Fe)"
        assert df_output.loc[1, "Media Role"] == "Essential Macronutrient (Mg)"
        assert df_output.loc[2, "Media Role"] == "Carbon Source"
        assert df_output.loc[3, "Media Role"] == "pH Buffer"
        assert df_output.loc[4, "Media Role"] == "Phosphate Source; pH Buffer"

    def test_batch_mode_auto_output_path(self, agent, sample_csv, tmp_path):
        """Test batch mode with automatic output path generation."""
        result = agent.run("batch", csv_path=str(sample_csv))

        assert result["success"] is True
        assert "output_path" in result["data"]
        assert Path(result["data"]["output_path"]).exists()

    def test_batch_mode_with_report(self, agent, sample_csv, tmp_path):
        """Test batch mode generates classification report."""
        output_path = tmp_path / "output_with_roles.csv"
        report_path = tmp_path / "classification_report.md"

        result = agent.run(
            "batch",
            csv_path=str(sample_csv),
            output_path=str(output_path),
            report_path=str(report_path)
        )

        assert result["success"] is True
        assert "classification_report" in result["data"]
        assert Path(result["data"]["classification_report"]).exists()

        # Verify report content
        report_content = Path(report_path).read_text()
        assert "# Media Role Classification Report" in report_content
        assert "Total components:" in report_content
        assert "Trace Element (Fe)" in report_content

    def test_batch_mode_missing_csv_path(self, agent):
        """Test batch mode without csv_path parameter."""
        result = agent.run("batch")

        assert result["success"] is False
        assert "error" in result
        assert "csv_path" in result["error"]

    def test_batch_mode_nonexistent_csv(self, agent):
        """Test batch mode with nonexistent CSV file."""
        result = agent.run("batch", csv_path="/nonexistent/path.csv")

        assert result["success"] is False
        assert "error" in result


class TestMediaRoleAgentEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def agent(self):
        """Create MediaRoleAgent instance."""
        return MediaRoleAgent()

    def test_invalid_mode(self, agent):
        """Test with invalid mode parameter."""
        result = agent.run("invalid_mode", ingredient_name="Test")

        assert result["success"] is False
        assert "error" in result
        assert "Unknown mode" in result["error"]

    def test_empty_ingredient_name(self, agent):
        """Test with empty ingredient name."""
        result = agent.run("query", ingredient_name="")

        assert result["success"] is True
        assert result["data"]["media_role"] == "Unknown"

    def test_none_ingredient_name(self, agent):
        """Test with None ingredient name."""
        result = agent.run("query", ingredient_name=None)

        assert result["success"] is False
        assert "error" in result

    def test_case_insensitive_matching(self, agent):
        """Test that classification is case-insensitive."""
        role1, conf1 = agent.infer_media_role("FESO4·7H2O")
        role2, conf2 = agent.infer_media_role("feso4·7h2o")
        role3, conf3 = agent.infer_media_role("FeSO₄·7H₂O")

        assert role1 == role2 == role3 == "Trace Element (Fe)"
        assert conf1 == conf2 == conf3 == "high"

    def test_unicode_and_ascii_variants(self, agent):
        """Test both Unicode and ASCII formula variants."""
        # Unicode subscripts
        role1, _ = agent.infer_media_role("K₂HPO₄")
        # ASCII
        role2, _ = agent.infer_media_role("K2HPO4")

        assert role1 == role2 == "Phosphate Source; pH Buffer"

    def test_with_hydration_numbers(self, agent):
        """Test compounds with various hydration numbers."""
        role1, _ = agent.infer_media_role("FeSO₄·7H₂O")
        role2, _ = agent.infer_media_role("FeSO₄·5H₂O")
        role3, _ = agent.infer_media_role("FeSO₄")

        # All should be classified the same
        assert role1 == role2 == role3 == "Trace Element (Fe)"

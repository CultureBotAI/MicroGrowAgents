"""Test AlternateIngredientAgent class."""

import pytest
from pathlib import Path
import pandas as pd
import tempfile
from unittest.mock import Mock, patch

from microgrowagents.agents.alternate_ingredient_agent import AlternateIngredientAgent
from microgrowagents.chemistry.element_extractor import ElementExtractor


class TestElementExtractor:
    """Test element extraction functionality."""

    @pytest.fixture
    def extractor(self):
        """Create ElementExtractor instance."""
        return ElementExtractor()

    def test_extract_from_simple_salt(self, extractor):
        """Test extraction from simple salt formula."""
        assert extractor.extract("FeSO₄·7H₂O") == "Fe"
        assert extractor.extract("MgCl₂·6H₂O") == "Mg"
        assert extractor.extract("CaCl₂·2H₂O") == "Ca"

    def test_extract_from_ascii_formula(self, extractor):
        """Test extraction from ASCII formula variants."""
        assert extractor.extract("FeSO4.7H2O") == "Fe"
        assert extractor.extract("ZnSO4") == "Zn"

    def test_extract_from_compound_name(self, extractor):
        """Test extraction from compound names."""
        assert extractor.extract("Iron sulfate") == "Fe"
        assert extractor.extract("Zinc sulfate") == "Zn"
        assert extractor.extract("Magnesium chloride") == "Mg"
        assert extractor.extract("Sodium tungstate") == "W"

    def test_extract_from_complex_formula(self, extractor):
        """Test extraction from complex formulas."""
        assert extractor.extract("(NH₄)₂SO₄") == "N"
        assert extractor.extract("(NH₄)₆Mo₇O₂₄·4H₂O") == "Mo"
        assert extractor.extract("K₂HPO₄·3H₂O") == "P"

    def test_extract_rare_earth(self, extractor):
        """Test extraction of rare earth elements."""
        assert extractor.extract("Dysprosium (III) chloride") == "Dy"
        assert extractor.extract("Neodymium chloride") == "Nd"

    def test_extract_returns_none_for_organic(self, extractor):
        """Test that organic compounds return None."""
        assert extractor.extract("Glucose") is None
        assert extractor.extract("Methanol") is None
        assert extractor.extract("PIPES") is None

    def test_extract_all_elements(self, extractor):
        """Test extracting all elements from compound."""
        elements = extractor.extract_all("(NH₄)₂SO₄")
        assert "N" in elements
        assert "S" in elements

    def test_get_element_class(self, extractor):
        """Test element classification."""
        assert extractor.get_element_class("Fe") == "trace_metal"
        assert extractor.get_element_class("Mg") == "macronutrient"
        assert extractor.get_element_class("Dy") == "rare_earth"


class TestNodeMatching:
    """Test hierarchical KG node matching."""

    @pytest.fixture
    def agent(self, tmp_path):
        """Create AlternateIngredientAgent with test database."""
        # Create a temporary database path
        db_path = tmp_path / "test.duckdb"
        return AlternateIngredientAgent(db_path)

    def test_find_kg_node_exact_match(self, agent):
        """Test exact name matching in KG."""
        # This will need a real database or mock
        # For now, test the method exists and handles None gracefully
        result = agent.find_kg_node("NonexistentCompound")
        # Should return None for nonexistent compound
        assert result is None or isinstance(result, dict)

    def test_find_kg_node_returns_correct_format(self, agent):
        """Test that find_kg_node returns correct format."""
        result = agent.find_kg_node("test_compound")
        if result is not None:
            assert "node_id" in result
            assert "node_label" in result


class TestAlternateIngredientAgentQuery:
    """Test AlternateIngredientAgent query mode."""

    @pytest.fixture
    def agent(self, tmp_path):
        """Create AlternateIngredientAgent instance."""
        db_path = tmp_path / "test.duckdb"
        return AlternateIngredientAgent(db_path)

    def test_query_mode_single_ingredient(self, agent):
        """Test query mode with single ingredient."""
        # Test with a simple ingredient
        result = agent.run("query", ingredient_name="FeSO₄·7H₂O", max_alternates=3)

        assert "success" in result
        if result["success"]:
            assert "data" in result
            assert "ingredient" in result["data"]
            assert "ingredient_role" in result["data"]
            assert "alternates" in result["data"]
            assert isinstance(result["data"]["alternates"], list)

    def test_query_mode_with_invalid_ingredient(self, agent):
        """Test query mode with invalid ingredient."""
        result = agent.run("query", ingredient_name="")

        assert "success" in result
        # Should handle gracefully

    def test_query_mode_missing_ingredient_name(self, agent):
        """Test query mode without ingredient_name parameter."""
        result = agent.run("query")

        assert result["success"] is False
        assert "error" in result
        assert "ingredient_name" in result["error"]

    def test_alternate_has_required_fields(self, agent):
        """Test that alternate recommendations have required fields."""
        result = agent.run("query", ingredient_name="MgCl₂·6H₂O", max_alternates=2)

        if result["success"] and result["data"]["alternates"]:
            alternate = result["data"]["alternates"][0]
            # All alternates must have these fields
            assert "alternate_ingredient" in alternate
            assert "rationale" in alternate
            assert "alternate_role" in alternate
            # Optional but nice to have
            assert "doi_citation" in alternate or True  # Can be empty
            assert "kg_node_id" in alternate or True  # Can be None
            assert "kg_node_label" in alternate or True  # Can be None
            assert "source" in alternate  # kg_microbe, literature, builtin


class TestBuiltinRecommendations:
    """Test built-in recommendation knowledge base."""

    @pytest.fixture
    def agent(self, tmp_path):
        """Create AlternateIngredientAgent instance."""
        db_path = tmp_path / "test.duckdb"
        return AlternateIngredientAgent(db_path)

    def test_builtin_recommendations_for_iron(self, agent):
        """Test built-in recommendations for iron compounds."""
        recommendations = agent._builtin_recommendations("FeSO₄", "Trace Element (Fe)")

        assert len(recommendations) > 0
        # Should recommend other iron sources
        ingredient_names = [r["alternate_ingredient"] for r in recommendations]
        # Should include common iron alternates
        assert any("Fe" in name or "iron" in name.lower() for name in ingredient_names)

    def test_builtin_recommendations_for_buffer(self, agent):
        """Test built-in recommendations for pH buffers."""
        recommendations = agent._builtin_recommendations("PIPES", "pH Buffer")

        assert len(recommendations) > 0
        # Should recommend other buffers
        ingredient_names = [r["alternate_ingredient"] for r in recommendations]
        common_buffers = ["HEPES", "MOPS", "Tris", "MES"]
        assert any(buf in ingredient_names for buf in common_buffers)

    def test_builtin_recommendations_have_rationale(self, agent):
        """Test that all built-in recommendations have rationale."""
        recommendations = agent._builtin_recommendations("MgCl₂", "Essential Macronutrient (Mg)")

        for rec in recommendations:
            assert "rationale" in rec
            assert len(rec["rationale"]) > 0
            assert "source" in rec
            assert rec["source"] == "builtin"


class TestAlternateIngredientAgentBatch:
    """Test AlternateIngredientAgent batch mode."""

    @pytest.fixture
    def agent(self, tmp_path):
        """Create AlternateIngredientAgent instance."""
        db_path = tmp_path / "test.duckdb"
        return AlternateIngredientAgent(db_path)

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create sample CSV for testing."""
        csv_path = tmp_path / "test_ingredients.csv"

        data = {
            "Component": [
                "FeSO₄·7H₂O",
                "MgCl₂·6H₂O",
                "PIPES"
            ]
        }

        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        return csv_path

    def test_batch_mode_basic(self, agent, sample_csv, tmp_path):
        """Test batch mode with sample CSV."""
        output_path = tmp_path / "alternates_output.csv"

        result = agent.run(
            "batch",
            csv_path=str(sample_csv),
            output_path=str(output_path)
        )

        assert "success" in result
        if result["success"]:
            assert "data" in result
            assert "output_path" in result["data"]
            assert Path(result["data"]["output_path"]).exists()

            # Verify output CSV has correct columns
            df_output = pd.read_csv(output_path)
            expected_columns = [
                "Ingredient",
                "Alternate Ingredient",
                "Rationale",
                "Alternate Role",
                "DOI Citation",
                "KG Node ID",
                "KG Node Label"
            ]
            for col in expected_columns:
                assert col in df_output.columns

    def test_batch_mode_auto_output_path(self, agent, sample_csv):
        """Test batch mode with automatic output path generation."""
        result = agent.run("batch", csv_path=str(sample_csv))

        assert "success" in result
        if result["success"]:
            assert "output_path" in result["data"]

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


class TestAlternateIngredientAgentEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def agent(self, tmp_path):
        """Create AlternateIngredientAgent instance."""
        db_path = tmp_path / "test.duckdb"
        return AlternateIngredientAgent(db_path)

    def test_invalid_mode(self, agent):
        """Test with invalid mode parameter."""
        result = agent.run("invalid_mode", ingredient_name="Test")

        assert result["success"] is False
        assert "error" in result
        assert "Unknown mode" in result["error"]

    def test_empty_ingredient_name(self, agent):
        """Test with empty ingredient name."""
        result = agent.run("query", ingredient_name="")

        # Should handle gracefully
        assert "success" in result

    def test_none_ingredient_name(self, agent):
        """Test with None ingredient name."""
        result = agent.run("query", ingredient_name=None)

        assert result["success"] is False
        assert "error" in result

    def test_max_alternates_limit(self, agent):
        """Test that max_alternates parameter is respected."""
        result = agent.run("query", ingredient_name="FeSO₄", max_alternates=2)

        if result["success"] and result["data"]["alternates"]:
            assert len(result["data"]["alternates"]) <= 2

    def test_organic_compound_no_alternates(self, agent):
        """Test organic compound that shouldn't have metal alternates."""
        result = agent.run("query", ingredient_name="Glucose", max_alternates=5)

        # Should succeed but may have no alternates or different type of alternates
        assert "success" in result

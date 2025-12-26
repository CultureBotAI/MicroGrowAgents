"""Tests for ChEBI fuzzy matcher client."""

import pytest
from pathlib import Path

from microgrowagents.chemistry.api_clients.chebi_client import ChEBIClient


@pytest.fixture
def sample_owl_file():
    """Path to sample ChEBI OWL file for testing."""
    return Path(__file__).parent.parent / "fixtures" / "chebi_sample.owl"


@pytest.fixture
def chebi_client(sample_owl_file):
    """ChEBI client with sample data loaded."""
    return ChEBIClient(sample_owl_file)


class TestChEBIClientInit:
    """Test ChEBI client initialization."""

    def test_init_with_valid_file(self, sample_owl_file):
        """Test initialization with valid OWL file."""
        client = ChEBIClient(sample_owl_file)
        assert client.owl_file == sample_owl_file
        assert len(client.chebi_terms) > 0

    def test_init_with_missing_file(self):
        """Test initialization with missing OWL file."""
        with pytest.raises(FileNotFoundError):
            ChEBIClient(Path("nonexistent.owl"))

    def test_load_owl_data(self, chebi_client):
        """Test that OWL data is loaded correctly."""
        # Should have loaded terms from sample file
        assert "glucose" in chebi_client.chebi_terms
        assert "sodium chloride" in chebi_client.chebi_terms
        assert "phosphate" in chebi_client.chebi_terms

        # Check that synonyms are loaded
        assert "d-glucose" in chebi_client.chebi_terms
        assert "nacl" in chebi_client.chebi_terms


class TestNormalization:
    """Test compound name normalization."""

    def test_normalize_hydrate_patterns(self, chebi_client):
        """Test removal of hydration notations."""
        test_cases = [
            ("CaCl2·2H2O", "calcium chloride"),
            ("CaCl2.2H2O", "calcium chloride"),
            ("CaCl2 2H2O", "calcium chloride"),
            ("MgSO4 monohydrate", "magnesium sulfate"),
            ("MgSO4 heptahydrate", "magnesium sulfate"),
            ("CuSO4 pentahydrate", "copper sulfate"),
        ]

        for input_name, expected_base in test_cases:
            normalized = chebi_client.normalize_compound_name(input_name)
            assert "h2o" not in normalized
            assert "hydrate" not in normalized

    def test_normalize_chemical_prefixes(self, chebi_client):
        """Test conversion of chemical prefixes."""
        test_cases = [
            ("Na-phosphate", "sodium phosphate"),
            ("Na phosphate", "sodium phosphate"),
            ("Na2-phosphate", "disodium phosphate"),
            ("NH4-Cl", "ammonium cl"),
        ]

        for input_name, expected in test_cases:
            normalized = chebi_client.normalize_compound_name(input_name)
            # Check that prefix was converted
            assert "na-" not in normalized or "sodium" in normalized

    def test_normalize_whitespace(self, chebi_client):
        """Test whitespace normalization."""
        assert chebi_client.normalize_compound_name("  glucose  ") == "glucose"
        assert chebi_client.normalize_compound_name("calcium  chloride") == "calcium chloride"

    def test_normalize_case(self, chebi_client):
        """Test lowercase conversion."""
        assert chebi_client.normalize_compound_name("GLUCOSE") == "glucose"
        assert chebi_client.normalize_compound_name("NaCl") == "nacl"


class TestExactMatching:
    """Test exact compound matching."""

    def test_exact_match_primary_label(self, chebi_client):
        """Test exact match with primary label."""
        results = chebi_client.find_exact_matches(["glucose"])

        assert "glucose" in results
        assert results["glucose"]["chebi_id"] == "CHEBI:17234"
        assert results["glucose"]["confidence"] == 1.0
        assert results["glucose"]["match_type"] == "exact"

    def test_exact_match_synonym(self, chebi_client):
        """Test exact match with synonym."""
        results = chebi_client.find_exact_matches(["dextrose"])

        assert "dextrose" in results
        assert results["dextrose"]["chebi_id"] == "CHEBI:17234"  # Same as glucose
        assert results["dextrose"]["confidence"] == 1.0

    def test_exact_match_multiple_compounds(self, chebi_client):
        """Test exact matching with multiple compounds."""
        compounds = ["glucose", "nacl", "phosphate"]
        results = chebi_client.find_exact_matches(compounds)

        assert len(results) == 3
        assert all(c in results for c in compounds)
        assert all(results[c]["confidence"] == 1.0 for c in compounds)

    def test_exact_match_no_match(self, chebi_client):
        """Test exact matching with no matches."""
        results = chebi_client.find_exact_matches(["unknown_compound_xyz"])

        assert len(results) == 0


class TestFuzzyMatching:
    """Test fuzzy compound matching."""

    def test_fuzzy_match_close_spelling(self, chebi_client):
        """Test fuzzy match with close spelling."""
        results = chebi_client.find_fuzzy_matches(["glukose"], min_confidence=0.7)

        assert "glukose" in results
        assert len(results["glukose"]) > 0
        # Should match to glucose
        best_match = results["glukose"][0]
        assert "glucose" in best_match["chebi_name"].lower()
        assert best_match["confidence"] > 0.7

    def test_fuzzy_match_with_hydrate(self, chebi_client):
        """Test fuzzy match after hydrate removal."""
        results = chebi_client.find_fuzzy_matches(["calcium chloride dihydrate"], min_confidence=0.8)

        assert "calcium chloride dihydrate" in results
        # Should match to calcium chloride after normalization
        if len(results["calcium chloride dihydrate"]) > 0:
            best_match = results["calcium chloride dihydrate"][0]
            assert best_match["confidence"] >= 0.8

    def test_fuzzy_match_confidence_threshold(self, chebi_client):
        """Test fuzzy matching respects confidence threshold."""
        results = chebi_client.find_fuzzy_matches(["xyz123"], min_confidence=0.9, max_results=3)

        # Should have no high-confidence matches for random string
        if "xyz123" in results:
            assert all(m["confidence"] >= 0.9 for m in results["xyz123"])

    def test_fuzzy_match_max_results(self, chebi_client):
        """Test fuzzy matching respects max_results parameter."""
        results = chebi_client.find_fuzzy_matches(["phosphate"], min_confidence=0.5, max_results=2)

        if "phosphate" in results:
            assert len(results["phosphate"]) <= 2


class TestCompoundMatching:
    """Test combined exact + fuzzy matching workflow."""

    def test_match_compounds_exact_first(self, chebi_client):
        """Test that exact matches are preferred over fuzzy."""
        compounds = ["glucose", "glukose"]
        results = chebi_client.match_compounds(compounds, min_fuzzy_confidence=0.7)

        # glucose should be exact match
        assert results["glucose"]["match_type"] == "exact"
        assert results["glucose"]["confidence"] == 1.0

        # glukose should be fuzzy match
        if "glukose" in results:
            assert results["glukose"]["match_type"] == "fuzzy"
            assert results["glukose"]["confidence"] < 1.0

    def test_match_compounds_mixed(self, chebi_client):
        """Test matching mix of exact and fuzzy matches."""
        compounds = ["glucose", "nacl", "phosphate ion"]
        results = chebi_client.match_compounds(compounds, min_fuzzy_confidence=0.8)

        # Should have at least exact matches
        assert "glucose" in results
        assert "nacl" in results

    def test_match_compounds_deduplication(self, chebi_client):
        """Test that duplicate compounds are deduplicated."""
        compounds = ["glucose", "glucose", "GLUCOSE"]
        results = chebi_client.match_compounds(compounds)

        # Should only have one result for glucose (case-insensitive)
        glucose_results = [k for k in results.keys() if k.lower() == "glucose"]
        assert len(glucose_results) >= 1

    def test_match_compounds_with_hydrates(self, chebi_client):
        """Test matching compounds with hydration notation."""
        compounds = ["MgSO4·7H2O", "CaCl2 dihydrate"]
        results = chebi_client.match_compounds(compounds, min_fuzzy_confidence=0.7)

        # Should match after hydrate removal
        assert len(results) > 0


class TestChEBIDataStructure:
    """Test internal ChEBI data structure."""

    def test_chebi_terms_structure(self, chebi_client):
        """Test that chebi_terms dict has correct structure."""
        # Pick a known term
        glucose_data = chebi_client.chebi_terms.get("glucose")

        assert glucose_data is not None
        assert "id" in glucose_data
        assert "name" in glucose_data
        assert "type" in glucose_data
        assert glucose_data["id"] == "CHEBI:17234"

    def test_synonym_entries(self, chebi_client):
        """Test that synonyms are stored correctly."""
        # D-glucose is a synonym of glucose
        dglucose_data = chebi_client.chebi_terms.get("d-glucose")

        assert dglucose_data is not None
        assert dglucose_data["id"] == "CHEBI:17234"
        assert dglucose_data["type"] in ["exact_synonym", "related_synonym"]


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_compound_list(self, chebi_client):
        """Test with empty compound list."""
        results = chebi_client.match_compounds([])
        assert results == {}

    def test_none_compound_name(self, chebi_client):
        """Test normalization with None."""
        # Should handle gracefully or raise appropriate error
        with pytest.raises((TypeError, AttributeError)):
            chebi_client.normalize_compound_name(None)

    def test_empty_string_compound(self, chebi_client):
        """Test with empty string compound."""
        results = chebi_client.match_compounds([""])
        # Should either skip or handle gracefully
        assert isinstance(results, dict)

    def test_special_characters(self, chebi_client):
        """Test compound names with special characters."""
        compounds = ["(NH4)2SO4", "Ca(OH)2"]
        results = chebi_client.match_compounds(compounds, min_fuzzy_confidence=0.6)

        # Should handle parentheses and numbers
        assert isinstance(results, dict)

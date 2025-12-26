"""Tests for GenMediaConcAgent."""

import pytest
from pathlib import Path
import duckdb

from microgrowagents.agents.gen_media_conc_agent import GenMediaConcAgent


@pytest.fixture
def test_db(tmp_path):
    """Create test database with sample data."""
    db_path = tmp_path / "test.duckdb"
    conn = duckdb.connect(str(db_path))

    # Create schema
    from microgrowagents.database.schema import create_schema
    create_schema(conn)

    # Insert test media
    conn.execute("""
        INSERT INTO media VALUES
        ('test:mp', 'MP Medium', 'defined', 7.0, 7.4, 'Test medium', 'test', NULL)
    """)

    # Insert test ingredients with categories
    conn.execute("""
        INSERT INTO ingredients VALUES
        ('CHEBI:17234', 'glucose', 'CHEBI:17234', NULL, NULL, NULL, 180.16, 'carbon source'),
        ('CHEBI:26710', 'NaCl', 'CHEBI:26710', NULL, NULL, NULL, 58.44, 'salt'),
        ('CHEBI:9754', 'tris', 'CHEBI:9754', NULL, NULL, NULL, 121.14, 'buffer'),
        ('CHEBI:49583', 'MgSO4', 'CHEBI:49583', NULL, NULL, NULL, 120.37, 'metal ion')
    """)

    # Insert media_ingredients
    conn.execute("""
        INSERT INTO media_ingredients VALUES
        (1, 'test:mp', 'CHEBI:17234', 10.0, 'g/L', 10.0, 55.5, 'carbon_source'),
        (2, 'test:mp', 'CHEBI:26710', 5.0, 'g/L', 5.0, 85.6, 'osmotic'),
        (3, 'test:mp', 'CHEBI:9754', 2.0, 'g/L', 2.0, 16.5, 'pH_buffering'),
        (4, 'test:mp', 'CHEBI:49583', 0.5, 'g/L', 0.5, 4.2, 'metal_ion')
    """)

    # Insert ingredient_effects
    conn.execute("""
        INSERT INTO ingredient_effects VALUES
        (1, 'CHEBI:17234', 'test:mp', 1.0, 100.0, 'mM', 'growth', 'Supports growth', 'Test literature', 'database'),
        (2, 'CHEBI:26710', NULL, 10.0, 500.0, 'mM', 'osmotic', 'Osmotic regulation', 'Test data', 'database'),
        (3, 'CHEBI:9754', NULL, 5.0, 50.0, 'mM', 'pH_buffering', 'pH buffer', 'Test data', 'database')
    """)

    # Insert test organism
    conn.execute("""
        INSERT INTO organisms VALUES
        ('NCBITaxon:562', 'Escherichia coli', 'species', 'Bacteria;Proteobacteria')
    """)

    # Insert organism_media
    conn.execute("""
        INSERT INTO organism_media VALUES
        (1, 'NCBITaxon:562', 'test:mp', 'test', NULL)
    """)

    conn.close()
    return db_path


@pytest.fixture
def gen_media_conc_agent(test_db):
    """GenMediaConcAgent with test database."""
    return GenMediaConcAgent(db_path=test_db)


class TestGenMediaConcAgentInit:
    """Test GenMediaConcAgent initialization."""

    def test_init_default(self):
        """Test default initialization."""
        agent = GenMediaConcAgent()
        assert agent.db_path is not None
        assert agent.sql_agent is not None
        assert agent.chemistry_agent is not None
        assert agent.literature_agent is not None

    def test_init_with_db_path(self, test_db):
        """Test initialization with custom db_path."""
        agent = GenMediaConcAgent(db_path=test_db)
        assert agent.db_path == test_db

    def test_essential_categories_defined(self):
        """Test that essential categories are defined."""
        agent = GenMediaConcAgent()
        assert "carbon source" in agent.ESSENTIAL_CATEGORIES
        assert "nitrogen source" in agent.ESSENTIAL_CATEGORIES
        assert "metal ion" in agent.ESSENTIAL_CATEGORIES

    def test_toxicity_thresholds_defined(self):
        """Test that toxicity thresholds are defined."""
        agent = GenMediaConcAgent()
        assert agent.TOXICITY_THRESHOLDS["metal"] == 10.0
        assert agent.TOXICITY_THRESHOLDS["salt"] == 500.0


class TestModeDetection:
    """Test mode detection logic."""

    def test_detect_mode_comma_separated(self, gen_media_conc_agent):
        """Test detection of comma-separated ingredient list."""
        mode = gen_media_conc_agent._detect_mode("glucose,NaCl,tris")
        assert mode == "ingredients"

    def test_detect_mode_medium_name(self, gen_media_conc_agent):
        """Test detection of medium name."""
        mode = gen_media_conc_agent._detect_mode("MP Medium")
        assert mode == "medium"

    def test_detect_mode_unknown(self, gen_media_conc_agent):
        """Test detection with unknown query."""
        mode = gen_media_conc_agent._detect_mode("UnknownMedium12345")
        assert mode == "ingredients"  # Default fallback


class TestIngredientExtraction:
    """Test ingredient extraction methods."""

    def test_get_ingredients_from_medium(self, gen_media_conc_agent):
        """Test extracting ingredients from existing medium."""
        ingredients = gen_media_conc_agent._get_ingredients_from_medium("MP Medium")

        assert len(ingredients) == 4
        assert any(ing["name"] == "glucose" for ing in ingredients)
        assert any(ing["name"] == "NaCl" for ing in ingredients)

        # Check structure
        glucose = [ing for ing in ingredients if ing["name"] == "glucose"][0]
        assert "id" in glucose
        assert "chebi_id" in glucose
        assert "current_concentration" in glucose

    def test_get_ingredients_from_nonexistent_medium(self, gen_media_conc_agent):
        """Test with nonexistent medium."""
        ingredients = gen_media_conc_agent._get_ingredients_from_medium("NonexistentMedium")
        assert ingredients == []

    def test_parse_ingredient_list(self, gen_media_conc_agent):
        """Test parsing comma-separated ingredient list."""
        ingredients = gen_media_conc_agent._parse_ingredient_list("glucose, NaCl, tris")

        assert len(ingredients) == 3
        assert ingredients[0]["name"] == "glucose"
        assert ingredients[1]["name"] == "NaCl"
        assert ingredients[2]["name"] == "tris"

    def test_parse_ingredient_list_with_unknown(self, gen_media_conc_agent):
        """Test parsing list with unknown ingredient."""
        ingredients = gen_media_conc_agent._parse_ingredient_list("glucose, UnknownCompound")

        assert len(ingredients) == 2
        # glucose should be found in DB
        assert ingredients[0]["id"] is not None
        # UnknownCompound should still be added
        assert ingredients[1]["name"] == "UnknownCompound"


class TestOrganismInfo:
    """Test organism information retrieval."""

    def test_get_organism_info_by_id(self, gen_media_conc_agent):
        """Test organism lookup by NCBITaxon ID."""
        org_info = gen_media_conc_agent._get_organism_info("NCBITaxon:562")

        assert org_info is not None
        assert org_info["id"] == "NCBITaxon:562"
        assert org_info["name"] == "Escherichia coli"
        assert org_info["rank"] == "species"

    def test_get_organism_info_by_name(self, gen_media_conc_agent):
        """Test organism lookup by name."""
        org_info = gen_media_conc_agent._get_organism_info("Escherichia coli")

        assert org_info is not None
        assert org_info["id"] == "NCBITaxon:562"

    def test_get_organism_info_not_found(self, gen_media_conc_agent):
        """Test with nonexistent organism."""
        org_info = gen_media_conc_agent._get_organism_info("NonexistentOrganism")
        assert org_info is None


class TestDatabaseRanges:
    """Test database range queries."""

    def test_get_database_ranges(self, gen_media_conc_agent):
        """Test retrieval of concentration ranges from database."""
        ingredient = {
            "id": "CHEBI:17234",
            "name": "glucose",
            "chebi_id": "CHEBI:17234",
        }

        ranges = gen_media_conc_agent._get_database_ranges(ingredient, None)

        assert len(ranges) > 0
        assert ranges[0]["low"] == 1.0
        assert ranges[0]["high"] == 100.0
        assert ranges[0]["unit"] == "mM"

    def test_get_database_ranges_no_ingredient_id(self, gen_media_conc_agent):
        """Test with ingredient without ID."""
        ingredient = {"name": "unknown"}
        ranges = gen_media_conc_agent._get_database_ranges(ingredient, None)
        assert ranges == []


class TestConcentrationExtraction:
    """Test concentration extraction from text."""

    def test_extract_concentration_dash_format(self, gen_media_conc_agent):
        """Test extraction of range with dash (5-50 mM)."""
        text = "The optimal concentration was 5-50 mM glucose."
        ranges = gen_media_conc_agent._extract_concentration_from_text(text)

        assert len(ranges) >= 1
        assert ranges[0]["low"] == 5.0
        assert ranges[0]["high"] == 50.0
        assert ranges[0]["unit"].lower() == "mm"

    def test_extract_concentration_to_format(self, gen_media_conc_agent):
        """Test extraction of range with 'to' (10 to 100 g/L)."""
        text = "Concentration ranged from 10 to 100 g/L."
        ranges = gen_media_conc_agent._extract_concentration_from_text(text)

        assert len(ranges) >= 1
        assert ranges[0]["low"] == 10.0
        assert ranges[0]["high"] == 100.0
        assert ranges[0]["unit"].lower() == "g/l"

    def test_extract_concentration_multiple_ranges(self, gen_media_conc_agent):
        """Test extraction of multiple ranges."""
        text = "Glucose at 1-10 mM and NaCl at 50-500 mM."
        ranges = gen_media_conc_agent._extract_concentration_from_text(text)

        assert len(ranges) == 2

    def test_extract_concentration_no_matches(self, gen_media_conc_agent):
        """Test with text containing no concentration ranges."""
        text = "This text has no concentration information."
        ranges = gen_media_conc_agent._extract_concentration_from_text(text)
        assert ranges == []


class TestEssentialityDetermination:
    """Test essentiality determination."""

    def test_determine_essentiality_carbon_source(self, gen_media_conc_agent):
        """Test essentiality for carbon source."""
        ingredient = {
            "id": "CHEBI:17234",
            "name": "glucose",
            "category": "carbon source",
        }

        is_essential = gen_media_conc_agent._determine_essentiality(
            ingredient, None, []
        )
        assert is_essential is True

    def test_determine_essentiality_metal_ion(self, gen_media_conc_agent):
        """Test essentiality for metal ion."""
        ingredient = {
            "id": "CHEBI:49583",
            "name": "MgSO4",
            "category": "metal ion",
        }

        is_essential = gen_media_conc_agent._determine_essentiality(
            ingredient, None, []
        )
        assert is_essential is True

    def test_determine_essentiality_non_essential(self, gen_media_conc_agent):
        """Test essentiality for non-essential ingredient."""
        ingredient = {
            "id": "CHEBI:26710",
            "name": "NaCl",
            "category": "salt",
        }

        is_essential = gen_media_conc_agent._determine_essentiality(
            ingredient, None, []
        )
        assert is_essential is False

    def test_determine_essentiality_from_database(self, gen_media_conc_agent):
        """Test essentiality determination from database."""
        ingredient = {
            "id": "CHEBI:49583",
            "name": "MgSO4",
        }

        is_essential = gen_media_conc_agent._determine_essentiality(
            ingredient, None, []
        )
        # Should query database and find metal ion category
        assert is_essential is True


class TestRangeAggregation:
    """Test range aggregation logic."""

    def test_aggregate_ranges_essential(self, gen_media_conc_agent):
        """Test range aggregation for essential ingredient."""
        ranges = [
            {"low": 1.0, "high": 100.0},
            {"low": 5.0, "high": 50.0},
            {"low": 0.1, "high": 200.0},
        ]

        low, high = gen_media_conc_agent._aggregate_ranges(ranges, is_essential=True)

        assert low == 0.1  # Minimum of lows
        assert 40.0 <= high <= 120.0  # Should be around median (100)

    def test_aggregate_ranges_non_essential(self, gen_media_conc_agent):
        """Test range aggregation for non-essential ingredient."""
        ranges = [
            {"low": 1.0, "high": 100.0},
            {"low": 5.0, "high": 50.0},
        ]

        low, high = gen_media_conc_agent._aggregate_ranges(ranges, is_essential=False)

        assert low == 0.0  # Non-essential can be 0
        assert high > 0

    def test_aggregate_ranges_empty(self, gen_media_conc_agent):
        """Test range aggregation with no ranges."""
        low, high = gen_media_conc_agent._aggregate_ranges([], is_essential=True)

        assert low == 0.0
        assert high == 100.0  # Default


class TestToxicityEstimation:
    """Test toxicity threshold estimation."""

    def test_estimate_toxicity_metal(self, gen_media_conc_agent):
        """Test toxicity estimation for metal compound."""
        ingredient = {"name": "iron sulfate"}
        threshold = gen_media_conc_agent._estimate_toxicity_threshold(ingredient)
        assert threshold == 10.0  # Metal threshold

    def test_estimate_toxicity_salt(self, gen_media_conc_agent):
        """Test toxicity estimation for salt."""
        ingredient = {"name": "sodium chloride"}
        threshold = gen_media_conc_agent._estimate_toxicity_threshold(ingredient)
        assert threshold == 500.0  # Salt threshold

    def test_estimate_toxicity_organic_acid(self, gen_media_conc_agent):
        """Test toxicity estimation for organic acid."""
        ingredient = {"name": "acetic acid"}
        threshold = gen_media_conc_agent._estimate_toxicity_threshold(ingredient)
        assert threshold == 100.0  # Organic acid threshold

    def test_estimate_toxicity_default(self, gen_media_conc_agent):
        """Test toxicity estimation with default fallback."""
        ingredient = {"name": "unknown compound"}
        threshold = gen_media_conc_agent._estimate_toxicity_threshold(ingredient)
        assert threshold == 1000.0  # Default


class TestConfidenceCalculation:
    """Test confidence score calculation."""

    def test_calculate_confidence_multiple_sources(self, gen_media_conc_agent):
        """Test confidence with multiple evidence sources."""
        evidence_sources = [
            {"source": "database", "confidence": 0.9},
            {"source": "literature", "confidence": 0.7},
            {"source": "chemistry", "confidence": 0.6},
        ]

        confidence = gen_media_conc_agent._calculate_confidence(evidence_sources, [])

        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be reasonably confident

    def test_calculate_confidence_single_source(self, gen_media_conc_agent):
        """Test confidence with single evidence source."""
        evidence_sources = [{"source": "database", "confidence": 0.9}]

        confidence = gen_media_conc_agent._calculate_confidence(evidence_sources, [])

        assert 0.0 <= confidence <= 1.0
        assert confidence < 0.95  # Shouldn't be too confident with one source

    def test_calculate_confidence_no_sources(self, gen_media_conc_agent):
        """Test confidence with no evidence sources."""
        confidence = gen_media_conc_agent._calculate_confidence([], [])

        assert confidence == 0.1  # Very low confidence

    def test_calculate_confidence_capped(self, gen_media_conc_agent):
        """Test that confidence is capped at 0.95."""
        evidence_sources = [
            {"source": "database", "confidence": 1.0},
            {"source": "literature", "confidence": 1.0},
            {"source": "chemistry", "confidence": 1.0},
            {"source": "heuristic", "confidence": 1.0},
        ]

        confidence = gen_media_conc_agent._calculate_confidence(evidence_sources, [])
        assert confidence <= 0.95


class TestSummaryCalculation:
    """Test summary statistics."""

    def test_calculate_summary(self, gen_media_conc_agent):
        """Test summary calculation."""
        predictions = [
            {"name": "glucose", "is_essential": True, "confidence": 0.9},
            {"name": "NaCl", "is_essential": False, "confidence": 0.7},
            {"name": "tris", "is_essential": False, "confidence": 0.8},
            {"name": "MgSO4", "is_essential": True, "confidence": 0.85},
        ]

        summary = gen_media_conc_agent._calculate_summary(predictions)

        assert summary["total_ingredients"] == 4
        assert summary["essential_count"] == 2
        assert summary["non_essential_count"] == 2
        assert 0.7 <= summary["avg_confidence"] <= 0.9
        assert summary["min_confidence"] == 0.7
        assert summary["max_confidence"] == 0.9


class TestRunMethod:
    """Test main run() method."""

    def test_run_medium_mode(self, gen_media_conc_agent):
        """Test full run with medium mode."""
        result = gen_media_conc_agent.run("MP Medium", mode="medium")

        assert result["success"] is True
        assert "data" in result
        assert len(result["data"]) == 4  # 4 ingredients in test medium
        assert result["mode"] == "medium"
        assert "summary" in result

    def test_run_ingredients_mode(self, gen_media_conc_agent):
        """Test full run with ingredients mode."""
        result = gen_media_conc_agent.run("glucose,NaCl", mode="ingredients")

        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["mode"] == "ingredients"

    def test_run_auto_mode_detection(self, gen_media_conc_agent):
        """Test automatic mode detection."""
        # Comma-separated should be ingredients
        result = gen_media_conc_agent.run("glucose,NaCl")
        assert result["mode"] == "ingredients"

        # Medium name should be medium
        result = gen_media_conc_agent.run("MP Medium")
        assert result["mode"] == "medium"

    def test_run_with_organism(self, gen_media_conc_agent):
        """Test run with organism-specific mode."""
        result = gen_media_conc_agent.run(
            "MP Medium",
            organism="NCBITaxon:562",
        )

        assert result["success"] is True
        assert result["organism"] is not None
        assert result["organism"]["id"] == "NCBITaxon:562"
        assert result["method"] == "multi-source"

    def test_run_with_unit_option(self, gen_media_conc_agent):
        """Test run with unit specification."""
        result = gen_media_conc_agent.run("glucose", mode="ingredients", unit="g/L")

        assert result["success"] is True
        assert result["unit"] == "g/L"
        assert result["data"][0]["unit"] == "g/L"

    def test_run_no_evidence(self, gen_media_conc_agent):
        """Test run without evidence details."""
        result = gen_media_conc_agent.run(
            "glucose",
            mode="ingredients",
            include_evidence=False,
        )

        assert result["success"] is True
        assert "evidence" not in result["data"][0]

    def test_run_invalid_query(self, gen_media_conc_agent):
        """Test with invalid/nonexistent query."""
        result = gen_media_conc_agent.run("NonexistentMedium12345", mode="medium")

        assert result["success"] is False
        assert "error" in result


class TestPredictionStructure:
    """Test prediction output structure."""

    def test_prediction_has_required_fields(self, gen_media_conc_agent):
        """Test that predictions have all required fields."""
        result = gen_media_conc_agent.run("glucose", mode="ingredients")

        assert result["success"] is True
        pred = result["data"][0]

        # Check required fields
        assert "name" in pred
        assert "concentration_low" in pred
        assert "concentration_high" in pred
        assert "unit" in pred
        assert "confidence" in pred
        assert "is_essential" in pred

    def test_prediction_ranges_valid(self, gen_media_conc_agent):
        """Test that predicted ranges are valid."""
        result = gen_media_conc_agent.run("glucose,NaCl", mode="ingredients")

        for pred in result["data"]:
            assert pred["concentration_low"] >= 0
            assert pred["concentration_high"] > pred["concentration_low"]
            assert 0.0 <= pred["confidence"] <= 1.0

    def test_prediction_essential_flag(self, gen_media_conc_agent):
        """Test essentiality flags in predictions."""
        result = gen_media_conc_agent.run("MP Medium", mode="medium")

        # Glucose should be essential (carbon source)
        glucose_pred = [p for p in result["data"] if p["name"] == "glucose"][0]
        assert glucose_pred["is_essential"] is True

        # Tris should not be essential (buffer)
        tris_pred = [p for p in result["data"] if p["name"] == "tris"][0]
        assert tris_pred["is_essential"] is False


class TestErrorHandling:
    """Test error handling."""

    def test_run_empty_query(self, gen_media_conc_agent):
        """Test with empty query."""
        result = gen_media_conc_agent.run("")
        assert result["success"] is False

    def test_run_database_missing(self):
        """Test with missing database."""
        agent = GenMediaConcAgent(db_path=Path("/nonexistent/path.duckdb"))
        result = agent.run("glucose")
        assert result["success"] is False

    def test_run_invalid_organism(self, gen_media_conc_agent):
        """Test with invalid organism."""
        result = gen_media_conc_agent.run(
            "glucose",
            organism="InvalidOrganism",
        )
        # Should still succeed but organism will be None
        assert result["success"] is True
        assert result["organism"] is None

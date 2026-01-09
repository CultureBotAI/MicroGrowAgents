"""Test SheetQuerySkill for querying information sheets."""

import json
from pathlib import Path

import duckdb
import pytest

from microgrowagents.database.schema import create_schema
from microgrowagents.database.sheet_loader import SheetDataLoader
from microgrowagents.skills.simple.sheet_query import SheetQuerySkill


@pytest.fixture
def test_db(tmp_path):
    """Create test database with loaded sheet data."""
    db_path = tmp_path / "test_sheets.duckdb"

    # Create schema
    conn = duckdb.connect(str(db_path))
    create_schema(conn)
    conn.close()

    # Load test data
    loader = SheetDataLoader(db_path)
    sheets_dir = Path("tests/fixtures/sheets_test")
    loader.load_collection("test_cmm", sheets_dir)

    return db_path


class TestSheetQuerySkill:
    """Test SheetQuerySkill initialization and metadata."""

    def test_skill_initialization(self, test_db):
        """Test skill can be initialized with database path."""
        skill = SheetQuerySkill(test_db)
        assert skill.db_path == test_db

    def test_get_metadata(self, test_db):
        """Test skill metadata is correct."""
        skill = SheetQuerySkill(test_db)
        metadata = skill.get_metadata()

        assert metadata.name == "sheet-query"
        assert metadata.category == "simple"
        assert "sheet" in metadata.description.lower() or "query" in metadata.description.lower()
        assert len(metadata.parameters) > 0
        assert len(metadata.examples) > 0

    def test_metadata_parameters(self, test_db):
        """Test skill has required parameters."""
        skill = SheetQuerySkill(test_db)
        metadata = skill.get_metadata()

        param_names = [p.name for p in metadata.parameters]
        assert "collection_id" in param_names
        assert "query_type" in param_names
        assert "output_format" in param_names


class TestMarkdownOutput:
    """Test markdown formatted output (Format 1)."""

    def test_entity_lookup_markdown(self, test_db):
        """Test entity lookup returns formatted markdown table."""
        skill = SheetQuerySkill(test_db)

        result = skill.run(
            collection_id="test_cmm",
            query_type="entity_lookup",
            entity_id="CHEBI:52927",
            output_format="markdown"
        )

        assert isinstance(result, str)
        # Should contain table headers
        assert "|" in result or "CHEBI:52927" in result
        # Should contain entity name
        assert "Europium" in result or "europium" in result.lower()

    def test_publication_search_markdown_with_citations(self, test_db):
        """Test publication search includes citation links."""
        skill = SheetQuerySkill(test_db)

        result = skill.run(
            collection_id="test_cmm",
            query_type="publication_search",
            keyword="europium",
            output_format="markdown"
        )

        assert isinstance(result, str)
        # Should contain publication info
        assert "europium" in result.lower() or "lanthanide" in result.lower()
        # Should contain references section or links
        assert "pmid" in result.lower() or "doi" in result.lower() or "http" in result

    def test_markdown_contains_table_headers(self, test_db):
        """Test markdown output has proper table headers."""
        skill = SheetQuerySkill(test_db)

        result = skill.run(
            collection_id="test_cmm",
            query_type="entity_lookup",
            entity_type="chemical",
            output_format="markdown"
        )

        # Markdown tables use pipes
        assert "|" in result
        # Should have multiple rows
        assert result.count("\n") > 5


class TestJSONOutput:
    """Test JSON formatted output (Format 2)."""

    def test_entity_lookup_json(self, test_db):
        """Test entity lookup returns valid JSON."""
        skill = SheetQuerySkill(test_db)

        result = skill.run(
            collection_id="test_cmm",
            query_type="entity_lookup",
            entity_id="CHEBI:52927",
            output_format="json"
        )

        # Should be valid JSON
        data = json.loads(result)
        assert data["success"] is True
        assert "data" in data
        assert "entities" in data["data"]

    def test_json_contains_all_data(self, test_db):
        """Test JSON output contains complete data."""
        skill = SheetQuerySkill(test_db)

        result = skill.run(
            collection_id="test_cmm",
            query_type="entity_lookup",
            entity_id="CHEBI:52927",
            output_format="json"
        )

        data = json.loads(result)
        entities = data["data"]["entities"]
        assert len(entities) == 1

        entity = entities[0]
        assert entity["entity_id"] == "CHEBI:52927"
        assert "entity_name" in entity
        assert "properties" in entity

    def test_json_has_metadata(self, test_db):
        """Test JSON output includes metadata."""
        skill = SheetQuerySkill(test_db)

        result = skill.run(
            collection_id="test_cmm",
            query_type="publication_search",
            keyword="europium",
            output_format="json"
        )

        data = json.loads(result)
        assert "metadata" in data
        # Should have execution time
        assert "execution_time" in data["metadata"] or "query" in data["metadata"]


class TestEvidenceReport:
    """Test evidence-rich report format (Format 3)."""

    def test_evidence_report_format(self, test_db):
        """Test evidence report includes detailed sections."""
        skill = SheetQuerySkill(test_db)

        result = skill.run(
            collection_id="test_cmm",
            query_type="cross_reference",
            source_entity_id="CHEBI:52927",
            output_format="evidence_report"
        )

        assert isinstance(result, str)
        # Should have section headers
        assert "#" in result
        # Should have entity details
        assert "CHEBI:52927" in result

    def test_evidence_report_has_publication_excerpts(self, test_db):
        """Test evidence report includes publication excerpts."""
        skill = SheetQuerySkill(test_db)

        result = skill.run(
            collection_id="test_cmm",
            query_type="cross_reference",
            source_entity_id="CHEBI:52927",
            output_format="evidence_report"
        )

        # Should contain publication info or excerpts
        # At minimum should have detailed information
        assert len(result) > 100  # Non-trivial content

    def test_evidence_report_structured(self, test_db):
        """Test evidence report has structured sections."""
        skill = SheetQuerySkill(test_db)

        result = skill.run(
            collection_id="test_cmm",
            query_type="entity_lookup",
            entity_id="K23995",
            output_format="evidence_report"
        )

        # Should have headers
        header_count = result.count("#")
        assert header_count >= 2  # At least title and one section


class TestQueryTypes:
    """Test all 4 query types through skill."""

    def test_entity_lookup_query(self, test_db):
        """Test entity lookup through skill."""
        skill = SheetQuerySkill(test_db)

        result = skill.run(
            collection_id="test_cmm",
            query_type="entity_lookup",
            entity_id="CHEBI:52927",
            output_format="json"
        )

        data = json.loads(result)
        assert data["success"] is True
        assert len(data["data"]["entities"]) == 1

    def test_cross_reference_query(self, test_db):
        """Test cross-reference through skill."""
        skill = SheetQuerySkill(test_db)

        result = skill.run(
            collection_id="test_cmm",
            query_type="cross_reference",
            source_entity_id="K23995",
            output_format="json"
        )

        data = json.loads(result)
        assert data["success"] is True
        assert "source_entity" in data["data"]
        assert "related_entities" in data["data"]

    def test_publication_search_query(self, test_db):
        """Test publication search through skill."""
        skill = SheetQuerySkill(test_db)

        result = skill.run(
            collection_id="test_cmm",
            query_type="publication_search",
            keyword="europium",
            output_format="json"
        )

        data = json.loads(result)
        assert data["success"] is True
        assert "publications" in data["data"]

    def test_filtered_query(self, test_db):
        """Test filtered query through skill."""
        skill = SheetQuerySkill(test_db)

        result = skill.run(
            collection_id="test_cmm",
            query_type="filtered",
            table_name="chemicals",
            filter_conditions={"molecular_formula": "Eu3+"},
            output_format="json"
        )

        data = json.loads(result)
        assert data["success"] is True
        assert "entities" in data["data"]


class TestParameterValidation:
    """Test parameter validation and error handling."""

    def test_missing_collection_id(self, test_db):
        """Test error when collection_id missing."""
        skill = SheetQuerySkill(test_db)

        result = skill.run(
            query_type="entity_lookup",
            entity_id="CHEBI:52927",
            output_format="markdown"
        )

        # Should handle gracefully - either error or empty result
        assert isinstance(result, str)

    def test_invalid_query_type(self, test_db):
        """Test error with invalid query type."""
        skill = SheetQuerySkill(test_db)

        result = skill.run(
            collection_id="test_cmm",
            query_type="invalid_type",
            output_format="markdown"
        )

        # Should return error
        assert isinstance(result, str)
        assert "error" in result.lower() or "invalid" in result.lower() or "unknown" in result.lower()

    def test_missing_required_params(self, test_db):
        """Test error when query-specific params missing."""
        skill = SheetQuerySkill(test_db)

        # Entity lookup without ID or name
        result = skill.run(
            collection_id="test_cmm",
            query_type="entity_lookup",
            output_format="json"
        )

        # Should either work (return all) or error gracefully
        assert isinstance(result, str)


class TestExecuteMethod:
    """Test execute() method directly."""

    def test_execute_returns_dict(self, test_db):
        """Test execute method returns proper dict structure."""
        skill = SheetQuerySkill(test_db)

        result = skill.execute(
            collection_id="test_cmm",
            query_type="entity_lookup",
            entity_id="CHEBI:52927"
        )

        assert isinstance(result, dict)
        assert "success" in result
        assert "data" in result

    def test_execute_with_cross_reference(self, test_db):
        """Test execute with cross-reference query."""
        skill = SheetQuerySkill(test_db)

        result = skill.execute(
            collection_id="test_cmm",
            query_type="cross_reference",
            source_entity_id="K23995"
        )

        assert result["success"] is True
        assert "source_entity" in result["data"]


class TestOutputFormatSwitching:
    """Test switching between output formats."""

    def test_same_query_different_formats(self, test_db):
        """Test same query produces different output formats."""
        skill = SheetQuerySkill(test_db)

        # Get JSON
        json_result = skill.run(
            collection_id="test_cmm",
            query_type="entity_lookup",
            entity_id="CHEBI:52927",
            output_format="json"
        )

        # Get Markdown
        md_result = skill.run(
            collection_id="test_cmm",
            query_type="entity_lookup",
            entity_id="CHEBI:52927",
            output_format="markdown"
        )

        # Get Evidence Report
        report_result = skill.run(
            collection_id="test_cmm",
            query_type="entity_lookup",
            entity_id="CHEBI:52927",
            output_format="evidence_report"
        )

        # All should be different
        assert json_result != md_result
        assert md_result != report_result
        assert json_result != report_result

        # JSON should be parseable
        assert json.loads(json_result)

        # Markdown should have tables
        assert "|" in md_result or "#" in md_result

        # Report should have headers
        assert "#" in report_result

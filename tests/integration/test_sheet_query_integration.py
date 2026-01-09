"""
Integration tests for SheetQuery system.

Tests the complete end-to-end workflow:
1. Schema creation
2. Data loading (TSV + publications)
3. Querying via agent
4. Querying via skill with different output formats
"""

import json
from pathlib import Path

import duckdb
import pytest

from microgrowagents.agents.sheet_query_agent import SheetQueryAgent
from microgrowagents.database.schema import create_schema
from microgrowagents.database.sheet_loader import SheetDataLoader
from microgrowagents.skills.simple.sheet_query import SheetQuerySkill


@pytest.fixture
def test_db(tmp_path):
    """Create test database with schema."""
    db_path = tmp_path / "integration_test.duckdb"
    conn = duckdb.connect(str(db_path))
    create_schema(conn)
    conn.close()
    return db_path


@pytest.fixture
def test_sheets_dir():
    """Path to test fixtures."""
    return Path("tests/fixtures/sheets_test")


class TestEndToEndWorkflow:
    """Test complete workflow from loading to querying."""

    def test_complete_workflow_cmm_collection(self, test_db, test_sheets_dir):
        """Test loading and querying CMM collection."""
        # Step 1: Load data
        loader = SheetDataLoader(test_db)
        load_result = loader.load_collection("test_cmm", test_sheets_dir)

        assert load_result["success"] is True
        assert load_result["tables_loaded"] == 2  # chemicals + genes
        assert load_result["publications_loaded"] == 2
        assert load_result["total_rows"] == 10  # 5 chemicals + 5 genes
        assert load_result["references_created"] > 0

        # Step 2: Validate loading
        validation = loader.validate_loading("test_cmm")
        assert validation["success"] is True
        assert validation["total_rows"] == 10
        assert validation["publications_loaded"] == 2

        # Step 3: Query with agent
        agent = SheetQueryAgent(test_db)

        # Entity lookup
        result = agent.entity_lookup(
            query="lookup europium",
            collection_id="test_cmm",
            entity_id="CHEBI:52927"
        )
        assert result["success"] is True
        assert len(result["data"]["entities"]) == 1
        assert result["data"]["entities"][0]["entity_id"] == "CHEBI:52927"

        # Cross-reference
        result = agent.cross_reference_query(
            query="find related to XoxF",
            collection_id="test_cmm",
            source_entity_id="K23995"
        )
        assert result["success"] is True
        assert result["data"]["source_entity"]["entity_id"] == "K23995"

        # Publication search
        result = agent.publication_search(
            query="search for europium",
            collection_id="test_cmm",
            keyword="europium"
        )
        assert result["success"] is True
        assert len(result["data"]["publications"]) > 0

        # Step 4: Query with skill (all 3 formats)
        skill = SheetQuerySkill(test_db)

        # Markdown format
        md_result = skill.run(
            collection_id="test_cmm",
            query_type="entity_lookup",
            entity_id="CHEBI:52927",
            output_format="markdown"
        )
        assert isinstance(md_result, str)
        assert "CHEBI:52927" in md_result
        assert "|" in md_result  # Has tables

        # JSON format
        json_result = skill.run(
            collection_id="test_cmm",
            query_type="entity_lookup",
            entity_id="CHEBI:52927",
            output_format="json"
        )
        data = json.loads(json_result)
        assert data["success"] is True

        # Evidence report format
        report_result = skill.run(
            collection_id="test_cmm",
            query_type="cross_reference",
            source_entity_id="CHEBI:52927",
            output_format="evidence_report"
        )
        assert isinstance(report_result, str)
        assert "#" in report_result  # Has headers
        assert "CHEBI:52927" in report_result


class TestDataIntegrity:
    """Test data integrity across loading and querying."""

    def test_all_entities_queryable(self, test_db, test_sheets_dir):
        """Test that all loaded entities are queryable."""
        # Load data
        loader = SheetDataLoader(test_db)
        loader.load_collection("test_cmm", test_sheets_dir)

        # Get all entities
        agent = SheetQueryAgent(test_db)
        result = agent.entity_lookup(
            query="list all",
            collection_id="test_cmm"
        )

        assert result["success"] is True
        entities = result["data"]["entities"]
        assert len(entities) == 10  # 5 chemicals + 5 genes

        # Verify entity types
        types = {e["entity_type"] for e in entities}
        assert "chemical" in types
        assert "gene" in types

    def test_all_publications_searchable(self, test_db, test_sheets_dir):
        """Test that all publications are searchable."""
        # Load data
        loader = SheetDataLoader(test_db)
        loader.load_collection("test_cmm", test_sheets_dir)

        # Search publications
        agent = SheetQueryAgent(test_db)
        result = agent.publication_search(
            query="search all",
            collection_id="test_cmm",
            keyword="the"  # Common word
        )

        assert result["success"] is True
        pubs = result["data"]["publications"]
        assert len(pubs) == 2  # Both publications contain "the"

    def test_cross_references_bidirectional(self, test_db, test_sheets_dir):
        """Test that cross-references work in both directions."""
        # Load data
        loader = SheetDataLoader(test_db)
        loader.load_collection("test_cmm", test_sheets_dir)

        agent = SheetQueryAgent(test_db)

        # Find genes related to europium (CHEBI:52927)
        result = agent.cross_reference_query(
            query="find genes using europium",
            collection_id="test_cmm",
            source_entity_id="CHEBI:52927",
            include_types=["gene"]
        )

        assert result["success"] is True
        # Should find genes that reference CHEBI:52927 in their CHEBI column
        related_genes = result["data"]["related_entities"]
        assert len(related_genes) > 0


class TestPublicationCitations:
    """Test publication citation functionality."""

    def test_publication_entity_links(self, test_db, test_sheets_dir):
        """Test that publications are linked to entities."""
        # Load data
        loader = SheetDataLoader(test_db)
        load_result = loader.load_collection("test_cmm", test_sheets_dir)

        # Verify references were created
        assert load_result["references_created"] > 0

        # Find entity with publication references
        agent = SheetQueryAgent(test_db)
        result = agent.cross_reference_query(
            query="find publications for europium",
            collection_id="test_cmm",
            source_entity_id="CHEBI:52927"
        )

        assert result["success"] is True
        pubs = result["data"]["publications"]
        assert len(pubs) > 0

        # Verify publication has proper ID
        pub = pubs[0]
        assert "publication_id" in pub
        assert pub["publication_id"].startswith(("pmid:", "doi:", "pmc:"))

    def test_skill_includes_citation_links(self, test_db, test_sheets_dir):
        """Test that skill output includes citation links."""
        # Load data
        loader = SheetDataLoader(test_db)
        loader.load_collection("test_cmm", test_sheets_dir)

        # Query with markdown output
        skill = SheetQuerySkill(test_db)
        result = skill.run(
            collection_id="test_cmm",
            query_type="publication_search",
            keyword="europium",
            output_format="markdown"
        )

        # Should contain links
        assert "http" in result or "pmid" in result.lower() or "doi" in result.lower()
        # Should contain markdown link syntax
        assert "[" in result and "](" in result


class TestMultipleCollections:
    """Test handling multiple collections."""

    def test_load_multiple_collections(self, test_db, test_sheets_dir):
        """Test loading same data as different collections."""
        loader = SheetDataLoader(test_db)

        # Load as collection 1
        result1 = loader.load_collection("collection_1", test_sheets_dir)
        assert result1["success"] is True

        # Load as collection 2 (same data, different ID)
        result2 = loader.load_collection("collection_2", test_sheets_dir)
        assert result2["success"] is True

        # Both should have same row counts
        assert result1["total_rows"] == result2["total_rows"]

        # Query each collection separately
        agent = SheetQueryAgent(test_db)

        result_c1 = agent.entity_lookup(
            query="collection 1",
            collection_id="collection_1",
            entity_type="chemical"
        )
        assert result_c1["success"] is True
        assert len(result_c1["data"]["entities"]) == 5

        result_c2 = agent.entity_lookup(
            query="collection 2",
            collection_id="collection_2",
            entity_type="chemical"
        )
        assert result_c2["success"] is True
        assert len(result_c2["data"]["entities"]) == 5


class TestQueryPerformance:
    """Test query performance and efficiency."""

    def test_entity_lookup_by_id_is_fast(self, test_db, test_sheets_dir):
        """Test entity lookup by ID uses indexes."""
        import time

        # Load data
        loader = SheetDataLoader(test_db)
        loader.load_collection("test_cmm", test_sheets_dir)

        # Query by ID should be very fast (indexed)
        agent = SheetQueryAgent(test_db)

        start = time.time()
        result = agent.entity_lookup(
            query="lookup by ID",
            collection_id="test_cmm",
            entity_id="CHEBI:52927"
        )
        elapsed = time.time() - start

        assert result["success"] is True
        assert elapsed < 0.1  # Should be under 100ms

    def test_publication_search_handles_large_text(self, test_db, test_sheets_dir):
        """Test publication search works with full-text content."""
        # Load data
        loader = SheetDataLoader(test_db)
        loader.load_collection("test_cmm", test_sheets_dir)

        # Search in publication text
        agent = SheetQueryAgent(test_db)
        result = agent.publication_search(
            query="search in full text",
            collection_id="test_cmm",
            keyword="lanthanide",
            include_excerpts=True
        )

        assert result["success"] is True
        pubs = result["data"]["publications"]
        assert len(pubs) > 0

        # Verify excerpts are reasonable size
        for pub in pubs:
            if "excerpt" in pub:
                assert len(pub["excerpt"]) < 1000  # Excerpts should be manageable


class TestErrorRecovery:
    """Test error handling and recovery."""

    def test_query_empty_collection(self, test_db):
        """Test querying collection with no data."""
        agent = SheetQueryAgent(test_db)

        result = agent.entity_lookup(
            query="query empty",
            collection_id="nonexistent",
            entity_id="CHEBI:52927"
        )

        # Should handle gracefully
        assert result["success"] is True
        assert len(result["data"]["entities"]) == 0

    def test_reload_collection(self, test_db, test_sheets_dir):
        """Test reloading a collection updates data."""
        loader = SheetDataLoader(test_db)

        # Load once
        result1 = loader.load_collection("test_cmm", test_sheets_dir)
        assert result1["success"] is True
        rows1 = result1["total_rows"]

        # Reload (should replace)
        result2 = loader.load_collection("test_cmm", test_sheets_dir)
        assert result2["success"] is True
        rows2 = result2["total_rows"]

        # Should have same number of rows
        assert rows1 == rows2


class TestOutputFormats:
    """Test all output formats produce valid results."""

    def test_all_query_types_all_formats(self, test_db, test_sheets_dir):
        """Test all query types with all output formats."""
        # Load data
        loader = SheetDataLoader(test_db)
        loader.load_collection("test_cmm", test_sheets_dir)

        skill = SheetQuerySkill(test_db)

        query_configs = [
            {
                "query_type": "entity_lookup",
                "entity_id": "CHEBI:52927"
            },
            {
                "query_type": "cross_reference",
                "source_entity_id": "K23995"
            },
            {
                "query_type": "publication_search",
                "keyword": "europium"
            },
            {
                "query_type": "filtered",
                "table_name": "chemicals",
                "filter_conditions": {"molecular_formula": "Eu3+"}
            }
        ]

        formats = ["markdown", "json", "evidence_report"]

        for config in query_configs:
            for fmt in formats:
                result = skill.run(
                    collection_id="test_cmm",
                    output_format=fmt,
                    **config
                )

                # All should produce valid output
                assert isinstance(result, str)
                assert len(result) > 0

                # JSON should be parseable
                if fmt == "json":
                    data = json.loads(result)
                    assert data["success"] is True

                # Markdown and evidence_report should have content
                else:
                    assert len(result) > 50  # Non-trivial content


class TestDataValidation:
    """Test data validation during loading."""

    def test_validate_after_load(self, test_db, test_sheets_dir):
        """Test validation reports accurate statistics."""
        loader = SheetDataLoader(test_db)
        loader.load_collection("test_cmm", test_sheets_dir)

        validation = loader.validate_loading("test_cmm")

        assert validation["success"] is True
        assert "tables_loaded" in validation
        assert "total_rows" in validation
        assert "publications_loaded" in validation
        assert "entity_counts" in validation

        # Entity counts by type
        counts = validation["entity_counts"]
        assert counts["chemical"] == 5
        assert counts["gene"] == 5

    def test_detect_missing_data(self, test_db):
        """Test validation detects missing collections."""
        loader = SheetDataLoader(test_db)

        validation = loader.validate_loading("nonexistent_collection")

        # Should handle gracefully - either success with 0 or error
        if validation.get("success"):
            assert validation.get("tables_loaded", 0) == 0
        else:
            assert "error" in validation

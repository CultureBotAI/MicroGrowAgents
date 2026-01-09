"""Test SheetQueryAgent for querying information sheets."""

import json
from pathlib import Path

import duckdb
import pytest

from microgrowagents.agents.sheet_query_agent import SheetQueryAgent
from microgrowagents.database.schema import create_schema
from microgrowagents.database.sheet_loader import SheetDataLoader


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


class TestSheetQueryAgent:
    """Test SheetQueryAgent initialization and basic functionality."""

    def test_agent_initialization(self, test_db):
        """Test agent can be initialized with database path."""
        agent = SheetQueryAgent(test_db)
        assert agent.db_path == test_db

    def test_agent_database_connection(self, test_db):
        """Test agent can connect to database."""
        agent = SheetQueryAgent(test_db)
        agent._connect()
        assert agent.conn is not None
        agent._close()


class TestEntityLookup:
    """Test entity lookup queries (Query Type 1)."""

    def test_lookup_entity_by_id(self, test_db):
        """Test looking up entity by exact ID."""
        agent = SheetQueryAgent(test_db)

        result = agent.entity_lookup(
            query="lookup chemical CHEBI:52927",
            collection_id="test_cmm",
            entity_id="CHEBI:52927"
        )

        assert result["success"] is True
        assert "entities" in result["data"]
        assert len(result["data"]["entities"]) == 1

        entity = result["data"]["entities"][0]
        assert entity["entity_id"] == "CHEBI:52927"
        assert entity["entity_name"] == "Europium(III) cation"
        assert entity["entity_type"] == "chemical"
        assert "properties" in entity
        assert entity["properties"]["molecular_formula"] == "Eu3+"

    def test_lookup_entity_by_name_exact(self, test_db):
        """Test looking up entity by exact name."""
        agent = SheetQueryAgent(test_db)

        result = agent.entity_lookup(
            query="find XoxF methanol dehydrogenase",
            collection_id="test_cmm",
            entity_name="PQQ-dependent methanol dehydrogenase (XoxF)"
        )

        assert result["success"] is True
        entities = result["data"]["entities"]
        assert len(entities) == 1
        assert entities[0]["entity_id"] == "K23995"
        assert "methanol dehydrogenase" in entities[0]["entity_name"]

    def test_lookup_entity_by_name_partial(self, test_db):
        """Test looking up entity by partial name match."""
        agent = SheetQueryAgent(test_db)

        result = agent.entity_lookup(
            query="find lanthanide compounds",
            collection_id="test_cmm",
            entity_name="lanthanide",
            exact_match=False
        )

        assert result["success"] is True
        entities = result["data"]["entities"]
        # Should find at least the Lanthanide-dependent methanol dehydrogenase
        assert len(entities) >= 1
        assert any("lanthanide" in e["entity_name"].lower() for e in entities)

    def test_lookup_by_entity_type(self, test_db):
        """Test looking up all entities of a specific type."""
        agent = SheetQueryAgent(test_db)

        result = agent.entity_lookup(
            query="list all chemicals",
            collection_id="test_cmm",
            entity_type="chemical"
        )

        assert result["success"] is True
        entities = result["data"]["entities"]
        assert len(entities) == 5  # 5 chemicals in test data
        assert all(e["entity_type"] == "chemical" for e in entities)

    def test_lookup_nonexistent_entity(self, test_db):
        """Test looking up entity that doesn't exist."""
        agent = SheetQueryAgent(test_db)

        result = agent.entity_lookup(
            query="find nonexistent entity",
            collection_id="test_cmm",
            entity_id="NONEXISTENT:999"
        )

        assert result["success"] is True
        assert len(result["data"]["entities"]) == 0


class TestCrossReferenceQuery:
    """Test cross-reference queries (Query Type 2)."""

    def test_find_related_entities(self, test_db):
        """Test finding entities related to a source entity."""
        agent = SheetQueryAgent(test_db)

        result = agent.cross_reference_query(
            query="find entities related to K23995",
            collection_id="test_cmm",
            source_entity_id="K23995"
        )

        assert result["success"] is True
        assert "source_entity" in result["data"]
        assert "related_entities" in result["data"]

        source = result["data"]["source_entity"]
        assert source["entity_id"] == "K23995"

        # Should find related chemicals via CHEBI references
        related = result["data"]["related_entities"]
        assert len(related) > 0

    def test_cross_reference_with_publications(self, test_db):
        """Test cross-reference includes publication links."""
        agent = SheetQueryAgent(test_db)

        result = agent.cross_reference_query(
            query="find what references CHEBI:52927",
            collection_id="test_cmm",
            source_entity_id="CHEBI:52927"
        )

        assert result["success"] is True
        assert "publications" in result["data"]

        # Should have publication references
        pubs = result["data"]["publications"]
        assert len(pubs) > 0

    def test_cross_reference_include_types(self, test_db):
        """Test filtering related entities by type."""
        agent = SheetQueryAgent(test_db)

        result = agent.cross_reference_query(
            query="find genes related to europium",
            collection_id="test_cmm",
            source_entity_id="CHEBI:52927",
            include_types=["gene"]
        )

        assert result["success"] is True
        related = result["data"]["related_entities"]
        # Only gene entities should be returned
        assert all(e["entity_type"] == "gene" for e in related)


class TestPublicationSearch:
    """Test full-text publication search (Query Type 3)."""

    def test_search_publications_single_keyword(self, test_db):
        """Test searching publications by keyword."""
        agent = SheetQueryAgent(test_db)

        result = agent.publication_search(
            query="search publications for europium",
            collection_id="test_cmm",
            keyword="europium"
        )

        assert result["success"] is True
        assert "publications" in result["data"]

        pubs = result["data"]["publications"]
        assert len(pubs) > 0

        # Check publication structure
        pub = pubs[0]
        assert "publication_id" in pub
        assert "title" in pub or "excerpt" in pub
        assert "full_text" in pub or "excerpt" in pub

    def test_search_publications_multiple_keywords(self, test_db):
        """Test searching with multiple keywords."""
        agent = SheetQueryAgent(test_db)

        result = agent.publication_search(
            query="search for lanthanide and methanol",
            collection_id="test_cmm",
            keywords=["lanthanide", "methanol"]
        )

        assert result["success"] is True
        pubs = result["data"]["publications"]

        # Should find publications containing both terms
        assert len(pubs) > 0
        for pub in pubs:
            full_text_lower = pub["full_text"].lower()
            assert "lanthanide" in full_text_lower or "methanol" in full_text_lower

    def test_search_publications_with_excerpts(self, test_db):
        """Test that search returns context excerpts."""
        agent = SheetQueryAgent(test_db)

        result = agent.publication_search(
            query="search for europium",
            collection_id="test_cmm",
            keyword="europium",
            include_excerpts=True
        )

        assert result["success"] is True
        pubs = result["data"]["publications"]
        assert len(pubs) > 0

        # At least one publication should have an excerpt
        assert any("excerpt" in pub for pub in pubs)

    def test_search_publications_max_results(self, test_db):
        """Test limiting search results."""
        agent = SheetQueryAgent(test_db)

        result = agent.publication_search(
            query="search all publications",
            collection_id="test_cmm",
            keyword="the",  # Common word
            max_results=1
        )

        assert result["success"] is True
        pubs = result["data"]["publications"]
        assert len(pubs) <= 1

    def test_search_publications_with_entity_counts(self, test_db):
        """Test that publications include entity reference counts."""
        agent = SheetQueryAgent(test_db)

        result = agent.publication_search(
            query="search for lanthanide",
            collection_id="test_cmm",
            keyword="lanthanide"
        )

        assert result["success"] is True
        pubs = result["data"]["publications"]

        # Publications should have entity_count
        for pub in pubs:
            assert "entity_count" in pub
            assert isinstance(pub["entity_count"], int)


class TestFilteredQuery:
    """Test filtered table queries (Query Type 4)."""

    def test_filter_by_property_equals(self, test_db):
        """Test filtering entities by property equality."""
        agent = SheetQueryAgent(test_db)

        result = agent.filtered_query(
            query="filter chemicals by molecular formula",
            collection_id="test_cmm",
            table_name="chemicals",
            filter_conditions={
                "molecular_formula": "Eu3+"
            }
        )

        assert result["success"] is True
        entities = result["data"]["entities"]
        assert len(entities) == 1
        assert entities[0]["properties"]["molecular_formula"] == "Eu3+"

    def test_filter_by_property_contains(self, test_db):
        """Test filtering with contains operator."""
        agent = SheetQueryAgent(test_db)

        result = agent.filtered_query(
            query="filter genes containing methanol in annotation",
            collection_id="test_cmm",
            table_name="genes_and_proteins",
            filter_conditions={
                "annotation": {"$contains": "methanol"}
            }
        )

        assert result["success"] is True
        entities = result["data"]["entities"]
        assert len(entities) >= 1
        for entity in entities:
            assert "methanol" in entity["properties"]["annotation"].lower()

    def test_filter_multiple_conditions(self, test_db):
        """Test filtering with multiple conditions (AND logic)."""
        agent = SheetQueryAgent(test_db)

        result = agent.filtered_query(
            query="filter genes by organism and annotation",
            collection_id="test_cmm",
            table_name="genes_and_proteins",
            filter_conditions={
                "organism": "NCBITaxon:469",
                "annotation": {"$contains": "dehydrogenase"}
            }
        )

        assert result["success"] is True
        entities = result["data"]["entities"]

        # All results should match both conditions
        for entity in entities:
            assert entity["properties"]["organism"] == "NCBITaxon:469"
            assert "dehydrogenase" in entity["properties"]["annotation"].lower()

    def test_filter_by_entity_type(self, test_db):
        """Test filtering combined with entity type."""
        agent = SheetQueryAgent(test_db)

        result = agent.filtered_query(
            query="filter all chemical entities",
            collection_id="test_cmm",
            entity_type="chemical"
        )

        assert result["success"] is True
        entities = result["data"]["entities"]
        assert all(e["entity_type"] == "chemical" for e in entities)

    def test_filter_no_matches(self, test_db):
        """Test filter with no matching results."""
        agent = SheetQueryAgent(test_db)

        result = agent.filtered_query(
            query="filter by impossible condition",
            collection_id="test_cmm",
            table_name="chemicals",
            filter_conditions={
                "chemical_id": "NONEXISTENT:999"
            }
        )

        assert result["success"] is True
        assert len(result["data"]["entities"]) == 0


class TestQueryRouting:
    """Test query routing in run() method."""

    def test_run_routes_to_entity_lookup(self, test_db):
        """Test that run() routes lookup queries correctly."""
        agent = SheetQueryAgent(test_db)

        result = agent.run(
            query="lookup chemical CHEBI:52927",
            collection_id="test_cmm",
            entity_id="CHEBI:52927"
        )

        assert result["success"] is True
        assert "entities" in result["data"]

    def test_run_routes_to_cross_reference(self, test_db):
        """Test that run() routes cross-reference queries."""
        agent = SheetQueryAgent(test_db)

        result = agent.run(
            query="find entities related to K23995",
            collection_id="test_cmm",
            source_entity_id="K23995"
        )

        assert result["success"] is True
        assert "related_entities" in result["data"]

    def test_run_routes_to_publication_search(self, test_db):
        """Test that run() routes publication searches."""
        agent = SheetQueryAgent(test_db)

        result = agent.run(
            query="search publications for europium",
            collection_id="test_cmm",
            keyword="europium"
        )

        assert result["success"] is True
        assert "publications" in result["data"]

    def test_run_routes_to_filtered_query(self, test_db):
        """Test that run() routes filter queries."""
        agent = SheetQueryAgent(test_db)

        result = agent.run(
            query="filter chemicals by formula",
            collection_id="test_cmm",
            table_name="chemicals",
            filter_conditions={"molecular_formula": "Eu3+"}
        )

        assert result["success"] is True
        assert "entities" in result["data"]

    def test_run_unknown_query_type(self, test_db):
        """Test handling of unknown query types."""
        agent = SheetQueryAgent(test_db)

        result = agent.run(
            query="do something unknown",
            collection_id="test_cmm"
        )

        assert result["success"] is False
        assert "error" in result


class TestErrorHandling:
    """Test error handling in agent."""

    def test_query_nonexistent_collection(self, test_db):
        """Test querying collection that doesn't exist."""
        agent = SheetQueryAgent(test_db)

        result = agent.entity_lookup(
            query="lookup in nonexistent collection",
            collection_id="nonexistent",
            entity_id="CHEBI:52927"
        )

        # Should handle gracefully
        assert result["success"] is True
        assert len(result["data"]["entities"]) == 0

    def test_malformed_filter_conditions(self, test_db):
        """Test handling malformed filter conditions."""
        agent = SheetQueryAgent(test_db)

        result = agent.filtered_query(
            query="filter with bad conditions",
            collection_id="test_cmm",
            table_name="chemicals",
            filter_conditions={"invalid": {"$unknown_operator": "value"}}
        )

        # Should either handle gracefully or return error
        assert "success" in result

"""Test KG Reasoning Agent for MicroGrowAgents.

Tests the Knowledge Graph Reasoning Agent that provides advanced graph queries,
pathway discovery, and graph algorithm capabilities using GRAPE.

Query Types Tested:
1. lookup <node_id>: Get node details
2. neighbors <node_id> [predicate]: Get neighbors
3. path <source> <target>: Shortest path(s)
4. traverse <start> <predicates>: Multi-hop traversal
5. filter <category>: Filter by category
6. enzymes_using <substrate_id>: Find enzymes using substrate
7. phenotype_media <phenotype_ids>: Find media for phenotypes
8. media_ingredients <media_id>: Get media ingredients pathway
9. centrality <category>: Graph centrality analysis
10. subgraph <node_ids>: Extract subgraph

Following TDD: These tests are written BEFORE implementation.
"""

import pytest
from pathlib import Path
import duckdb
import pandas as pd
import tempfile

from microgrowagents.kg.loader import KGLoader
from microgrowagents.kg.graph_builder import GraphBuilder, GRAPE_AVAILABLE
from microgrowagents.database.schema import create_schema


# Skip all tests if GRAPE is not available
pytestmark = pytest.mark.skipif(
    not GRAPE_AVAILABLE,
    reason="GRAPE not available - see docs/grape_installation.md"
)


@pytest.fixture
def test_kg_dir(tmp_path):
    """Create test KG data directory with sample TSV files."""
    kg_dir = tmp_path / "kg_microbe_core"
    kg_dir.mkdir()

    # Create sample nodes with diverse categories
    nodes_data = """id\tcategory\tname
CHEBI:16828\tbiolink:ChemicalSubstance\theme
CHEBI:15841\tbiolink:ChemicalSubstance\tpolypeptide
CHEBI:24431\tbiolink:ChemicalSubstance\tchemical entity
NCBITaxon:562\tbiolink:OrganismTaxon\tEscherichia coli
EC:4.1.99.1\tbiolink:MolecularActivity\ttryptophan deaminase
METPO:2000303\tbiolink:Phenotype\taerobic growth
METPO:2000517\tbiolink:Medium\tLB medium
CHEBI:51460\tbiolink:Role\tmetabolic role"""

    with open(kg_dir / "merged-kg_nodes.tsv", "w") as f:
        f.write(nodes_data)

    # Create sample edges with diverse predicates
    edges_data = """subject\tpredicate\tobject
CHEBI:16828\tbiolink:subclass_of\tCHEBI:15841
CHEBI:15841\tbiolink:subclass_of\tCHEBI:24431
CHEBI:16828\tbiolink:has_role\tCHEBI:51460
NCBITaxon:562\tbiolink:has_phenotype\tMETPO:2000303
EC:4.1.99.1\tbiolink:has_input\tCHEBI:16828
NCBITaxon:562\tMETPO:grows_in\tMETPO:2000517
METPO:2000517\tbiolink:has_part\tCHEBI:16828"""

    with open(kg_dir / "merged-kg_edges.tsv", "w") as f:
        f.write(edges_data)

    return kg_dir


@pytest.fixture
def test_db_with_kg(tmp_path, test_kg_dir):
    """Create test database with full KG data loaded."""
    db_path = tmp_path / "test_kg.duckdb"
    conn = duckdb.connect(str(db_path))
    create_schema(conn)
    conn.close()

    # Load KG data
    loader = KGLoader(db_path)
    nodes_file = test_kg_dir / "merged-kg_nodes.tsv"
    edges_file = test_kg_dir / "merged-kg_edges.tsv"
    loader.load_kg_microbe(nodes_file, edges_file, build_hierarchies=True)
    loader.close()

    return db_path


class TestKGReasoningAgentInit:
    """Test KGReasoningAgent initialization."""

    def test_init_with_db_path(self, test_db_with_kg):
        """Test agent initialization with database path."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        assert agent.db_path == test_db_with_kg
        assert agent.conn is not None

    def test_init_without_db_path_raises_error(self):
        """Test that initialization without DB path raises appropriate error."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        with pytest.raises((ValueError, TypeError)):
            agent = KGReasoningAgent(db_path=None)

    def test_lazy_graph_loading(self, test_db_with_kg):
        """Test that graph is loaded lazily (not on init)."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg, lazy_load_graph=True)
        # Graph should not be loaded yet
        assert agent._graph is None

        # Access graph property triggers loading
        graph = agent.graph
        assert graph is not None
        assert agent._graph is not None

    def test_eager_graph_loading(self, test_db_with_kg):
        """Test that graph can be loaded eagerly on init."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg, lazy_load_graph=False)
        # Graph should be loaded immediately
        assert agent._graph is not None


class TestLookupQuery:
    """Test lookup query: get node details by ID."""

    def test_lookup_existing_node(self, test_db_with_kg):
        """Test looking up a node that exists."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("lookup CHEBI:16828")

        assert result["success"] is True
        assert result["node_id"] == "CHEBI:16828"
        assert result["name"] == "heme"
        assert result["category"] == "biolink:ChemicalSubstance"

    def test_lookup_nonexistent_node(self, test_db_with_kg):
        """Test looking up a node that doesn't exist."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("lookup NONEXISTENT:123")

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_lookup_returns_full_details(self, test_db_with_kg):
        """Test that lookup returns all node properties."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("lookup CHEBI:16828")

        assert "node_id" in result
        assert "name" in result
        assert "category" in result
        # Optional fields may be None
        assert "description" in result or result["description"] is None
        assert "xref" in result or result["xref"] is None


class TestNeighborsQuery:
    """Test neighbors query: get adjacent nodes."""

    def test_neighbors_all_predicates(self, test_db_with_kg):
        """Test getting all neighbors regardless of predicate."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("neighbors CHEBI:16828")

        assert result["success"] is True
        assert "neighbors" in result
        assert len(result["neighbors"]) > 0

        # Should include neighbors via subclass_of and has_role
        neighbor_ids = [n["node_id"] for n in result["neighbors"]]
        assert "CHEBI:15841" in neighbor_ids  # subclass_of
        assert "CHEBI:51460" in neighbor_ids  # has_role

    def test_neighbors_filtered_by_predicate(self, test_db_with_kg):
        """Test getting neighbors filtered by specific predicate."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("neighbors CHEBI:16828 biolink:subclass_of")

        assert result["success"] is True
        assert len(result["neighbors"]) == 1
        assert result["neighbors"][0]["node_id"] == "CHEBI:15841"
        assert result["neighbors"][0]["predicate"] == "biolink:subclass_of"

    def test_neighbors_includes_edge_direction(self, test_db_with_kg):
        """Test that neighbors query includes edge direction info."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("neighbors CHEBI:16828")

        assert result["success"] is True
        for neighbor in result["neighbors"]:
            assert "direction" in neighbor
            assert neighbor["direction"] in ["outgoing", "incoming"]

    def test_neighbors_node_without_edges(self, test_db_with_kg):
        """Test querying neighbors for a node with no edges."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        # Create isolated node
        agent = KGReasoningAgent(db_path=test_db_with_kg)
        # CHEBI:24431 has no outgoing edges in test data
        result = agent.run("neighbors CHEBI:24431")

        assert result["success"] is True
        # May have incoming edges, so just check it doesn't crash
        assert "neighbors" in result


class TestPathQuery:
    """Test path finding query using GRAPE algorithms."""

    def test_shortest_path_exists(self, test_db_with_kg):
        """Test finding shortest path between two connected nodes."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("path CHEBI:16828 CHEBI:24431")

        assert result["success"] is True
        assert "path" in result
        assert len(result["path"]) >= 3  # source, intermediate(s), target
        assert result["path"][0] == "CHEBI:16828"
        assert result["path"][-1] == "CHEBI:24431"

    def test_path_returns_intermediate_nodes(self, test_db_with_kg):
        """Test that path includes intermediate nodes."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("path CHEBI:16828 CHEBI:24431")

        assert result["success"] is True
        # Path should be: CHEBI:16828 -> CHEBI:15841 -> CHEBI:24431
        assert "CHEBI:15841" in result["path"]

    def test_path_no_connection(self, test_db_with_kg):
        """Test path query when no path exists between nodes."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        # Try to find path between unconnected components
        result = agent.run("path EC:4.1.99.1 METPO:2000303")

        # Should either return no path or indicate disconnected
        assert result["success"] is False or result["path"] is None

    def test_path_with_max_hops_limit(self, test_db_with_kg):
        """Test path finding with max hops constraint."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("path CHEBI:16828 CHEBI:24431", max_hops=1)

        # Should fail because path requires 2 hops
        assert result["success"] is False or len(result["path"]) <= 2


class TestQueryRouting:
    """Test query type routing and parsing."""

    def test_unknown_query_type_raises_error(self, test_db_with_kg):
        """Test that unknown query type returns error."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("invalid_query CHEBI:16828")

        assert result["success"] is False
        assert "unknown" in result["error"].lower() or "invalid" in result["error"].lower()

    def test_query_routing_to_correct_handler(self, test_db_with_kg):
        """Test that queries route to correct handlers."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)

        # Test different query types
        lookup_result = agent.run("lookup CHEBI:16828")
        assert "node_id" in lookup_result  # Lookup-specific field

        neighbors_result = agent.run("neighbors CHEBI:16828")
        assert "neighbors" in neighbors_result  # Neighbors-specific field

        path_result = agent.run("path CHEBI:16828 CHEBI:15841")
        assert "path" in path_result  # Path-specific field


class TestEnzymesUsingQuery:
    """Test USE CASE 3: Find enzymes using a substrate."""

    def test_enzymes_using_substrate(self, test_db_with_kg):
        """Test finding enzymes that use a specific substrate."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("enzymes_using CHEBI:16828")

        assert result["success"] is True
        assert "enzymes" in result
        assert len(result["enzymes"]) > 0

        # Should find EC:4.1.99.1 which has_input CHEBI:16828
        enzyme_ids = [e["enzyme_id"] for e in result["enzymes"]]
        assert "EC:4.1.99.1" in enzyme_ids

    def test_enzymes_using_includes_enzyme_details(self, test_db_with_kg):
        """Test that enzyme results include name and relationship."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("enzymes_using CHEBI:16828")

        assert result["success"] is True
        for enzyme in result["enzymes"]:
            assert "enzyme_id" in enzyme
            assert "enzyme_name" in enzyme
            assert "relationship" in enzyme

    def test_enzymes_using_no_enzymes_found(self, test_db_with_kg):
        """Test querying for substrate with no associated enzymes."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("enzymes_using CHEBI:24431")

        assert result["success"] is True
        assert len(result["enzymes"]) == 0


class TestMediaIngredientsQuery:
    """Test USE CASE 1: Get media ingredients pathway."""

    def test_media_ingredients_pathway(self, test_db_with_kg):
        """Test getting full pathway from media to ingredients."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("media_ingredients METPO:2000517")

        assert result["success"] is True
        assert "media_info" in result
        assert "ingredients" in result
        assert result["media_info"]["media_id"] == "METPO:2000517"

    def test_media_ingredients_includes_chemical_details(self, test_db_with_kg):
        """Test that ingredients include chemical properties."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("media_ingredients METPO:2000517")

        assert result["success"] is True
        # Should include CHEBI:16828 via biolink:has_part
        ingredient_ids = [i["ingredient_id"] for i in result["ingredients"]]
        assert "CHEBI:16828" in ingredient_ids


class TestPhenotypeMediaQuery:
    """Test USE CASE 2: Find media for phenotypes."""

    def test_phenotype_media_recommendations(self, test_db_with_kg):
        """Test finding media suitable for organisms with specific phenotypes."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("phenotype_media METPO:2000303")

        assert result["success"] is True
        assert "recommended_media" in result
        assert len(result["recommended_media"]) > 0

    def test_phenotype_media_includes_organism_count(self, test_db_with_kg):
        """Test that media recommendations include organism counts."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("phenotype_media METPO:2000303")

        assert result["success"] is True
        for media in result["recommended_media"]:
            assert "media_id" in media
            assert "organism_count" in media
            assert media["organism_count"] > 0


class TestCentralityQuery:
    """Test graph centrality analysis using GRAPE algorithms."""

    def test_centrality_betweenness(self, test_db_with_kg):
        """Test betweenness centrality calculation."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("centrality biolink:ChemicalSubstance", algorithm="betweenness")

        assert result["success"] is True
        assert "centrality_scores" in result
        assert len(result["centrality_scores"]) > 0

        # Scores should be floats
        for node_id, score in result["centrality_scores"].items():
            assert isinstance(score, float)

    def test_centrality_pagerank(self, test_db_with_kg):
        """Test PageRank centrality calculation."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("centrality biolink:ChemicalSubstance", algorithm="pagerank")

        assert result["success"] is True
        assert "centrality_scores" in result

    def test_centrality_filters_by_category(self, test_db_with_kg):
        """Test that centrality respects category filtering."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("centrality biolink:ChemicalSubstance")

        assert result["success"] is True
        # All returned nodes should be ChemicalSubstance
        for node_id in result["centrality_scores"].keys():
            # Verify by lookup
            assert node_id.startswith("CHEBI:")


class TestSubgraphQuery:
    """Test subgraph extraction."""

    def test_extract_subgraph_single_node(self, test_db_with_kg):
        """Test extracting subgraph around a single node."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("subgraph CHEBI:16828", radius=1)

        assert result["success"] is True
        assert "subgraph" in result
        assert result["subgraph"] is not None

    def test_extract_subgraph_multiple_nodes(self, test_db_with_kg):
        """Test extracting subgraph around multiple nodes."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("subgraph CHEBI:16828,CHEBI:15841", radius=1)

        assert result["success"] is True
        assert "subgraph" in result


class TestFilterQuery:
    """Test filtering nodes by category."""

    def test_filter_by_category(self, test_db_with_kg):
        """Test filtering nodes by biolink category."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("filter biolink:ChemicalSubstance")

        assert result["success"] is True
        assert "nodes" in result
        assert len(result["nodes"]) > 0

        # All nodes should be ChemicalSubstance
        for node in result["nodes"]:
            assert node["category"] == "biolink:ChemicalSubstance"

    def test_filter_with_limit(self, test_db_with_kg):
        """Test filtering with result limit."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("filter biolink:ChemicalSubstance", limit=2)

        assert result["success"] is True
        assert len(result["nodes"]) <= 2


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_empty_query_returns_error(self, test_db_with_kg):
        """Test that empty query returns error."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("")

        assert result["success"] is False
        assert "error" in result

    def test_malformed_query_returns_error(self, test_db_with_kg):
        """Test that malformed query returns error."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)
        result = agent.run("lookup")  # Missing node_id argument

        assert result["success"] is False
        assert "error" in result

    def test_database_error_handled_gracefully(self, tmp_path):
        """Test that database errors are handled gracefully."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        # Try to use non-existent database
        with pytest.raises((ValueError, FileNotFoundError, duckdb.Error)):
            agent = KGReasoningAgent(db_path=tmp_path / "nonexistent.db")
            result = agent.run("lookup CHEBI:16828")


class TestIntegration:
    """Integration tests for full workflows."""

    def test_organism_to_media_workflow(self, test_db_with_kg):
        """Test complete workflow: organism -> phenotype -> media -> ingredients."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)

        # 1. Lookup organism
        organism = agent.run("lookup NCBITaxon:562")
        assert organism["success"] is True

        # 2. Get neighbors (phenotypes)
        phenotypes = agent.run("neighbors NCBITaxon:562 biolink:has_phenotype")
        assert phenotypes["success"] is True

        # 3. Find suitable media
        media = agent.run("phenotype_media METPO:2000303")
        assert media["success"] is True

        # 4. Get media ingredients
        ingredients = agent.run("media_ingredients METPO:2000517")
        assert ingredients["success"] is True

    def test_enzyme_substrate_workflow(self, test_db_with_kg):
        """Test workflow: substrate -> enzymes -> enzyme details."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)

        # 1. Find enzymes using substrate
        enzymes = agent.run("enzymes_using CHEBI:16828")
        assert enzymes["success"] is True
        assert len(enzymes["enzymes"]) > 0

        # 2. Lookup enzyme details
        enzyme_id = enzymes["enzymes"][0]["enzyme_id"]
        enzyme_details = agent.run(f"lookup {enzyme_id}")
        assert enzyme_details["success"] is True

    def test_path_and_centrality_workflow(self, test_db_with_kg):
        """Test workflow combining path finding and centrality analysis."""
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)

        # 1. Find path
        path = agent.run("path CHEBI:16828 CHEBI:24431")
        assert path["success"] is True

        # 2. Calculate centrality of intermediate nodes
        centrality = agent.run("centrality biolink:ChemicalSubstance", algorithm="betweenness")
        assert centrality["success"] is True

        # Intermediate node CHEBI:15841 should have non-zero centrality
        assert "CHEBI:15841" in centrality["centrality_scores"]
        assert centrality["centrality_scores"]["CHEBI:15841"] > 0


class TestPerformance:
    """Test performance characteristics of agent queries."""

    def test_lookup_query_is_fast(self, test_db_with_kg):
        """Test that SQL-based lookup is fast (<100ms)."""
        import time
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)

        start = time.time()
        result = agent.run("lookup CHEBI:16828")
        elapsed = time.time() - start

        assert result["success"] is True
        assert elapsed < 0.1  # <100ms

    def test_neighbors_query_is_fast(self, test_db_with_kg):
        """Test that SQL-based neighbors query is fast (<100ms)."""
        import time
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)

        start = time.time()
        result = agent.run("neighbors CHEBI:16828")
        elapsed = time.time() - start

        assert result["success"] is True
        assert elapsed < 0.1  # <100ms

    def test_path_query_reasonable_time(self, test_db_with_kg):
        """Test that GRAPE path finding completes in reasonable time."""
        import time
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        agent = KGReasoningAgent(db_path=test_db_with_kg)

        start = time.time()
        result = agent.run("path CHEBI:16828 CHEBI:24431")
        elapsed = time.time() - start

        assert result["success"] is True
        # For small test graph, should be very fast (<1s)
        assert elapsed < 1.0

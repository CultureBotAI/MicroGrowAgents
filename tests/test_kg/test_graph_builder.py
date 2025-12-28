"""Test GRAPE graph builder for KG-Microbe.

Tests building GRAPE (Graph Representation leArning, Predictions and Evaluations) graphs
from KG-Microbe data for high-performance graph algorithms.

GRAPE advantages over NetworkX:
- 10-100x faster for large graphs (5M edges)
- Rust backend with zero-copy memory mapping
- Direct TSV loading (5-15s vs 60s)
- Memory efficient (~800MB vs ~2GB)

Following TDD: These tests are written BEFORE implementation.
"""

import pytest
from pathlib import Path
import duckdb
import pandas as pd
import tempfile

from microgrowagents.kg.graph_builder import GraphBuilder
from microgrowagents.kg.loader import KGLoader
from microgrowagents.database.schema import create_schema


@pytest.fixture
def test_kg_dir(tmp_path):
    """Create test KG data directory with sample TSV files."""
    kg_dir = tmp_path / "kg_microbe_core"
    kg_dir.mkdir()

    # Create sample nodes TSV (GRAPE format: simpler than full KG nodes)
    # For GRAPE we need: node_id, node_type
    nodes_data = """id\tcategory\tname
CHEBI:16828\tbiolink:ChemicalSubstance\theme
CHEBI:15841\tbiolink:ChemicalSubstance\tpolypeptide
CHEBI:24431\tbiolink:ChemicalSubstance\tchemical entity
NCBITaxon:562\tbiolink:OrganismTaxon\tEscherichia coli
EC:4.1.99.1\tbiolink:MolecularActivity\ttryptophan deaminase"""

    with open(kg_dir / "merged-kg_nodes.tsv", "w") as f:
        f.write(nodes_data)

    # Create sample edges TSV (GRAPE format: source, edge_type, destination)
    edges_data = """subject\tpredicate\tobject
CHEBI:16828\tbiolink:subclass_of\tCHEBI:15841
CHEBI:15841\tbiolink:subclass_of\tCHEBI:24431
CHEBI:16828\tbiolink:has_role\tCHEBI:51460
NCBITaxon:562\tbiolink:has_phenotype\tMETPO:2000303
EC:4.1.99.1\tbiolink:has_input\tCHEBI:16828"""

    with open(kg_dir / "merged-kg_edges.tsv", "w") as f:
        f.write(edges_data)

    return kg_dir


@pytest.fixture
def test_db_with_data(tmp_path, test_kg_dir):
    """Create test database with KG data loaded."""
    db_path = tmp_path / "test_kg.duckdb"
    conn = duckdb.connect(str(db_path))
    create_schema(conn)
    conn.close()

    # Load data using KGLoader
    loader = KGLoader(db_path)
    nodes_file = test_kg_dir / "merged-kg_nodes.tsv"
    edges_file = test_kg_dir / "merged-kg_edges.tsv"
    loader.load_kg_microbe(nodes_file, edges_file, build_hierarchies=False)
    loader.close()

    return db_path


class TestGraphBuilderInit:
    """Test GraphBuilder initialization."""

    def test_init_with_db_path(self, test_db_with_data):
        """Test GraphBuilder initialization with database path."""
        builder = GraphBuilder(test_db_with_data)
        assert builder.db_path == test_db_with_data
        assert builder.conn is not None

    def test_init_creates_connection(self, test_db_with_data):
        """Test that initialization creates a valid DuckDB connection."""
        builder = GraphBuilder(test_db_with_data)
        # Should be able to query the database
        result = builder.conn.execute("SELECT COUNT(*) FROM kg_nodes").fetchone()[0]
        assert result > 0


class TestBuildFromTSVDirect:
    """Test direct TSV loading (fastest method)."""

    def test_build_from_tsv_creates_graph(self, test_kg_dir):
        """Test that build_from_tsv_direct creates a GRAPE Graph."""
        builder = GraphBuilder(None)  # No DB needed for direct TSV

        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"
        edges_file = test_kg_dir / "merged-kg_edges.tsv"

        graph = builder.build_from_tsv_direct(nodes_file, edges_file)

        # Should return a GRAPE Graph object
        assert graph is not None
        assert hasattr(graph, 'get_number_of_nodes')
        assert hasattr(graph, 'get_number_of_edges')

    def test_tsv_graph_has_correct_node_count(self, test_kg_dir):
        """Test that TSV-loaded graph has correct number of nodes."""
        builder = GraphBuilder(None)

        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"
        edges_file = test_kg_dir / "merged-kg_edges.tsv"

        graph = builder.build_from_tsv_direct(nodes_file, edges_file)

        # Should have 5 nodes from our test data
        assert graph.get_number_of_nodes() == 5

    def test_tsv_graph_has_correct_edge_count(self, test_kg_dir):
        """Test that TSV-loaded graph has correct number of edges."""
        builder = GraphBuilder(None)

        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"
        edges_file = test_kg_dir / "merged-kg_edges.tsv"

        graph = builder.build_from_tsv_direct(nodes_file, edges_file)

        # Should have 5 edges from our test data
        assert graph.get_number_of_edges() == 5

    def test_tsv_graph_preserves_node_names(self, test_kg_dir):
        """Test that node names are preserved in the graph."""
        builder = GraphBuilder(None)

        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"
        edges_file = test_kg_dir / "merged-kg_edges.tsv"

        graph = builder.build_from_tsv_direct(nodes_file, edges_file)

        # Check that we can query nodes by name
        node_names = graph.get_node_names()
        assert "CHEBI:16828" in node_names
        assert "NCBITaxon:562" in node_names

    def test_tsv_graph_handles_edge_types(self, test_kg_dir):
        """Test that edge types (predicates) are preserved."""
        builder = GraphBuilder(None)

        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"
        edges_file = test_kg_dir / "merged-kg_edges.tsv"

        graph = builder.build_from_tsv_direct(nodes_file, edges_file)

        # GRAPE stores edge types - check if they're preserved
        edge_types = graph.get_unique_edge_type_names()
        assert "biolink:subclass_of" in edge_types
        assert "biolink:has_phenotype" in edge_types


class TestBuildFromDuckDB:
    """Test building graph from DuckDB with filtering."""

    def test_build_from_duckdb_creates_graph(self, test_db_with_data):
        """Test that build_from_duckdb creates a GRAPE Graph."""
        builder = GraphBuilder(test_db_with_data)

        graph = builder.build_from_duckdb()

        assert graph is not None
        assert hasattr(graph, 'get_number_of_nodes')

    def test_duckdb_graph_has_all_nodes(self, test_db_with_data):
        """Test that DuckDB graph loads all nodes."""
        builder = GraphBuilder(test_db_with_data)

        graph = builder.build_from_duckdb()

        # Should have all 5 nodes
        assert graph.get_number_of_nodes() == 5

    def test_duckdb_graph_filter_by_category(self, test_db_with_data):
        """Test filtering nodes by category."""
        builder = GraphBuilder(test_db_with_data)

        # Only load ChemicalSubstance nodes
        graph = builder.build_from_duckdb(
            node_categories={"biolink:ChemicalSubstance"}
        )

        # Should have 3 ChemicalSubstance nodes (CHEBI:16828, 15841, 24431)
        assert graph.get_number_of_nodes() == 3

    def test_duckdb_graph_filter_by_predicate(self, test_db_with_data):
        """Test filtering edges by predicate."""
        builder = GraphBuilder(test_db_with_data)

        # Only load subclass_of edges
        graph = builder.build_from_duckdb(
            edge_predicates={"biolink:subclass_of"}
        )

        # Should have fewer edges (only subclass_of: 2 edges)
        # But all nodes that appear in those edges should be included
        assert graph.get_number_of_edges() == 2

    def test_duckdb_graph_filter_both_category_and_predicate(self, test_db_with_data):
        """Test filtering by both category and predicate."""
        builder = GraphBuilder(test_db_with_data)

        graph = builder.build_from_duckdb(
            node_categories={"biolink:ChemicalSubstance"},
            edge_predicates={"biolink:subclass_of"}
        )

        # Only ChemicalSubstance nodes with subclass_of edges
        assert graph.get_number_of_nodes() == 3  # CHEBI nodes
        assert graph.get_number_of_edges() == 2  # 2 subclass_of edges

    def test_duckdb_graph_empty_filter_returns_empty_graph(self, test_db_with_data):
        """Test that filtering with non-existent category returns empty graph."""
        builder = GraphBuilder(test_db_with_data)

        graph = builder.build_from_duckdb(
            node_categories={"biolink:NonExistentCategory"}
        )

        # Should have 0 nodes
        assert graph.get_number_of_nodes() == 0


class TestBuildGraph:
    """Test main build_graph method (with strategy selection)."""

    def test_build_graph_direct_tsv_strategy(self, test_kg_dir):
        """Test build_graph with direct TSV strategy."""
        builder = GraphBuilder(None)

        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"
        edges_file = test_kg_dir / "merged-kg_edges.tsv"

        graph = builder.build_graph(
            nodes_file=nodes_file,
            edges_file=edges_file,
            use_tsv_direct=True
        )

        assert graph.get_number_of_nodes() == 5
        assert graph.get_number_of_edges() == 5

    def test_build_graph_duckdb_strategy(self, test_db_with_data):
        """Test build_graph with DuckDB strategy."""
        builder = GraphBuilder(test_db_with_data)

        graph = builder.build_graph(use_tsv_direct=False)

        assert graph.get_number_of_nodes() == 5

    def test_build_graph_with_filtering(self, test_db_with_data):
        """Test build_graph with category filtering."""
        builder = GraphBuilder(test_db_with_data)

        graph = builder.build_graph(
            use_tsv_direct=False,
            node_categories={"biolink:ChemicalSubstance"}
        )

        assert graph.get_number_of_nodes() == 3


class TestGraphProperties:
    """Test graph properties and methods."""

    def test_graph_is_directed(self, test_kg_dir):
        """Test that the graph is directed."""
        builder = GraphBuilder(None)

        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"
        edges_file = test_kg_dir / "merged-kg_edges.tsv"

        graph = builder.build_from_tsv_direct(nodes_file, edges_file)

        # GRAPE graphs should be directed
        assert graph.is_directed()

    def test_graph_has_node_types(self, test_kg_dir):
        """Test that graph preserves node types (categories)."""
        builder = GraphBuilder(None)

        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"
        edges_file = test_kg_dir / "merged-kg_edges.tsv"

        graph = builder.build_from_tsv_direct(nodes_file, edges_file)

        # Should have node types
        node_types = graph.get_unique_node_type_names()
        assert len(node_types) > 0
        assert "biolink:ChemicalSubstance" in node_types

    def test_graph_supports_node_lookup(self, test_kg_dir):
        """Test that we can look up nodes by name."""
        builder = GraphBuilder(None)

        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"
        edges_file = test_kg_dir / "merged-kg_edges.tsv"

        graph = builder.build_from_tsv_direct(nodes_file, edges_file)

        # Should be able to get node ID from name
        node_id = graph.get_node_id_from_node_name("CHEBI:16828")
        assert node_id is not None
        assert node_id >= 0

    def test_graph_supports_neighbors_query(self, test_kg_dir):
        """Test that we can query node neighbors."""
        builder = GraphBuilder(None)

        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"
        edges_file = test_kg_dir / "merged-kg_edges.tsv"

        graph = builder.build_from_tsv_direct(nodes_file, edges_file)

        # Get neighbors of CHEBI:16828
        node_id = graph.get_node_id_from_node_name("CHEBI:16828")
        neighbors = graph.get_neighbour_node_ids_from_node_id(node_id)

        # Should have neighbors (CHEBI:15841 and CHEBI:51460)
        assert len(neighbors) > 0


class TestPerformance:
    """Test performance characteristics."""

    def test_tsv_loading_is_fast(self, test_kg_dir):
        """Test that TSV loading completes quickly."""
        import time

        builder = GraphBuilder(None)

        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"
        edges_file = test_kg_dir / "merged-kg_edges.tsv"

        start = time.time()
        graph = builder.build_from_tsv_direct(nodes_file, edges_file)
        elapsed = time.time() - start

        # Should complete in < 1 second for small test data
        assert elapsed < 1.0
        assert graph is not None

    def test_duckdb_loading_with_filter_is_fast(self, test_db_with_data):
        """Test that filtered DuckDB loading is fast."""
        import time

        builder = GraphBuilder(test_db_with_data)

        start = time.time()
        graph = builder.build_from_duckdb(
            node_categories={"biolink:ChemicalSubstance"}
        )
        elapsed = time.time() - start

        # Should complete quickly for small filtered data
        assert elapsed < 2.0
        assert graph is not None


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_missing_nodes_file_raises_error(self):
        """Test that missing nodes file raises appropriate error."""
        builder = GraphBuilder(None)

        missing_nodes = Path("/nonexistent/nodes.tsv")
        missing_edges = Path("/nonexistent/edges.tsv")

        with pytest.raises((FileNotFoundError, ValueError)):
            builder.build_from_tsv_direct(missing_nodes, missing_edges)

    def test_empty_tsv_creates_empty_graph(self, tmp_path):
        """Test that empty TSV files create an empty graph."""
        # Create empty TSV files
        nodes_file = tmp_path / "empty_nodes.tsv"
        edges_file = tmp_path / "empty_edges.tsv"

        nodes_file.write_text("id\tcategory\tname\n")
        edges_file.write_text("subject\tpredicate\tobject\n")

        builder = GraphBuilder(None)
        graph = builder.build_from_tsv_direct(nodes_file, edges_file)

        assert graph.get_number_of_nodes() == 0
        assert graph.get_number_of_edges() == 0

    def test_build_without_db_path_and_duckdb_strategy_raises_error(self):
        """Test that using DuckDB strategy without DB path raises error."""
        builder = GraphBuilder(None)

        with pytest.raises((ValueError, AttributeError)):
            builder.build_from_duckdb()


class TestIntegration:
    """Integration tests for graph builder."""

    def test_build_query_workflow(self, test_kg_dir):
        """Test complete workflow: build graph -> query nodes -> query edges."""
        builder = GraphBuilder(None)

        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"
        edges_file = test_kg_dir / "merged-kg_edges.tsv"

        # Build graph
        graph = builder.build_from_tsv_direct(nodes_file, edges_file)

        # Query nodes
        assert graph.get_number_of_nodes() == 5

        # Query specific node
        node_id = graph.get_node_id_from_node_name("CHEBI:16828")
        assert node_id >= 0

        # Query neighbors
        neighbors = graph.get_neighbour_node_ids_from_node_id(node_id)
        assert len(neighbors) > 0

        # Get neighbor names
        neighbor_names = [graph.get_node_name_from_node_id(n) for n in neighbors]
        assert "CHEBI:15841" in neighbor_names

    def test_filtered_graph_workflow(self, test_db_with_data):
        """Test workflow with filtered graph."""
        builder = GraphBuilder(test_db_with_data)

        # Build filtered graph (only ChemicalSubstance)
        graph = builder.build_from_duckdb(
            node_categories={"biolink:ChemicalSubstance"}
        )

        # Should only have ChemicalSubstance nodes
        assert graph.get_number_of_nodes() == 3

        # All nodes should be ChemicalSubstance
        node_types = graph.get_unique_node_type_names()
        assert node_types == ["biolink:ChemicalSubstance"]

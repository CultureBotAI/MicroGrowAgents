"""Test KG (Knowledge Graph) data loader.

Tests loading of KG-Microbe data (1.5M nodes, 5.1M edges) into DuckDB.

Following TDD: These tests are written BEFORE implementation.
"""

import pytest
from pathlib import Path
import duckdb
import pandas as pd
from io import StringIO

from microgrowagents.kg.loader import KGLoader
from microgrowagents.database.schema import create_schema


@pytest.fixture
def test_kg_dir(tmp_path):
    """Create test KG data directory with sample TSV files."""
    kg_dir = tmp_path / "kg_microbe_core"
    kg_dir.mkdir()

    # Create sample nodes TSV (following merged-kg_nodes.tsv format)
    nodes_data = """id\tcategory\tname\tdescription\txref\tsynonym\tiri\tprovided_by\tdeprecated\tsubsets
CHEBI:16828\tbiolink:ChemicalSubstance\theme\tA complex metal ion\tKEGG:C00032|PubChem:26945\thaem|protoheme\thttp://purl.obolibrary.org/obo/CHEBI_16828\tchebi\tFalse\t
CHEBI:15841\tbiolink:ChemicalSubstance\tpolypeptide\tA peptide with more than 20 amino acids\t\t\thttp://purl.obolibrary.org/obo/CHEBI_15841\tchebi\tFalse\t
CHEBI:24431\tbiolink:ChemicalSubstance\tchemical entity\tA chemical entity is a physical entity of interest in chemistry\t\t\thttp://purl.obolibrary.org/obo/CHEBI_24431\tchebi\tFalse\t
NCBITaxon:562\tbiolink:OrganismTaxon\tEscherichia coli\tA species of bacteria\t\t\thttp://purl.obolibrary.org/obo/NCBITaxon_562\tncbitaxon\tFalse\t
EC:4.1.99.1\tbiolink:MolecularActivity\ttryptophan deaminase\tEnzyme activity\t\t\thttp://example.org/ec/4.1.99.1\tec\tFalse\t
METPO:2000303\tbiolink:BiologicalProcess\tgrowth process\tMicrobial growth process\t\t\thttp://example.org/metpo/2000303\tmetpo\tFalse\t"""

    with open(kg_dir / "merged-kg_nodes.tsv", "w") as f:
        f.write(nodes_data)

    # Create sample edges TSV (following merged-kg_edges.tsv format)
    edges_data = """id\tsubject\tpredicate\tobject\trelation\tknowledge_source\tprimary_knowledge_source
edge_1\tCHEBI:16828\tbiolink:subclass_of\tCHEBI:15841\trdfs:subClassOf\tinfores:chebi\tinfores:chebi
edge_2\tCHEBI:15841\tbiolink:subclass_of\tCHEBI:24431\trdfs:subClassOf\tinfores:chebi\tinfores:chebi
edge_3\tCHEBI:16828\tbiolink:has_role\tCHEBI:51460\tRO:0000087\tinfores:chebi\tinfores:chebi
edge_4\tNCBITaxon:562\tbiolink:has_phenotype\tMETPO:2000303\t\tinfores:bacdive\tinfores:bacdive
edge_5\tEC:4.1.99.1\tbiolink:has_input\tCHEBI:16828\t\tinfores:ec\tinfores:ec
edge_6\tNCBITaxon:562\tMETPO:2000517\tmediadive:medium_123\t\tinfores:mediadive\tinfores:mediadive"""

    with open(kg_dir / "merged-kg_edges.tsv", "w") as f:
        f.write(edges_data)

    return kg_dir


@pytest.fixture
def test_db(tmp_path):
    """Create test database with KG schema."""
    db_path = tmp_path / "test_kg.duckdb"
    conn = duckdb.connect(str(db_path))
    create_schema(conn)
    yield conn
    conn.close()


@pytest.fixture
def test_db_path(tmp_path):
    """Create test database path."""
    db_path = tmp_path / "test_kg.duckdb"
    # Create schema
    conn = duckdb.connect(str(db_path))
    create_schema(conn)
    conn.close()
    return db_path


class TestKGLoaderInit:
    """Test KG loader initialization."""

    def test_init_with_db_path(self, test_db_path):
        """Test KGLoader initialization with database path."""
        loader = KGLoader(test_db_path)
        assert loader.db_path == test_db_path
        assert loader.conn is not None
        loader.close()

    def test_init_creates_connection(self, test_db_path):
        """Test that initialization creates a valid DuckDB connection."""
        loader = KGLoader(test_db_path)
        # Should be able to query the database
        result = loader.conn.execute("SELECT 1").fetchone()
        assert result[0] == 1
        loader.close()


class TestLoadNodes:
    """Test loading KG nodes from TSV."""

    def test_load_nodes_from_file(self, test_kg_dir, test_db_path):
        """Test loading nodes from TSV file."""
        loader = KGLoader(test_db_path)
        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"

        loader._load_nodes(nodes_file)

        # Check that nodes were loaded
        count = loader.conn.execute("SELECT COUNT(*) FROM kg_nodes").fetchone()[0]
        assert count == 6, "Should load 6 nodes"

        loader.close()

    def test_load_nodes_correct_data(self, test_kg_dir, test_db_path):
        """Test that node data is loaded correctly."""
        loader = KGLoader(test_db_path)
        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"

        loader._load_nodes(nodes_file)

        # Check specific node (heme)
        heme = loader.conn.execute(
            "SELECT * FROM kg_nodes WHERE id = 'CHEBI:16828'"
        ).fetchone()

        assert heme is not None
        assert heme[0] == "CHEBI:16828"  # id
        assert heme[1] == "biolink:ChemicalSubstance"  # category
        assert heme[2] == "heme"  # name
        assert "complex metal ion" in heme[3]  # description
        assert "KEGG:C00032" in heme[4]  # xref
        assert "haem" in heme[5]  # synonym

        loader.close()

    def test_load_nodes_different_categories(self, test_kg_dir, test_db_path):
        """Test that nodes of different categories are loaded."""
        loader = KGLoader(test_db_path)
        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"

        loader._load_nodes(nodes_file)

        # Check we have different categories
        categories = loader.conn.execute(
            "SELECT DISTINCT category FROM kg_nodes"
        ).fetchall()
        category_list = [c[0] for c in categories]

        assert "biolink:ChemicalSubstance" in category_list
        assert "biolink:OrganismTaxon" in category_list
        assert "biolink:MolecularActivity" in category_list

        loader.close()

    def test_load_nodes_batch_processing(self, test_db_path):
        """Test that nodes are loaded in batches for large files."""
        loader = KGLoader(test_db_path)

        # Create a larger TSV with 150 nodes (should trigger batching at 50k batch size)
        large_nodes = []
        large_nodes.append(
            "id\tcategory\tname\tdescription\txref\tsynonym\tiri\tprovided_by\tdeprecated\tsubsets"
        )
        for i in range(150):
            large_nodes.append(
                f"CHEBI:{i}\tbiolink:ChemicalSubstance\tcompound_{i}\t\t\t\t\tchebi\tFalse\t"
            )

        # Write to temporary file
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("\n".join(large_nodes))
            temp_file = Path(f.name)

        loader._load_nodes(temp_file)

        count = loader.conn.execute("SELECT COUNT(*) FROM kg_nodes").fetchone()[0]
        assert count == 150

        temp_file.unlink()  # Clean up
        loader.close()

    def test_load_nodes_handles_missing_file(self, test_db_path):
        """Test that loading handles missing file gracefully."""
        loader = KGLoader(test_db_path)
        missing_file = Path("/nonexistent/nodes.tsv")

        # Should not raise error, just log warning
        loader._load_nodes(missing_file)

        # Should have 0 nodes
        count = loader.conn.execute("SELECT COUNT(*) FROM kg_nodes").fetchone()[0]
        assert count == 0

        loader.close()


class TestLoadEdges:
    """Test loading KG edges from TSV."""

    def test_load_edges_from_file(self, test_kg_dir, test_db_path):
        """Test loading edges from TSV file."""
        loader = KGLoader(test_db_path)
        edges_file = test_kg_dir / "merged-kg_edges.tsv"

        loader._load_edges(edges_file)

        # Check that edges were loaded
        count = loader.conn.execute("SELECT COUNT(*) FROM kg_edges").fetchone()[0]
        assert count == 6, "Should load 6 edges"

        loader.close()

    def test_load_edges_correct_data(self, test_kg_dir, test_db_path):
        """Test that edge data is loaded correctly."""
        loader = KGLoader(test_db_path)
        edges_file = test_kg_dir / "merged-kg_edges.tsv"

        loader._load_edges(edges_file)

        # Check specific edge (heme subclass_of polypeptide)
        edge = loader.conn.execute(
            "SELECT * FROM kg_edges WHERE id = 'edge_1'"
        ).fetchone()

        assert edge is not None
        assert edge[0] == "edge_1"  # id
        assert edge[1] == "CHEBI:16828"  # subject
        assert edge[2] == "biolink:subclass_of"  # predicate
        assert edge[3] == "CHEBI:15841"  # object

        loader.close()

    def test_load_edges_different_predicates(self, test_kg_dir, test_db_path):
        """Test that edges with different predicates are loaded."""
        loader = KGLoader(test_db_path)
        edges_file = test_kg_dir / "merged-kg_edges.tsv"

        loader._load_edges(edges_file)

        # Check we have different predicates
        predicates = loader.conn.execute(
            "SELECT DISTINCT predicate FROM kg_edges"
        ).fetchall()
        predicate_list = [p[0] for p in predicates]

        assert "biolink:subclass_of" in predicate_list
        assert "biolink:has_phenotype" in predicate_list
        assert "biolink:has_input" in predicate_list
        assert "METPO:2000517" in predicate_list

        loader.close()

    def test_load_edges_batch_processing(self, test_db_path):
        """Test that edges are loaded in batches for large files."""
        loader = KGLoader(test_db_path)

        # Create a larger TSV with 200 edges
        large_edges = []
        large_edges.append(
            "id\tsubject\tpredicate\tobject\trelation\tknowledge_source\tprimary_knowledge_source"
        )
        for i in range(200):
            large_edges.append(
                f"edge_{i}\tCHEBI:{i}\tbiolink:subclass_of\tCHEBI:{i+1}\t\tinfores:chebi\tinfores:chebi"
            )

        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("\n".join(large_edges))
            temp_file = Path(f.name)

        loader._load_edges(temp_file)

        count = loader.conn.execute("SELECT COUNT(*) FROM kg_edges").fetchone()[0]
        assert count == 200

        temp_file.unlink()
        loader.close()


class TestBuildHierarchies:
    """Test building materialized hierarchy table."""

    def test_build_hierarchies_from_subclass_edges(self, test_kg_dir, test_db_path):
        """Test building transitive closure from biolink:subclass_of edges."""
        loader = KGLoader(test_db_path)

        # Load nodes and edges first
        loader._load_nodes(test_kg_dir / "merged-kg_nodes.tsv")
        loader._load_edges(test_kg_dir / "merged-kg_edges.tsv")

        # Build hierarchies
        loader._build_hierarchies()

        # Check that hierarchies were created
        count = loader.conn.execute("SELECT COUNT(*) FROM kg_hierarchies").fetchone()[0]
        assert count > 0, "Should create hierarchy entries"

        loader.close()

    def test_hierarchy_transitive_closure(self, test_kg_dir, test_db_path):
        """Test that transitive closure computes all ancestor-descendant pairs."""
        loader = KGLoader(test_db_path)

        # Load data
        loader._load_nodes(test_kg_dir / "merged-kg_nodes.tsv")
        loader._load_edges(test_kg_dir / "merged-kg_edges.tsv")
        loader._build_hierarchies()

        # CHEBI:16828 -> CHEBI:15841 -> CHEBI:24431
        # So CHEBI:16828 should have 2 ancestors in hierarchy:
        # 1. CHEBI:15841 (path_length=1)
        # 2. CHEBI:24431 (path_length=2)

        ancestors = loader.conn.execute(
            """
            SELECT ancestor_id, path_length FROM kg_hierarchies
            WHERE descendant_id = 'CHEBI:16828'
            ORDER BY path_length
            """
        ).fetchall()

        assert len(ancestors) >= 2, "Should have at least 2 ancestors"
        assert ancestors[0][0] == "CHEBI:15841"
        assert ancestors[0][1] == 1
        assert ancestors[1][0] == "CHEBI:24431"
        assert ancestors[1][1] == 2

        loader.close()

    def test_hierarchy_max_depth_limit(self, test_db_path):
        """Test that hierarchy building respects max depth limit (10 hops)."""
        loader = KGLoader(test_db_path)

        # Create a deep hierarchy chain (15 levels)
        import tempfile

        nodes = ["id\tcategory\tname\tdescription\txref\tsynonym\tiri\tprovided_by\tdeprecated\tsubsets"]
        edges = ["id\tsubject\tpredicate\tobject\trelation\tknowledge_source\tprimary_knowledge_source"]

        for i in range(15):
            nodes.append(
                f"CHEBI:{i}\tbiolink:ChemicalSubstance\tcompound_{i}\t\t\t\tchebi\tFalse\t"
            )
            if i > 0:
                edges.append(
                    f"edge_{i}\tCHEBI:{i-1}\tbiolink:subclass_of\tCHEBI:{i}\t\tinfores:chebi\tinfores:chebi"
                )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("\n".join(nodes))
            nodes_file = Path(f.name)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("\n".join(edges))
            edges_file = Path(f.name)

        loader._load_nodes(nodes_file)
        loader._load_edges(edges_file)
        loader._build_hierarchies()

        # CHEBI:0 should have ancestors up to depth 10
        max_depth = loader.conn.execute(
            "SELECT MAX(path_length) FROM kg_hierarchies WHERE descendant_id = 'CHEBI:0'"
        ).fetchone()[0]

        assert max_depth <= 10, "Should limit to 10 hops"

        nodes_file.unlink()
        edges_file.unlink()
        loader.close()

    def test_hierarchy_stores_path(self, test_kg_dir, test_db_path):
        """Test that hierarchy stores the full path."""
        loader = KGLoader(test_db_path)

        loader._load_nodes(test_kg_dir / "merged-kg_nodes.tsv")
        loader._load_edges(test_kg_dir / "merged-kg_edges.tsv")
        loader._build_hierarchies()

        # Get path from CHEBI:16828 to CHEBI:24431
        path_result = loader.conn.execute(
            """
            SELECT path FROM kg_hierarchies
            WHERE ancestor_id = 'CHEBI:24431' AND descendant_id = 'CHEBI:16828'
            """
        ).fetchone()

        assert path_result is not None
        path = path_result[0]
        # Path should contain all IDs in the chain
        assert "CHEBI:24431" in path
        assert "CHEBI:15841" in path
        assert "CHEBI:16828" in path

        loader.close()


class TestBuildPredicateIndex:
    """Test building predicate statistics index."""

    def test_build_predicate_index_counts_edges(self, test_kg_dir, test_db_path):
        """Test that predicate index counts edges correctly."""
        loader = KGLoader(test_db_path)

        loader._load_edges(test_kg_dir / "merged-kg_edges.tsv")
        loader._build_predicate_index()

        # Check that predicate index has entries
        count = loader.conn.execute(
            "SELECT COUNT(*) FROM kg_predicate_index"
        ).fetchone()[0]
        assert count > 0, "Should create predicate index entries"

        loader.close()

    def test_predicate_index_edge_counts(self, test_kg_dir, test_db_path):
        """Test that predicate index has correct edge counts."""
        loader = KGLoader(test_db_path)

        loader._load_edges(test_kg_dir / "merged-kg_edges.tsv")
        loader._build_predicate_index()

        # biolink:subclass_of appears 2 times in our test data
        subclass_entry = loader.conn.execute(
            """
            SELECT edge_count FROM kg_predicate_index
            WHERE predicate = 'biolink:subclass_of'
            """
        ).fetchone()

        assert subclass_entry is not None
        assert subclass_entry[0] == 2, "Should have 2 subclass_of edges"

        loader.close()

    def test_predicate_index_all_predicates(self, test_kg_dir, test_db_path):
        """Test that index contains all unique predicates."""
        loader = KGLoader(test_db_path)

        loader._load_edges(test_kg_dir / "merged-kg_edges.tsv")
        loader._build_predicate_index()

        # Get all predicates from index
        predicates = loader.conn.execute(
            "SELECT predicate FROM kg_predicate_index ORDER BY predicate"
        ).fetchall()
        predicate_list = [p[0] for p in predicates]

        # Should have 4 unique predicates in test data
        expected = [
            "METPO:2000517",
            "biolink:has_input",
            "biolink:has_phenotype",
            "biolink:subclass_of",
        ]

        for pred in expected:
            assert pred in predicate_list, f"Missing predicate {pred}"

        loader.close()


class TestLoadKGMicrobe:
    """Test high-level load_kg_microbe method."""

    def test_load_kg_microbe_loads_all_components(self, test_kg_dir, test_db_path):
        """Test that load_kg_microbe loads nodes, edges, hierarchies, and index."""
        loader = KGLoader(test_db_path)

        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"
        edges_file = test_kg_dir / "merged-kg_edges.tsv"

        loader.load_kg_microbe(
            nodes_file=nodes_file, edges_file=edges_file, build_hierarchies=True
        )

        # Check all tables have data
        node_count = loader.conn.execute("SELECT COUNT(*) FROM kg_nodes").fetchone()[0]
        edge_count = loader.conn.execute("SELECT COUNT(*) FROM kg_edges").fetchone()[0]
        hier_count = loader.conn.execute(
            "SELECT COUNT(*) FROM kg_hierarchies"
        ).fetchone()[0]
        pred_count = loader.conn.execute(
            "SELECT COUNT(*) FROM kg_predicate_index"
        ).fetchone()[0]

        assert node_count > 0, "Should load nodes"
        assert edge_count > 0, "Should load edges"
        assert hier_count > 0, "Should build hierarchies"
        assert pred_count > 0, "Should build predicate index"

        loader.close()

    def test_load_kg_microbe_skip_hierarchies(self, test_kg_dir, test_db_path):
        """Test loading without building hierarchies."""
        loader = KGLoader(test_db_path)

        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"
        edges_file = test_kg_dir / "merged-kg_edges.tsv"

        loader.load_kg_microbe(
            nodes_file=nodes_file, edges_file=edges_file, build_hierarchies=False
        )

        # Should have nodes and edges but not hierarchies
        node_count = loader.conn.execute("SELECT COUNT(*) FROM kg_nodes").fetchone()[0]
        edge_count = loader.conn.execute("SELECT COUNT(*) FROM kg_edges").fetchone()[0]
        hier_count = loader.conn.execute(
            "SELECT COUNT(*) FROM kg_hierarchies"
        ).fetchone()[0]

        assert node_count > 0
        assert edge_count > 0
        assert hier_count == 0, "Should not build hierarchies when disabled"

        loader.close()


class TestIntegration:
    """Integration tests for KG loader."""

    def test_full_loading_workflow(self, test_kg_dir, test_db_path):
        """Test complete workflow: init -> load -> query."""
        loader = KGLoader(test_db_path)

        # Load all data
        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"
        edges_file = test_kg_dir / "merged-kg_edges.tsv"
        loader.load_kg_microbe(nodes_file, edges_file, build_hierarchies=True)

        # Query: Find all ChemicalSubstance nodes
        chem_nodes = loader.conn.execute(
            """
            SELECT COUNT(*) FROM kg_nodes
            WHERE category = 'biolink:ChemicalSubstance'
            """
        ).fetchone()[0]

        assert chem_nodes == 3, "Should have 3 chemical substance nodes"

        # Query: Find all outgoing edges from CHEBI:16828
        outgoing_edges = loader.conn.execute(
            """
            SELECT COUNT(*) FROM kg_edges
            WHERE subject = 'CHEBI:16828'
            """
        ).fetchone()[0]

        assert outgoing_edges == 2, "CHEBI:16828 should have 2 outgoing edges"

        # Query: Use hierarchy to find all ancestors of CHEBI:16828
        ancestors = loader.conn.execute(
            """
            SELECT COUNT(*) FROM kg_hierarchies
            WHERE descendant_id = 'CHEBI:16828'
            """
        ).fetchone()[0]

        assert ancestors >= 2, "Should have at least 2 ancestors"

        loader.close()

    def test_query_with_indexes(self, test_kg_dir, test_db_path):
        """Test that queries use the indexes efficiently."""
        loader = KGLoader(test_db_path)

        nodes_file = test_kg_dir / "merged-kg_nodes.tsv"
        edges_file = test_kg_dir / "merged-kg_edges.tsv"
        loader.load_kg_microbe(nodes_file, edges_file, build_hierarchies=True)

        # Query using composite index (subject, predicate)
        result = loader.conn.execute(
            """
            SELECT object FROM kg_edges
            WHERE subject = 'CHEBI:16828' AND predicate = 'biolink:subclass_of'
            """
        ).fetchone()

        assert result is not None
        assert result[0] == "CHEBI:15841"

        loader.close()

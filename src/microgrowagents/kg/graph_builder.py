"""GRAPE graph builder for KG-Microbe.

Builds high-performance GRAPE (Graph Representation leArning, Predictions and Evaluations)
graphs from KG-Microbe data for advanced graph algorithms.

GRAPE advantages over NetworkX:
- 10-100x faster for large graphs (5M edges)
- Rust backend (ensmallen) with zero-copy memory mapping
- Direct TSV loading (5-15s vs 60s with NetworkX)
- Memory efficient (~800MB vs ~2GB for 5M edge graph)
- Parallel algorithms optimized for biological networks

Two loading strategies:
1. Direct TSV: Load from merged-kg_*.tsv directly (FASTEST)
2. DuckDB export: Query filtered data → temp TSV → GRAPE (for filtering)
"""

from pathlib import Path
from typing import Optional, Set
import tempfile

import duckdb
import pandas as pd

# Try to import GRAPE (ensmallen Rust backend)
# If it fails, provide helpful error message
try:
    from grape import Graph
    GRAPE_AVAILABLE = True
except ImportError as e:
    GRAPE_AVAILABLE = False
    GRAPE_IMPORT_ERROR = str(e)

    # Create a stub Graph class for testing/development
    class Graph:
        """Stub Graph class when GRAPE is not available."""
        def __init__(self, *args, **kwargs):
            raise ImportError(
                f"GRAPE (ensmallen) not available: {GRAPE_IMPORT_ERROR}\n\n"
                "GRAPE requires Rust compilation and may not have pre-built wheels for your platform.\n"
                "Installation options:\n"
                "1. Build from source: pip install --no-binary grape grape\n"
                "2. Use Conda: conda install -c conda-forge grape\n"
                "3. For ARM64 Mac: May need to compile ensmallen manually\n"
                "4. Alternative: Use NetworkX (slower but pure Python)\n\n"
                "System info: Check 'uname -m' and 'python --version'\n"
                "See: https://github.com/AnacletoLAB/grape"
            )

        @staticmethod
        def from_csv(*args, **kwargs):
            raise ImportError("GRAPE not available - see Graph.__init__ for details")


class GraphBuilder:
    """Build GRAPE graphs from KG-Microbe data.

    Examples:
        >>> # Strategy 1: Direct TSV loading (fastest)
        >>> builder = GraphBuilder()
        >>> graph = builder.build_from_tsv_direct(
        ...     "data/raw/kg_microbe_core/merged-kg_nodes.tsv",
        ...     "data/raw/kg_microbe_core/merged-kg_edges.tsv"
        ... )

        >>> # Strategy 2: DuckDB with filtering
        >>> builder = GraphBuilder("data/processed/microgrow.duckdb")
        >>> graph = builder.build_from_duckdb(
        ...     node_categories={"biolink:ChemicalSubstance"},
        ...     edge_predicates={"biolink:subclass_of"}
        ... )
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize graph builder.

        Args:
            db_path: Path to DuckDB database (optional, needed for DuckDB strategy)
        """
        self.db_path = Path(db_path) if db_path else None
        self.conn = None

        if self.db_path and self.db_path.exists():
            self.conn = duckdb.connect(str(self.db_path), read_only=True)

    def build_graph(
        self,
        nodes_file: Optional[Path] = None,
        edges_file: Optional[Path] = None,
        use_tsv_direct: bool = True,
        node_categories: Optional[Set[str]] = None,
        edge_predicates: Optional[Set[str]] = None,
    ) -> Graph:
        """
        Build GRAPE graph (main method with strategy selection).

        Args:
            nodes_file: Path to nodes TSV (for direct TSV strategy)
            edges_file: Path to edges TSV (for direct TSV strategy)
            use_tsv_direct: If True, load from TSV directly (fastest)
            node_categories: Filter by node categories (DuckDB strategy only)
            edge_predicates: Filter by edge predicates (DuckDB strategy only)

        Returns:
            GRAPE Graph object
        """
        if use_tsv_direct:
            if not nodes_file or not edges_file:
                raise ValueError("nodes_file and edges_file required for TSV strategy")
            return self.build_from_tsv_direct(nodes_file, edges_file)
        else:
            return self.build_from_duckdb(node_categories, edge_predicates)

    def build_from_tsv_direct(
        self, nodes_file: Path, edges_file: Path
    ) -> Graph:
        """
        Load GRAPE graph directly from TSV files (FASTEST method).

        Uses GRAPE's native TSV parser with zero-copy memory mapping.
        This is the fastest loading method for full graphs.

        GRAPE expects:
        - Nodes TSV: columns with node IDs and optional node types
        - Edges TSV: columns with source, destination, optional edge types

        Args:
            nodes_file: Path to merged-kg_nodes.tsv
            edges_file: Path to merged-kg_edges.tsv

        Returns:
            GRAPE Graph object

        Raises:
            FileNotFoundError: If TSV files don't exist
        """
        nodes_file = Path(nodes_file)
        edges_file = Path(edges_file)

        if not nodes_file.exists():
            raise FileNotFoundError(f"Nodes file not found: {nodes_file}")
        if not edges_file.exists():
            raise FileNotFoundError(f"Edges file not found: {edges_file}")

        # GRAPE can load from CSV/TSV directly
        # We need to prepare the files in GRAPE's expected format
        # GRAPE expects:
        #   - edge_path: file with source\tdestination\tedge_type (optional)
        #   - node_path: file with node_name\tnode_type (optional)

        # Load graph from edge list (GRAPE will infer nodes from edges)
        graph = Graph.from_csv(
            directed=True,
            edge_path=str(edges_file),
            edge_list_separator="\t",
            edge_list_header=True,
            sources_column="subject",
            destinations_column="object",
            edge_list_edge_types_column="predicate",
            node_path=str(nodes_file),
            node_list_separator="\t",
            node_list_header=True,
            nodes_column="id",
            node_list_node_types_column="category",
            name="KG-Microbe"
        )

        return graph

    def build_from_duckdb(
        self,
        node_categories: Optional[Set[str]] = None,
        edge_predicates: Optional[Set[str]] = None,
    ) -> Graph:
        """
        Build GRAPE graph from DuckDB with optional filtering.

        Queries filtered data from DuckDB, exports to temporary TSV files,
        then loads into GRAPE. This allows filtering by node categories
        and edge predicates before graph construction.

        Process:
        1. Query nodes (with optional category filter) from DuckDB
        2. Query edges (with optional predicate filter) from DuckDB
        3. Export to temporary TSV files
        4. Load into GRAPE using direct TSV method

        Args:
            node_categories: Set of node categories to include (e.g., {"biolink:ChemicalSubstance"})
            edge_predicates: Set of predicates to include (e.g., {"biolink:subclass_of"})

        Returns:
            GRAPE Graph object

        Raises:
            ValueError: If database connection not initialized
        """
        if not self.conn:
            raise ValueError("Database connection required for DuckDB strategy")

        # Build node query
        if node_categories:
            category_list = ",".join([f"'{c}'" for c in node_categories])
            node_query = f"""
                SELECT id, category, name FROM kg_nodes
                WHERE category IN ({category_list})
            """
        else:
            node_query = "SELECT id, category, name FROM kg_nodes"

        # Build edge query
        if edge_predicates:
            predicate_list = ",".join([f"'{p}'" for p in edge_predicates])
            edge_query = f"""
                SELECT subject, predicate, object FROM kg_edges
                WHERE predicate IN ({predicate_list})
            """
        else:
            edge_query = "SELECT subject, predicate, object FROM kg_edges"

        # If filtering nodes, also filter edges to only include edges between filtered nodes
        if node_categories:
            edge_query += f"""
                AND subject IN (SELECT id FROM kg_nodes WHERE category IN ({category_list}))
                AND object IN (SELECT id FROM kg_nodes WHERE category IN ({category_list}))
            """

        # Execute queries
        nodes_df = self.conn.execute(node_query).fetchdf()
        edges_df = self.conn.execute(edge_query).fetchdf()

        # Export to temporary TSV files
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tsv", delete=False
        ) as nodes_temp:
            nodes_df.to_csv(nodes_temp, sep="\t", index=False)
            nodes_temp_path = Path(nodes_temp.name)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tsv", delete=False
        ) as edges_temp:
            edges_df.to_csv(edges_temp, sep="\t", index=False)
            edges_temp_path = Path(edges_temp.name)

        # Load graph from temporary files
        try:
            graph = self.build_from_tsv_direct(nodes_temp_path, edges_temp_path)
        finally:
            # Clean up temporary files
            nodes_temp_path.unlink()
            edges_temp_path.unlink()

        return graph

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

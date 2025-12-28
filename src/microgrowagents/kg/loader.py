"""KG (Knowledge Graph) data loader for KG-Microbe.

Loads 1.5M nodes and 5.1M edges from merged-kg_nodes.tsv and merged-kg_edges.tsv
into DuckDB tables for efficient querying and graph analysis.

Key features:
- Batch loading (50k nodes, 100k edges per batch)
- Materialized hierarchies (transitive closure of biolink:subclass_of)
- Predicate index (edge type statistics)
- Efficient INSERT OR IGNORE for idempotent loading
"""

from pathlib import Path
from typing import Optional

import duckdb
import pandas as pd
from tqdm import tqdm


class KGLoader:
    """Load KG-Microbe data into DuckDB.

    Examples:
        >>> loader = KGLoader("data/processed/microgrow.duckdb")
        >>> loader.load_kg_microbe(
        ...     nodes_file="data/raw/kg_microbe_core/merged-kg_nodes.tsv",
        ...     edges_file="data/raw/kg_microbe_core/merged-kg_edges.tsv"
        ... )
        >>> loader.close()
    """

    def __init__(self, db_path: Path):
        """
        Initialize KG loader.

        Args:
            db_path: Path to DuckDB database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(str(db_path))

    def load_kg_microbe(
        self,
        nodes_file: Path,
        edges_file: Path,
        build_hierarchies: bool = True,
    ) -> None:
        """
        Load KG-Microbe data: nodes, edges, hierarchies, predicate index.

        Process:
        1. Load nodes in 50k batches
        2. Load edges in 100k batches
        3. Build materialized hierarchy table (recursive CTE, max 10 hops)
        4. Build predicate statistics index

        Args:
            nodes_file: Path to merged-kg_nodes.tsv
            edges_file: Path to merged-kg_edges.tsv
            build_hierarchies: Whether to build materialized hierarchies (default: True)
        """
        print("Loading KG-Microbe data...")

        # Load nodes
        if nodes_file.exists():
            self._load_nodes(nodes_file)
        else:
            print(f"  ⚠️  Nodes file not found: {nodes_file}")

        # Load edges
        if edges_file.exists():
            self._load_edges(edges_file)
        else:
            print(f"  ⚠️  Edges file not found: {edges_file}")

        # Build hierarchies
        if build_hierarchies:
            self._build_hierarchies()

        # Build predicate index
        self._build_predicate_index()

        print("✓ KG-Microbe data loaded successfully")

    def _load_nodes(self, nodes_file: Path) -> None:
        """
        Load KG nodes from TSV file in batches.

        Loads nodes in chunks of 50,000 to handle large files efficiently.
        Uses INSERT OR IGNORE for idempotent loading.

        Args:
            nodes_file: Path to merged-kg_nodes.tsv
        """
        if not nodes_file.exists():
            print(f"  ⚠️  Nodes file not found: {nodes_file}")
            return

        print(f"  Loading nodes from {nodes_file.name}...")

        # Read TSV in chunks
        chunk_size = 50000
        chunks_loaded = 0

        for chunk in pd.read_csv(
            nodes_file, sep="\t", chunksize=chunk_size, low_memory=False
        ):
            # Clean up the data
            # Replace NaN with None for proper NULL handling
            chunk = chunk.where(pd.notnull(chunk), None)

            # Insert batch using DuckDB's DataFrame support
            self.conn.execute(
                """
                INSERT OR IGNORE INTO kg_nodes (
                    id, category, name, description, xref, synonym,
                    iri, provided_by, deprecated, subsets
                )
                SELECT
                    id, category, name, description, xref, synonym,
                    iri, provided_by, deprecated, subsets
                FROM chunk
                """
            )

            chunks_loaded += 1

        # Get total count
        total_nodes = self.conn.execute("SELECT COUNT(*) FROM kg_nodes").fetchone()[0]
        print(f"    ✓ Loaded {total_nodes:,} nodes ({chunks_loaded} batches)")

    def _load_edges(self, edges_file: Path) -> None:
        """
        Load KG edges from TSV file in batches.

        Loads edges in chunks of 100,000 to handle large files efficiently.
        Uses INSERT OR IGNORE for idempotent loading.

        Args:
            edges_file: Path to merged-kg_edges.tsv
        """
        if not edges_file.exists():
            print(f"  ⚠️  Edges file not found: {edges_file}")
            return

        print(f"  Loading edges from {edges_file.name}...")

        # Read TSV in chunks (larger for edges as they're smaller)
        chunk_size = 100000
        chunks_loaded = 0

        for chunk in pd.read_csv(
            edges_file, sep="\t", chunksize=chunk_size, low_memory=False
        ):
            # Clean up the data
            chunk = chunk.where(pd.notnull(chunk), None)

            # Insert batch
            self.conn.execute(
                """
                INSERT OR IGNORE INTO kg_edges (
                    id, subject, predicate, object, relation,
                    knowledge_source, primary_knowledge_source
                )
                SELECT
                    id, subject, predicate, object, relation,
                    knowledge_source, primary_knowledge_source
                FROM chunk
                """
            )

            chunks_loaded += 1

        # Get total count
        total_edges = self.conn.execute("SELECT COUNT(*) FROM kg_edges").fetchone()[0]
        print(f"    ✓ Loaded {total_edges:,} edges ({chunks_loaded} batches)")

    def _build_hierarchies(self) -> None:
        """
        Build materialized hierarchy table via transitive closure.

        Computes all ancestor-descendant pairs from biolink:subclass_of edges
        using a recursive CTE limited to 10 hops.

        Creates entries in kg_hierarchies with:
        - ancestor_id, descendant_id (primary key)
        - path_length (number of hops)
        - path (pipe-separated path of node IDs)

        This enables fast "find all ancestors" queries without graph traversal.
        """
        print("  Building materialized hierarchies (recursive CTE)...")

        # Clear existing hierarchies
        self.conn.execute("DELETE FROM kg_hierarchies")

        # Build transitive closure using recursive CTE
        # Limited to 10 hops to prevent infinite loops
        self.conn.execute(
            """
            INSERT INTO kg_hierarchies (ancestor_id, descendant_id, path_length, path)
            WITH RECURSIVE hierarchy AS (
                -- Base case: direct parent-child relationships
                SELECT
                    object AS ancestor_id,
                    subject AS descendant_id,
                    1 AS path_length,
                    object || '|' || subject AS path
                FROM kg_edges
                WHERE predicate = 'biolink:subclass_of'

                UNION ALL

                -- Recursive case: extend paths
                SELECT
                    h.ancestor_id,
                    e.subject AS descendant_id,
                    h.path_length + 1 AS path_length,
                    h.path || '|' || e.subject AS path
                FROM hierarchy h
                JOIN kg_edges e ON e.object = h.descendant_id
                WHERE
                    e.predicate = 'biolink:subclass_of'
                    AND h.path_length < 10  -- Limit depth to 10 hops
            )
            SELECT DISTINCT ancestor_id, descendant_id, path_length, path
            FROM hierarchy
            """
        )

        # Get count
        total_hierarchies = self.conn.execute(
            "SELECT COUNT(*) FROM kg_hierarchies"
        ).fetchone()[0]
        print(f"    ✓ Built {total_hierarchies:,} hierarchy relationships")

    def _build_predicate_index(self) -> None:
        """
        Build predicate statistics index.

        Aggregates edge counts by predicate type and stores in kg_predicate_index.
        This enables fast queries like "how many biolink:subclass_of edges exist?"

        Creates entries with:
        - predicate (primary key)
        - edge_count (number of edges with this predicate)
        - description, domain_category, range_category (optional metadata)
        """
        print("  Building predicate index...")

        # Clear existing index
        self.conn.execute("DELETE FROM kg_predicate_index")

        # Aggregate edge counts by predicate
        self.conn.execute(
            """
            INSERT INTO kg_predicate_index (predicate, edge_count)
            SELECT
                predicate,
                COUNT(*) AS edge_count
            FROM kg_edges
            GROUP BY predicate
            ORDER BY edge_count DESC
            """
        )

        # Get count
        total_predicates = self.conn.execute(
            "SELECT COUNT(*) FROM kg_predicate_index"
        ).fetchone()[0]
        print(f"    ✓ Indexed {total_predicates:,} unique predicates")

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

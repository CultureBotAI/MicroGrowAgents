"""Knowledge Graph Reasoning Agent for MicroGrowAgents.

Provides advanced graph querying, pathway discovery, and graph algorithm capabilities
using KG-Microbe data (1.5M nodes, 5.1M edges) with GRAPE for high-performance algorithms.

Query Types:
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

Examples:
    >>> agent = KGReasoningAgent(db_path)
    >>> result = agent.run("lookup CHEBI:16828")
    >>> result = agent.run("path NCBITaxon:562 CHEBI:16828", max_hops=5)
    >>> result = agent.run("enzymes_using CHEBI:16828")
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import duckdb

from microgrowagents.agents.base_agent import BaseAgent
from microgrowagents.kg.graph_builder import GraphBuilder, GRAPE_AVAILABLE
from microgrowagents.kg.query_patterns import QueryPatterns
from microgrowagents.kg.algorithms import GraphAlgorithms


class KGReasoningAgent(BaseAgent):
    """
    Knowledge Graph Reasoning Agent.

    Combines SQL-based queries (fast lookups/filtering) with GRAPE graph algorithms
    (path finding, centrality, community detection) for comprehensive KG analysis.

    Architecture:
    - DuckDB: Fast SQL for lookups, filtering, aggregations
    - GRAPE: High-performance Rust-backed graph library (10-100x faster than NetworkX)
    - QueryPatterns: Pre-built SQL queries for common use cases
    - GraphAlgorithms: GRAPE algorithm wrappers

    Performance:
    - SQL queries: <100ms
    - Graph loading (lazy): 5-15s first time for full 5M edge graph
    - Path finding: <100ms (GRAPE cached)
    - Centrality: 10-100x faster than NetworkX
    """

    def __init__(
        self,
        db_path: Path,
        lazy_load_graph: bool = True,
        use_ontology_reasoner: bool = False
    ):
        """
        Initialize KG Reasoning Agent.

        Args:
            db_path: Path to DuckDB database with KG data
            lazy_load_graph: If True, load GRAPE graph only when needed (default: True)
            use_ontology_reasoner: If True, enable RDFLib ontology reasoning (default: False)

        Raises:
            ValueError: If db_path is None
            FileNotFoundError: If database doesn't exist
        """
        if db_path is None:
            raise ValueError("db_path is required for KGReasoningAgent")

        super().__init__(db_path)

        if not self.validate_database():
            raise FileNotFoundError(f"Database not found at {self.db_path}")

        # Connect to DuckDB
        self.conn = duckdb.connect(str(self.db_path), read_only=True)

        # Graph loading strategy
        self.lazy_load_graph = lazy_load_graph
        self._graph: Optional[Any] = None  # Graph type when GRAPE available

        # Helper components
        self.graph_builder = GraphBuilder(self.db_path)
        self.patterns = QueryPatterns(self.db_path)
        self.algorithms = GraphAlgorithms()

        # Optional ontology reasoner (future feature)
        self.ontology_reasoner = None
        if use_ontology_reasoner:
            # Placeholder for future RDFLib integration
            self.log("Ontology reasoner not yet implemented", level="WARNING")

        # Eager graph loading if requested
        if not lazy_load_graph and GRAPE_AVAILABLE:
            self._load_graph()

    @property
    def graph(self) -> Any:
        """
        Lazy-load GRAPE graph (cached after first access).

        Returns:
            GRAPE Graph object

        Raises:
            ImportError: If GRAPE is not available on this system
        """
        if not GRAPE_AVAILABLE:
            raise ImportError(
                "GRAPE not available on this system. "
                "See docs/grape_installation.md for installation instructions."
            )

        if self._graph is None:
            self._load_graph()

        return self._graph

    def _load_graph(self) -> None:
        """Load GRAPE graph from DuckDB or TSV files."""
        self.log("Loading GRAPE graph (this may take 5-15s for full graph)...")

        # Try direct TSV loading first (fastest)
        tsv_nodes = Path("data/raw/kg_microbe_core/merged-kg_nodes.tsv")
        tsv_edges = Path("data/raw/kg_microbe_core/merged-kg_edges.tsv")

        if tsv_nodes.exists() and tsv_edges.exists():
            self._graph = self.graph_builder.build_from_tsv_direct(tsv_nodes, tsv_edges)
            self.log("Graph loaded via direct TSV (fastest method)")
        else:
            # Fallback to DuckDB export
            self._graph = self.graph_builder.build_from_duckdb()
            self.log("Graph loaded via DuckDB export")

    def run(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute KG query.

        Routes query to appropriate handler based on query type.

        Args:
            query: Query string (format: "<type> <args>")
            **kwargs: Additional arguments (max_hops, limit, algorithm, etc.)

        Returns:
            Dictionary with results:
            {
                "success": bool,
                "query_type": str,
                "data": dict/list,
                "error": str (if success=False)
            }

        Examples:
            >>> result = agent.run("lookup CHEBI:16828")
            >>> result = agent.run("path NCBITaxon:562 CHEBI:16828", max_hops=5)
            >>> result = agent.run("enzymes_using CHEBI:16828", limit=20)
        """
        # Parse query
        if not query or not query.strip():
            return {"success": False, "error": "Empty query"}

        tokens = query.strip().split()
        query_type = tokens[0].lower()
        args = tokens[1:] if len(tokens) > 1 else []

        # Route to appropriate handler
        try:
            if query_type == "lookup":
                return self._handle_lookup(args, **kwargs)
            elif query_type == "neighbors":
                return self._handle_neighbors(args, **kwargs)
            elif query_type == "path":
                return self._handle_path(args, **kwargs)
            elif query_type == "filter":
                return self._handle_filter(args, **kwargs)
            elif query_type == "enzymes_using":
                return self._handle_enzymes_using(args, **kwargs)
            elif query_type == "media_ingredients":
                return self._handle_media_ingredients(args, **kwargs)
            elif query_type == "phenotype_media":
                return self._handle_phenotype_media(args, **kwargs)
            elif query_type == "centrality":
                return self._handle_centrality(args, **kwargs)
            elif query_type == "subgraph":
                return self._handle_subgraph(args, **kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown query type: {query_type}. "
                            f"Supported: lookup, neighbors, path, filter, enzymes_using, "
                            f"media_ingredients, phenotype_media, centrality, subgraph"
                }

        except Exception as e:
            self.log(f"Error executing query '{query}': {e}", level="ERROR")
            return {"success": False, "error": str(e)}

    def _handle_lookup(self, args: List[str], **kwargs) -> Dict[str, Any]:
        """
        Handle node lookup query.

        Args:
            args: [node_id]
            **kwargs: Not used

        Returns:
            {success: bool, node_id: str, name: str, category: str, ...}
        """
        if not args:
            return {"success": False, "error": "Missing node_id argument"}

        node_id = args[0]

        # SQL query for node details
        result = self.conn.execute(
            """
            SELECT id, category, name, description, xref, synonym,
                   iri, provided_by, deprecated, subsets
            FROM kg_nodes
            WHERE id = ?
            """,
            [node_id]
        ).fetchone()

        if not result:
            return {"success": False, "error": f"Node not found: {node_id}"}

        # Map result to dictionary
        return {
            "success": True,
            "query_type": "lookup",
            "node_id": result[0],
            "category": result[1],
            "name": result[2],
            "description": result[3],
            "xref": result[4],
            "synonym": result[5],
            "iri": result[6],
            "provided_by": result[7],
            "deprecated": result[8],
            "subsets": result[9]
        }

    def _handle_neighbors(self, args: List[str], **kwargs) -> Dict[str, Any]:
        """
        Handle neighbors query.

        Args:
            args: [node_id] or [node_id, predicate]
            **kwargs: Not used

        Returns:
            {success: bool, neighbors: [{node_id, name, category, predicate, direction}, ...]}
        """
        if not args:
            return {"success": False, "error": "Missing node_id argument"}

        node_id = args[0]
        predicate_filter = args[1] if len(args) > 1 else None

        # Build query for outgoing edges
        if predicate_filter:
            outgoing_query = """
                SELECT e.object, n.name, n.category, e.predicate, 'outgoing' AS direction
                FROM kg_edges e
                JOIN kg_nodes n ON e.object = n.id
                WHERE e.subject = ? AND e.predicate = ?
            """
            outgoing_params = [node_id, predicate_filter]
        else:
            outgoing_query = """
                SELECT e.object, n.name, n.category, e.predicate, 'outgoing' AS direction
                FROM kg_edges e
                JOIN kg_nodes n ON e.object = n.id
                WHERE e.subject = ?
            """
            outgoing_params = [node_id]

        # Build query for incoming edges
        if predicate_filter:
            incoming_query = """
                SELECT e.subject, n.name, n.category, e.predicate, 'incoming' AS direction
                FROM kg_edges e
                JOIN kg_nodes n ON e.subject = n.id
                WHERE e.object = ? AND e.predicate = ?
            """
            incoming_params = [node_id, predicate_filter]
        else:
            incoming_query = """
                SELECT e.subject, n.name, n.category, e.predicate, 'incoming' AS direction
                FROM kg_edges e
                JOIN kg_nodes n ON e.subject = n.id
                WHERE e.object = ?
            """
            incoming_params = [node_id]

        # Execute both queries
        outgoing_results = self.conn.execute(outgoing_query, outgoing_params).fetchall()
        incoming_results = self.conn.execute(incoming_query, incoming_params).fetchall()

        # Combine results
        neighbors = []
        for row in outgoing_results + incoming_results:
            neighbors.append({
                "node_id": row[0],
                "name": row[1],
                "category": row[2],
                "predicate": row[3],
                "direction": row[4]
            })

        return {
            "success": True,
            "query_type": "neighbors",
            "node_id": node_id,
            "neighbors": neighbors
        }

    def _handle_path(self, args: List[str], **kwargs) -> Dict[str, Any]:
        """
        Handle shortest path query using GRAPE.

        Args:
            args: [source, target]
            **kwargs: max_hops (int, default=10)

        Returns:
            {success: bool, path: [node_id, ...], length: int}
        """
        if len(args) < 2:
            return {"success": False, "error": "Missing source and/or target arguments"}

        source_id = args[0]
        target_id = args[1]
        max_hops = kwargs.get("max_hops", 10)

        try:
            # Use GRAPE for path finding
            graph = self.graph
            path = self.algorithms.find_shortest_path(graph, source_id, target_id)

            if not path:
                return {
                    "success": False,
                    "error": f"No path found between {source_id} and {target_id}"
                }

            # Check max hops
            if len(path) - 1 > max_hops:
                return {
                    "success": False,
                    "error": f"Path length {len(path) - 1} exceeds max_hops={max_hops}"
                }

            return {
                "success": True,
                "query_type": "path",
                "source": source_id,
                "target": target_id,
                "path": path,
                "length": len(path) - 1
            }

        except ImportError as e:
            return {"success": False, "error": str(e)}

    def _handle_filter(self, args: List[str], **kwargs) -> Dict[str, Any]:
        """
        Handle filter by category query.

        Args:
            args: [category]
            **kwargs: limit (int, default=100)

        Returns:
            {success: bool, nodes: [{node_id, name, category}, ...]}
        """
        if not args:
            return {"success": False, "error": "Missing category argument"}

        category = args[0]
        limit = kwargs.get("limit", 100)

        # SQL query with limit
        results = self.conn.execute(
            """
            SELECT id, name, category
            FROM kg_nodes
            WHERE category = ?
            LIMIT ?
            """,
            [category, limit]
        ).fetchall()

        nodes = [
            {"node_id": row[0], "name": row[1], "category": row[2]}
            for row in results
        ]

        return {
            "success": True,
            "query_type": "filter",
            "category": category,
            "nodes": nodes,
            "count": len(nodes)
        }

    def _handle_enzymes_using(self, args: List[str], **kwargs) -> Dict[str, Any]:
        """
        Handle enzymes_using query (USE CASE 3).

        Args:
            args: [substrate_id]
            **kwargs: Not used

        Returns:
            {success: bool, enzymes: [{enzyme_id, enzyme_name, relationship}, ...]}
        """
        if not args:
            return {"success": False, "error": "Missing substrate_id argument"}

        substrate_id = args[0]

        # Delegate to QueryPatterns
        enzymes_df = self.patterns.find_enzymes_for_substrate(substrate_id)

        enzymes = enzymes_df.to_dict(orient="records")

        return {
            "success": True,
            "query_type": "enzymes_using",
            "substrate_id": substrate_id,
            "enzymes": enzymes,
            "count": len(enzymes)
        }

    def _handle_media_ingredients(self, args: List[str], **kwargs) -> Dict[str, Any]:
        """
        Handle media_ingredients query (USE CASE 1).

        Args:
            args: [media_id]
            **kwargs: Not used

        Returns:
            {success: bool, media_info: dict, ingredients: [dict, ...]}
        """
        if not args:
            return {"success": False, "error": "Missing media_id argument"}

        media_id = args[0]

        # Delegate to QueryPatterns
        pathway = self.patterns.get_media_ingredient_pathway(media_id)

        return {
            "success": True,
            "query_type": "media_ingredients",
            **pathway
        }

    def _handle_phenotype_media(self, args: List[str], **kwargs) -> Dict[str, Any]:
        """
        Handle phenotype_media query (USE CASE 2).

        Args:
            args: [phenotype_id] or [phenotype_id1,phenotype_id2,...]
            **kwargs: Not used

        Returns:
            {success: bool, recommended_media: [{media_id, organism_count}, ...]}
        """
        if not args:
            return {"success": False, "error": "Missing phenotype_id argument"}

        # Parse comma-separated phenotype IDs
        phenotype_ids = args[0].split(",")

        # Delegate to QueryPatterns
        media_df = self.patterns.find_media_for_phenotypes(phenotype_ids)

        recommended_media = media_df.to_dict(orient="records")

        return {
            "success": True,
            "query_type": "phenotype_media",
            "phenotype_ids": phenotype_ids,
            "recommended_media": recommended_media,
            "count": len(recommended_media)
        }

    def _handle_centrality(self, args: List[str], **kwargs) -> Dict[str, Any]:
        """
        Handle centrality analysis query.

        Args:
            args: [category]
            **kwargs: algorithm (str, default="betweenness")

        Returns:
            {success: bool, centrality_scores: {node_id: score, ...}}
        """
        if not args:
            return {"success": False, "error": "Missing category argument"}

        category = args[0]
        algorithm = kwargs.get("algorithm", "betweenness")

        try:
            # Build filtered graph for category
            graph = self.graph_builder.build_from_duckdb(
                node_categories={category}
            )

            # Calculate centrality
            centrality_scores = self.algorithms.calculate_centrality(
                graph, algorithm=algorithm
            )

            return {
                "success": True,
                "query_type": "centrality",
                "category": category,
                "algorithm": algorithm,
                "centrality_scores": centrality_scores
            }

        except ImportError as e:
            return {"success": False, "error": str(e)}

    def _handle_subgraph(self, args: List[str], **kwargs) -> Dict[str, Any]:
        """
        Handle subgraph extraction query.

        Args:
            args: [node_id] or [node_id1,node_id2,...]
            **kwargs: radius (int, default=1)

        Returns:
            {success: bool, subgraph: Graph, node_count: int, edge_count: int}
        """
        if not args:
            return {"success": False, "error": "Missing node_id argument"}

        # Parse comma-separated node IDs
        center_nodes = args[0].split(",")
        radius = kwargs.get("radius", 1)

        try:
            # Use GRAPE for neighborhood extraction
            graph = self.graph
            subgraph = self.algorithms.extract_neighborhood(
                graph, center_nodes, radius=radius
            )

            return {
                "success": True,
                "query_type": "subgraph",
                "center_nodes": center_nodes,
                "radius": radius,
                "subgraph": subgraph,
                "node_count": subgraph.get_number_of_nodes(),
                "edge_count": subgraph.get_number_of_edges()
            }

        except ImportError as e:
            return {"success": False, "error": str(e)}

    def close(self) -> None:
        """Close database connection and cleanup resources."""
        if self.conn:
            self.conn.close()
        if self.graph_builder:
            self.graph_builder.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

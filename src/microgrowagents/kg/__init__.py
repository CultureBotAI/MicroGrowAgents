"""Knowledge Graph (KG-Microbe) integration module.

This module provides tools for loading and querying the KG-Microbe knowledge graph:
- loader.py: Load 1.5M nodes and 5.1M edges into DuckDB
- graph_builder.py: Build GRAPE graphs for advanced algorithms
- query_patterns.py: Pre-built SQL queries for common use cases
- algorithms.py: GRAPE graph algorithms wrapper
"""

from microgrowagents.kg.loader import KGLoader
from microgrowagents.kg.graph_builder import GraphBuilder, GRAPE_AVAILABLE
from microgrowagents.kg.query_patterns import QueryPatterns
from microgrowagents.kg.algorithms import GraphAlgorithms

__all__ = [
    "KGLoader",
    "GraphBuilder",
    "QueryPatterns",
    "GraphAlgorithms",
    "GRAPE_AVAILABLE",
]

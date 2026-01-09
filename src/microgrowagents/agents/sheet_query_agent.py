"""
Sheet Query Agent for querying extended information sheets.

Provides 4 query types:
1. Entity lookup by ID/name
2. Cross-reference queries (link related entities)
3. Full-text publication search
4. Filtered table queries

Author: MicroGrowAgents Team
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import duckdb

from microgrowagents.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SheetQueryAgent(BaseAgent):
    """
    Agent for querying information sheets from data/sheets_* directories.

    Supports 4 query types:
    - Entity lookup: Find entities by ID, name, or type
    - Cross-reference: Find related entities across tables
    - Publication search: Full-text search in publications
    - Filtered queries: SQL-like filtering on tables

    Example:
        >>> agent = SheetQueryAgent()
        >>> result = agent.entity_lookup(
        ...     query="lookup chemical CHEBI:52927",
        ...     collection_id="cmm",
        ...     entity_id="CHEBI:52927"
        ... )
        >>> result["success"]
        True
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize Sheet Query Agent.

        Args:
            db_path: Path to DuckDB database with sheet tables
        """
        super().__init__(db_path)
        self.conn = None

    def _connect(self):
        """Establish database connection."""
        if self.conn is None:
            self.conn = duckdb.connect(str(self.db_path))

    def _close(self):
        """Close database connection."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def run(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute sheet query.

        Routes query to appropriate handler based on query type.

        Args:
            query: Query string describing task
            **kwargs: Query-specific parameters

        Returns:
            Dict with success status, data, and metadata
        """
        query_lower = query.lower()

        # Route based on query keywords or explicit parameters
        if "lookup" in query_lower or "find" in query_lower and "entity_id" in kwargs:
            return self.entity_lookup(query, **kwargs)
        elif "related" in query_lower or "cross" in query_lower or "source_entity_id" in kwargs:
            return self.cross_reference_query(query, **kwargs)
        elif "search" in query_lower and "publication" in query_lower or "keyword" in kwargs:
            return self.publication_search(query, **kwargs)
        elif "filter" in query_lower or "filter_conditions" in kwargs:
            return self.filtered_query(query, **kwargs)
        else:
            return {
                "success": False,
                "error": f"Unknown query type: {query}. Use 'lookup', 'related', 'search publications', or 'filter'.",
                "query": query
            }

    # ==================================================================
    # QUERY TYPE 1: Entity Lookup
    # ==================================================================

    def entity_lookup(
        self,
        query: str,
        collection_id: str,
        entity_id: Optional[str] = None,
        entity_name: Optional[str] = None,
        entity_type: Optional[str] = None,
        exact_match: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Find entities by ID, name, or type.

        Args:
            query: Query string
            collection_id: Collection ID (e.g., 'cmm')
            entity_id: Entity ID to lookup (exact match)
            entity_name: Entity name to lookup
            entity_type: Filter by entity type
            exact_match: If False, use partial name matching

        Returns:
            Dict with success, data (entities list), metadata
        """
        self._connect()

        try:
            # Build WHERE clause
            where_clauses = [f"table_id LIKE '{collection_id}_%'"]

            if entity_id:
                where_clauses.append(f"entity_id = '{entity_id}'")

            if entity_name:
                if exact_match:
                    where_clauses.append(f"entity_name = '{entity_name}'")
                else:
                    where_clauses.append(f"LOWER(entity_name) LIKE LOWER('%{entity_name}%')")

            if entity_type:
                where_clauses.append(f"entity_type = '{entity_type}'")

            where_clause = " AND ".join(where_clauses)

            # Execute query
            sql = f"""
                SELECT
                    entity_id,
                    entity_name,
                    entity_type,
                    table_id,
                    data_json
                FROM sheet_data
                WHERE {where_clause}
                ORDER BY entity_type, entity_name
            """

            rows = self.conn.execute(sql).fetchall()

            # Parse results
            entities = []
            for row in rows:
                entity = {
                    "entity_id": row[0],
                    "entity_name": row[1],
                    "entity_type": row[2],
                    "table_id": row[3],
                    "properties": json.loads(row[4]) if row[4] else {}
                }
                entities.append(entity)

            return {
                "success": True,
                "data": {
                    "entities": entities,
                    "count": len(entities)
                },
                "metadata": {
                    "query": query,
                    "collection_id": collection_id,
                    "entity_id": entity_id,
                    "entity_name": entity_name,
                    "entity_type": entity_type
                }
            }

        except Exception as e:
            logger.error(f"Entity lookup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }

    # ==================================================================
    # QUERY TYPE 2: Cross-Reference Query
    # ==================================================================

    def cross_reference_query(
        self,
        query: str,
        collection_id: str,
        source_entity_id: str,
        include_types: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Find entities related to a source entity.

        Strategy:
        1. Find source entity
        2. Parse data_json for foreign key columns
        3. Find related entities in other tables
        4. Include publication references

        Args:
            query: Query string
            collection_id: Collection ID
            source_entity_id: Source entity ID
            include_types: Filter related entities by type

        Returns:
            Dict with source_entity, related_entities, publications
        """
        self._connect()

        try:
            # Get source entity
            source_sql = f"""
                SELECT entity_id, entity_name, entity_type, table_id, data_json
                FROM sheet_data
                WHERE table_id LIKE '{collection_id}_%'
                  AND entity_id = '{source_entity_id}'
            """
            source_row = self.conn.execute(source_sql).fetchone()

            if not source_row:
                return {
                    "success": True,
                    "data": {
                        "source_entity": None,
                        "related_entities": [],
                        "publications": []
                    },
                    "metadata": {"error": f"Source entity not found: {source_entity_id}"}
                }

            source_entity = {
                "entity_id": source_row[0],
                "entity_name": source_row[1],
                "entity_type": source_row[2],
                "table_id": source_row[3],
                "properties": json.loads(source_row[4]) if source_row[4] else {}
            }

            # Extract potential foreign keys from properties
            properties = source_entity["properties"]
            related_ids = self._extract_related_ids(properties)

            # Find related entities
            related_entities = []
            if related_ids:
                ids_list = "', '".join(related_ids)
                related_sql = f"""
                    SELECT DISTINCT entity_id, entity_name, entity_type, table_id, data_json
                    FROM sheet_data
                    WHERE table_id LIKE '{collection_id}_%'
                      AND entity_id IN ('{ids_list}')
                """

                if include_types:
                    types_list = "', '".join(include_types)
                    related_sql += f" AND entity_type IN ('{types_list}')"

                for row in self.conn.execute(related_sql).fetchall():
                    related_entities.append({
                        "entity_id": row[0],
                        "entity_name": row[1],
                        "entity_type": row[2],
                        "table_id": row[3],
                        "properties": json.loads(row[4]) if row[4] else {},
                        "relationship": "referenced_by_source"
                    })

            # Also search for entities that reference the source
            searchable_sql = f"""
                SELECT DISTINCT entity_id, entity_name, entity_type, table_id, data_json
                FROM sheet_data
                WHERE table_id LIKE '{collection_id}_%'
                  AND searchable_text LIKE '%{source_entity_id}%'
                  AND entity_id != '{source_entity_id}'
            """

            if include_types:
                types_list = "', '".join(include_types)
                searchable_sql += f" AND entity_type IN ('{types_list}')"

            for row in self.conn.execute(searchable_sql).fetchall():
                # Avoid duplicates
                if not any(e["entity_id"] == row[0] for e in related_entities):
                    related_entities.append({
                        "entity_id": row[0],
                        "entity_name": row[1],
                        "entity_type": row[2],
                        "table_id": row[3],
                        "properties": json.loads(row[4]) if row[4] else {},
                        "relationship": "references_source"
                    })

            # Get publication references
            pub_sql = f"""
                SELECT DISTINCT p.publication_id, p.publication_type, p.title, p.full_text
                FROM sheet_publication_references r
                JOIN sheet_publications p ON r.publication_id = p.id
                WHERE r.entity_id = '{source_entity_id}'
            """
            publications = []
            for row in self.conn.execute(pub_sql).fetchall():
                publications.append({
                    "publication_id": row[0],
                    "publication_type": row[1],
                    "title": row[2],
                    "full_text": row[3]
                })

            return {
                "success": True,
                "data": {
                    "source_entity": source_entity,
                    "related_entities": related_entities,
                    "publications": publications
                },
                "metadata": {
                    "query": query,
                    "collection_id": collection_id,
                    "source_entity_id": source_entity_id
                }
            }

        except Exception as e:
            logger.error(f"Cross-reference query failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }

    def _extract_related_ids(self, properties: Dict) -> List[str]:
        """
        Extract potential related entity IDs from properties.

        Looks for columns like: CHEBI, GO, organism, chemical_id, gene_id, etc.
        """
        related_ids = set()

        for key, value in properties.items():
            if not value or not isinstance(value, str):
                continue

            # Check for ontology ID patterns
            if any(prefix in key.lower() for prefix in ["chebi", "go", "kegg", "ncbi", "taxon"]):
                # Split on common delimiters
                for id_str in re.split(r'[,;\s]+', value):
                    id_str = id_str.strip()
                    if id_str and (":" in id_str or id_str.startswith("K") or id_str.isdigit()):
                        related_ids.add(id_str)

        return list(related_ids)

    # ==================================================================
    # QUERY TYPE 3: Publication Search
    # ==================================================================

    def publication_search(
        self,
        query: str,
        collection_id: str,
        keyword: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        max_results: int = 50,
        include_excerpts: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search publications by keyword(s).

        Args:
            query: Query string
            collection_id: Collection ID
            keyword: Single keyword to search
            keywords: Multiple keywords (OR logic)
            max_results: Maximum number of results
            include_excerpts: Include text excerpts around keywords

        Returns:
            Dict with publications list
        """
        self._connect()

        try:
            # Build search keywords list
            search_keywords = keywords if keywords else [keyword] if keyword else []

            if not search_keywords:
                return {
                    "success": False,
                    "error": "No keywords provided",
                    "query": query
                }

            # Build WHERE clause for keyword search
            keyword_clauses = []
            for kw in search_keywords:
                keyword_clauses.append(f"LOWER(full_text) LIKE LOWER('%{kw}%')")

            keyword_where = " OR ".join(keyword_clauses)

            # Query publications with entity counts
            sql = f"""
                SELECT
                    p.id,
                    p.publication_id,
                    p.publication_type,
                    p.title,
                    p.full_text,
                    COUNT(r.id) as entity_count
                FROM sheet_publications p
                LEFT JOIN sheet_publication_references r ON p.id = r.publication_id
                WHERE p.collection_id = '{collection_id}'
                  AND ({keyword_where})
                GROUP BY p.id, p.publication_id, p.publication_type, p.title, p.full_text
                ORDER BY entity_count DESC
                LIMIT {max_results}
            """

            rows = self.conn.execute(sql).fetchall()

            publications = []
            for row in rows:
                pub = {
                    "id": row[0],
                    "publication_id": row[1],
                    "publication_type": row[2],
                    "title": row[3],
                    "full_text": row[4],
                    "entity_count": row[5]
                }

                # Add excerpt if requested
                if include_excerpts and search_keywords:
                    pub["excerpt"] = self._extract_excerpt(row[4], search_keywords[0])

                publications.append(pub)

            return {
                "success": True,
                "data": {
                    "publications": publications,
                    "count": len(publications)
                },
                "metadata": {
                    "query": query,
                    "collection_id": collection_id,
                    "keywords": search_keywords,
                    "max_results": max_results
                }
            }

        except Exception as e:
            logger.error(f"Publication search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }

    def _extract_excerpt(self, text: str, keyword: str, context_chars: int = 200) -> str:
        """
        Extract text excerpt around keyword.

        Args:
            text: Full text
            keyword: Keyword to find
            context_chars: Characters of context on each side

        Returns:
            Excerpt string with keyword in context
        """
        text_lower = text.lower()
        keyword_lower = keyword.lower()

        # Find first occurrence
        pos = text_lower.find(keyword_lower)
        if pos == -1:
            return text[:context_chars * 2] if len(text) > context_chars * 2 else text

        # Extract context
        start = max(0, pos - context_chars)
        end = min(len(text), pos + len(keyword) + context_chars)

        excerpt = text[start:end]

        # Add ellipsis if truncated
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(text):
            excerpt = excerpt + "..."

        return excerpt

    # ==================================================================
    # QUERY TYPE 4: Filtered Query
    # ==================================================================

    def filtered_query(
        self,
        query: str,
        collection_id: str,
        table_name: Optional[str] = None,
        entity_type: Optional[str] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Filter entities by properties.

        Supports operators:
        - Equality: {"property": "value"}
        - Contains: {"property": {"$contains": "substring"}}

        Args:
            query: Query string
            collection_id: Collection ID
            table_name: Table name to filter
            entity_type: Entity type to filter
            filter_conditions: Dict of property filters

        Returns:
            Dict with filtered entities
        """
        self._connect()

        try:
            # Build base WHERE clause
            where_clauses = [f"table_id LIKE '{collection_id}_%'"]

            if table_name:
                where_clauses.append(f"table_id = '{collection_id}_{table_name}'")

            if entity_type:
                where_clauses.append(f"entity_type = '{entity_type}'")

            # Build filter conditions
            if filter_conditions:
                for key, value in filter_conditions.items():
                    if isinstance(value, dict):
                        # Operator-based filter
                        if "$contains" in value:
                            # Use JSON extraction
                            where_clauses.append(
                                f"LOWER(json_extract_string(data_json, '$.{key}')) LIKE LOWER('%{value['$contains']}%')"
                            )
                    else:
                        # Equality filter
                        where_clauses.append(
                            f"json_extract_string(data_json, '$.{key}') = '{value}'"
                        )

            where_clause = " AND ".join(where_clauses)

            # Execute query
            sql = f"""
                SELECT
                    entity_id,
                    entity_name,
                    entity_type,
                    table_id,
                    data_json
                FROM sheet_data
                WHERE {where_clause}
                ORDER BY entity_type, entity_name
            """

            rows = self.conn.execute(sql).fetchall()

            # Parse results
            entities = []
            for row in rows:
                entity = {
                    "entity_id": row[0],
                    "entity_name": row[1],
                    "entity_type": row[2],
                    "table_id": row[3],
                    "properties": json.loads(row[4]) if row[4] else {}
                }
                entities.append(entity)

            return {
                "success": True,
                "data": {
                    "entities": entities,
                    "count": len(entities)
                },
                "metadata": {
                    "query": query,
                    "collection_id": collection_id,
                    "table_name": table_name,
                    "entity_type": entity_type,
                    "filter_conditions": filter_conditions
                }
            }

        except Exception as e:
            logger.error(f"Filtered query failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }

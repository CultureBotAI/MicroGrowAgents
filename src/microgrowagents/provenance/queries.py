"""
Provenance query utilities for analyzing execution traces.

Provides helper functions to query and analyze provenance data from DuckDB.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import duckdb
import pandas as pd


class ProvenanceQueries:
    """Helper class for querying provenance data."""

    def __init__(self, db_path: Path):
        """
        Initialize provenance queries.

        Args:
            db_path: Path to DuckDB database
        """
        self.db_path = db_path

    def get_session_trace(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve full execution trace for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with complete session trace
        """
        conn = duckdb.connect(str(self.db_path), read_only=True)

        try:
            # Get session info
            session = conn.execute(
                "SELECT * FROM provenance_sessions WHERE session_id = ?", [session_id]
            ).fetchdf()

            if session.empty:
                return {"error": f"Session {session_id} not found"}

            # Get events
            events = conn.execute(
                """
                SELECT * FROM provenance_events
                WHERE session_id = ?
                ORDER BY sequence_number
                """,
                [session_id],
            ).fetchdf()

            # Get tool calls
            tool_calls = conn.execute(
                "SELECT * FROM provenance_tool_calls WHERE session_id = ?",
                [session_id],
            ).fetchdf()

            # Get decisions
            decisions = conn.execute(
                "SELECT * FROM provenance_decisions WHERE session_id = ?", [session_id]
            ).fetchdf()

            # Get transformations
            transformations = conn.execute(
                "SELECT * FROM provenance_transformations WHERE session_id = ?",
                [session_id],
            ).fetchdf()

            # Get entity links
            entity_links = conn.execute(
                "SELECT * FROM provenance_entity_links WHERE session_id = ?",
                [session_id],
            ).fetchdf()

            return {
                "session": session.to_dict("records")[0],
                "events": events.to_dict("records"),
                "tool_calls": tool_calls.to_dict("records"),
                "decisions": decisions.to_dict("records"),
                "transformations": transformations.to_dict("records"),
                "entity_links": entity_links.to_dict("records"),
            }

        finally:
            conn.close()

    def get_agent_statistics(
        self, agent_type: Optional[str] = None, days: int = 7
    ) -> pd.DataFrame:
        """
        Get performance statistics for agents.

        Args:
            agent_type: Specific agent type to filter by (optional)
            days: Number of days to look back

        Returns:
            DataFrame with agent statistics
        """
        conn = duckdb.connect(str(self.db_path), read_only=True)

        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            if agent_type:
                query = """
                    SELECT
                        agent_type,
                        COUNT(*) as executions,
                        AVG(duration_ms) as avg_duration_ms,
                        MAX(duration_ms) as max_duration_ms,
                        MIN(duration_ms) as min_duration_ms,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
                        SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed
                    FROM provenance_sessions
                    WHERE agent_type = ?
                      AND created_at >= ?
                    GROUP BY agent_type
                """
                params = [agent_type, cutoff_date.isoformat()]
            else:
                query = """
                    SELECT
                        agent_type,
                        COUNT(*) as executions,
                        AVG(duration_ms) as avg_duration_ms,
                        MAX(duration_ms) as max_duration_ms,
                        MIN(duration_ms) as min_duration_ms,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
                        SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed
                    FROM provenance_sessions
                    WHERE created_at >= ?
                    GROUP BY agent_type
                    ORDER BY executions DESC
                """
                params = [cutoff_date.isoformat()]

            return conn.execute(query, params).fetchdf()

        finally:
            conn.close()

    def find_entity_provenance(
        self, entity_table: str, entity_id: str
    ) -> pd.DataFrame:
        """
        Find all sessions that touched a specific entity.

        Args:
            entity_table: Domain table name
            entity_id: Entity ID

        Returns:
            DataFrame with session information
        """
        conn = duckdb.connect(str(self.db_path), read_only=True)

        try:
            query = """
                SELECT
                    ps.session_id,
                    ps.agent_type,
                    ps.query,
                    ps.start_time,
                    ps.duration_ms,
                    ps.success,
                    pel.link_type,
                    pel.timestamp
                FROM provenance_sessions ps
                JOIN provenance_entity_links pel ON ps.session_id = pel.session_id
                WHERE pel.entity_table = ?
                  AND pel.entity_id = ?
                ORDER BY pel.timestamp DESC
            """

            return conn.execute(query, [entity_table, entity_id]).fetchdf()

        finally:
            conn.close()

    def get_tool_call_statistics(self, days: int = 7) -> pd.DataFrame:
        """
        Get statistics on tool/API calls.

        Args:
            days: Number of days to look back

        Returns:
            DataFrame with tool call statistics
        """
        conn = duckdb.connect(str(self.db_path), read_only=True)

        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            query = """
                SELECT
                    tool_type,
                    tool_name,
                    COUNT(*) as call_count,
                    AVG(duration_ms) as avg_duration_ms,
                    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits,
                    SUM(CASE WHEN NOT cache_hit THEN 1 ELSE 0 END) as cache_misses,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed
                FROM provenance_tool_calls
                WHERE call_time >= ?
                GROUP BY tool_type, tool_name
                ORDER BY call_count DESC
            """

            return conn.execute(query, [cutoff_date.isoformat()]).fetchdf()

        finally:
            conn.close()

    def get_decision_patterns(
        self, agent_type: Optional[str] = None, days: int = 7
    ) -> pd.DataFrame:
        """
        Analyze decision patterns in agent executions.

        Args:
            agent_type: Specific agent type to filter by (optional)
            days: Number of days to look back

        Returns:
            DataFrame with decision pattern statistics
        """
        conn = duckdb.connect(str(self.db_path), read_only=True)

        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            if agent_type:
                query = """
                    SELECT
                        ps.agent_type,
                        pd.decision_type,
                        pd.branch_taken,
                        COUNT(*) as count
                    FROM provenance_decisions pd
                    JOIN provenance_sessions ps ON pd.session_id = ps.session_id
                    WHERE ps.agent_type = ?
                      AND pd.timestamp >= ?
                    GROUP BY ps.agent_type, pd.decision_type, pd.branch_taken
                    ORDER BY count DESC
                """
                params = [agent_type, cutoff_date.isoformat()]
            else:
                query = """
                    SELECT
                        ps.agent_type,
                        pd.decision_type,
                        pd.branch_taken,
                        COUNT(*) as count
                    FROM provenance_decisions pd
                    JOIN provenance_sessions ps ON pd.session_id = ps.session_id
                    WHERE pd.timestamp >= ?
                    GROUP BY ps.agent_type, pd.decision_type, pd.branch_taken
                    ORDER BY count DESC
                """
                params = [cutoff_date.isoformat()]

            return conn.execute(query, params).fetchdf()

        finally:
            conn.close()

    def get_session_hierarchy(self, root_session_id: str) -> List[Dict[str, Any]]:
        """
        Get full session hierarchy (parent and all child sessions).

        Args:
            root_session_id: Root session identifier

        Returns:
            List of session dictionaries in hierarchical order
        """
        conn = duckdb.connect(str(self.db_path), read_only=True)

        try:
            query = """
                WITH RECURSIVE session_tree AS (
                    SELECT
                        session_id,
                        agent_type,
                        query,
                        parent_session_id,
                        depth,
                        duration_ms,
                        success,
                        0 as level
                    FROM provenance_sessions
                    WHERE session_id = ?

                    UNION ALL

                    SELECT
                        ps.session_id,
                        ps.agent_type,
                        ps.query,
                        ps.parent_session_id,
                        ps.depth,
                        ps.duration_ms,
                        ps.success,
                        st.level + 1
                    FROM provenance_sessions ps
                    JOIN session_tree st ON ps.parent_session_id = st.session_id
                )
                SELECT * FROM session_tree ORDER BY level, session_id
            """

            result = conn.execute(query, [root_session_id]).fetchdf()
            return result.to_dict("records")

        finally:
            conn.close()

    def compare_sessions(
        self, session_id_1: str, session_id_2: str
    ) -> Dict[str, Any]:
        """
        Compare two execution sessions.

        Args:
            session_id_1: First session ID
            session_id_2: Second session ID

        Returns:
            Dictionary with comparison results
        """
        trace1 = self.get_session_trace(session_id_1)
        trace2 = self.get_session_trace(session_id_2)

        if "error" in trace1 or "error" in trace2:
            return {"error": "One or both sessions not found"}

        s1 = trace1["session"]
        s2 = trace2["session"]

        return {
            "inputs_differ": (
                s1["query"] != s2["query"] or s1["kwargs"] != s2["kwargs"]
            ),
            "agent_types_match": s1["agent_type"] == s2["agent_type"],
            "duration_diff_ms": s1["duration_ms"] - s2["duration_ms"],
            "both_successful": s1["success"] and s2["success"],
            "event_count_diff": len(trace1["events"]) - len(trace2["events"]),
            "tool_call_count_diff": len(trace1["tool_calls"])
            - len(trace2["tool_calls"]),
            "decision_count_diff": len(trace1["decisions"]) - len(trace2["decisions"]),
            "session_1": {
                "session_id": s1["session_id"],
                "agent_type": s1["agent_type"],
                "duration_ms": s1["duration_ms"],
                "success": s1["success"],
            },
            "session_2": {
                "session_id": s2["session_id"],
                "agent_type": s2["agent_type"],
                "duration_ms": s2["duration_ms"],
                "success": s2["success"],
            },
        }

    def get_recent_sessions(
        self, agent_type: Optional[str] = None, limit: int = 10
    ) -> pd.DataFrame:
        """
        Get recent sessions.

        Args:
            agent_type: Filter by agent type (optional)
            limit: Maximum number of sessions to return

        Returns:
            DataFrame with recent sessions
        """
        conn = duckdb.connect(str(self.db_path), read_only=True)

        try:
            if agent_type:
                query = """
                    SELECT
                        session_id,
                        agent_type,
                        query,
                        start_time,
                        end_time,
                        duration_ms,
                        success,
                        error_message
                    FROM provenance_sessions
                    WHERE agent_type = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                params = [agent_type, limit]
            else:
                query = """
                    SELECT
                        session_id,
                        agent_type,
                        query,
                        start_time,
                        end_time,
                        duration_ms,
                        success,
                        error_message
                    FROM provenance_sessions
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                params = [limit]

            return conn.execute(query, params).fetchdf()

        finally:
            conn.close()

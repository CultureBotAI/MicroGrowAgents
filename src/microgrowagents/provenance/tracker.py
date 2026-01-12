"""
Provenance tracking system for MicroGrowAgents.

Hybrid system combining database-based tracking (DuckDB) with
file-based tracking (.claude/provenance/) for cross-project compatibility.

Provides automatic instrumentation via context managers and decorators.
"""

import json
import platform
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import duckdb

from microgrowagents.provenance.file_writer import FileBasedProvenanceWriter


class ProvenanceTracker:
    """Thread-safe provenance tracker with hybrid storage (DuckDB + YAML/JSONL)."""

    def __init__(
        self,
        db_path: Path,
        manifest_dir: Path,
        detail_level: str = "standard",
        enable_file_based: bool = True,
    ):
        """
        Initialize provenance tracker.

        Args:
            db_path: Path to DuckDB database
            manifest_dir: Directory for JSON manifests
            detail_level: "minimal", "standard", or "full"
            enable_file_based: Enable file-based provenance (YAML/JSONL)
        """
        self.db_path = db_path
        self.manifest_dir = manifest_dir
        self.detail_level = detail_level
        self.manifest_dir.mkdir(parents=True, exist_ok=True)

        # Thread-local storage for current session context
        self._local = threading.local()

        # Event batching for performance
        self._event_buffer = []
        self._buffer_lock = threading.Lock()
        self._batch_size = 50

        # File-based provenance writer
        self.enable_file_based = enable_file_based
        self.file_writer = None
        if enable_file_based:
            self.file_writer = FileBasedProvenanceWriter()

    @property
    def current_session(self) -> Optional[Dict]:
        """Get current session from thread-local storage."""
        return getattr(self._local, "session", None)

    @current_session.setter
    def current_session(self, value: Optional[Dict]):
        """Set current session in thread-local storage."""
        self._local.session = value

    def start_session(
        self,
        agent_type: str,
        query: str,
        kwargs: Dict[str, Any],
        parent_session_id: Optional[str] = None,
    ) -> str:
        """
        Start a new provenance session.

        Returns:
            session_id
        """
        session_id = str(uuid.uuid4())

        session = {
            "session_id": session_id,
            "agent_type": agent_type,
            "query": query,
            "kwargs": kwargs,
            "start_time": datetime.utcnow().isoformat(),
            "parent_session_id": parent_session_id,
            "depth": (
                0
                if parent_session_id is None
                else self._get_session_depth(parent_session_id) + 1
            ),
            "events": [],
            "tool_calls": [],
            "decisions": [],
            "transformations": [],
            "entity_links": [],
            "sequence_counter": 0,
            "environment": self._capture_environment(),
        }

        # Create file-based session directory
        if self.enable_file_based and self.file_writer:
            session_timestamp = datetime.fromisoformat(session["start_time"])
            session["file_session_dir"] = self.file_writer.create_session_dir(
                session_timestamp
            )
            session["file_session_name"] = session["file_session_dir"].name
            session["file_actions"] = []  # Track actions for file-based storage

        self.current_session = session

        # Record lifecycle event
        self.record_event(
            "lifecycle", "agent_start", {"agent_type": agent_type, "query": query}
        )

        return session_id

    def end_session(
        self, success: bool, result: Any = None, error: Optional[str] = None
    ):
        """End current provenance session and persist to storage."""
        if not self.current_session:
            return

        session = self.current_session
        session["end_time"] = datetime.utcnow().isoformat()
        session["duration_ms"] = self._calculate_duration(
            session["start_time"], session["end_time"]
        )
        session["success"] = success
        session["result_summary"] = self._summarize_result(result) if result else None
        session["error_message"] = error
        session["action_count"] = session["sequence_counter"]

        # Record lifecycle event
        self.record_event(
            "lifecycle",
            "agent_end",
            {"success": success, "duration_ms": session["duration_ms"]},
        )

        # Persist to DuckDB (this will also flush events)
        self._persist_session_to_db(session)

        # Write JSON manifest
        self._write_manifest(session)

        # Write file-based provenance (YAML + JSONL + Markdown)
        if self.enable_file_based and self.file_writer and session.get("file_session_dir"):
            session_dir = session["file_session_dir"]
            file_actions = session.get("file_actions", [])

            # Write initial manifest
            self.file_writer.write_manifest_yaml(session_dir, session)

            # Update manifest with action statistics
            if file_actions:
                self.file_writer.update_manifest_stats(session_dir, file_actions)

            # Generate summary
            self.file_writer.write_summary_md(session_dir, session, file_actions)

        # Clear session
        self.current_session = None

    def record_event(
        self, event_type: str, event_name: str, details: Dict[str, Any]
    ):
        """Record a provenance event."""
        if not self.current_session:
            return

        session = self.current_session
        session["sequence_counter"] += 1

        # Use UUID for globally unique event_id (not just sequence number)
        event = {
            "event_id": str(uuid.uuid4()),
            "session_id": session["session_id"],
            "event_type": event_type,
            "event_name": event_name,
            "timestamp": datetime.utcnow().isoformat(),
            "sequence_number": session["sequence_counter"],
            "details": details,
        }

        session["events"].append(event)

        # Add to buffer for batch insert (will be flushed at session end)
        with self._buffer_lock:
            self._event_buffer.append(event)

        # Convert to action and write to JSONL
        if self.enable_file_based and self.file_writer and session.get("file_session_dir"):
            action = self._event_to_action(event)
            self.file_writer.append_action_jsonl(session["file_session_dir"], action)
            session.get("file_actions", []).append(action)

    def record_tool_call(
        self,
        tool_type: str,
        tool_name: str,
        input_params: Dict,
        output_data: Any = None,
        duration_ms: Optional[int] = None,
        cache_hit: bool = False,
        success: bool = True,
        error: Optional[str] = None,
    ):
        """Record a tool/API call."""
        if not self.current_session:
            return

        call_id = str(uuid.uuid4())

        tool_call = {
            "call_id": call_id,
            "session_id": self.current_session["session_id"],
            "tool_type": tool_type,
            "tool_name": tool_name,
            "call_time": datetime.utcnow().isoformat(),
            "input_params": input_params,
            "output_data": self._summarize_output(output_data),
            "duration_ms": duration_ms,
            "cache_hit": cache_hit,
            "success": success,
            "error_message": error,
        }

        self.current_session["tool_calls"].append(tool_call)

        # Also record as event
        self.record_event(
            "tool_call",
            f"{tool_type}.{tool_name}",
            {"call_id": call_id, "cache_hit": cache_hit, "duration_ms": duration_ms},
        )

    def record_decision(
        self,
        decision_type: str,
        decision_point: str,
        input_values: Dict,
        branch_taken: str,
        branches_available: List[str],
        reason: str,
    ):
        """Record a decision point."""
        if not self.current_session:
            return

        decision = {
            "decision_id": str(uuid.uuid4()),
            "session_id": self.current_session["session_id"],
            "decision_type": decision_type,
            "decision_point": decision_point,
            "input_values": input_values,
            "branch_taken": branch_taken,
            "branches_available": branches_available,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.current_session["decisions"].append(decision)

        # Also record as event
        self.record_event(
            "decision", decision_point, {"branch_taken": branch_taken, "reason": reason}
        )

    def record_transformation(
        self,
        transformation_type: str,
        transformation_name: str,
        input_data: Any,
        output_data: Any,
        method: str,
        parameters: Optional[Dict] = None,
        duration_ms: Optional[int] = None,
    ):
        """Record a data transformation."""
        if not self.current_session:
            return

        transformation = {
            "transformation_id": str(uuid.uuid4()),
            "session_id": self.current_session["session_id"],
            "transformation_type": transformation_type,
            "transformation_name": transformation_name,
            "input_schema": self._infer_schema(input_data),
            "input_sample": self._sample_data(input_data),
            "output_schema": self._infer_schema(output_data),
            "output_sample": self._sample_data(output_data),
            "method": method,
            "parameters": parameters or {},
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": duration_ms,
        }

        self.current_session["transformations"].append(transformation)

        # Also record as event
        self.record_event(
            "transformation",
            transformation_name,
            {"method": method, "duration_ms": duration_ms},
        )

    def link_entity(self, entity_table: str, entity_id: str, link_type: str):
        """Link a domain entity to current session."""
        if not self.current_session:
            return

        link = {
            "entity_table": entity_table,
            "entity_id": entity_id,
            "link_type": link_type,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.current_session["entity_links"].append(link)

    @contextmanager
    def track_tool_call(self, tool_type: str, tool_name: str, input_params: Dict):
        """Context manager for automatic tool call tracking."""
        start_time = time.time()
        output_data = None
        error = None
        success = True

        try:
            yield
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            self.record_tool_call(
                tool_type,
                tool_name,
                input_params,
                output_data=output_data,
                duration_ms=duration_ms,
                success=success,
                error=error,
            )

    # Helper methods
    def _capture_environment(self) -> Dict:
        """Capture execution environment metadata."""
        dependencies = {}
        try:
            import pkg_resources

            for pkg in pkg_resources.working_set:
                if pkg.key in ["duckdb", "pandas", "requests", "linkml-runtime"]:
                    dependencies[pkg.key] = pkg.version
        except Exception:
            # If pkg_resources fails, continue without dependencies
            pass

        return {
            "python_version": sys.version,
            "platform": platform.platform(),
            "hostname": platform.node(),
            "dependencies": dependencies,
        }

    def _get_session_depth(self, session_id: str) -> int:
        """Get nesting depth of a session."""
        # Query database for session depth
        try:
            conn = duckdb.connect(str(self.db_path), read_only=True)
            try:
                result = conn.execute(
                    "SELECT depth FROM provenance_sessions WHERE session_id = ?",
                    [session_id],
                ).fetchone()
                return result[0] if result else 0
            finally:
                conn.close()
        except Exception:
            # If table doesn't exist or query fails, return 0
            return 0

    def _summarize_result(self, result: Any) -> Dict:
        """Summarize result data for storage."""
        # Truncate large results, keep metadata
        if isinstance(result, dict):
            return {
                k: str(v)[:100] if isinstance(v, str) and len(v) > 100 else v
                for k, v in list(result.items())[:10]
            }
        return {"type": type(result).__name__, "repr": str(result)[:200]}

    def _summarize_output(self, output: Any) -> Any:
        """Summarize output data."""
        if self.detail_level == "minimal":
            return {"type": type(output).__name__}
        elif self.detail_level == "standard":
            return self._sample_data(output)
        else:  # full
            return output

    def _infer_schema(self, data: Any) -> Dict:
        """Infer schema from data."""
        if isinstance(data, dict):
            return {k: type(v).__name__ for k, v in list(data.items())[:5]}
        elif isinstance(data, list) and data:
            return {
                "type": "list",
                "element_type": type(data[0]).__name__,
                "count": len(data),
            }
        return {"type": type(data).__name__}

    def _sample_data(self, data: Any) -> Any:
        """Take sample of data for storage."""
        if isinstance(data, list):
            return data[:3] if len(data) > 3 else data
        elif isinstance(data, dict):
            return {k: v for k, v in list(data.items())[:5]}
        return data

    def _calculate_duration(self, start_iso: str, end_iso: str) -> int:
        """Calculate duration in milliseconds."""
        start = datetime.fromisoformat(start_iso)
        end = datetime.fromisoformat(end_iso)
        return int((end - start).total_seconds() * 1000)

    def _event_to_action(self, event: Dict) -> Dict:
        """
        Convert database event to file-based action format.

        Maps event types to action types using the mapping table:
        - lifecycle -> execute
        - tool_call -> query
        - decision -> decision
        - transformation -> analyze
        - log -> read
        """
        # Event type to action type mapping
        action_type_map = {
            "lifecycle": "execute",
            "tool_call": "query",
            "decision": "decision",
            "transformation": "analyze",
            "log": "read",
            "cache_hit": "query",
            "validation": "execute",
            "database_query": "query",
        }

        # Determine tool name from event
        tool = self._map_tool_name(event["event_name"], event.get("details", {}))

        # Determine if read-only
        read_only = event["event_type"] in ["lifecycle", "log", "cache_hit"]

        # Build action
        action = {
            "timestamp": event["timestamp"] + "Z" if not event["timestamp"].endswith("Z") else event["timestamp"],
            "action_id": event["sequence_number"],
            "type": action_type_map.get(event["event_type"], "execute"),
            "tool": tool,
            "status": "success",  # Default to success; can be overridden by details
            "duration_ms": event.get("details", {}).get("duration_ms", 0),
            "details": event.get("details", {}),
            "files_affected": [],
            "read_only": read_only,
            "database_event_id": event["event_id"],
        }

        # Add entity links if present
        if self.current_session and self.current_session.get("entity_links"):
            recent_links = [
                {
                    "entity_table": link["entity_table"],
                    "entity_id": link["entity_id"],
                    "link_type": link["link_type"],
                }
                for link in self.current_session["entity_links"][-5:]  # Last 5 links
            ]
            if recent_links:
                action["entity_links"] = recent_links

        return action

    def _map_tool_name(self, event_name: str, details: Dict) -> str:
        """Map event name to tool name for file-based action."""
        # MicroGrow-specific tool mapping
        if "kegg" in event_name.lower():
            return "KEGGPathwayAPI"
        elif "biocyc" in event_name.lower():
            return "BioCycAPI"
        elif "ncbi" in event_name.lower() or "genome" in event_name.lower():
            return "NCBIGenomeAPI"
        elif "chebi" in event_name.lower():
            return "ChEBIAPI"
        elif "equilibrator" in event_name.lower():
            return "EquilibratorAPI"
        elif "media" in event_name.lower() and "optimization" in event_name.lower():
            return "MediaOptimizationAgent"
        elif "media" in event_name.lower() and "formulation" in event_name.lower():
            return "MediaFormulationAgent"
        elif "growth" in event_name.lower() and "prediction" in event_name.lower():
            return "GrowthPredictionAgent"
        elif "pathway" in event_name.lower():
            return "PathwayAnalysisAgent"
        elif "literature" in event_name.lower() or "evidence" in event_name.lower():
            return "LiteratureAgent"
        # Generic tool mappings (fallback from PFASCommunityAgents)
        elif "pubchem" in event_name.lower():
            return "PubChemAPI"
        elif "pubmed" in event_name.lower():
            return "PubMedAPI"
        elif "duckdb" in event_name.lower() or "database" in event_name.lower():
            return "DuckDB"
        elif "chemistry" in event_name.lower():
            return "ChemistryAgent"
        elif "sql" in event_name.lower():
            return "SQLAgent"
        elif "media" in event_name.lower():
            return "MediaAgent"
        elif event_name in ["agent_start", "agent_end"]:
            return "AgentExecution"
        elif "calculation" in event_name.lower() or "bcf" in event_name.lower():
            return "ChemicalCalculation"
        elif "aggregate" in event_name.lower() or "transform" in event_name.lower():
            return "DataAggregation"
        elif "decision" in event_name.lower() or "route" in event_name.lower():
            return "AgentRouter"
        elif "template" in event_name.lower():
            return "SQLTemplateMatch"
        else:
            # Default: use event name as tool name
            return event_name

    def _flush_event_buffer(self):
        """Flush event buffer to database."""
        with self._buffer_lock:
            if not self._event_buffer:
                return

            try:
                conn = duckdb.connect(str(self.db_path))
                try:
                    conn.executemany(
                        """
                        INSERT INTO provenance_events
                        (event_id, session_id, event_type, event_name, timestamp, sequence_number, details)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        [
                            (
                                e["event_id"],
                                e["session_id"],
                                e["event_type"],
                                e["event_name"],
                                e["timestamp"],
                                e["sequence_number"],
                                json.dumps(e["details"]),
                            )
                            for e in self._event_buffer
                        ],
                    )
                    conn.commit()
                finally:
                    conn.close()
            except Exception as e:
                # If DB write fails, just log and continue
                print(f"Warning: Failed to flush event buffer: {e}")
            finally:
                # Always clear buffer, even on error, to prevent duplicates
                self._event_buffer.clear()

    def _persist_session_to_db(self, session: Dict):
        """Persist session to DuckDB."""
        try:
            conn = duckdb.connect(str(self.db_path))
            try:
                # Insert session record FIRST (so events can reference it)
                conn.execute(
                    """
                    INSERT INTO provenance_sessions
                    (session_id, agent_type, query, kwargs, user_context, start_time, end_time,
                     duration_ms, success, result_summary, error_message, python_version,
                     dependencies, db_path, parent_session_id, depth)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        session["session_id"],
                        session["agent_type"],
                        session["query"],
                        json.dumps(session["kwargs"]),
                        json.dumps(session.get("user_context", {})),
                        session["start_time"],
                        session["end_time"],
                        session["duration_ms"],
                        session["success"],
                        json.dumps(session.get("result_summary")),
                        session.get("error_message"),
                        session["environment"]["python_version"],
                        json.dumps(session["environment"]["dependencies"]),
                        str(self.db_path),
                        session.get("parent_session_id"),
                        session["depth"],
                    ],
                )

                # Commit session so events can reference it
                conn.commit()
                conn.close()

                # Now flush event buffer (events will have valid foreign key)
                self._flush_event_buffer()

                # Reopen connection for remaining inserts
                conn = duckdb.connect(str(self.db_path))

                # Insert tool calls
                for call in session["tool_calls"]:
                    conn.execute(
                        """
                        INSERT INTO provenance_tool_calls
                        (call_id, session_id, event_id, tool_type, tool_name, input_params,
                         output_data, call_time, duration_ms, cache_hit, success, error_message)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        [
                            call["call_id"],
                            call["session_id"],
                            None,  # event_id will be linked later if needed
                            call["tool_type"],
                            call["tool_name"],
                            json.dumps(call["input_params"]),
                            json.dumps(call.get("output_data")),
                            call["call_time"],
                            call.get("duration_ms"),
                            call.get("cache_hit", False),
                            call.get("success", True),
                            call.get("error_message"),
                        ],
                    )

                # Insert decisions
                for dec in session["decisions"]:
                    conn.execute(
                        """
                        INSERT INTO provenance_decisions
                        (decision_id, session_id, event_id, decision_type, decision_point,
                         input_values, branch_taken, branches_available, reason, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        [
                            dec["decision_id"],
                            dec["session_id"],
                            None,  # event_id
                            dec["decision_type"],
                            dec["decision_point"],
                            json.dumps(dec["input_values"]),
                            dec["branch_taken"],
                            json.dumps(dec["branches_available"]),
                            dec["reason"],
                            dec["timestamp"],
                        ],
                    )

                # Insert transformations
                for trans in session["transformations"]:
                    conn.execute(
                        """
                        INSERT INTO provenance_transformations
                        (transformation_id, session_id, event_id, transformation_type,
                         transformation_name, input_schema, input_sample, output_schema,
                         output_sample, method, parameters, timestamp, duration_ms)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        [
                            trans["transformation_id"],
                            trans["session_id"],
                            None,  # event_id
                            trans["transformation_type"],
                            trans["transformation_name"],
                            json.dumps(trans["input_schema"]),
                            json.dumps(trans["input_sample"]),
                            json.dumps(trans["output_schema"]),
                            json.dumps(trans["output_sample"]),
                            trans["method"],
                            json.dumps(trans["parameters"]),
                            trans["timestamp"],
                            trans.get("duration_ms"),
                        ],
                    )

                # Insert entity links
                for link in session["entity_links"]:
                    conn.execute(
                        """
                        INSERT INTO provenance_entity_links
                        (session_id, event_id, entity_table, entity_id, link_type, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        [
                            session["session_id"],
                            None,  # event_id
                            link["entity_table"],
                            link["entity_id"],
                            link["link_type"],
                            link["timestamp"],
                        ],
                    )

                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            # If DB write fails, just log and continue (JSON manifest will still be written)
            print(f"Warning: Failed to persist session to database: {e}")

    def _write_manifest(self, session: Dict):
        """Write JSON manifest to file."""
        try:
            manifest_path = self.manifest_dir / f"{session['session_id']}.json"

            # Exclude file-based storage fields from JSON manifest
            excluded_keys = [
                "events",
                "tool_calls",
                "decisions",
                "transformations",
                "entity_links",
                "file_session_dir",  # Path object - not JSON serializable
                "file_session_name",  # Duplicate of session dir name
                "file_actions",  # Actions are written to JSONL separately
            ]

            manifest = {
                "manifest_version": "1.0",
                "session": {k: v for k, v in session.items() if k not in excluded_keys},
                "environment": session["environment"],
                "execution_trace": session["events"],
                "tool_calls": session["tool_calls"],
                "decisions": session["decisions"],
                "transformations": session["transformations"],
                "entity_links": session["entity_links"],
            }

            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)
        except Exception as e:
            # If manifest write fails, just log and continue
            print(f"Warning: Failed to write manifest: {e}")


# Global tracker instance
_global_tracker: Optional[ProvenanceTracker] = None


def get_tracker(db_path: Optional[Path] = None) -> ProvenanceTracker:
    """Get global provenance tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        default_db = db_path or Path("data/processed/microgrow.duckdb")
        manifest_dir = Path(".claude/provenance")
        _global_tracker = ProvenanceTracker(default_db, manifest_dir)
    return _global_tracker

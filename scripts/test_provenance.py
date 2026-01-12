#!/usr/bin/env python
"""
Test provenance tracking hybrid system.

Verifies that provenance is recorded to both:
1. DuckDB tables
2. .claude/provenance/ files
"""

from pathlib import Path

import duckdb


class TestAgent:
    """Simple test agent for provenance validation."""

    def __init__(self):
        self.db_path = Path("data/processed/microgrow.duckdb")
        self.enable_provenance = True
        self._tracker = None

        # Initialize provenance tracker
        if self.enable_provenance:
            try:
                from microgrowagents.provenance.tracker import get_tracker
                self._tracker = get_tracker(db_path=self.db_path)
                print("✓ Provenance tracker initialized")
            except Exception as e:
                print(f"✗ Failed to initialize tracker: {e}")
                raise

    def execute(self, query: str):
        """Execute a test query with provenance tracking."""
        if not self._tracker:
            print("✗ No tracker available")
            return

        # Start session
        session_id = self._tracker.start_session(
            agent_type="TestAgent",
            query=query,
            kwargs={"test": True},
        )
        print(f"✓ Started session: {session_id}")

        try:
            # Record some events
            self._tracker.record_event(
                "lifecycle",
                "agent_start",
                {"message": "Test agent started"}
            )

            self._tracker.record_event(
                "log",
                "log_info",
                {"message": "Processing test query", "level": "INFO"}
            )

            # Simulate a decision
            self._tracker.record_decision(
                decision_type="route",
                decision_point="query_type",
                input_values={"query": query},
                branch_taken="test_mode",
                branches_available=["test_mode", "production_mode"],
                reason="Running in test mode"
            )

            # End session successfully
            result = {"status": "success", "message": "Test completed"}
            self._tracker.end_session(success=True, result=result)
            print(f"✓ Session completed successfully")

            return session_id

        except Exception as e:
            self._tracker.end_session(success=False, error=str(e))
            raise


def verify_database_storage(session_id: str):
    """Verify provenance was stored in DuckDB."""
    print("\n=== Verifying Database Storage ===")

    conn = duckdb.connect("data/processed/microgrow.duckdb")

    # Check session exists
    session = conn.execute(
        "SELECT * FROM provenance_sessions WHERE session_id = ?",
        [session_id]
    ).fetchone()

    if session:
        print(f"✓ Session found in database: {session[0]}")
        print(f"  Agent: {session[1]}")
        print(f"  Query: {session[3]}")
        print(f"  Success: {session[9]}")
    else:
        print("✗ Session not found in database")
        conn.close()
        return False

    # Check events
    events = conn.execute(
        "SELECT COUNT(*) FROM provenance_events WHERE session_id = ?",
        [session_id]
    ).fetchone()[0]
    print(f"✓ Events recorded: {events}")

    # Check decisions
    decisions = conn.execute(
        "SELECT COUNT(*) FROM provenance_decisions WHERE session_id = ?",
        [session_id]
    ).fetchone()[0]
    print(f"✓ Decisions recorded: {decisions}")

    conn.close()
    return True


def verify_file_storage(session_id: str):
    """Verify provenance was stored in .claude/provenance/ files."""
    print("\n=== Verifying File Storage ===")

    # Find session directory
    provenance_dir = Path(".claude/provenance/sessions")
    session_dirs = list(provenance_dir.glob("*"))

    if not session_dirs:
        print("✗ No session directories found")
        return False

    # Get most recent session (should be ours)
    latest_session = sorted(session_dirs, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    print(f"✓ Session directory found: {latest_session.name}")

    # Check for files
    manifest = latest_session / "manifest.yaml"
    actions = latest_session / "actions.jsonl"
    summary = latest_session / "summary.md"

    files_exist = []
    if manifest.exists():
        print(f"✓ manifest.yaml exists ({manifest.stat().st_size} bytes)")
        files_exist.append(True)
    else:
        print("✗ manifest.yaml not found")
        files_exist.append(False)

    if actions.exists():
        # Count actions
        action_count = len(actions.read_text().strip().split("\n"))
        print(f"✓ actions.jsonl exists ({action_count} actions)")
        files_exist.append(True)
    else:
        print("✗ actions.jsonl not found")
        files_exist.append(False)

    if summary.exists():
        print(f"✓ summary.md exists ({summary.stat().st_size} bytes)")
        files_exist.append(True)
    else:
        print("✗ summary.md not found")
        files_exist.append(False)

    return all(files_exist)


def main():
    """Run provenance tracking test."""
    print("=" * 60)
    print("Testing MicroGrowAgents Hybrid Provenance System")
    print("=" * 60)

    # Create test agent and execute
    agent = TestAgent()
    session_id = agent.execute("Test provenance tracking")

    # Verify both storage systems
    db_ok = verify_database_storage(session_id)
    file_ok = verify_file_storage(session_id)

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Database storage: {'✓ PASS' if db_ok else '✗ FAIL'}")
    print(f"File storage:     {'✓ PASS' if file_ok else '✗ FAIL'}")

    if db_ok and file_ok:
        print("\n✓ Hybrid provenance tracking is working correctly!")
        print("\nYou can now:")
        print("  1. Query sessions with SQL: just show-sessions")
        print("  2. Query actions with jq:   cat .claude/provenance/sessions/*/actions.jsonl | jq")
        print("  3. View summaries:          ls .claude/provenance/sessions/")
        return 0
    else:
        print("\n✗ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

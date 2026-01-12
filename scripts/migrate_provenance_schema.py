#!/usr/bin/env python
"""
Migrate existing MicroGrowAgents database to add provenance tracking tables.

This script adds 6 provenance tables to enable hybrid provenance tracking
(database + file-based) across PFASCommunityAgents and MicroGrowAgents.
"""

import sys
from pathlib import Path

import duckdb


def migrate_schema(db_path: str):
    """Add provenance tracking tables to existing database."""
    print(f"Migrating database: {db_path}")

    # Ensure database file exists
    db_file = Path(db_path)
    if not db_file.exists():
        print(f"Error: Database file not found: {db_path}")
        print("Please run data loading first to create the database.")
        sys.exit(1)

    conn = duckdb.connect(db_path)

    try:
        # Check if tables already exist
        existing = conn.execute(
            """
            SELECT table_name FROM duckdb_tables()
            WHERE schema_name = 'main' AND table_name LIKE 'provenance_%'
            """
        ).fetchall()

        if existing:
            print(f"Found {len(existing)} existing provenance tables:")
            for (table_name,) in existing:
                print(f"  - {table_name}")
            response = input("\nDo you want to recreate them? (yes/no): ")
            if response.lower() != "yes":
                print("Migration cancelled")
                return

            # Drop existing tables in correct order (child tables first)
            drop_order = [
                "provenance_entity_links",
                "provenance_transformations",
                "provenance_decisions",
                "provenance_tool_calls",
                "provenance_events",
                "provenance_sessions",
            ]
            for table_name in drop_order:
                print(f"Dropping table: {table_name}")
                conn.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")

        # Create provenance_sessions table
        print("Creating provenance_sessions...")
        conn.execute("""
            CREATE TABLE provenance_sessions (
                session_id VARCHAR PRIMARY KEY,
                agent_type VARCHAR NOT NULL,
                agent_version VARCHAR,
                query TEXT NOT NULL,
                kwargs JSON,
                user_context JSON,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration_ms INTEGER,
                success BOOLEAN,
                result_summary JSON,
                error_message TEXT,
                python_version VARCHAR,
                dependencies JSON,
                db_path VARCHAR,
                parent_session_id VARCHAR,
                depth INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_session_id) REFERENCES provenance_sessions(session_id)
            )
        """)

        # Create provenance_events table
        print("Creating provenance_events...")
        conn.execute("""
            CREATE TABLE provenance_events (
                event_id VARCHAR PRIMARY KEY,
                session_id VARCHAR NOT NULL,
                event_type VARCHAR NOT NULL,
                event_name VARCHAR NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                sequence_number INTEGER NOT NULL,
                details JSON NOT NULL,
                duration_ms INTEGER,
                related_event_id VARCHAR,
                FOREIGN KEY (session_id) REFERENCES provenance_sessions(session_id)
            )
        """)

        # Create provenance_tool_calls table
        print("Creating provenance_tool_calls...")
        conn.execute("""
            CREATE TABLE provenance_tool_calls (
                call_id VARCHAR PRIMARY KEY,
                session_id VARCHAR NOT NULL,
                event_id VARCHAR NOT NULL,
                tool_type VARCHAR NOT NULL,
                tool_name VARCHAR NOT NULL,
                input_params JSON NOT NULL,
                output_data JSON,
                output_size_bytes INTEGER,
                call_time TIMESTAMP NOT NULL,
                duration_ms INTEGER,
                cache_hit BOOLEAN DEFAULT FALSE,
                cache_key VARCHAR,
                cache_source VARCHAR,
                rate_limit_delay_ms INTEGER,
                retry_count INTEGER DEFAULT 0,
                success BOOLEAN NOT NULL,
                error_type VARCHAR,
                error_message TEXT,
                FOREIGN KEY (session_id) REFERENCES provenance_sessions(session_id)
            )
        """)

        # Create provenance_decisions table
        print("Creating provenance_decisions...")
        conn.execute("""
            CREATE TABLE provenance_decisions (
                decision_id VARCHAR PRIMARY KEY,
                session_id VARCHAR NOT NULL,
                event_id VARCHAR NOT NULL,
                decision_type VARCHAR NOT NULL,
                decision_point VARCHAR NOT NULL,
                input_values JSON NOT NULL,
                condition_evaluated TEXT,
                branch_taken VARCHAR,
                branches_available JSON,
                reason TEXT,
                timestamp TIMESTAMP NOT NULL,
                FOREIGN KEY (session_id) REFERENCES provenance_sessions(session_id)
            )
        """)

        # Create provenance_transformations table
        print("Creating provenance_transformations...")
        conn.execute("""
            CREATE TABLE provenance_transformations (
                transformation_id VARCHAR PRIMARY KEY,
                session_id VARCHAR NOT NULL,
                event_id VARCHAR NOT NULL,
                transformation_type VARCHAR NOT NULL,
                transformation_name VARCHAR NOT NULL,
                input_schema JSON,
                input_sample JSON,
                input_size INTEGER,
                output_schema JSON,
                output_sample JSON,
                output_size INTEGER,
                method VARCHAR,
                parameters JSON,
                timestamp TIMESTAMP NOT NULL,
                duration_ms INTEGER,
                FOREIGN KEY (session_id) REFERENCES provenance_sessions(session_id)
            )
        """)

        # Create provenance_entity_links table
        print("Creating provenance_entity_links...")
        conn.execute("""
            CREATE TABLE provenance_entity_links (
                link_id INTEGER PRIMARY KEY,
                session_id VARCHAR NOT NULL,
                event_id VARCHAR,
                entity_table VARCHAR NOT NULL,
                entity_id VARCHAR NOT NULL,
                link_type VARCHAR NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                FOREIGN KEY (session_id) REFERENCES provenance_sessions(session_id)
            )
        """)

        # Create indexes
        print("Creating indexes...")
        conn.execute("CREATE INDEX idx_prov_sessions_agent ON provenance_sessions(agent_type, created_at)")
        conn.execute("CREATE INDEX idx_prov_events_session ON provenance_events(session_id, sequence_number)")
        conn.execute("CREATE INDEX idx_prov_tools_session ON provenance_tool_calls(session_id, call_time)")
        conn.execute("CREATE INDEX idx_prov_decisions_session ON provenance_decisions(session_id, timestamp)")
        conn.execute("CREATE INDEX idx_prov_transformations_session ON provenance_transformations(session_id, timestamp)")
        conn.execute("CREATE INDEX idx_prov_entity_links_entity ON provenance_entity_links(entity_table, entity_id)")

        conn.commit()
        print("\n✓ Migration completed successfully!")

        # Verify
        tables = conn.execute(
            """
            SELECT table_name FROM duckdb_tables()
            WHERE schema_name = 'main' AND table_name LIKE 'provenance_%'
            ORDER BY table_name
            """
        ).fetchall()
        print(f"\nCreated {len(tables)} provenance tables:")
        for (table,) in tables:
            # Get row count
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  - {table} ({count} rows)")

        print("\nProvenance tracking is now enabled!")
        print("Agents will automatically record sessions to both:")
        print("  1. DuckDB tables (for SQL analytics)")
        print("  2. .claude/provenance/ files (for cross-project compatibility)")

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/processed/microgrow.duckdb"
    migrate_schema(db_path)

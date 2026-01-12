## Add your own just recipes here. This is imported by the main justfile.

# Initialize provenance tracking tables in database
[group('database')]
init-provenance DB_PATH="data/processed/microgrow.duckdb":
    uv run python scripts/migrate_provenance_schema.py {{DB_PATH}}

# Query provenance data from database
[group('database')]
query-provenance QUERY:
    @echo "Querying provenance data..."
    uv run python -c "import duckdb; conn = duckdb.connect('data/processed/microgrow.duckdb'); print(conn.execute('{{QUERY}}').fetchdf())"

# Show recent agent sessions
[group('database')]
show-sessions LIMIT="10":
    @just query-provenance "SELECT session_id, agent_type, query, duration_ms, success FROM provenance_sessions ORDER BY created_at DESC LIMIT {{LIMIT}}"

# Show provenance statistics
[group('database')]
provenance-stats:
    @echo "\n=== Provenance Statistics ==="
    @just query-provenance "SELECT 'Total Sessions' as metric, COUNT(*) as count FROM provenance_sessions UNION ALL SELECT 'Total Events', COUNT(*) FROM provenance_events UNION ALL SELECT 'Total Tool Calls', COUNT(*) FROM provenance_tool_calls"

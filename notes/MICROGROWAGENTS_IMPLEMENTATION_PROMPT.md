# Claude Code Prompt: Hybrid Provenance System for MicroGrowAgents

## Context
This prompt enables you to implement a hybrid provenance tracking system in MicroGrowAgents that mirrors the PFASCommunityAgents implementation. The hybrid system combines:
- **Existing file-based tracking** (YAML manifests + JSONL action logs) - KEEP THIS
- **New database-based tracking** (DuckDB tables for SQL analytics) - ADD THIS

## Goals
1. Add DuckDB provenance tables to MicroGrowAgents database
2. Implement ProvenanceTracker with dual storage (database + files)
3. Integrate with BaseAgent for automatic tracking
4. Maintain full compatibility with PFASCommunityAgents provenance format
5. Keep existing .claude/provenance/ file structure unchanged

## Implementation Steps

### Step 1: Add Provenance Tables to Database Schema

**File:** `src/microgrowagents/database/schema.py`

Add these 6 tables from PFASCommunityAgents:

```sql
-- Copy from: /Users/marcin/Documents/VIMSS/ontology/PFAS/PFASCommunityAgents/src/pfascommunityagents/database/schema.py
-- Lines 548-675

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
);

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
);

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
);

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
);

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
);

CREATE TABLE provenance_entity_links (
    link_id INTEGER PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    event_id VARCHAR,
    entity_table VARCHAR NOT NULL,
    entity_id VARCHAR NOT NULL,
    link_type VARCHAR NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (session_id) REFERENCES provenance_sessions(session_id)
);

-- Indexes for performance
CREATE INDEX idx_prov_sessions_agent ON provenance_sessions(agent_type, created_at);
CREATE INDEX idx_prov_events_session ON provenance_events(session_id, sequence_number);
CREATE INDEX idx_prov_tools_session ON provenance_tool_calls(session_id, call_time);
CREATE INDEX idx_prov_decisions_session ON provenance_decisions(session_id, timestamp);
CREATE INDEX idx_prov_transformations_session ON provenance_transformations(session_id, timestamp);
CREATE INDEX idx_prov_entity_links_entity ON provenance_entity_links(entity_table, entity_id);
```

### Step 2: Create ProvenanceTracker Module

**File:** `src/microgrowagents/provenance/tracker.py` (NEW)

Copy the complete implementation from PFASCommunityAgents:
```bash
# Source file
/Users/marcin/Documents/VIMSS/ontology/PFAS/PFASCommunityAgents/src/pfascommunityagents/provenance/tracker.py
```

**Key Features:**
- Thread-safe session management with `threading.local()`
- Event batching (buffer of 50 events before DB insert)
- Dual storage: writes to both DuckDB tables AND .claude/provenance/ files
- `start_session()` - Creates both database session and file directory
- `end_session()` - Persists to database, writes YAML manifest, generates summary
- `record_event()` - Records to database AND writes to JSONL
- `record_tool_call()`, `record_decision()`, `record_transformation()` - Specialized tracking
- `_event_to_action()` - Converts database events to file-based actions

**Customizations for MicroGrowAgents:**
Update `_map_tool_name()` method to include MicroGrow-specific tools:
```python
def _map_tool_name(self, event_name: str, details: Dict) -> str:
    """Map event name to tool name for file-based action."""
    if "kegg" in event_name.lower():
        return "KEGGPathwayAPI"
    elif "biocyc" in event_name.lower():
        return "BioCycAPI"
    elif "ncbi" in event_name.lower():
        return "NCBIGenomeAPI"
    # ... add other MicroGrow-specific tools
    elif "media" in event_name.lower():
        return "MediaOptimizationAgent"
    elif "growth" in event_name.lower():
        return "GrowthPredictionAgent"
    # ... continue with PFASCommunityAgents mappings as fallback
```

### Step 3: Create ProvenanceQueries Utility

**File:** `src/microgrowagents/provenance/queries.py` (NEW)

Copy from PFASCommunityAgents:
```bash
# Source file
/Users/marcin/Documents/VIMSS/ontology/PFAS/PFASCommunityAgents/src/pfascommunityagents/provenance/queries.py
```

No modifications needed - SQL queries work the same way.

### Step 4: Update BaseAgent Integration

**File:** `src/microgrowagents/agents/base_agent.py`

Copy the provenance integration pattern from PFASCommunityAgents:
```bash
# Reference file
/Users/marcin/Documents/VIMSS/ontology/PFAS/PFASCommunityAgents/src/pfascommunityagents/agents/base_agent.py
```

**Changes:**
1. Add `enable_provenance: bool = True` parameter to `__init__()`
2. Initialize tracker: `self._tracker = get_tracker()`
3. Add `execute()` method that calls `_run_with_provenance()`
4. Keep existing `run()` as abstract method
5. Update `log()` to call `tracker.record_event()`

**Example Integration:**
```python
class BaseAgent:
    def __init__(self, enable_provenance: bool = True):
        self.enable_provenance = enable_provenance
        self._tracker = None
        if enable_provenance:
            try:
                from microgrowagents.provenance.tracker import get_tracker
                self._tracker = get_tracker()
            except Exception as e:
                print(f"Warning: Provenance tracking disabled: {e}")
                self.enable_provenance = False

    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """Public entry point with provenance tracking."""
        return self._run_with_provenance(query, **kwargs)

    def _run_with_provenance(self, query: str, **kwargs) -> Dict[str, Any]:
        """Wrapper for run() with automatic provenance tracking."""
        if not self.enable_provenance or not self._tracker:
            return self.run(query, **kwargs)

        parent_session_id = kwargs.pop("_parent_session_id", None)
        session_id = self._tracker.start_session(
            agent_type=self.__class__.__name__,
            query=query,
            kwargs=kwargs,
            parent_session_id=parent_session_id,
        )

        try:
            result = self.run(query, **kwargs)
            self._tracker.end_session(success=True, result=result)
            return result
        except Exception as e:
            self._tracker.end_session(success=False, error=str(e))
            raise

    @abstractmethod
    def run(self, query: str, **kwargs) -> Dict[str, Any]:
        """Implement agent logic here."""
        pass

    def log(self, message: str, level: str = "INFO"):
        """Log message with provenance tracking."""
        print(f"[{self.__class__.__name__}] [{level}] {message}")
        if self.enable_provenance and self._tracker:
            self._tracker.record_event(
                "log", f"log_{level.lower()}", {"message": message, "level": level}
            )
```

### Step 5: Create Migration Script

**File:** `scripts/migrate_provenance_schema.py` (NEW)

```python
#!/usr/bin/env python
"""
Migrate existing MicroGrowAgents database to add provenance tables.
"""

import sys
from pathlib import Path
import duckdb

def migrate_schema(db_path: str):
    """Add provenance tracking tables to existing database."""
    print(f"Migrating database: {db_path}")

    conn = duckdb.connect(db_path)

    try:
        # Check if tables already exist
        existing = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'provenance_%'"
        ).fetchall()

        if existing:
            print(f"Found {len(existing)} existing provenance tables")
            response = input("Do you want to recreate them? (yes/no): ")
            if response.lower() != "yes":
                print("Migration cancelled")
                return

            # Drop existing tables
            for (table_name,) in existing:
                print(f"Dropping table: {table_name}")
                conn.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")

        # Create tables (paste SQL from Step 1 here)
        print("Creating provenance_sessions...")
        conn.execute("""CREATE TABLE provenance_sessions (...) """)

        print("Creating provenance_events...")
        conn.execute("""CREATE TABLE provenance_events (...) """)

        # ... create remaining tables

        # Create indexes
        print("Creating indexes...")
        conn.execute("CREATE INDEX idx_prov_sessions_agent ON provenance_sessions(agent_type, created_at)")
        # ... create remaining indexes

        conn.commit()
        print("✓ Migration completed successfully!")

        # Verify
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'provenance_%' ORDER BY name"
        ).fetchall()
        print(f"\\nCreated {len(tables)} provenance tables:")
        for (table,) in tables:
            print(f"  - {table}")

    finally:
        conn.close()

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/processed/microgrow.duckdb"
    migrate_schema(db_path)
```

### Step 6: Update Justfile

**File:** `Justfile`

Add command:
```makefile
# Initialize provenance tracking tables
init-provenance:
    uv run python scripts/migrate_provenance_schema.py data/processed/microgrow.duckdb
```

### Step 7: Create __init__.py

**File:** `src/microgrowagents/provenance/__init__.py` (NEW)

```python
"""
Provenance tracking system for MicroGrowAgents.

Hybrid system combining database-based tracking (DuckDB) with
file-based tracking (.claude/provenance/) for cross-project compatibility.
"""

from microgrowagents.provenance.queries import ProvenanceQueries
from microgrowagents.provenance.tracker import ProvenanceTracker, get_tracker

__all__ = ["ProvenanceTracker", "get_tracker", "ProvenanceQueries"]
```

## Verification Steps

After implementation, verify the hybrid system works:

### 1. Database Migration
```bash
just init-provenance
```

Expected output:
- Creates 6 tables: provenance_sessions, provenance_events, etc.
- Creates 6 indexes

### 2. Agent Execution Test
```python
from microgrowagents.agents import YourAgent

agent = YourAgent(enable_provenance=True)
result = agent.execute("test query")

# Verify dual storage:
# 1. Check database: SELECT * FROM provenance_sessions ORDER BY created_at DESC LIMIT 1;
# 2. Check files: ls .claude/provenance/sessions/
```

### 3. File-Based Queries (MicroGrowAgents Standard)
```bash
# Count actions by type
cat .claude/provenance/sessions/*/actions.jsonl | jq -r '.type' | sort | uniq -c

# View recent sessions
ls -lt .claude/provenance/sessions/ | head -10

# Check manifest
yq eval . .claude/provenance/sessions/LATEST/manifest.yaml
```

### 4. Database Queries (SQL Analytics)
```sql
-- Recent agent executions
SELECT session_id, agent_type, query, duration_ms, success
FROM provenance_sessions
ORDER BY created_at DESC
LIMIT 10;

-- Tool call statistics
SELECT tool_type, tool_name, COUNT(*) as calls,
       AVG(duration_ms) as avg_duration,
       SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits
FROM provenance_tool_calls
GROUP BY tool_type, tool_name
ORDER BY calls DESC;

-- Decision patterns
SELECT agent_type, decision_type, branch_taken, COUNT(*) as count
FROM provenance_decisions pd
JOIN provenance_sessions ps ON pd.session_id = ps.session_id
GROUP BY agent_type, decision_type, branch_taken
ORDER BY count DESC;
```

### 5. Cross-Project Compatibility Test
```bash
# Copy a PFASCommunityAgents session to MicroGrowAgents
cp -r /Users/marcin/Documents/VIMSS/ontology/PFAS/PFASCommunityAgents/.claude/provenance/sessions/2026-01-11-06-47 \
      .claude/provenance/sessions/

# Verify it works with MicroGrowAgents queries
cat .claude/provenance/sessions/2026-01-11-06-47/actions.jsonl | jq -r '.type' | sort | uniq -c

# Should output:
#    2 execute
#    2 read
```

## Key Differences from PFASCommunityAgents

1. **Tool Mappings:** Update `_map_tool_name()` in tracker.py to include MicroGrow-specific tools (KEGG, BioCyc, NCBI, etc.)

2. **Entity Tables:** MicroGrow uses different domain tables:
   - `genome_annotations` instead of `pfas_compounds`
   - `pathway_models` instead of `media_formulations`
   - Update entity_links sections in manifests accordingly

3. **Database Path:** Use `data/processed/microgrow.duckdb` instead of `pfascommunity.duckdb`

4. **Agent Names:** Different agent class names (GrowthPredictionAgent vs ChemistryAgent)

## Benefits of Hybrid System

### For MicroGrowAgents
- **Powerful SQL Analytics:** Query provenance data with complex joins and aggregations
- **Long-term Storage:** DuckDB efficiently stores historical execution data
- **Entity Linking:** Connect provenance to genome annotations, pathways, etc.
- **Performance Metrics:** Track agent execution times, cache hit rates, decision patterns
- **Cross-Project Compatibility:** Share provenance with PFASCommunityAgents

### Maintains Existing Workflow
- **Same .claude/provenance/ structure:** No changes to existing file-based workflow
- **Same jq queries:** All existing analysis scripts continue to work
- **Same git tracking:** YAML manifests and summaries still tracked in git
- **Backward compatible:** Existing sessions remain readable

## Implementation Checklist

- [ ] Add 6 provenance tables to database schema
- [ ] Create `src/microgrowagents/provenance/tracker.py`
- [ ] Create `src/microgrowagents/provenance/queries.py`
- [ ] Create `src/microgrowagents/provenance/__init__.py`
- [ ] Update `src/microgrowagents/agents/base_agent.py` with provenance integration
- [ ] Create `scripts/migrate_provenance_schema.py`
- [ ] Update `Justfile` with `init-provenance` command
- [ ] Customize `_map_tool_name()` for MicroGrow-specific tools
- [ ] Run migration script: `just init-provenance`
- [ ] Test agent execution creates both database and file records
- [ ] Verify jq queries work on actions.jsonl
- [ ] Verify SQL queries work on DuckDB tables
- [ ] Test cross-project compatibility with PFASCommunityAgents session

## Reference Implementation

Complete working implementation available at:
```
/Users/marcin/Documents/VIMSS/ontology/PFAS/PFASCommunityAgents/
```

Key files to reference:
- `src/pfascommunityagents/provenance/tracker.py` - Complete tracker implementation
- `src/pfascommunityagents/provenance/file_writer.py` - File-based writer
- `src/pfascommunityagents/provenance/queries.py` - SQL query utilities
- `src/pfascommunityagents/database/schema.py` - Provenance table definitions
- `src/pfascommunityagents/agents/base_agent.py` - Agent integration pattern
- `.claude/provenance/sessions/2026-01-11-06-47/` - Example session with all files

## Support

If you encounter issues during implementation:
1. Check that all 6 tables were created successfully
2. Verify event_id uses UUID (not sequential numbers)
3. Ensure Path objects are excluded from JSON serialization
4. Check that event buffer is cleared in finally block
5. Verify file_session_dir is created before writing actions

---

**Version:** 1.0.0
**Date:** 2026-01-11
**Author:** PFASCommunityAgents Hybrid Provenance System

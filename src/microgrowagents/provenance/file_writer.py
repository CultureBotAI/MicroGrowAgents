"""
File-based provenance writer for MicroGrowAgents compatibility.

Writes provenance data in YAML/JSONL format to .claude/provenance/ directory.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class FileBasedProvenanceWriter:
    """Writes provenance in MicroGrowAgents-compatible format."""

    def __init__(self, claude_dir: Path = Path(".claude/provenance")):
        """
        Initialize file-based provenance writer.

        Args:
            claude_dir: Base directory for provenance files
        """
        self.claude_dir = Path(claude_dir)
        self.sessions_dir = self.claude_dir / "sessions"

        # Ensure directories exist
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        (self.claude_dir / "indices").mkdir(parents=True, exist_ok=True)

    def create_session_dir(self, timestamp: datetime) -> Path:
        """
        Create YYYY-MM-DD-HH-mm session directory.

        Args:
            timestamp: Session start timestamp

        Returns:
            Path to created session directory
        """
        session_name = timestamp.strftime("%Y-%m-%d-%H-%M")
        session_dir = self.sessions_dir / session_name
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def write_manifest_yaml(self, session_dir: Path, session_data: Dict):
        """
        Write manifest.yaml in MicroGrowAgents format.

        Args:
            session_dir: Session directory path
            session_data: Session metadata from ProvenanceTracker
        """
        manifest_path = session_dir / "manifest.yaml"

        # Convert session data to YAML manifest format
        start_time = datetime.fromisoformat(session_data["start_time"])
        end_time = (
            datetime.fromisoformat(session_data["end_time"])
            if session_data.get("end_time")
            else None
        )
        duration_minutes = (
            session_data.get("duration_ms", 0) / 60000 if session_data.get("duration_ms") else None
        )

        manifest = {
            "session": {
                "id": f"agent-session-{session_dir.name}",
                "database_session_id": session_data["session_id"],
                "date_started": start_time.isoformat() + "Z",
                "date_ended": end_time.isoformat() + "Z" if end_time else None,
                "duration_minutes": round(duration_minutes, 2) if duration_minutes else None,
                "model": "claude-sonnet-4-5",
                "user": "marcin",
                "session_type": "agent_execution",
                "agent_type": session_data.get("agent_type"),
            },
            "user_context": {
                "working_directory": str(Path.cwd()),
                "git_branch": session_data.get("git_branch"),
                "git_commit_before": session_data.get("git_commit"),
                "git_commit_after": None,
                "python_version": session_data.get("python_version"),
                "project_status": "MicroGrowAgents development",
            },
            "agent_context": {
                "query": session_data.get("query"),
                "kwargs": session_data.get("kwargs", {}),
                "parent_session_id": session_data.get("parent_session_id"),
                "depth": session_data.get("depth", 0),
            },
            "goals": [session_data.get("query", "Agent execution")],
            "results": {
                "success": session_data.get("success"),
                "actions_performed": session_data.get("action_count", 0),
                "files_analyzed": 0,
                "files_created": 0,
                "files_modified": 0,
                "api_calls_made": 0,
                "cache_hits": 0,
                "notes": "",
            },
            "action_summary": {
                "reads": {"total": 0, "files": []},
                "searches": {"total": 0, "patterns": []},
                "modifications": {"total": 0, "files": []},
                "executions": {"total": 0, "commands": []},
                "queries": {"total": 0, "apis": []},
                "decisions": {"total": 0, "key_decisions": []},
                "transformations": {"total": 0, "transformation_types": []},
            },
            "tool_usage": {
                "pubchem": {"calls": 0, "cache_hits": 0, "operations": []},
                "pubmed": {"calls": 0, "cache_hits": 0, "operations": []},
                "duckdb": {"calls": 0, "queries": []},
                "sub_agents": {"calls": 0, "agent_types": []},
            },
            "key_findings": [],
            "recommendations": [],
            "errors": [session_data.get("error_message")] if session_data.get("error_message") else [],
            "warnings": [],
            "entity_links": {
                "genome_annotations": [],
                "pathway_models": [],
                "media_formulations": [],
                "ingredients": [],
            },
            "metadata": {
                "created_by": "MicroGrowAgents Provenance System v1.0",
                "schema_version": "1.0.0",
                "hybrid_storage": True,
                "database_path": "data/processed/microgrow.duckdb",
                "file_session_dir": str(session_dir),
            },
        }

        # Write YAML file
        with open(manifest_path, "w") as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def append_action_jsonl(self, session_dir: Path, action: Dict):
        """
        Append action to actions.jsonl.

        Args:
            session_dir: Session directory path
            action: Action data in JSONL format
        """
        actions_path = session_dir / "actions.jsonl"

        # Append to JSONL file (one JSON object per line)
        with open(actions_path, "a") as f:
            f.write(json.dumps(action, ensure_ascii=False) + "\n")

    def update_manifest_stats(self, session_dir: Path, actions: List[Dict]):
        """
        Update manifest.yaml with statistics from actions.

        Args:
            session_dir: Session directory path
            actions: List of action dictionaries
        """
        manifest_path = session_dir / "manifest.yaml"

        if not manifest_path.exists():
            return

        # Load existing manifest
        with open(manifest_path, "r") as f:
            manifest = yaml.safe_load(f)

        # Calculate statistics
        action_counts = {
            "read": 0,
            "search": 0,
            "modify": 0,
            "execute": 0,
            "query": 0,
            "decision": 0,
            "analyze": 0,
            "create": 0,
        }

        files_affected = set()
        apis_used = set()
        queries = []
        decisions = []
        transformations = []

        for action in actions:
            action_type = action.get("type", "")
            action_counts[action_type] = action_counts.get(action_type, 0) + 1

            # Collect files
            if action.get("files_affected"):
                files_affected.update(action["files_affected"])

            # Track queries
            if action_type == "query":
                apis_used.add(action.get("tool", ""))
                if action.get("details", {}).get("query"):
                    queries.append(action["details"]["query"])

            # Track decisions
            if action_type == "decision":
                if action.get("details", {}).get("decision_type"):
                    decisions.append(action["details"]["decision_type"])

            # Track transformations
            if action_type == "analyze":
                if action.get("details", {}).get("transformation_type"):
                    transformations.append(action["details"]["transformation_type"])

        # Update manifest
        manifest["results"]["actions_performed"] = len(actions)
        manifest["results"]["api_calls_made"] = action_counts.get("query", 0)
        manifest["results"]["cache_hits"] = sum(
            1 for a in actions if a.get("details", {}).get("cache_hit")
        )

        manifest["action_summary"]["reads"]["total"] = action_counts.get("read", 0)
        manifest["action_summary"]["searches"]["total"] = action_counts.get("search", 0)
        manifest["action_summary"]["modifications"]["total"] = action_counts.get("modify", 0)
        manifest["action_summary"]["executions"]["total"] = action_counts.get("execute", 0)
        manifest["action_summary"]["queries"]["total"] = action_counts.get("query", 0)
        manifest["action_summary"]["queries"]["apis"] = list(apis_used)
        manifest["action_summary"]["decisions"]["total"] = action_counts.get("decision", 0)
        manifest["action_summary"]["decisions"]["key_decisions"] = decisions[:5]
        manifest["action_summary"]["transformations"]["total"] = action_counts.get("analyze", 0)
        manifest["action_summary"]["transformations"]["transformation_types"] = list(
            set(transformations)
        )

        # Count PubChem/PubMed/DuckDB calls
        pubchem_actions = [a for a in actions if a.get("tool") == "PubChemAPI"]
        pubmed_actions = [a for a in actions if a.get("tool") == "PubMedAPI"]
        duckdb_actions = [a for a in actions if a.get("tool") == "DuckDB"]

        manifest["tool_usage"]["pubchem"]["calls"] = len(pubchem_actions)
        manifest["tool_usage"]["pubchem"]["cache_hits"] = sum(
            1 for a in pubchem_actions if a.get("details", {}).get("cache_hit")
        )
        manifest["tool_usage"]["pubmed"]["calls"] = len(pubmed_actions)
        manifest["tool_usage"]["duckdb"]["calls"] = len(duckdb_actions)

        # Write updated manifest
        with open(manifest_path, "w") as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def write_summary_md(self, session_dir: Path, session_data: Dict, actions: List[Dict]):
        """
        Generate summary.md markdown file.

        Args:
            session_dir: Session directory path
            session_data: Session metadata
            actions: List of action dictionaries
        """
        summary_path = session_dir / "summary.md"

        # Calculate statistics
        total_actions = len(actions)
        successful = sum(1 for a in actions if a.get("status") == "success")
        failed = sum(1 for a in actions if a.get("status") == "failure")
        api_calls = sum(1 for a in actions if a.get("type") == "query")
        decisions = sum(1 for a in actions if a.get("type") == "decision")
        analyses = sum(1 for a in actions if a.get("type") == "analyze")

        duration_str = "N/A"
        if session_data.get("duration_ms"):
            duration_str = f"{session_data['duration_ms']}ms ({session_data['duration_ms']/1000:.2f}s)"

        status_icon = "✓" if session_data.get("success") else "✗"

        # Generate markdown
        summary = f"""# Agent Execution Summary

**Session:** {session_dir.name}
**Agent:** {session_data.get('agent_type', 'Unknown')}
**Duration:** {duration_str}
**Status:** {status_icon} {'Success' if session_data.get('success') else 'Failed'}

## Query
```
{session_data.get('query', 'N/A')}
```

## Results
- Total actions: {total_actions}
- Successful: {successful}
- Failed: {failed}
- API calls: {api_calls}
- Decisions: {decisions}
- Analyses: {analyses}

## Actions Performed

### By Type
"""

        # Count by type
        type_counts = {}
        for action in actions:
            action_type = action.get("type", "unknown")
            type_counts[action_type] = type_counts.get(action_type, 0) + 1

        for action_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            summary += f"- **{action_type}**: {count}\n"

        # List unique tools used
        tools_used = set(a.get("tool", "Unknown") for a in actions)
        summary += f"\n### Tools Used\n"
        for tool in sorted(tools_used):
            tool_actions = [a for a in actions if a.get("tool") == tool]
            summary += f"- **{tool}**: {len(tool_actions)} calls\n"

        # API call details
        if api_calls > 0:
            summary += f"\n## API Call Summary\n"
            cache_hits = sum(1 for a in actions if a.get("details", {}).get("cache_hit"))
            cache_misses = api_calls - cache_hits
            cache_rate = (cache_hits / api_calls * 100) if api_calls > 0 else 0

            summary += f"- Total API calls: {api_calls}\n"
            summary += f"- Cache hits: {cache_hits}\n"
            summary += f"- Cache misses: {cache_misses}\n"
            summary += f"- Cache hit rate: {cache_rate:.1f}%\n"

        # Error summary
        errors = [a for a in actions if a.get("status") == "failure"]
        if errors:
            summary += f"\n## Errors\n"
            for error_action in errors[:5]:  # Show first 5 errors
                summary += f"- **{error_action.get('tool', 'Unknown')}**: {error_action.get('error', {}).get('message', 'Unknown error')}\n"

        # Example queries
        summary += f"""

## Example Queries

### View all actions
```bash
cat .claude/provenance/sessions/{session_dir.name}/actions.jsonl | jq
```

### Count actions by type
```bash
cat .claude/provenance/sessions/{session_dir.name}/actions.jsonl | jq -r '.type' | sort | uniq -c
```

### Filter successful queries
```bash
cat .claude/provenance/sessions/{session_dir.name}/actions.jsonl | jq 'select(.type == "query" and .status == "success")'
```

### Show cache hits
```bash
cat .claude/provenance/sessions/{session_dir.name}/actions.jsonl | jq 'select(.details.cache_hit == true)'
```

## Database Query

To view full trace in DuckDB:
```sql
SELECT * FROM provenance_sessions WHERE session_id = '{session_data.get('session_id', '')}';
```

---
*Generated by MicroGrowAgents Provenance System v1.0*
"""

        # Write summary
        with open(summary_path, "w") as f:
            f.write(summary)

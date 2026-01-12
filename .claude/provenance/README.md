# Claude Code Provenance Tracking

## Overview
Detailed tracking system for all Claude Code actions, decisions, and tool usage during user interactions with the MicroGrowAgents repository.

## Directory Structure
- `sessions/YYYY-MM-DD-HH-mm/` - Per-session provenance records
- `indices/` - Aggregated indices for querying
- `manifest-template.yaml` - Template for new sessions
- `action-types.yaml` - Action type definitions
- `metadata-schema.json` - JSON Schema for validation

## Session Structure
Each session directory contains:
- `manifest.yaml` - Session metadata and summary
- `actions.jsonl` - Action-by-action log (JSONL format)
- `summary.md` - Human-readable summary

## Action Types
- **read** - File reads, schema inspections
- **search** - Grep, glob, find operations
- **analyze** - Code analysis, pattern detection
- **modify** - File edits, updates
- **create** - New file creation
- **execute** - Bash commands, scripts
- **query** - Database queries, API calls
- **decision** - Decision points and rationale

## Usage

### Creating a New Session
```bash
# Manual creation
SESSION_DIR=".claude/provenance/sessions/$(date +%Y-%m-%d-%H-%M)"
mkdir -p "$SESSION_DIR"
cp .claude/provenance/manifest-template.yaml "$SESSION_DIR/manifest.yaml"
touch "$SESSION_DIR/actions.jsonl"
```

### Querying Actions
```bash
# Find all file modifications
jq 'select(.type == "modify")' .claude/provenance/sessions/*/actions.jsonl

# Count actions by type
cat .claude/provenance/sessions/*/actions.jsonl | jq -r '.type' | sort | uniq -c

# Calculate success rate by tool
cat .claude/provenance/sessions/*/actions.jsonl | \
  jq -s 'group_by(.tool) | map({tool: .[0].tool, total: length, success: map(select(.status == "success")) | length}) | .[] | {tool, success_rate: (.success / .total)}'

# Find longest running actions
cat .claude/provenance/sessions/*/actions.jsonl | \
  jq 'select(.duration_ms > 1000) | {tool, duration_ms, details}' | \
  jq -s 'sort_by(.duration_ms) | reverse | .[:10]'

# Files accessed most frequently
cat .claude/provenance/sessions/*/actions.jsonl | \
  jq -r '.files_affected[]?' | sort | uniq -c | sort -rn | head -20
```

### Analyzing Sessions
```bash
# List all sessions with summaries
ls -1 .claude/provenance/sessions/

# View session manifest
yq eval . .claude/provenance/sessions/2026-01-10-14-30/manifest.yaml

# Count total actions across all sessions
cat .claude/provenance/sessions/*/actions.jsonl | wc -l

# Generate session timeline
for session in .claude/provenance/sessions/*/manifest.yaml; do
  echo "$(yq eval '.session.date_started' "$session"): $(yq eval '.session.session_type' "$session") - $(yq eval '.goals | join(", ")' "$session")"
done | sort
```

## Schema
See `metadata-schema.json` for complete action metadata schema.

## Integration

### Git Integration
Session manifests and summaries are tracked in git.
Action logs (JSONL) are gitignored due to size.

### Documentation Integration
Session summaries follow the same pattern as `notes/SESSION_SUMMARY_*.md`.

## Examples

### Example Session Manifest
```yaml
session:
  id: "claude-session-2026-01-10-14-30-00"
  date_started: "2026-01-10T14:30:00Z"
  date_ended: "2026-01-10T16:15:00Z"
  duration_minutes: 105
  model: "claude-sonnet-4-5"
  session_type: "development"

goals:
  - "Implement provenance tracking system"
  - "Create directory structure and templates"

results:
  success: true
  actions_performed: 47
  files_created: 4
  files_modified: 1
```

### Example Action Log Entry
```jsonl
{"timestamp": "2026-01-10T14:30:15.123Z", "action_id": 1, "type": "read", "tool": "Read", "status": "success", "duration_ms": 245, "details": {"file_path": "/path/to/schema.yaml", "bytes_read": 45230, "line_count": 892}, "files_affected": ["/path/to/schema.yaml"], "read_only": true}
```

## Maintenance

### Regenerating Indices
```bash
# Update all indices from session data
python scripts/provenance/update_indices.py
```

### Cleaning Old Sessions
```bash
# Archive sessions older than 90 days
find .claude/provenance/sessions -type d -mtime +90 -exec tar czf {}.tar.gz {} \; -exec rm -rf {} \;
```

## Version
Provenance tracking system v1.0.0

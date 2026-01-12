# CLAUDE.md for MicroGrowAgents

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agent-based system for microbial growth predictions

The project uses `uv` for dependency management and `just` as the command runner.

## IMPORTANT INSTRUCTIONS

- we use test driven development, write tests first before implementing a feature
- do not try and 'cheat' by making mock tests (unless asked)
- if functionality does not work, keep trying, do not relax the test just to get poor code in
- always run tests
- use docstrings

We make heavy use of doctests, these serve as both docs and tests. `just test` will include these,
or do `just doctest` just to write doctests

In general AVOID try/except blocks, except when these are truly called for, for example
when interfacing with external systems. For wrapping deterministic code,  these are ALMOST
NEVER required, if you think you need them, it's likely a bad smell that your logic is wrong.

## Essential Commands


### Testing and Quality
- `just test` - Run all tests, type checking, and formatting checks
- `just pytest` - Run Python tests only
- `just mypy` - Run type checking
- `just format` - Run ruff linting/formatting checks
- `uv run pytest tests/test_simple.py::test_simple` - Run a specific test

### Running the CLI
- `uv run MicroGrowAgents --help` - Run the CLI tool with options

### Documentation
- `just _serve` - Run local documentation server with mkdocs

## Project Architecture

### Core Structure
- **src/my_awesome_tool/** - Main package containing the CLI and application logic
  - `cli.py` - Typer-based CLI interface, entry point for the application
- **tests/** - Test suite using pytest with parametrized tests
- **docs/** - MkDocs-managed documentation with Material theme

### Technology Stack
- **Python 3.10+** with `uv` for dependency management
- **LinkML** for data modeling (linkml-runtime)
- **Typer** for CLI interface
- **pytest** for testing
- **mypy** for type checking
- **ruff** for linting and formatting
- **MkDocs Material** for documentation

### Key Configuration Files
- `pyproject.toml` - Python project configuration, dependencies, and tool settings
- `justfile` - Command runner recipes for common development tasks
- `mkdocs.yml` - Documentation configuration
- `uv.lock` - Locked dependency versions

## Development Workflow

1. Dependencies are managed via `uv` - use `uv add` for new dependencies
2. All commands are run through `just` or `uv run`
3. The project uses dynamic versioning from git tags
4. Documentation is auto-deployed to GitHub Pages at https://monarch-initiative.github.io/my-awesome-tool

## Project-Specific Files & Locations

### Quick Start: Understanding Project State

**READ THIS FIRST:** `docs/STATUS.md`
- Current project status and metrics
- Citation coverage: 90.5% (143/158 DOIs)
- Recent DOI corrections (7 applied)
- Remaining issues and next actions
- Index to all key files

### Key Data Files

**Main Dataset:** `data/raw/mp_medium_ingredient_properties.csv`
- 158 ingredients with 68 columns (47 data + 21 organism context)
- 158 unique DOI citations tracked
- LinkML schema: `src/microgrowagents/schema/mp_medium_schema.yaml`

### DOI Corrections

**Complete Report:** `notes/DOI_CORRECTIONS_FINAL_UPDATED.md`
- Comprehensive documentation of all DOI correction work
- 7 corrections applied (14 CSV instances)
- Coverage improvement: 86.1% → 90.5%
- Remaining invalid DOIs and next steps

**Correction Definitions:** `data/corrections/`
- `doi_corrections_17_invalid.yaml` - Primary correction mappings
- `additional_corrections_found.yaml` - Extended research findings
- `doi_corrections.yaml` - Historical corrections

**Correction Results:** `data/results/`
- `doi_corrections_applied.json` - Batch 1 log (4 DOIs)
- `additional_corrections_applied.json` - Batch 2 log (3 DOIs)
- `doi_validation_22.json` - Validation results

### Scripts (Organized by Function)

All scripts located in `scripts/` with subdirectories:

**DOI Validation:** `scripts/doi_validation/`
- `validate_failed_dois.py` - Check DOI HTTP resolution
- `validate_new_corrections.py` - Validate correction candidates
- `find_correct_dois.py` - Research correct alternatives

**DOI Corrections:** `scripts/doi_corrections/`
- `apply_doi_corrections.py` - Apply validated corrections
- `apply_additional_corrections.py` - Batch corrections
- `clean_invalid_dois.py` - Remove invalid DOIs

**PDF Downloads:** `scripts/pdf_downloads/`
- `download_all_pdfs_automated.py` - Automated PDF retrieval
- `retry_failed_dois_with_fallbackpdf.py` - Fallback service

**Schema Management:** `scripts/schema/`
- `add_role_columns.py` - Add organism context columns
- `migrate_schema.py` - Schema migrations

**Enrichment:** `scripts/enrichment/`
- `enrich_ingredient_effects.py` - Enrich ingredient data

### Running Scripts

```bash
# Validate DOIs
uv run python scripts/doi_validation/validate_failed_dois.py

# Apply corrections
uv run python scripts/doi_corrections/apply_doi_corrections.py

# Download PDFs
uv run python scripts/pdf_downloads/download_all_pdfs_automated.py
```

### Documentation

**Research Notes:** `notes/`
- 27+ documentation files covering:
  - DOI corrections and validation
  - Citation coverage analysis
  - Schema updates
  - Implementation notes
- See `notes/README.md` for guide

**Results & Logs:** `data/results/`
- Validation results (JSON)
- Download logs (TXT)
- Processing outputs
- See `data/results/README.md` for guide

### Current Project Metrics

- **Total DOIs:** 158 unique
- **Citation Coverage:** 90.5% (143/158 with evidence)
  - PDFs: 92 (58.2%)
  - Abstracts: 44 (27.8%)
  - Missing: 15 (9.5%)
- **DOI Corrections Applied:** 7 corrections → 14 CSV cells updated
- **Schema Columns:** 68 total (47 data + 21 organism context)
- **Missing Citations:** 77 empty DOI cells across 18 ingredients

### File Organization

```
MicroGrowAgents/
├── docs/STATUS.md           # ⭐ START HERE - Current state
├── notes/                   # Research & documentation
├── data/
│   ├── raw/                 # Main CSV and source data
│   ├── corrections/         # DOI correction definitions (YAML/JSON)
│   └── results/             # Validation & processing logs
└── scripts/                 # Organized by function
    ├── doi_validation/
    ├── doi_corrections/
    ├── pdf_downloads/
    ├── enrichment/
    └── schema/
```

Each directory has a README.md explaining its contents and usage.

## Provenance Tracking

Claude Code actions are tracked in `.claude/provenance/` for audit trails and analysis:

### Session Records
- **Session manifests:** `.claude/provenance/sessions/YYYY-MM-DD-HH-mm/manifest.yaml`
  - Session metadata, goals, results, and summaries
  - Tracked in git for documentation purposes

- **Action logs:** `.claude/provenance/sessions/YYYY-MM-DD-HH-mm/actions.jsonl`
  - Detailed action-by-action logs in JSONL format (one action per line)
  - Gitignored due to size, but queryable with standard tools

- **Human summaries:** `.claude/provenance/sessions/YYYY-MM-DD-HH-mm/summary.md`
  - Human-readable session summaries following `notes/SESSION_SUMMARY_*.md` pattern
  - Tracked in git for documentation

### Usage

**Query action logs:**
```bash
# Count actions by type
cat .claude/provenance/sessions/*/actions.jsonl | jq -r '.type' | sort | uniq -c

# Find all file modifications
jq 'select(.type == "modify")' .claude/provenance/sessions/*/actions.jsonl

# Most frequently accessed files
cat .claude/provenance/sessions/*/actions.jsonl | jq -r '.files_affected[]?' | sort | uniq -c | sort -rn
```

**View session summaries:**
```bash
# List all sessions
ls -1 .claude/provenance/sessions/

# View session manifest
yq eval . .claude/provenance/sessions/2026-01-10-21-16/manifest.yaml

# Read human summary
cat .claude/provenance/sessions/2026-01-10-21-16/summary.md
```

See `.claude/provenance/README.md` for complete documentation, templates, and query examples.

### Important: When Working on DOI Corrections

1. Read `docs/STATUS.md` for current state
2. Check `notes/DOI_CORRECTIONS_FINAL_UPDATED.md` for complete history
3. Review correction definitions in `data/corrections/`
4. Run validation scripts from `scripts/doi_validation/`
5. Apply corrections using `scripts/doi_corrections/`
6. Check results in `data/results/`

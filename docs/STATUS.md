# MicroGrowAgents Project Status

**Last Updated:** 2026-01-07

## Quick Summary

This project manages the **MP Medium Ingredient Properties dataset** with comprehensive citation tracking and validation.

### Current Metrics

- **Total Ingredients:** 158 rows
- **Total Columns:** 68 (47 data + 21 organism context columns)
- **DOI Citations:** 158 unique DOIs
- **Citation Coverage:** **90.5%** (143/158 DOIs with evidence)
  - PDFs: 92 (58.2%)
  - Abstracts: 44 (27.8%)
  - Missing: 15 (9.5%)

### Recent Work: DOI Corrections (2026-01-07)

✅ **7 invalid DOIs successfully corrected** (14 instances in CSV)
- Improved coverage from 86.1% → **90.5%** (+4.4%)
- See: `notes/DOI_CORRECTIONS_FINAL_UPDATED.md` for complete details

## Key Files

### Main Data
- **CSV:** `data/raw/mp_medium_ingredient_properties.csv` (68 columns)
- **Schema:** `src/microgrowagents/schema/mp_medium_schema.yaml` (LinkML)

### DOI Corrections & Validation
- **Final Report:** `notes/DOI_CORRECTIONS_FINAL_UPDATED.md` ⭐ **MOST IMPORTANT**
- **Corrections Applied:**
  - Batch 1: `data/results/doi_corrections_applied.json` (4 DOIs → 10 cells)
  - Batch 2: `data/results/additional_corrections_applied.json` (3 DOIs → 4 cells)
- **Correction Definitions:**
  - `data/corrections/doi_corrections_17_invalid.yaml`
  - `data/corrections/additional_corrections_found.yaml`
- **Validation Results:**
  - `data/results/doi_validation_22.json` (validation of 22 invalid DOIs)
  - `data/results/csv_all_dois_results.json` (all CSV DOIs)

### Citation Resources
- **All DOIs:** `data/results/all_doi_links.txt` (158 unique DOIs)
- **Missing Citations:** `data/results/missing_citations_report.txt` (77 missing)
- **Coverage Summary:** `notes/CITATION_COVERAGE_SUMMARY.md`

### Scripts

Located in `scripts/` organized by function:

**DOI Validation:** `scripts/doi_validation/`
- `validate_failed_dois.py` - Validate DOI HTTP resolution
- `validate_new_corrections.py` - Validate correction candidates
- `find_correct_dois.py` - Research correct DOI alternatives

**DOI Corrections:** `scripts/doi_corrections/`
- `apply_doi_corrections.py` - Apply validated corrections
- `apply_additional_corrections.py` - Batch corrections
- `clean_invalid_dois.py` - Remove invalid DOIs

**PDF Downloads:** `scripts/pdf_downloads/`
- `download_all_pdfs_automated.py` - Automated PDF retrieval
- `retry_failed_dois_with_fallbackpdf.py` - Fallback PDF service

**Schema:** `scripts/schema/`
- `add_role_columns.py` - Add organism/role columns
- `migrate_schema.py` - Schema migration utility

**Enrichment:** `scripts/enrichment/`
- `enrich_ingredient_effects.py` - Enrich ingredient data

## Remaining Issues

### 1. Invalid DOIs Still Unresolved (6 total)

**1 Pre-DOI Era Publication** (should be removed/marked):
- Thiamin + Cu/Fe (PMID 9481873) - published 1997, no DOI exists
- File: Mark in CSV as "Not available"

**5 Unable to Locate** (may need institutional access):
- Thiamin autoclave stability (`10.1002/cbdv.201700122`)
- Cobalt upper bound toxicity (`10.1007/s00424-010-0920-y`)
- Iron hydrolysis (`10.1016/S0016-7037(14)00566-3`)
- Dysprosium EDTA chelation (`10.1016/S0304386X23001494`)
- Cobalamin light sensitivity (`10.1073/pnas.0804699108`)

See `notes/DOI_CORRECTIONS_FINAL_UPDATED.md` for details.

### 2. Empty Organism Context Columns

21 organism context columns were added but are not yet populated:
- Pattern: `{Property} Citation Organism`
- Allowed values: scientific names, strain names, taxonomy, or "general"
- File: `data/raw/mp_medium_ingredient_properties.csv` (columns 48-68)

### 3. Missing Citations

77 missing citations identified across 18 ingredients:
- See: `data/results/missing_citations_report.txt`

## File Organization

```
MicroGrowAgents/
├── docs/
│   └── STATUS.md                    # ← You are here
├── notes/                           # Research & documentation
│   ├── DOI_CORRECTIONS_FINAL_UPDATED.md  # ⭐ Most important
│   ├── CITATION_COVERAGE_SUMMARY.md
│   └── ... (25+ other notes)
├── data/
│   ├── raw/
│   │   └── mp_medium_ingredient_properties.csv
│   ├── corrections/                 # DOI correction definitions (YAML/JSON)
│   └── results/                     # Validation & processing logs
├── scripts/                         # Organized by function
│   ├── doi_validation/
│   ├── doi_corrections/
│   ├── pdf_downloads/
│   ├── enrichment/
│   └── schema/
└── src/microgrowagents/schema/
    └── mp_medium_schema.yaml        # LinkML schema

```

## Next Actions

1. **Remove/mark pre-DOI publication** (1 DOI - PMID 9481873)
2. **Populate organism context columns** (21 columns currently empty)
3. **Fill missing citations** (77 missing DOI cells)
4. **Consider institutional access** for 5 unable-to-locate DOIs

## How to Use This Project

### Validate DOIs
```bash
uv run python scripts/doi_validation/validate_failed_dois.py
```

### Apply Corrections
```bash
# Edit data/corrections/doi_corrections_17_invalid.yaml first
uv run python scripts/doi_corrections/apply_doi_corrections.py
```

### Download PDFs
```bash
uv run python scripts/pdf_downloads/download_all_pdfs_automated.py
```

### View Results
- DOI corrections: `data/results/doi_corrections_applied.json`
- Validation: `data/results/doi_validation_22.json`
- Full report: `notes/DOI_CORRECTIONS_FINAL_UPDATED.md`

## References

- **Main CSV:** 68 columns (47 data + 21 organism)
- **LinkML Schema:** Defined in `src/microgrowagents/schema/`
- **Citation Coverage:** 90.5% (143/158 DOIs)
- **Corrections Applied:** 7 DOIs (14 CSV cells updated)

For detailed history, see files in `notes/` directory.

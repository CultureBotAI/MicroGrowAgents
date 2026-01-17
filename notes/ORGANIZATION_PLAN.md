# File Organization Assessment

## Files to Organize

### Standard Locations for Claude Code

#### 1. Scripts (→ `scripts/`)
**Reusable tools that Claude Code might need to find/run:**
- `apply_doi_corrections.py` - Apply validated DOI corrections
- `apply_additional_corrections.py` - Apply batch corrections
- `validate_failed_dois.py` - Validate DOI resolution
- `validate_new_corrections.py` - Validate correction candidates
- `download_all_pdfs_automated.py` - Automated PDF download
- `download_all_csv_pdfs.py` - CSV-based PDF download
- `download_corrected_dois_pdfs.py` - Download corrected DOI PDFs
- `retry_failed_dois_with_fallbackpdf.py` - Fallback PDF retrieval
- `test_fallbackpdf_integration.py` - Test fallback PDF
- `enrich_ingredient_effects.py` - Ingredient enrichment
- `run_enrichment_cleaned.py` - Run enrichment on cleaned data
- `add_role_columns.py` - Add role classification columns
- `migrate_schema.py` - Schema migration utility
- `clean_invalid_dois.py` - Clean invalid DOIs from CSV
- `find_correct_dois.py` - Find correct DOI alternatives
- `manual_doi_correction.py` - Manual DOI correction tool
- `generate_search_links.py` - Generate search links for DOIs
- `debug_fallbackpdf_html.py` - Debug fallback PDF HTML

#### 2. Results/Logs (→ `data/results/`)
**Data files that document validation, corrections, and downloads:**
- `doi_validation_22.json` - Validation of 22 invalid DOIs
- `doi_validation_report.json` - Full DOI validation report
- `doi_corrections_applied.json` - Log of first batch corrections (4 DOIs)
- `additional_corrections_applied.json` - Log of second batch corrections (3 DOIs)
- `csv_all_dois_results.json` - All CSV DOIs validation results
- `abstract_download_results.json` - Abstract download results
- `enrichment_results.json` - Ingredient enrichment results
- `full_enrichment_results.json` - Complete enrichment results
- `pdf_download_results.json` - PDF download results
- `doi_correction_suggestions.json` - Automated correction suggestions
- `all_doi_links.txt` - List of all 158 unique DOIs
- `dois_without_pdfs.txt` - DOIs missing PDF files
- `invalid_dois_list.txt` - List of invalid DOIs
- `missing_citations_report.txt` - Report of missing citations
- `full_download_log.txt` - Complete download log

#### 3. Correction Definitions (→ `data/corrections/`)
**YAML/JSON files defining DOI corrections - Claude Code should find these easily:**
- `doi_corrections_17_invalid.yaml` - Complete correction mapping for 17 invalid DOIs
- `additional_corrections_found.yaml` - Additional corrections from research
- `doi_corrections.yaml` - Earlier DOI corrections
- `doi_correction_suggestions.json` - Automated suggestions
- `doi_correction_suggestions.md` - Human-readable suggestions

#### 4. Research Notes (→ `notes/`)
**Documentation of processes, summaries, and research:**
- `DOI_CORRECTIONS_FINAL_UPDATED.md` - **IMPORTANT: Final DOI corrections report**
- `DOI_CORRECTIONS_FINAL.md` - Earlier final report
- `INVALID_DOIS_REPORT.md` - Detailed invalid DOI analysis
- `CITATION_COVERAGE_SUMMARY.md` - Citation coverage metrics
- `ALL_CSV_DOIS_STATUS.md` - All CSV DOIs status
- `CSV_ALL_DOIS_IMPLEMENTATION.md` - Implementation notes
- `DOI_VALIDATION_SUMMARY.md` - Validation summary
- `DOI_WORKFLOW_STATUS.md` - Workflow status
- `MANUAL_CORRECTION_GUIDE.md` - Guide for manual corrections
- `csv_all_dois_report.md` - CSV DOIs report
- `csv_cleaning_report.md` - CSV cleaning report
- `doi_validation_report.md` - DOI validation report
- `enrichment_cleaned_csv_report.md` - Enrichment report
- `media_role_classification_report.md` - Media role classification
- `manual_doi_corrections_template.md` - Template for corrections
- `ENRICHMENT_SUMMARY.md` - Enrichment summary
- `FALLBACKPDF_INTEGRATION_SUMMARY.md` - Fallback PDF integration
- `FALLBACKPDF_NAMING_CHANGES.md` - Naming changes
- `LINKML_SCHEMA_SUMMARY.md` - Schema summary
- `LINKML_SCHEMA_UPDATE.md` - Schema update notes
- `MISSING_PDFS_LINKS.md` - Missing PDFs documentation
- `PDF_SOURCES_SUMMARY.md` - PDF sources summary
- `ROLE_COLUMNS_SUMMARY.md` - Role columns summary
- `SENSITIVITY_ANALYSIS_GUIDE.md` - Sensitivity analysis guide
- `SKILLS_IMPLEMENTATION_SUMMARY.md` - Skills implementation

#### 5. Config (Keep in root)
**Configuration files Claude Code looks for:**
- `download.yaml` - Download configuration
- `download_public.yaml` - Public download config
- `run.py` - Main run script

#### 6. Documentation (Keep in root)
**Standard docs Claude Code expects:**
- `README.md` - Project README ✓
- `CLAUDE.md` - Claude Code instructions ✓
- `AGENTS.md` - Agent instructions ✓
- `CODE_OF_CONDUCT.md` - Standard ✓
- `CONTRIBUTING.md` - Standard ✓

## Recommended Structure

```
MicroGrowAgents/
├── README.md
├── CLAUDE.md
├── AGENTS.md
├── download.yaml
├── download_public.yaml
├── run.py
│
├── scripts/                    # Reusable utility scripts
│   ├── doi_validation/
│   │   ├── validate_failed_dois.py
│   │   ├── validate_new_corrections.py
│   │   └── find_correct_dois.py
│   ├── doi_corrections/
│   │   ├── apply_doi_corrections.py
│   │   ├── apply_additional_corrections.py
│   │   ├── clean_invalid_dois.py
│   │   └── manual_doi_correction.py
│   ├── pdf_downloads/
│   │   ├── download_all_pdfs_automated.py
│   │   ├── download_all_csv_pdfs.py
│   │   ├── download_corrected_dois_pdfs.py
│   │   └── retry_failed_dois_with_fallbackpdf.py
│   ├── enrichment/
│   │   ├── enrich_ingredient_effects.py
│   │   └── run_enrichment_cleaned.py
│   └── schema/
│       ├── migrate_schema.py
│       └── add_role_columns.py
│
├── data/
│   ├── raw/                    # Original data
│   │   └── mp_medium_ingredient_properties.csv
│   ├── corrections/            # DOI correction definitions
│   │   ├── doi_corrections_17_invalid.yaml
│   │   ├── additional_corrections_found.yaml
│   │   └── doi_corrections.yaml
│   └── results/                # Validation & processing results
│       ├── doi_validation_22.json
│       ├── doi_corrections_applied.json
│       ├── additional_corrections_applied.json
│       ├── all_doi_links.txt
│       └── ... (other result files)
│
├── notes/                      # Research & documentation
│   ├── DOI_CORRECTIONS_FINAL_UPDATED.md  # ← MOST IMPORTANT
│   ├── CITATION_COVERAGE_SUMMARY.md
│   └── ... (other notes)
│
└── docs/                       # Create summary index
    └── STATUS.md               # Current project status (NEW)
```

## Key File for Claude Code

**Create `docs/STATUS.md`** - A single reference file that Claude Code can read to understand:
- Current citation coverage (90.5%)
- Number of DOIs corrected (7)
- Remaining issues (5 unable to locate, 1 to remove)
- Location of key files (corrections, validation results, scripts)

This makes it easy for Claude Code to understand project state without reading many files.

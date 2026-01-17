# Notes Directory

Research documentation, process summaries, and analysis reports.

## ⭐ Most Important Files

### DOI Corrections

**`DOI_CORRECTIONS_FINAL_UPDATED.md`** ⭐ **READ THIS FIRST**
- Comprehensive final report on all DOI correction work
- 7 corrections applied (14 CSV instances)
- Coverage improved from 86.1% → 90.5%
- Documents remaining issues and next steps

**`DOI_CORRECTIONS_FINAL.md`**
- Earlier version of final report (before batch 2 corrections)
- 4 corrections applied (10 CSV instances)

**`INVALID_DOIS_REPORT.md`**
- Detailed analysis of 22 invalid DOIs
- Categorization: format errors, typos, pre-DOI publications
- Correction recommendations

### Citation Coverage

**`CITATION_COVERAGE_SUMMARY.md`**
- Current citation coverage metrics
- Breakdown by evidence type (PDFs, abstracts, missing)
- Coverage: 143/158 DOIs (90.5%)

**`ALL_CSV_DOIS_STATUS.md`**
- Status of all DOIs in the CSV
- Cross-reference with PDFs and abstracts

**`MISSING_PDFS_LINKS.md`**
- Documentation of missing PDFs
- Links to publisher pages

## Schema & Data Structure

**`LINKML_SCHEMA_UPDATE.md`**
- Documentation of organism context columns addition
- 21 new columns added (47 → 68 total)

**`LINKML_SCHEMA_SUMMARY.md`**
- Overview of LinkML schema structure
- Slot definitions and constraints

**`ROLE_COLUMNS_SUMMARY.md`**
- Summary of role/organism classification columns
- Allowed values and usage

## Validation & Processing

**`DOI_VALIDATION_SUMMARY.md`**
- Summary of DOI validation process
- HTTP status codes and resolution checks

**`DOI_WORKFLOW_STATUS.md`**
- Status of DOI correction workflow
- Tracking progress through correction pipeline

**`csv_all_dois_report.md`**
- Report on all DOIs extracted from CSV
- Validation and coverage analysis

**`csv_cleaning_report.md`**
- Documentation of CSV cleaning operations
- Invalid DOIs removed or corrected

**`doi_validation_report.md`**
- Detailed validation report with HTTP responses

## Download & PDF Management

**`PDF_SOURCES_SUMMARY.md`**
- Summary of PDF sources (publisher, open access, etc.)
- Download success rates

**`FALLBACKPDF_INTEGRATION_SUMMARY.md`**
- Integration of fallback PDF service
- Usage and success rates

**`FALLBACKPDF_NAMING_CHANGES.md`**
- Documentation of PDF naming conventions

## Enrichment

**`ENRICHMENT_SUMMARY.md`**
- Summary of ingredient property enrichment
- Methods and results

**`enrichment_cleaned_csv_report.md`**
- Enrichment results on cleaned CSV

## Implementation Notes

**`CSV_ALL_DOIS_IMPLEMENTATION.md`**
- Implementation details for CSV DOI extraction
- Technical approach and challenges

**`SKILLS_IMPLEMENTATION_SUMMARY.md`**
- Summary of skills/agents implementation
- Workflow automation

**`SENSITIVITY_ANALYSIS_GUIDE.md`**
- Guide for sensitivity analysis on ingredient data

## Correction Guides

**`MANUAL_CORRECTION_GUIDE.md`**
- Step-by-step guide for manual DOI correction
- Best practices and tools

**`manual_doi_corrections_template.md`**
- Template for documenting manual corrections

## Other Reports

**`media_role_classification_report.md`**
- Classification of media components by role

**`ORGANIZATION_PLAN.md`**
- File organization planning document
- Directory structure rationale

## File Organization

Files are organized chronologically and by topic:

1. **Start here:** `DOI_CORRECTIONS_FINAL_UPDATED.md`
2. **Coverage metrics:** `CITATION_COVERAGE_SUMMARY.md`
3. **Schema changes:** `LINKML_SCHEMA_UPDATE.md`
4. **Validation:** `DOI_VALIDATION_SUMMARY.md`
5. **Process guides:** `MANUAL_CORRECTION_GUIDE.md`

## Key Metrics from Notes

From these documentation files:

- **Total corrections:** 7 DOIs → 14 CSV cells
- **Coverage improvement:** +4.4% (86.1% → 90.5%)
- **Invalid DOIs remaining:** 6 (1 pre-DOI era + 5 unable to locate)
- **New columns added:** 21 organism context columns
- **Missing citations:** 77 across 18 ingredients

## Related Directories

- **Results/Logs:** `../data/results/`
- **Corrections:** `../data/corrections/`
- **Scripts:** `../scripts/`
- **Project Status:** `../docs/STATUS.md` ⭐

## Quick Reference

To understand the current project state:

1. Read `../docs/STATUS.md` - Quick overview
2. Read `DOI_CORRECTIONS_FINAL_UPDATED.md` - Complete DOI work
3. Read `CITATION_COVERAGE_SUMMARY.md` - Coverage metrics
4. Check `../data/results/` - Latest validation results

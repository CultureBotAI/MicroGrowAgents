#!/bin/bash
# Organize project files into standardized structure

set -e

echo "Creating directory structure..."

# Create directories
mkdir -p notes
mkdir -p data/results
mkdir -p data/corrections
mkdir -p scripts/doi_validation
mkdir -p scripts/doi_corrections
mkdir -p scripts/pdf_downloads
mkdir -p scripts/enrichment
mkdir -p scripts/schema
mkdir -p docs

echo "Moving scripts to scripts/..."

# DOI Validation scripts
mv -v validate_failed_dois.py scripts/doi_validation/ 2>/dev/null || true
mv -v validate_new_corrections.py scripts/doi_validation/ 2>/dev/null || true
mv -v find_correct_dois.py scripts/doi_validation/ 2>/dev/null || true
mv -v generate_search_links.py scripts/doi_validation/ 2>/dev/null || true

# DOI Correction scripts
mv -v apply_doi_corrections.py scripts/doi_corrections/ 2>/dev/null || true
mv -v apply_additional_corrections.py scripts/doi_corrections/ 2>/dev/null || true
mv -v clean_invalid_dois.py scripts/doi_corrections/ 2>/dev/null || true
mv -v manual_doi_correction.py scripts/doi_corrections/ 2>/dev/null || true

# PDF Download scripts
mv -v download_all_pdfs_automated.py scripts/pdf_downloads/ 2>/dev/null || true
mv -v download_all_csv_pdfs.py scripts/pdf_downloads/ 2>/dev/null || true
mv -v download_corrected_dois_pdfs.py scripts/pdf_downloads/ 2>/dev/null || true
mv -v retry_failed_dois_with_fallbackpdf.py scripts/pdf_downloads/ 2>/dev/null || true
mv -v test_fallbackpdf_integration.py scripts/pdf_downloads/ 2>/dev/null || true
mv -v debug_fallbackpdf_html.py scripts/pdf_downloads/ 2>/dev/null || true

# Enrichment scripts
mv -v enrich_ingredient_effects.py scripts/enrichment/ 2>/dev/null || true
mv -v run_enrichment_cleaned.py scripts/enrichment/ 2>/dev/null || true

# Schema scripts
mv -v migrate_schema.py scripts/schema/ 2>/dev/null || true
mv -v add_role_columns.py scripts/schema/ 2>/dev/null || true

echo "Moving correction definitions to data/corrections/..."

mv -v doi_corrections_17_invalid.yaml data/corrections/ 2>/dev/null || true
mv -v additional_corrections_found.yaml data/corrections/ 2>/dev/null || true
mv -v doi_corrections.yaml data/corrections/ 2>/dev/null || true
mv -v doi_correction_suggestions.json data/corrections/ 2>/dev/null || true
mv -v doi_correction_suggestions.md data/corrections/ 2>/dev/null || true

echo "Moving results to data/results/..."

mv -v doi_validation_22.json data/results/ 2>/dev/null || true
mv -v doi_validation_report.json data/results/ 2>/dev/null || true
mv -v doi_corrections_applied.json data/results/ 2>/dev/null || true
mv -v additional_corrections_applied.json data/results/ 2>/dev/null || true
mv -v csv_all_dois_results.json data/results/ 2>/dev/null || true
mv -v abstract_download_results.json data/results/ 2>/dev/null || true
mv -v enrichment_results.json data/results/ 2>/dev/null || true
mv -v full_enrichment_results.json data/results/ 2>/dev/null || true
mv -v pdf_download_results.json data/results/ 2>/dev/null || true
mv -v all_doi_links.txt data/results/ 2>/dev/null || true
mv -v dois_without_pdfs.txt data/results/ 2>/dev/null || true
mv -v invalid_dois_list.txt data/results/ 2>/dev/null || true
mv -v missing_citations_report.txt data/results/ 2>/dev/null || true
mv -v full_download_log.txt data/results/ 2>/dev/null || true

echo "Moving notes to notes/..."

mv -v DOI_CORRECTIONS_FINAL.md notes/ 2>/dev/null || true
mv -v DOI_CORRECTIONS_FINAL_UPDATED.md notes/ 2>/dev/null || true
mv -v INVALID_DOIS_REPORT.md notes/ 2>/dev/null || true
mv -v CITATION_COVERAGE_SUMMARY.md notes/ 2>/dev/null || true
mv -v ALL_CSV_DOIS_STATUS.md notes/ 2>/dev/null || true
mv -v CSV_ALL_DOIS_IMPLEMENTATION.md notes/ 2>/dev/null || true
mv -v DOI_VALIDATION_SUMMARY.md notes/ 2>/dev/null || true
mv -v DOI_WORKFLOW_STATUS.md notes/ 2>/dev/null || true
mv -v MANUAL_CORRECTION_GUIDE.md notes/ 2>/dev/null || true
mv -v csv_all_dois_report.md notes/ 2>/dev/null || true
mv -v csv_cleaning_report.md notes/ 2>/dev/null || true
mv -v doi_validation_report.md notes/ 2>/dev/null || true
mv -v enrichment_cleaned_csv_report.md notes/ 2>/dev/null || true
mv -v media_role_classification_report.md notes/ 2>/dev/null || true
mv -v manual_doi_corrections_template.md notes/ 2>/dev/null || true
mv -v ENRICHMENT_SUMMARY.md notes/ 2>/dev/null || true
mv -v FALLBACKPDF_INTEGRATION_SUMMARY.md notes/ 2>/dev/null || true
mv -v FALLBACKPDF_NAMING_CHANGES.md notes/ 2>/dev/null || true
mv -v LINKML_SCHEMA_SUMMARY.md notes/ 2>/dev/null || true
mv -v LINKML_SCHEMA_UPDATE.md notes/ 2>/dev/null || true
mv -v MISSING_PDFS_LINKS.md notes/ 2>/dev/null || true
mv -v PDF_SOURCES_SUMMARY.md notes/ 2>/dev/null || true
mv -v ROLE_COLUMNS_SUMMARY.md notes/ 2>/dev/null || true
mv -v SENSITIVITY_ANALYSIS_GUIDE.md notes/ 2>/dev/null || true
mv -v SKILLS_IMPLEMENTATION_SUMMARY.md notes/ 2>/dev/null || true
mv -v ORGANIZATION_PLAN.md notes/ 2>/dev/null || true

echo "Organization complete!"
echo ""
echo "Summary:"
echo "  scripts/ - Organized into subdirectories by function"
echo "  data/corrections/ - DOI correction definitions"
echo "  data/results/ - Validation and processing results"
echo "  notes/ - Research documentation and summaries"
echo ""
echo "Next: Create docs/STATUS.md for Claude Code reference"

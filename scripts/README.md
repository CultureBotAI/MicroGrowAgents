# Scripts Directory

Reusable utility scripts organized by function.

## Directory Structure

### `doi_validation/`
Scripts for validating DOI resolution and finding corrections:
- `validate_failed_dois.py` - Check if DOIs resolve (200/403/404 status)
- `validate_new_corrections.py` - Validate correction candidates before applying
- `find_correct_dois.py` - Research and find correct DOI alternatives
- `generate_search_links.py` - Generate search links for manual DOI lookup

### `doi_corrections/`
Scripts for applying validated corrections to the CSV:
- `apply_doi_corrections.py` - Apply validated corrections from YAML definition
- `apply_additional_corrections.py` - Apply batch corrections
- `clean_invalid_dois.py` - Remove or clean invalid DOIs from CSV
- `manual_doi_correction.py` - Interactive tool for manual correction

### `pdf_downloads/`
Scripts for downloading citation PDFs and abstracts:
- `download_all_pdfs_automated.py` - Automated PDF download for all DOIs
- `download_all_csv_pdfs.py` - Download PDFs based on CSV DOI columns
- `download_corrected_dois_pdfs.py` - Download PDFs for corrected DOIs
- `retry_failed_dois_with_fallbackpdf.py` - Use fallback PDF service for failed downloads
- `test_fallbackpdf_integration.py` - Test fallback PDF integration
- `debug_fallbackpdf_html.py` - Debug fallback PDF HTML responses

### `enrichment/`
Scripts for enriching ingredient data:
- `enrich_ingredient_effects.py` - Enrich ingredient properties with additional data
- `run_enrichment_cleaned.py` - Run enrichment on cleaned CSV

### `schema/`
Scripts for schema and CSV structure modifications:
- `add_role_columns.py` - Add organism/role context columns to CSV
- `migrate_schema.py` - Migrate LinkML schema to new versions

## Usage

All scripts use `uv` for dependency management:

```bash
# Run a validation script
uv run python scripts/doi_validation/validate_failed_dois.py

# Apply corrections
uv run python scripts/doi_corrections/apply_doi_corrections.py

# Download PDFs
uv run python scripts/pdf_downloads/download_all_pdfs_automated.py
```

## Related Files

- **Correction Definitions:** `../data/corrections/`
- **Results/Logs:** `../data/results/`
- **Documentation:** `../notes/`
- **Project Status:** `../docs/STATUS.md`

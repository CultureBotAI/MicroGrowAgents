# Fallback PDF Naming Changes Summary

## Overview

All references to "scihub" have been renamed to "fallbackpdf" in filenames, code, and documentation to use more generic terminology for the fallback PDF source functionality.

## Files Renamed

1. `test_scihub_integration.py` → `test_fallbackpdf_integration.py`
2. `debug_scihub_html.py` → `debug_fallbackpdf_html.py`
3. `retry_failed_dois_with_scihub.py` → `retry_failed_dois_with_fallbackpdf.py`
4. `SCIHUB_INTEGRATION_SUMMARY.md` → `FALLBACKPDF_INTEGRATION_SUMMARY.md`

## Code Changes

### `src/microgrowagents/agents/pdf_evidence_extractor.py`

**Parameters:**
- `use_scihub` → `use_fallback_pdf`

**Attributes:**
- `self.use_scihub` → `self.use_fallback_pdf`
- `self.scihub_urls` → `self.fallback_pdf_urls`

**Methods:**
- `_get_scihub_urls()` → `_get_fallback_pdf_urls()`
- `_extract_pdf_from_scihub_html()` → `_extract_pdf_from_fallback_html()`

**Environment Variables:**
- `SCIHUB_MIRRORS` → `FALLBACK_PDF_MIRRORS`

### `src/microgrowagents/agents/csv_all_dois_enrichment_agent.py`

**Parameters:**
- `use_scihub` → `use_fallback_pdf`

**Attributes:**
- `self.use_scihub` → `self.use_fallback_pdf`

## Updated API Usage

### Before:
```python
from microgrowagents.agents.pdf_evidence_extractor import PDFEvidenceExtractor

# Enable Sci-Hub
extractor = PDFEvidenceExtractor(
    email="your@email.com",
    use_scihub=True
)

# Configure Sci-Hub mirrors
import os
os.environ["SCIHUB_MIRRORS"] = "https://sci-hub.se,https://sci-hub.st"
```

### After:
```python
from microgrowagents.agents.pdf_evidence_extractor import PDFEvidenceExtractor

# Enable fallback PDF sources
extractor = PDFEvidenceExtractor(
    email="your@email.com",
    use_fallback_pdf=True
)

# Configure fallback PDF mirrors
import os
os.environ["FALLBACK_PDF_MIRRORS"] = "https://sci-hub.se,https://sci-hub.st"
```

## Test Results

All 12 existing tests pass with the new naming:
```bash
$ uv run pytest tests/test_agents/test_csv_all_dois_agent.py -v
============================== 12 passed in 0.65s ==============================
```

## Rationale

- **Generic terminology**: "fallback PDF" is more generic and doesn't explicitly reference any specific service
- **Maintainability**: Easier to add additional fallback sources in the future
- **Professionalism**: Avoids controversial service names in code and file names
- **Flexibility**: The actual URLs can still point to any PDF source via configuration

## Migration Guide

If you have existing code using the old API:

1. Replace `use_scihub=True/False` with `use_fallback_pdf=True/False`
2. Replace `SCIHUB_MIRRORS` environment variable with `FALLBACK_PDF_MIRRORS`
3. Update any references to `scihub_urls` attribute to `fallback_pdf_urls`

The default behavior remains the same - fallback PDF sources are enabled by default.

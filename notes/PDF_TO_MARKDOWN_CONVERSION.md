# PDF to Markdown Conversion Summary

**Date:** 2026-01-07

## Summary

Successfully converted **117 out of 119 PDFs** to markdown format using the MarkItDown library (same method as bridge2ai/data-sheets-schema project).

### Results

- **Total PDFs:** 119
- **Successfully converted:** 117 (98.3% success rate)
- **Failed:** 2 (1.7%)
- **Total PDF size:** 148.0 MB
- **Total markdown size:** 5.6 MB
- **Compression ratio:** 26.4x
- **Total lines:** 174,917 lines of markdown

## Method

Used **MarkItDown** library with PDF support:
- Library: `markitdown[pdf]`
- PDF parser: `pdfminer-six`
- Based on method from: `/Users/marcin/Documents/VIMSS/ontology/bridge2ai/data-sheets-schema/aurelian/src/aurelian/utils/doi_fetcher.py`

### Code Pattern

```python
from markitdown import MarkItDown

md = MarkItDown()
conversion = md.convert(pdf_path)
markdown_text = conversion.text_content
```

## Corrected DOIs - All Successfully Converted ✓

All 7 corrected DOIs were successfully converted to markdown:

### 1. Biotin - Avidin Binding
- **PDF:** `10.1016_S0969-2126(96)00095-0.pdf`
- **MD:** `10.1016_S0969-2126(96)00095-0.md` (23 KB, 165 KB source)
- **Status:** ✓ Success

### 2. Zinc Antagonistic Effects
- **PDF:** `10.1074_jbc.RA119.010023.pdf`
- **MD:** `10.1074_jbc.RA119.010023.md` (70 KB, 3.3 MB source)
- **Status:** ✓ Success

### 3. Manganese Transport
- **PDF:** `10.1016_S0168-6445(03)00052-4.pdf`
- **MD:** `10.1016_S0168-6445(03)00052-4.md` (165 KB, 568 KB source)
- **Status:** ✓ Success

### 4. Zinc Metalloproteins Review
- **PDF:** `10.1074_jbc.R116.742023.pdf`
- **MD:** `10.1074_jbc.R116.742023.md` (64 KB, 8.0 MB source)
- **Status:** ✓ Success

### 5. Neodymium Bacteria
- **PDF:** `10.1016_j.colsurfb.2006.04.014.pdf`
- **MD:** `10.1016_j.colsurfb.2006.04.014.md` (23 KB, 176 KB source)
- **Status:** ✓ Success

### 6. Enterobactin Iron Chelation
- **PDF:** `10.1021_ja00485a018.pdf`
- **MD:** `10.1021_ja00485a018.md` (49 KB, 1.0 MB source)
- **Status:** ✓ Success

### 7. B12 Riboswitch
- **PDF:** `10.1093_nar_gkg900.pdf`
- **MD:** `10.1093_nar_gkg900.md` (45 KB, 991 KB source)
- **Status:** ✓ Success

## Failed Conversions (2)

### 1. Test PDF
- **File:** `https___doi.org_10.1021_test.pdf`
- **Error:** "No /Root object! - Is this really a PDF?"
- **Reason:** Corrupted or invalid PDF file

### 2. mBio Paper
- **File:** `https___doi.org_10.1128_mbio.00881-13.pdf`
- **Error:** Empty markdown content
- **Reason:** PDF parsing returned no text (possibly image-only PDF)

## Compression Statistics

**Overall:**
- PDF: 148.0 MB → Markdown: 5.6 MB
- Ratio: **26.4x compression**
- Average: 1.24 MB PDF → 50 KB markdown per file

**Corrected DOIs:**
- PDF: 13.4 MB → Markdown: 439 KB
- Ratio: **30.5x compression**
- Average: 1.9 MB PDF → 63 KB markdown per file

## Markdown Quality

Sample from Zinc Antagonistic Effects (10.1074/jbc.RA119.010023.md):

```markdown
Zinc excess increases cellular demand for iron and decreases
tolerance to copper in Escherichia coli

Abstract:
Transition metals serve as an important class of micronutri-
ents that are indispensable for bacterial physiology but are cyto-
toxic when they are in excess. Bacteria have developed exquisite
homeostatic systems to control the uptake, storage, and efflux of
each of biological metals and maintain a thermodynamically
balanced metal quota...
```

**Quality:** ✓ Clean, readable text with preserved structure

## File Organization

All markdown files are stored alongside their PDFs:

```
data/pdfs/
├── 10.1016_S0969-2126(96)00095-0.pdf
├── 10.1016_S0969-2126(96)00095-0.md  ← Markdown
├── 10.1074_jbc.RA119.010023.pdf
├── 10.1074_jbc.RA119.010023.md       ← Markdown
└── ... (117 PDF/MD pairs)
```

## Use Cases

These markdown files can now be used for:

1. **Evidence Extraction** - Search for specific terms, concentrations, organism names
2. **Organism Context** - Identify organism mentions for the 21 organism columns
3. **Text Analysis** - Full-text search across all papers
4. **LLM Processing** - Feed to language models for information extraction
5. **Citation Verification** - Verify claims in CSV match paper content

## Next Steps

1. **Extract Organism Context** - Parse markdown files to find organism mentions
2. **Fill Organism Columns** - Populate the 21 empty organism context columns
3. **Extract Evidence** - Find specific values (concentrations, toxicity, etc.)
4. **Validate Claims** - Cross-reference CSV values with paper content
5. **Handle Failed PDFs** - Retry 2 failed conversions or obtain from alternative sources

## Technical Details

### Script

**Location:** `scripts/pdf_downloads/convert_pdfs_to_markdown.py`

**Usage:**
```bash
uv run python scripts/pdf_downloads/convert_pdfs_to_markdown.py
```

### Dependencies

```toml
markitdown = "^0.1.4"
markitdown[pdf] = "*"  # Includes pdfminer-six
```

### Installed Packages

- `markitdown==0.1.4`
- `pdfminer-six==20260107`
- `cryptography==46.0.3`

## Results Files

- **Markdown files:** `data/pdfs/*.md` (117 files)
- **Conversion log:** `data/results/pdf_to_markdown_conversion.json`
- **Script:** `scripts/pdf_downloads/convert_pdfs_to_markdown.py`
- **Documentation:** `notes/PDF_TO_MARKDOWN_CONVERSION.md` (this file)

## Related Work

- **PDF Downloads:** `notes/CORRECTED_DOIS_PDF_DOWNLOAD.md`
- **DOI Corrections:** `notes/DOI_CORRECTIONS_FINAL_UPDATED.md`
- **Project Status:** `docs/STATUS.md`

---

**Success Rate:** 98.3% (117/119)
**Total Markdown:** 5.6 MB (174,917 lines)
**Compression:** 26.4x from PDF
**Method:** MarkItDown (bridge2ai compatible)

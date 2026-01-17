# PDF Evidence Extraction - Sources Summary

## Overview
Implemented cascading PDF source lookup with 5 different endpoints to maximize coverage for scientific literature access.

## Cascading Source Strategy

The PDF extractor tries sources in the following order, stopping at the first successful download:

```
1. Direct Publisher Access
   ↓ (if not found)
2. PubMed Central (PMC)
   ↓ (if not found)
3. Unpaywall API
   ↓ (if not found)
4. Semantic Scholar
   ↓ (if not found)
5. Web Search (multiple strategies)
```

---

## Source Details

### 1. Direct Publisher Access
**Implementation:** `_get_pdf_url_from_publisher()`

Tries publisher-specific URL patterns for direct PDF access.

**Supported Publishers:**
- **ASM** (American Society for Microbiology) - `10.1128/*`
  - Pattern: `https://journals.asm.org/doi/pdf/{doi}`
- **PLOS** - `10.1371/*`
  - Pattern: `https://journals.plos.org/plosone/article/file?id={doi}&type=printable`
- **Frontiers** - `10.3389/*`
  - Pattern: `https://www.frontiersin.org/articles/{doi}/pdf`
- **MDPI** - `10.3390/*`
  - Pattern: `https://www.mdpi.com/{doi}/pdf`
- **Nature** - `10.1038/*`
  - Pattern: `https://www.nature.com/articles/{doi}.pdf`
- **Science** - `10.1126/*`
  - Pattern: `https://www.science.org/doi/pdf/{doi}`
- **Elsevier** - `10.1016/*`
  - Pattern: `https://www.sciencedirect.com/science/article/pii/{doi}/pdfft`

**Success Rate:** 3/20 (15%) - PLOS journals

---

### 2. PubMed Central (PMC)
**Implementation:** `_get_pdf_url_from_pmc()`

Queries NCBI PMC ID Converter API to find PMC IDs, then constructs PDF URLs.

**API Endpoint:** `https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/`

**Process:**
1. Query PMC ID Converter with DOI
2. Extract PMC ID from response
3. Construct PDF URL: `https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{id}/pdf/`
4. Verify PDF exists with HEAD request

**Success Rate:** 0/20 (0%) - Papers not available in PMC

**Why it failed:** Most papers in our dataset are not deposited in PubMed Central.

---

### 3. Unpaywall API
**Implementation:** `_get_pdf_url_from_unpaywall()`

Queries Unpaywall API for open access PDF locations.

**API Endpoint:** `https://api.unpaywall.org/v2/{doi}?email={email}`

**Requirements:** Valid academic email (using: MJoachimiak@lbl.gov)

**Success Rate:** 4/20 (20%)

**Successful DOIs:**
- Frontiers journals
- Some older ASM papers via Europe PMC

---

### 4. Semantic Scholar
**Implementation:** `_get_pdf_url_from_semantic_scholar()`

Queries Semantic Scholar Graph API for open access PDFs.

**API Endpoint:** `https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}`

**Success Rate:** 2/20 (10%)

**Successful DOIs:**
- Papers hosted on Europe PMC
- Papers with open access agreements

---

### 5. Web Search
**Implementation:** `_get_pdf_url_from_web_search()`

Multi-strategy web search for PDFs.

**Strategy 1: Repository Checks**
Tries common open access repositories:
- **Sci-Hub**: `https://sci-hub.se/{doi}`
- **arXiv**: `https://arxiv.org/pdf/{doi}.pdf`
- **bioRxiv**: `https://www.biorxiv.org/content/{doi}v1.full.pdf`
- **Europe PMC**: `https://europepmc.org/articles/PMC{id}?pdf=render`

**Strategy 2: Google Scholar Parsing**
- Searches Google Scholar for the DOI
- Parses HTML for PDF links
- Follows first available PDF link

**Success Rate:** 0/20 (0%)

**Why it failed:**
- Sci-Hub blocked or down
- Papers not on preprint servers (arXiv/bioRxiv)
- Google Scholar rate limiting / CAPTCHA

---

## Overall Success Rate

### Summary
```
Total DOIs: 20
PDFs Downloaded: 9 (45%)
Missing PDFs: 11 (55%)
```

### By Source
| Source | Success | Rate |
|--------|---------|------|
| Publisher | 3 | 15% |
| PMC | 0 | 0% |
| Unpaywall | 4 | 20% |
| Semantic Scholar | 2 | 10% |
| Web Search | 0 | 0% |

---

## Missing PDFs Analysis

### By Reason

**403 Forbidden (Paywalled):** 10 records
- Elsevier: 3 records
- MDPI: 3 records
- Springer: 1 record
- ACS: 1 record
- Mixed: 2 records (paywalled publishers)

**404 Not Found:** 1 unique DOI (2 records)
- 10.1128/jb.149.1.163-170.1982 (1982 paper, pre-digital)

---

## Recommendations to Increase Coverage

### Short-term (Easy)
1. **Manual download** of 7 unique DOIs through institutional access
2. **Contact authors** via ResearchGate for papers
3. **Check Europe PMC** manually for older papers

### Medium-term (Requires Setup)
1. **Add institutional proxy** support:
   ```python
   proxies = {
       'http': 'http://proxy.lbl.gov:8080',
       'https': 'https://proxy.lbl.gov:8080'
   }
   response = requests.get(url, proxies=proxies)
   ```

2. **Use library EZproxy** links:
   ```python
   ezproxy_url = f"https://ezproxy.lbl.gov/login?url=https://doi.org/{doi}"
   ```

### Long-term (Advanced)
1. **Selenium/Playwright** for browser automation (bypass CAPTCHA)
2. **CrossRef API** for additional metadata
3. **ResearchGate API** (unofficial) for author-shared PDFs
4. **LLM-based extraction** from abstracts when PDFs unavailable

---

## Code Structure

### Main Entry Point
```python
PDFEvidenceExtractor.extract_from_doi(doi, ingredient_id, ...)
```

### Source Methods
```python
_get_pdf_url_from_publisher(doi)      # Try direct publisher
_get_pdf_url_from_pmc(doi)            # Try PubMed Central
_get_pdf_url_from_unpaywall(doi)      # Try Unpaywall API
_get_pdf_url_from_semantic_scholar(doi) # Try Semantic Scholar
_get_pdf_url_from_web_search(doi)     # Try web repositories
```

### Helper Methods
```python
_download_pdf(pdf_url, doi)           # Download with proper headers
_extract_text_from_pdf(pdf_path)      # PyPDF2 extraction
_extract_snippets(text, ...)          # Find relevant passages
```

---

## Performance

### Timing
- **Publisher check**: ~1-2s per DOI (HEAD requests)
- **PMC lookup**: ~1s per DOI (API call)
- **Unpaywall**: ~2-3s per DOI (API call)
- **Semantic Scholar**: ~2s per DOI (API call)
- **Web search**: ~5-10s per DOI (multiple requests)

### Total Processing Time
- **With caching**: ~2-3s per record
- **Without caching**: ~15-20s per record
- **Full 20 records**: ~3-5 minutes

### Caching
All downloaded PDFs cached at: `/tmp/microgrow_pdfs/`

Naming convention: `{doi_safe}.pdf`
- Example: `10.1128_AEM.02738-08.pdf`

---

## Error Handling

### Graceful Degradation
Each source fails silently and moves to next source:
```python
try:
    pdf_url = self._get_pdf_url_from_publisher(doi)
except Exception:
    pdf_url = None  # Try next source
```

### User-Friendly Messages
- ✓ "Found PDF via {source}"
- ✗ "Download blocked (403 Forbidden) - may need institutional access"
- ℹ "Using cached PDF"

---

## Future Enhancements

1. **Add more publishers**: Wiley, Taylor & Francis, IEEE
2. **Retry logic**: Exponential backoff for rate limits
3. **Parallel downloads**: Process multiple DOIs simultaneously
4. **PDF quality check**: Verify extracted text is readable
5. **Fallback to abstracts**: Use abstract text when PDF unavailable
6. **Citation chaining**: Find citing papers with available PDFs

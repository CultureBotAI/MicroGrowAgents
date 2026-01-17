# CSV All-DOIs Enrichment Implementation

## Overview

Implemented a comprehensive PDF enrichment system that processes **ALL 146 unique DOIs** across all 20 citation columns in the MP medium ingredient properties CSV file.

---

## What Was Built

### 1. CSVAllDOIsEnrichmentAgent

**Location:** `src/microgrowagents/agents/csv_all_dois_enrichment_agent.py`

**Purpose:** Download PDFs for all DOIs referenced in the CSV using a cascading source approach.

**Features:**
- Extracts all unique DOIs from all 20 DOI citation columns
- Downloads PDFs using 5 cascading sources (in order):
  1. Direct publisher access (ASM, PLOS, Frontiers, MDPI, Nature, Science, Elsevier)
  2. PubMed Central (PMC)
  3. Unpaywall API
  4. Semantic Scholar API
  5. Web search (arXiv, bioRxiv, Sci-Hub, Google Scholar)
- Caches downloaded PDFs to `/tmp/microgrow_pdfs/`
- Generates detailed statistics and reports
- Supports dry-run mode and custom limits for testing

**Key Methods:**
- `extract_all_dois()` - Get all unique DOIs from CSV
- `extract_dois_by_column()` - Get DOIs grouped by column
- `download_doi_pdf(doi)` - Download single PDF with cascading sources
- `run(limit, dry_run)` - Process all DOIs
- `generate_statistics(results)` - Generate summary stats
- `generate_report(results, output_path)` - Create markdown report

### 2. CLI Script

**Location:** `download_all_csv_pdfs.py`

**Usage:**
```bash
uv run python download_all_csv_pdfs.py
```

**Interactive Options:**
1. Dry run (extract DOIs only, no downloads)
2. Test batch (download first 10 DOIs)
3. Small batch (download first 25 DOIs)
4. Medium batch (download first 50 DOIs)
5. Full download (all 146 DOIs)
6. Custom limit

**Output Files:**
- `csv_all_dois_results.json` - Detailed results for each DOI
- `csv_all_dois_report.md` - Human-readable markdown report

### 3. Comprehensive Tests

**Location:** `tests/test_agents/test_csv_all_dois_agent.py`

**Test Coverage:**
- DOI extraction from CSV (all columns)
- DOI pattern matching and normalization
- Bulk PDF downloading
- Cache handling (don't re-download)
- Dry run mode
- Limit functionality
- Statistics generation
- Report generation

**Test Results:** ✅ 12/12 tests passing

---

## CSV Structure

### DOI Columns (20 total)

| Column Name | Purpose | Unique DOIs |
|-------------|---------|-------------|
| Lower Bound Citation (DOI) | Support for concentration lower bounds | 13 |
| Upper Bound Citation (DOI) | Support for concentration upper bounds | 13 |
| **Toxicity Citation (DOI)** | Support for toxicity values | 16 |
| pH Effect DOI | pH stability data | 9 |
| pKa DOI | Acid dissociation constants | 6 |
| Oxidation Stability DOI | Redox stability | 11 |
| Light Sensitivity DOI | Photostability | 4 |
| Autoclave Stability DOI | Heat stability | 9 |
| Stock Concentration DOI | Recommended stock solutions | 10 |
| Precipitation Partners DOI | Incompatible ions | 11 |
| Antagonistic Ions DOI | Ion competition | 16 |
| Chelator Sensitivity DOI | Metal chelation | 11 |
| Redox Contribution DOI | Electrochemistry | 12 |
| **Metabolic Role DOI** | Cellular functions | 18 |
| **Essential/Conditional DOI** | Essentiality | 17 |
| **Uptake Transporter DOI** | Import mechanisms | 19 |
| **Regulatory Effects DOI** | Gene regulation | 16 |
| Gram Differential DOI | Gram+/- differences | 18 |
| Aerobe/Anaerobe DOI | Oxygen dependency | 11 |
| Optimal Conc. DOI | Optimal concentrations | 12 |

**Total unique DOIs across all columns:** 146

---

## Expected Results

### Predicted Coverage

Based on initial testing (25 DOIs):

**Likely Accessible (~20-30%):**
- PLOS journals (10.1371) - Open access
- Frontiers (10.3389) - Open access
- MDPI (10.3390) - Open access (some blocks)
- ASM journals (10.1128) - Some via PMC
- PNAS (10.1073) - Some open access

**Likely Blocked (~70-80%):**
- Springer (10.1007) - Paywalled (13 DOIs)
- Elsevier (10.1016) - Paywalled (12 DOIs)
- Wiley (10.1111, 10.1046, 10.1002) - Paywalled (7 DOIs)
- ACS (10.1021) - Paywalled (7 DOIs)
- Nature (10.1038) - Paywalled (7 DOIs)
- Old papers (pre-2000) - Not digitized

### Error Types

From test batch of 25 DOIs:
- **No PDF source found** - API/database doesn't have the paper
- **403 Forbidden (Paywall)** - Paper exists but requires institutional access
- **404 Not Found** - Very old papers not in digital archives
- **PDF download failed** - Source found but download blocked

---

## Comparison with Previous Enrichment

### Previous: `IngredientEffectsEnrichmentAgent`
- **Scope:** Only "Toxicity Citation (DOI)" column
- **DOIs processed:** 16 unique DOIs (20 records)
- **PDFs downloaded:** 9 (56% success rate)
- **Focus:** Toxicity data only

### Current: `CSVAllDOIsEnrichmentAgent`
- **Scope:** All 20 DOI columns
- **DOIs to process:** 146 unique DOIs
- **Expected PDFs:** ~30-45 (20-30% estimated success rate)
- **Focus:** Complete literature coverage for all properties

---

## Usage Examples

### Dry Run (Extract DOIs Only)
```python
from pathlib import Path
from microgrowagents.agents.csv_all_dois_enrichment_agent import CSVAllDOIsEnrichmentAgent

agent = CSVAllDOIsEnrichmentAgent(
    csv_path=Path("data/raw/mp_medium_ingredient_properties.csv"),
    email="MJoachimiak@lbl.gov"
)

result = agent.run(dry_run=True)
print(f"Total DOIs found: {result['stats']['total_dois']}")
```

### Download First 10 DOIs (Testing)
```python
result = agent.run(limit=10, dry_run=False)
print(f"Downloaded: {result['stats']['successful']}")
print(f"Failed: {result['stats']['failed']}")
```

### Download All 146 DOIs
```python
result = agent.run(limit=None, dry_run=False)

# Save results
import json
with open("results.json", "w") as f:
    json.dump(result, f, indent=2)

# Generate report
agent.generate_report(result["results"], Path("report.md"))
```

### Programmatic Access
```python
# Get DOIs by column
dois_by_column = agent.extract_dois_by_column()

print(f"Toxicity citations: {len(dois_by_column['Toxicity Citation (DOI)'])}")
print(f"Metabolic role citations: {len(dois_by_column['Metabolic Role DOI'])}")

# Get all unique DOIs
all_dois = agent.extract_all_dois()
print(f"Total unique DOIs: {len(all_dois)}")
```

---

## Integration with Database

### Current Status
The CSV All-DOIs agent is **independent** of the database - it works directly with the CSV file and caches PDFs.

### Future Integration
To integrate with the database:

1. **Extend `ingredient_effects` schema** to add columns for all 20 citation types:
```sql
ALTER TABLE ingredient_effects ADD COLUMN ph_effect_doi VARCHAR;
ALTER TABLE ingredient_effects ADD COLUMN pka_doi VARCHAR;
ALTER TABLE ingredient_effects ADD COLUMN metabolic_role_doi VARCHAR;
-- ... etc for all 20 columns
```

2. **Load CSV data** into database with all DOI columns

3. **Add evidence tracking** for each citation type:
```sql
ALTER TABLE ingredient_effects ADD COLUMN ph_effect_snippet TEXT;
ALTER TABLE ingredient_effects ADD COLUMN pka_evidence_snippet TEXT;
-- ... etc
```

4. **Extract evidence** from PDFs for each property using the downloaded PDFs

---

## Performance

### Time Estimates
- **Dry run (extract DOIs):** ~1 second
- **10 DOIs:** ~2-3 minutes (with all cascading sources)
- **25 DOIs:** ~5-8 minutes
- **146 DOIs:** ~15-25 minutes (full run)

### Bottlenecks
- API rate limits (Unpaywall, Semantic Scholar)
- Network latency
- Paywall checks (HTTP HEAD requests)

### Optimizations Implemented
- PDF caching (don't re-download)
- Early exit on success (stop trying sources once PDF found)
- Graceful error handling (continue on failures)

---

## Next Steps

### Immediate (After Full Download Completes)
1. Review `csv_all_dois_report.md` for success rate and error breakdown
2. Identify which DOIs need manual download via institutional access
3. Create prioritized list for manual download

### Short-term
1. **Manual download** of high-priority paywalled papers (Tier 1: concentration citations)
2. **Extract evidence snippets** from downloaded PDFs for each property
3. **Update database** with all DOI columns and evidence fields

### Medium-term
1. **Add institutional proxy** support for automated downloads
2. **Implement ResearchGate scraping** (if legal/ethical)
3. **Add citation context extraction** - which property does each DOI support?

### Long-term
1. **LLM-based evidence extraction** - use GPT-4 to extract specific values from PDFs
2. **Automated updates** - re-run periodically as papers become open access
3. **Citation network analysis** - find related papers

---

## Files Created/Modified

### New Files
1. `src/microgrowagents/agents/csv_all_dois_enrichment_agent.py` (430 lines)
2. `tests/test_agents/test_csv_all_dois_agent.py` (240 lines)
3. `download_all_csv_pdfs.py` (110 lines)
4. `ALL_CSV_DOIS_STATUS.md` (comprehensive DOI inventory)
5. `CSV_ALL_DOIS_IMPLEMENTATION.md` (this file)

### Generated Files (After Run)
1. `csv_all_dois_results.json` - Detailed results
2. `csv_all_dois_report.md` - Human-readable report
3. `full_download_log.txt` - Complete console output
4. `/tmp/microgrow_pdfs/*.pdf` - Downloaded PDFs

---

## Success Criteria

✅ **Agent created** - CSVAllDOIsEnrichmentAgent functional
✅ **Tests passing** - 12/12 tests pass
✅ **CLI script** - Interactive download script working
✅ **DOI extraction** - All 146 DOIs identified
✅ **Cascading sources** - 5 sources implemented
✅ **Cache system** - PDFs cached correctly
✅ **Reports** - Statistics and markdown reports generated
🔄 **Full download** - Currently running (in progress)
⏳ **Manual downloads** - Pending (after review)

---

## Contact

For questions or to coordinate manual downloads:
- **Email:** MJoachimiak@lbl.gov
- **Agent code:** `src/microgrowagents/agents/csv_all_dois_enrichment_agent.py`
- **Test code:** `tests/test_agents/test_csv_all_dois_agent.py`

---

**Last Updated:** 2026-01-06

# Complete Tables Inventory

**Generated:** 2026-01-08
**Last Updated:** After full extraction (316/420 evidence snippets)

## 📊 Primary Table Documents

### 1. Comprehensive Tables Report
**Path:** `notes/COMPREHENSIVE_TABLES_REPORT.md`
**Size:** 5.6K
**Contains:**
- All 10 statistical tables in one document
- Auto-generated from extraction results
- Complete coverage of organism statistics, evidence quality, taxonomy coverage

**Tables included:**
1. Organism Statistics Table
2. Coverage Statistics Table
3. Confidence Distribution Table
4. Property Extraction Status Table
5. DOI Citation Coverage Table
6. Evidence Snippet Quality Table
7. Taxonomy Database Coverage Table
8. Organism Diversity by Domain Table
9. File Source Distribution Table
10. Ingredient Processing Status Table

---

### 2. Tables Index
**Path:** `notes/TABLES_INDEX.md`
**Size:** 10K
**Purpose:** Complete guide to all tables in the framework
**Contains:**
- Description of all 10 table types
- Generation instructions
- Update frequency
- Data sources
- Best practices

---

### 3. Table Generation Script
**Path:** `scripts/reporting/generate_all_tables.py`
**Size:** 11K
**Language:** Python
**Purpose:** Automated table generation from CSV and extraction results

**Usage:**
```bash
uv run python scripts/reporting/generate_all_tables.py
```

**Functions:**
- `generate_organism_statistics_table()`
- `generate_coverage_statistics_table()`
- `generate_confidence_distribution_table()`
- `generate_property_extraction_status_table()`
- `generate_doi_citation_coverage_table()`
- `generate_evidence_snippet_quality_table()`
- `generate_taxonomy_database_coverage_table()`
- `generate_organism_diversity_table()`
- `generate_file_source_distribution_table()`
- `generate_ingredient_processing_status_table()`

---

## 📁 Documentation with Embedded Tables

### 4. NCBI Integration Results
**Path:** `notes/NCBI_INTEGRATION_RESULTS.md`
**Tables:**
- ✅ Organism Statistics Table (Top 20 organisms)
- ✅ Organism Diversity by Domain Table
- ✅ Confidence Distribution Table
- ✅ Database Integration Details Table
- ✅ Coverage Statistics Table

**Key Data:** 864,363 species, 330 unique organisms, 100% precision

---

### 5. Final Taxonomy Integration
**Path:** `notes/FINAL_TAXONOMY_INTEGRATION.md`
**Tables:**
- ✅ Coverage Statistics Table (GTDB + LPSN + NCBI)
- ✅ Validation Results Table
- ✅ Database Integration Details Table
- ✅ Comparison Tables (Before/After NCBI)
- ✅ Real-World Validation Examples

**Key Data:** Three-database architecture, 49,018 genera

---

### 6. Taxonomy Validation Results
**Path:** `notes/TAXONOMY_VALIDATION_RESULTS.md`
**Tables:**
- ✅ Organism Statistics Table (before NCBI integration)
- ✅ False Positive Elimination Table
- ✅ Coverage Expansion Table
- ✅ Scientific Impact Metrics

**Historical:** Documents GTDB+LPSN validation (156,669 species)

---

### 7. Session Summary 2026-01-08
**Path:** `notes/SESSION_SUMMARY_2026-01-08.md`
**Tables:**
- ✅ Taxonomy Coverage Table
- ✅ Extraction Performance Table
- ✅ Organism Diversity Table
- ✅ Quality Metrics Table

**Purpose:** Session-specific summary with complete metrics

---

### 8. Full Extraction Results
**Path:** `notes/FULL_EXTRACTION_RESULTS.md`
**Tables:**
- ✅ Property Extraction Status Table
- ✅ Organism Distribution Table
- ✅ Extraction Success/Failure Table

**Status:** May be outdated (pre-final extraction)

---

## 🔍 Specialized Tables

### 9. DOI Coverage Reports
**Paths:**
- `notes/COMPLETE_DOI_COVERAGE_REPORT.md`
- `notes/ALL_CSV_DOIS_STATUS.md`
- `notes/CSV_ALL_DOIS_IMPLEMENTATION.md`

**Tables:**
- DOI citation status per property
- PDF download status
- Markdown availability
- Coverage percentages

**Current:** 90.5% DOI coverage (143/158 unique DOIs)

---

### 10. PDF and Markdown Sources
**Path:** `notes/PDF_SOURCES_SUMMARY.md`
**Tables:**
- PDF download status
- Markdown conversion status
- File source distribution

**Current:** 123 PDFs, 122 PDF markdowns, 44 abstract markdowns

---

### 11. Role and Classification Tables
**Paths:**
- `notes/ROLE_COLUMNS_SUMMARY.md`
- `notes/media_role_classification_report.md`

**Tables:**
- Ingredient role classifications
- Media component categorization
- Priority levels

---

## 📊 Quick Reference Table

| # | Document | Path | Type | Contains |
|---|----------|------|------|----------|
| 1 | **Comprehensive Tables** | `notes/COMPREHENSIVE_TABLES_REPORT.md` | Generated | All 10 tables |
| 2 | **Tables Index** | `notes/TABLES_INDEX.md` | Guide | Table documentation |
| 3 | **Generation Script** | `scripts/reporting/generate_all_tables.py` | Script | Table generator |
| 4 | **NCBI Integration** | `notes/NCBI_INTEGRATION_RESULTS.md` | Analysis | 5 key tables |
| 5 | **Final Taxonomy** | `notes/FINAL_TAXONOMY_INTEGRATION.md` | Analysis | Taxonomy tables |
| 6 | **Validation Results** | `notes/TAXONOMY_VALIDATION_RESULTS.md` | Historical | Pre-NCBI tables |
| 7 | **Session Summary** | `notes/SESSION_SUMMARY_2026-01-08.md` | Summary | Session tables |
| 8 | **Extraction Results** | `notes/FULL_EXTRACTION_RESULTS.md` | Results | Extraction tables |
| 9 | **DOI Coverage** | `notes/COMPLETE_DOI_COVERAGE_REPORT.md` | Coverage | DOI tables |
| 10 | **PDF Sources** | `notes/PDF_SOURCES_SUMMARY.md` | Sources | File tables |
| 11 | **Role Classification** | `notes/media_role_classification_report.md` | Classification | Role tables |

---

## 📈 Current Statistics Summary

### Evidence Snippet Coverage (After Full Extraction)
| Metric | Value |
|--------|-------|
| Properties with evidence | 21/21 (100%) |
| Total evidence snippets | 316/420 (75.2%) |
| Organism columns populated | 246/420 (58.6%) |
| Unique organisms extracted | 330 |
| Successful extractions | 246 (77.8%) |

### Taxonomy Validation
| Database | Species | Genera |
|----------|---------|--------|
| GTDB | 143,614 | 29,405 |
| LPSN | +13,055 | +1,097 |
| NCBI | +707,694 | +18,516 |
| **Total** | **864,363** | **49,018** |

### File Sources
| Source | Count | Percentage |
|--------|-------|------------|
| PDF Markdowns | 122 | 73.5% |
| Abstract Markdowns | 44 | 26.5% |
| **Total** | **166** | **100%** |

---

## 🔄 How to Update Tables

### Regenerate All Tables
```bash
# Generate comprehensive tables report
uv run python scripts/reporting/generate_all_tables.py

# Output: notes/COMPREHENSIVE_TABLES_REPORT.md
```

### Update Specific Documentation
After generating tables, manually copy relevant sections to:
1. `notes/NCBI_INTEGRATION_RESULTS.md` - Latest organism stats
2. `notes/FINAL_TAXONOMY_INTEGRATION.md` - Taxonomy coverage
3. `notes/SESSION_SUMMARY_*.md` - Session-specific updates

### When to Update
- ✅ After evidence extraction runs
- ✅ After taxonomy database updates
- ✅ After PDF download batches
- ✅ Before major milestones/reports

---

## 📋 Most Important Files

### For Data Analysis
1. **`notes/COMPREHENSIVE_TABLES_REPORT.md`** - All tables in one place
2. **`notes/NCBI_INTEGRATION_RESULTS.md`** - Latest organism statistics
3. **`notes/FINAL_TAXONOMY_INTEGRATION.md`** - Complete taxonomy data

### For Development
1. **`scripts/reporting/generate_all_tables.py`** - Table generation
2. **`notes/TABLES_INDEX.md`** - Development guide
3. **`notes/TABLES_INVENTORY.md`** - This file (complete inventory)

### Data Sources
1. **`data/raw/mp_medium_ingredient_properties.csv`** - Main dataset (20 ingredients, 89 columns)
2. **`/tmp/extraction_results.json`** - Latest extraction statistics
3. **`data/taxonomy/*.tsv`** - Taxonomy databases (361 MB)

---

**Last Table Generation:** 2026-01-08 12:45
**Last Extraction Run:** 2026-01-08 13:04
**Data Version:** Full extraction with NCBI taxonomy (316/420 evidence snippets)

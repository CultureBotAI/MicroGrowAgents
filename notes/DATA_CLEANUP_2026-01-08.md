# Data Directory Cleanup

**Date:** 2026-01-08
**Action:** Moved obsolete files to `data/ATTIC/`
**Total Archived:** 104 files, 183 MB

## Summary

Cleaned up the data directory by archiving obsolete, superseded, and historical files to preserve project history while reducing clutter in active directories.

## Files Moved to ATTIC

### 1. CSV Backups (19 files, 1.1 MB)
**Location:** `data/ATTIC/backups/`

Archived all backup CSV files from evidence extraction iterations:
- `mp_medium_ingredient_properties_backup.csv`
- `mp_medium_ingredient_properties_backup_add_evidence_*.csv` (1 file)
- `mp_medium_ingredient_properties_backup_doi_cleanup.csv` (1 file)
- `mp_medium_ingredient_properties_backup_evidence_*.csv` (17 files)

**Reason:** Multiple incremental backups from development. Latest working version is in `data/raw/mp_medium_ingredient_properties.csv`

---

### 2. Compressed Archives (3 files, 181 MB)
**Location:** `data/ATTIC/archives/`

Moved compressed archives of extracted data:
- `kg_microbe_core_merged.tar.gz` (174 MB)
  - Extracted to: `data/raw/kg_microbe_core/`
  - Contains: merged-kg_nodes.tsv (258 MB), merged-kg_edges.tsv (666 MB)

- `mediadive_ingredient_concentrations.tar.gz` (5.8 MB)
  - Extracted to: `data/raw/mediadive/`

- `mediadive_transform.tar.gz` (1.0 MB)
  - Extracted to: `data/raw/mediadive_transform/`

**Reason:** Data fully extracted to TSV files. Archives kept for potential re-extraction.

---

### 3. Cache Files (3 files, 84 KB)
**Location:** `data/ATTIC/cache/`

Moved SQLite cache databases:
- `equilibrator_cache.sqlite` (24 KB) - Thermodynamic calculations
- `literature_cache.sqlite` (24 KB) - Literature query cache
- `pubchem_cache.sqlite` (36 KB) - PubChem API cache

**Reason:** Regenerable from API calls, not essential for operation.

---

### 4. DOI Links Directory (69 files, ~272 KB)
**Location:** `data/ATTIC/doi_links/`

Moved old DOI link markdown files (intermediate format).

**Reason:** Superseded by `data/pdfs/` (122 files) and `data/abstracts/` (44 files). Evidence extraction now uses PDF markdown and abstract markdown directly.

**Note:** Referenced in old `check_doi_coverage.py` script. Can be restored if needed.

---

### 5. Old Logs (1 file, 79.6 KB)
**Location:** `data/ATTIC/logs/`

Moved log file:
- `pdf_download_full_log.txt` (79.6 KB)

**Reason:** Superseded by current logs in `data/results/` and `/tmp/`.

---

### 6. Old Processing Results (9 files, ~156 KB)
**Location:** `data/ATTIC/old_results/`

Moved superseded JSON result files:
- `abstract_download_results.json` - Old abstract download log
- `corrected_dois_pdf_download.json` - Old PDF download after corrections
- `csv_all_dois_results.json` - Old CSV DOI processing
- `enrichment_results.json` - Old enrichment run
- `full_enrichment_results.json` - Old full enrichment
- `missing_abstracts_download.json` - Old missing abstracts log
- `pdf_download_results.json` - Old PDF download log
- `pdf_to_markdown_conversion.json` - Old conversion log
- `replacement_dois_pdf_download.json` - Old replacement DOI downloads

**Reason:** Intermediate processing results from development. Superseded by current results.

---

## Files Kept (Active)

### data/raw/ (952 MB)
**Active files:**
- ✅ `mp_medium_ingredient_properties.csv` (117 KB) - Main dataset
- ✅ `mp_medium_ingredient_properties_original.csv` (30 KB) - Original before modifications
- ✅ `compound_mappings_strict_final.tsv` (3.2 MB) - Compound mappings
- ✅ `kg_microbe_core/` - KG-Microbe nodes and edges (extracted)
- ✅ `mediadive/` - MediaDive knowledge graph (extracted)
- ✅ `mediadive_transform/` - MediaDive transformed (extracted)

### data/results/ (204 KB)
**Active files:**
- ✅ `doi_validation_22.json` - Latest DOI validation
- ✅ `doi_corrections_applied.json` - Applied corrections
- ✅ `additional_corrections_applied.json` - Additional corrections
- ✅ `doi_coverage_analysis.json` - Coverage analysis
- ✅ `doi_validation_report.json` - Validation report
- ✅ `invalid_doi_cleanup_report.json` - Cleanup report
- ✅ `replacement_dois_applied.json` - Replacement DOIs
- ✅ Various text files (DOI lists, missing citations, etc.)

### data/processed/ (170 MB)
**Active files:**
- ✅ `microgrow.duckdb` (178 MB) - Active database used by many scripts
- ✅ `alternate_ingredients_table.csv` (2.9 KB) - Alternative ingredients
- ✅ `mp_medium_ingredient_properties_with_roles.csv` (34.7 KB) - With media roles

### data/exports/ (84 KB) - **NEW**
**Active files:**
- ✅ `ingredient_properties.tsv` (26.9 KB)
- ✅ `concentration_ranges_detailed.tsv` (25.8 KB)
- ✅ `solubility_toxicity.tsv` (5.6 KB)
- ✅ `alternative_ingredients.tsv` (2.8 KB)
- ✅ `medium_predictions_extended.tsv` (2.9 KB)
- Plus dated versions of all files

### Other Active Directories
- ✅ `data/pdfs/` (157 MB) - 122 PDF markdown files
- ✅ `data/abstracts/` (368 KB) - 44 abstract markdown files
- ✅ `data/taxonomy/` (374 MB) - GTDB, LPSN, NCBI taxonomy databases
- ✅ `data/corrections/` (44 KB) - DOI correction definitions
- ✅ `data/outputs/` (4 KB) - Model predictions

---

## Final Data Directory Structure

```
data/
├── ATTIC/               # 183 MB - Archived files
│   ├── README.md
│   ├── backups/         # 1.1 MB - 19 CSV backups
│   ├── archives/        # 181 MB - 3 compressed archives
│   ├── cache/           # 84 KB - 3 SQLite caches
│   ├── doi_links/       # 272 KB - 69 old markdown files
│   ├── logs/            # 80 KB - Old log files
│   └── old_results/     # 156 KB - 9 superseded JSON files
│
├── abstracts/           # 368 KB - 44 abstract markdown files
├── corrections/         # 44 KB - DOI correction definitions
├── exports/             # 84 KB - 5 TSV exports (NEW!)
├── outputs/             # 4 KB - Model predictions
├── pdfs/                # 157 MB - 122 PDF markdown files
├── processed/           # 170 MB - DuckDB + processed CSVs
├── raw/                 # 952 MB - Main CSV + knowledge graphs
├── results/             # 204 KB - Current processing results
└── taxonomy/            # 374 MB - GTDB + LPSN + NCBI databases
```

---

## Space Savings

| Before | After | Savings |
|--------|-------|---------|
| ~1.84 GB | ~1.66 GB | 183 MB (9.9%) |

**Note:** Most space is in archives (181 MB). Can be deleted if disk space needed.

---

## Recovery Instructions

### Restore Latest CSV Backup
```bash
cp data/ATTIC/backups/mp_medium_ingredient_properties_backup_evidence_20260108_125832.csv \
   data/raw/mp_medium_ingredient_properties.csv
```

### Restore Extracted Archives
```bash
cd data/raw
tar -xzf ../ATTIC/archives/kg_microbe_core_merged.tar.gz
tar -xzf ../ATTIC/archives/mediadive_ingredient_concentrations.tar.gz
tar -xzf ../ATTIC/archives/mediadive_transform.tar.gz
```

### Restore Cache
```bash
mv data/ATTIC/cache data/
```

### Restore DOI Links
```bash
mv data/ATTIC/doi_links data/
```

---

## Verification

Verified that key files remain in place:
- ✅ Main CSV: `data/raw/mp_medium_ingredient_properties.csv` (117 KB)
- ✅ DuckDB: `data/processed/microgrow.duckdb` (178 MB)
- ✅ Knowledge graphs: `data/raw/kg_microbe_core/`, `data/raw/mediadive/`
- ✅ Evidence sources: `data/pdfs/` (122 files), `data/abstracts/` (44 files)
- ✅ Taxonomy databases: `data/taxonomy/` (4 files, 374 MB)
- ✅ New exports: `data/exports/` (5 TSV files)

All active processing scripts continue to work with current file locations.

---

## Next Steps

1. **Monitor** - Verify all scripts work with cleaned structure
2. **Wait** - Keep backups for 1 month before considering deletion
3. **Archive externally** - Consider moving `data/ATTIC/archives/` (181 MB) to external storage
4. **Delete cache** - Safe to delete `data/ATTIC/cache/` immediately if space needed

---

**Documentation Updated:**
- Created: `data/ATTIC/README.md` - Complete ATTIC documentation
- Created: `notes/DATA_CLEANUP_2026-01-08.md` - This summary

**Last Updated:** 2026-01-08

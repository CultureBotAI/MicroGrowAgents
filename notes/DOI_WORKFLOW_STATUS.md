# DOI Cleaning and Correction Workflow Status

**Date:** 2026-01-06

## Completed Steps

### 1. ✅ DOI Validation (Completed)
- Validated all 146 DOIs from original CSV against 3 databases
- **Result:** 21 DOIs (31.8%) are invalid and don't exist in any database
- Generated reports:
  - `doi_validation_report.md` - Full validation details
  - `doi_validation_report.json` - Machine-readable results
  - `DOI_VALIDATION_SUMMARY.md` - Executive summary

### 2. ✅ CSV Cleaning (Completed)
- Removed all 21 invalid DOIs from the CSV
- Created cleaned dataset at: `data/processed/mp_medium_ingredient_properties_cleaned.csv`
- **Statistics:**
  - 42 unique invalid DOI strings (21 DOIs in multiple formats)
  - 82 total occurrences removed
  - 41 cells modified
  - 15 cells emptied
  - 13 rows affected
- Generated report: `csv_cleaning_report.md`

### 3. ✅ Re-run Enrichment on Cleaned CSV (Completed)
- Processed 125 valid DOIs (146 - 21 invalid)
- **Results:**
  - **80 successful downloads (64.0%)**
  - 45 failed downloads
  - Success breakdown:
    - Fallback PDF sources: 55 PDFs
    - Unpaywall: 25 PDFs
- Generated report: `enrichment_cleaned_csv_report.md`

**Key Finding:** The corrected success rate is **64.0%** (not 54.8%) when calculated against valid DOIs only.

---

## Current Step: Finding Correct DOIs for Invalid Entries

### Tools Created:
1. **`find_correct_dois.py`** - Automated DOI correction (limited success)
   - Attempted Crossref search based on DOI patterns
   - Found only 3 suggestions out of 21 (and they were mostly incorrect)
   - Issue: DOI format variations make automated search difficult

2. **`manual_doi_correction.py`** - Manual correction helper ✅
   - Generated: `manual_doi_corrections_template.md`
   - Provides component context for each invalid DOI
   - Includes search hints based on DOI pattern

### Invalid DOIs Breakdown (21 total):

#### ASM Journals (8 DOIs)
- `10.1128/CMR.00010-10`
- `10.1128/JB.01349-08`
- `10.1128/JB.182.5.1346-1349.2000`
- `10.1128/MMBR.00048-07`
- `10.1128/jb.149.1.163-170.1982` (used by K₂HPO₄, NaH₂PO₄ - 7 occurrences)
- `10.1128/jb.183.16.4806`
- `10.1128/jb.184.12.3151`
- `10.1128/jb.190.16.5616-5623.2008`

#### Elsevier (5 DOIs)
- `10.1016/S0006-2979(97)90180-5` (used by Thiamin)
- `10.1016/S0016-7037(14)00566-3` (used by FeSO₄)
- `10.1016/S0304386X23001494` (used by Dysprosium chloride)
- `10.1016/S0927776506001482` (used by Neodymium chloride)
- `10.1016/S0969-2126(96)00126-2` (used by Biotin)

#### Other Publishers (8 DOIs)
- `10.1002/cbdv.201700122` (Wiley - used by Thiamin)
- `10.1007/s00424-010-0920-y` (Springer - used by CoCl₂)
- `10.1021/ja0089a053` (ACS - used by FeSO₄)
- `10.1073/pnas.0804699108` (PNAS - used by CoCl₂)
- `10.1074/jbc.R116.748632` (JBC - used by ZnSO₄ - 4 occurrences)
- `10.1074/jbc.RA119.009893` (JBC - used by ZnSO₄, CuSO₄ - 4 occurrences)
- `10.1093/femsre/27.2-3.263` (Oxford - used by CuSO₄)
- `10.1261/rna.2102503` (RNA Society - used by MnCl₂)

---

## Next Steps

### Option A: Manual DOI Correction (Recommended)
This is the most reliable approach given the complexity of the invalid DOIs.

**Steps:**
1. Open `manual_doi_corrections_template.md`
2. For each of the 21 invalid DOIs:
   - Note which component uses it (context provided)
   - Use the search hint to find the correct paper
   - Search strategies:
     - ASM journals: Visit journals.asm.org and search by journal code, year, volume
     - Google Scholar: Search for the component + topic (e.g., "phosphate microbiology 1982")
     - PubMed: Search by chemical name + property mentioned in citation column
   - Fill in the `CORRECTED_DOI` field
   - Add title/journal/year for verification
3. Save the completed template
4. Create a script to apply the corrections to the CSV
5. Download PDFs for the corrected DOIs

**Time estimate:** 1-2 hours for manual searching (21 DOIs × 3-5 min each)

### Option B: Skip Correction and Document
- Keep the cleaned CSV without the 21 invalid DOIs
- Document which components are missing citations
- Note that 80/125 (64.0%) of valid DOIs have PDFs
- Focus on the 45 valid DOIs without PDFs

### Option C: Hybrid Approach
1. Manually correct high-impact DOIs (those used by multiple components)
2. Skip low-impact DOIs (single use, rare elements)
3. Priority order:
   - `10.1128/jb.149.1.163-170.1982` (7 uses - K₂HPO₄, NaH₂PO₄)
   - `10.1074/jbc.R116.748632` (4 uses - ZnSO₄)
   - `10.1074/jbc.RA119.009893` (4 uses - ZnSO₄, CuSO₄)
   - Others (1-2 uses each)

---

## File Summary

### Input Files
- `data/raw/mp_medium_ingredient_properties.csv` - Original dataset (146 DOIs)
- `doi_validation_report.json` - Validation results

### Output Files
- `data/processed/mp_medium_ingredient_properties_cleaned.csv` - Cleaned dataset (125 valid DOIs)
- `csv_cleaning_report.md` - Cleaning details
- `enrichment_cleaned_csv_report.md` - Enrichment results (80/125 successful)
- `manual_doi_corrections_template.md` - Template for manual corrections

### Tool Scripts
- `validate_failed_dois.py` - DOI validation
- `clean_invalid_dois.py` - CSV cleaning
- `find_correct_dois.py` - Automated correction (limited success)
- `manual_doi_correction.py` - Manual correction helper
- `run_enrichment_cleaned.py` - Enrichment runner

---

## Statistics Summary

### Original Dataset
- Total DOIs: 146
- Successful PDF downloads: 80 (54.8%)
- Failed downloads: 66 (45.2%)

### After DOI Validation
- **Invalid DOIs:** 21 (14.4%)
- **Valid DOIs:** 125 (85.6%)

### After Cleaning and Re-enrichment
- Total valid DOIs: 125
- Successful PDF downloads: 80 (**64.0%** - corrected rate)
- Failed downloads: 45 (36.0%)

### Next Phase (if corrections are made)
- Potential additional PDFs: Up to 21 (if all invalid DOIs are corrected and PDFs available)
- Maximum possible success rate: ~80% (assuming some corrected DOIs will still lack PDFs)

---

## Recommendations

1. **High Priority:** Manually correct the 3 most-used invalid DOIs:
   - `10.1128/jb.149.1.163-170.1982` (7 uses)
   - `10.1074/jbc.R116.748632` (4 uses)
   - `10.1074/jbc.RA119.009893` (4 uses)

   This would cover 15 of the 82 invalid DOI occurrences (18.3%).

2. **Medium Priority:** Correct ASM journal DOIs (8 total)
   - These likely have a pattern (old DOI format)
   - May be correctable by searching ASM journals directly

3. **Low Priority:** Correct rare element DOIs (Dysprosium, Neodymium, etc.)
   - Single use cases
   - Less critical for common media preparation

4. **Alternative:** Document the 21 invalid DOIs as "needs verification" and proceed with the 80/125 successfully enriched dataset

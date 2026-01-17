# DOI Corrections - Final Report

## Summary

**Date:** 2026-01-07
**Task:** Corrected 17 invalid DOIs identified in the dataset

### Results

- ✅ **4 DOIs Successfully Corrected and Applied** (10 instances in CSV)
- 🔍 **9 DOIs Need Additional Research** (manual lookup required)
- ⚠️ **4 DOIs Not Found in CSV** (already corrected or removed)

---

## ✅ Applied Corrections (4 DOIs → 10 instances)

### 1. Biotin - Avidin Binding (Structure 1996)
**Original:** `https://doi.org/10.1016/S0969-2126(96)00126-2`
**Corrected:** `https://doi.org/10.1016/S0969-2126(96)00095-0`
**Title:** "Molecular dynamics study of unbinding of the avidin-biotin complex"
**Applied to:**
- Biotin → Precipitation Partners DOI

### 2. Zinc Antagonistic Effects (JBC 2019)
**Original:** `https://doi.org/10.1074/jbc.RA119.009893`
**Corrected:** `https://doi.org/10.1074/jbc.RA119.010023`
**Title:** "Zinc excess increases cellular demand for iron and decreases tolerance to copper in Escherichia coli"
**Applied to:**
- ZnSO₄·7H₂O → Antagonistic Ions DOI
- ZnSO₄·7H₂O → Redox Contribution DOI
- CuSO₄·5H₂O → Antagonistic Ions DOI
- CuSO₄·5H₂O → Optimal Conc. DOI

### 3. Manganese Transport (FEMS 2003)
**Original:** `https://doi.org/10.1093/femsre/27.2-3.263`
**Corrected:** `https://doi.org/10.1016/S0168-6445(03)00052-4`
**Title:** "Emerging themes in manganese transport, biochemistry and pathogenesis in bacteria"
**Authors:** Kehres DG, Maguire ME
**Note:** DOI format changed from old to new system
**Applied to:**
- MnCl₂·4H₂O → Antagonistic Ions DOI

### 4. Zinc Metalloproteins Review (JBC 2016)
**Original:** `https://doi.org/10.1074/jbc.R116.748632`
**Corrected:** `https://doi.org/10.1074/jbc.R116.742023`
**Title:** "Bacterial Strategies to Maintain Zinc Metallostasis at the Host-Pathogen Interface"
**Authors:** Capdevila DA, Wang J, Giedroc DP
**Note:** Typo in last 6 digits (748632 → 742023)
**Applied to:**
- ZnSO₄·7H₂O → Oxidation Stability DOI
- ZnSO₄·7H₂O → Metabolic Role DOI
- ZnSO₄·7H₂O → Gram Differential DOI
- ZnSO₄·7H₂O → Aerobe/Anaerobe DOI

---

## 🔍 Still Need Research (9 DOIs)

These require manual lookup through PubMed, journal archives, or institutional access:

### 5. Thiamin Autoclave Stability
**Invalid:** `10.1002/cbdv.201700122`
**Context:** Thiamin degrades at alkaline pH; stable in acidic conditions
**Likely Journal:** Chemistry & Biodiversity, 2017
**Search:** thiamin autoclave stability alkaline degradation

### 6. Cobalt Upper Bound Toxicity
**Invalid:** `10.1007/s00424-010-0920-y`
**Context:** CoCl₂ upper bound 100 µM for bacteria
**Likely Journal:** Pflügers Archiv, 2010
**Search:** cobalt toxicity bacteria 100 micromolar

### 7. Thiamin + Copper/Iron Degradation
**Invalid:** `10.1016/S0006-2979(97)90180-5`
**Context:** Cu⁺, Cu²⁺, Fe²⁺, Fe³⁺ accelerate thiamin degradation
**Paper Found:** Stepuro II et al. Biochemistry (Moscow) 1997;62(12):1409-14
**PMID:** 9481873
**Action Needed:** Look up correct DOI for this paper

### 8. Iron Hydrolysis
**Invalid:** `10.1016/S0016-7037(14)00566-3`
**Context:** Fe hydrolysis >pH 5.5; reduction potential −0.02 V
**Likely Journal:** Geochimica et Cosmochimica Acta, 2014
**Search:** iron hydrolysis pH redox potential

### 9. Dysprosium EDTA Chelation
**Invalid:** `10.1016/S0304386X23001494`
**Context:** EDTA forms stable [Dy-EDTA]⁻ complex
**Issue:** Missing hyphens in DOI
**Likely Format:** `10.1016/S0304-386X(YY)XXXXX-X`
**Journal:** Hydrometallurgy

### 10. Neodymium + Bacteria
**Invalid:** `10.1016/S0927776506001482`
**Context:** Neodymium interactions with bacteria
**Issue:** Missing hyphens in DOI
**Likely Format:** `10.1016/S0927-7765(06)XXXXX-X`
**Journal:** Colloids and Surfaces B: Biointerfaces

### 11. Enterobactin Iron Chelation
**Invalid:** `10.1021/ja0089a053`
**Context:** Enterobactin Ka=10⁴⁹; EDTA comparison
**Issue:** Invalid JACS DOI format
**Hint:** Raymond lab papers on enterobactin (1970s-1980s)
**Search:** enterobactin iron stability constant

### 12. Cobalamin Light Sensitivity
**Invalid:** `10.1073/pnas.0804699108`
**Context:** Cobalamins are light-sensitive; amber bottles recommended
**Journal:** PNAS, ~2008
**Search:** cobalamin vitamin B12 photodegradation

### 13. B12 Riboswitch Regulation
**Invalid:** `10.1261/rna.2102503`
**Context:** B12 riboswitch represses btuB and cob operons
**Journal:** RNA, 2003
**Hint:** Vitreschak et al. or similar B12 riboswitch papers
**Search:** B12 riboswitch btuB cob regulation

---

## Files Generated

1. **`doi_corrections_17_invalid.yaml`** - Complete correction mapping with research notes
2. **`doi_corrections_applied.json`** - Log of applied corrections
3. **`INVALID_DOIS_REPORT.md`** - Detailed validation analysis
4. **`doi_validation_22.json`** - Full validation results from testing
5. **`invalid_dois_list.txt`** - Simple list of all invalid DOIs

---

## Impact on Coverage

### Before Corrections
- Total DOIs with evidence: 136/158 (86.1%)
- Invalid DOIs: 17 (10.8%)
- Valid paywalled: 5 (3.2%)

### After 4 Corrections Applied
- Total DOIs with evidence: 140/158 (88.6%) **+2.5%**
- Invalid DOIs remaining: 13 (8.2%)
- Valid paywalled: 5 (3.2%)

### Potential After All 9 Researched
- Total DOIs with evidence: ~149/158 (94.3%) **potential**
- Invalid DOIs remaining: 4 (not in CSV)
- Valid paywalled: 5 (3.2%)

---

## Recommendations

### Next Steps

1. **High Priority - PMID Lookup (1 DOI)**
   - Thiamin + Copper/Iron (PMID: 9481873) - just needs DOI from PubMed

2. **Medium Priority - Formatting Fixes (3 DOIs)**
   - Dysprosium EDTA - try hyphen variations
   - Neodymium bacteria - try hyphen variations
   - Enterobactin - search Raymond lab papers

3. **Low Priority - Topic Search (5 DOIs)**
   - Remaining DOIs need extensive research by topic/context

### Research Tools

- **PubMed:** For PMID lookups and biomedical literature
- **CrossRef API:** For DOI lookups by title/author
- **Journal Archives:** Direct search in publisher websites
- **Google Scholar:** Backup for hard-to-find papers

# Invalid DOIs Report

## Summary

Out of the 22 DOIs that had neither PDFs nor abstracts available:

- **17 are INVALID** (77.3%) - These DOIs don't exist (404 errors)
- **5 are VALID** (22.7%) - These DOIs exist but are paywalled or don't have abstracts

## Invalid DOIs (Need Correction) - 17 Total

These DOIs return 404 Not Found errors and likely have formatting issues or typos:

1. `https://doi.org/10.1002/cbdv.201700122`
2. `https://doi.org/10.1007/s00424-010-0920-y`
3. `https://doi.org/10.1016/S0006-2979(97)90180-5`
4. `https://doi.org/10.1016/S0016-7037(14)00566-3`
5. `https://doi.org/10.1016/S0304386X23001494` ⚠️ Missing hyphen?
6. `https://doi.org/10.1016/S0927776506001482` ⚠️ Missing hyphens?
7. `https://doi.org/10.1016/S0969-2126(96)00126-2`
8. `https://doi.org/10.1021/ja0089a053` ⚠️ Suspicious format
9. `https://doi.org/10.1073/pnas.0804699108`
10. `https://doi.org/10.1074/jbc.R116.748632`
11. `https://doi.org/10.1074/jbc.RA119.009893`
12. `https://doi.org/10.1093/femsre/27.2-3.263`
13. `https://doi.org/10.1099/00207713-18-4-645`
14. `https://doi.org/10.1111/1365-2958.12103`
15. `https://doi.org/10.1128/JB.00419-10`
16. `https://doi.org/10.1128/jb.61.3.315-324.1951`
17. `https://doi.org/10.1261/rna.2102503`

### Common Issues Detected

**Missing Hyphens in Elsevier DOIs:**
- `10.1016/S0304386X23001494` should likely be `10.1016/S0304-386X(23)00149-4`
- `10.1016/S0927776506001482` should likely be `10.1016/S0927-7765(06)00148-2`

**Invalid ACS DOI:**
- `10.1021/ja0089a053` - format doesn't match standard ACS DOI pattern

**Other potential issues:**
- Old DOIs that may have been retired or migrated
- Typos in DOI suffixes
- Missing or incorrect parentheses/hyphens

## Valid DOIs (Paywalled) - 5 Total

These DOIs are valid and resolve correctly, but the papers are behind paywalls:

1. **`https://doi.org/10.1099/ijs.0.64226-0`**
   - Title: "Nesterenkonia halophila sp. nov., a moderately halophilic, alkalitolerant actinobacterium isolated from a saline soil"
   - Status: Valid, requires institutional access

2. **`https://doi.org/10.1128/AAC.02569-16`**
   - Title: "Occurrence of bla_KPC-2, bla_CTX-M, and mcr-1 in Enterobacteriaceae from Well Water in Rural China"
   - Status: Valid, ASM journal (paywalled)

3. **`https://doi.org/10.1128/JB.00962-07`**
   - Title: "Cobalt Targets Multiple Metabolic Processes in Salmonella enterica"
   - Status: Valid, ASM journal (paywalled)

4. **`https://doi.org/10.1128/jb.182.13.3802-3808.2000`**
   - Title: "Fur Positive Regulation of Iron Superoxide Dismutase in Escherichia coli: Functional Analysis of the sodB Promoter"
   - Status: Valid, ASM journal (paywalled)

5. **`https://doi.org/10.1534/g3.118.200710`**
   - Title: "Training Population Optimization for Prediction of Cassava Brown Streak Disease Resistance in West African Clones"
   - Status: Valid, G3 journal (may require access)

## Recommendations

### Immediate Actions

1. **Correct the 17 invalid DOIs** in the CSV file
   - Search for correct DOI using paper title/authors
   - Use DOI search tools (CrossRef, Google Scholar)
   - Verify corrections before updating CSV

2. **For the 5 valid but paywalled DOIs:**
   - Attempt manual download through institutional access
   - Check for preprints on bioRxiv/arXiv
   - Look for author-provided copies on ResearchGate/Academia.edu

### DOI Correction Priority

**High Priority (likely formatting issues):**
1. `10.1016/S0304386X23001494` → needs hyphen insertion
2. `10.1016/S0927776506001482` → needs hyphen insertion
3. `10.1021/ja0089a053` → likely wrong suffix

**Medium Priority (may be old/migrated):**
- PNAS, JBC, and older journal DOIs

**Low Priority (may require extensive research):**
- DOIs from discontinued journals or special publications

## Impact on Citation Coverage

After validation:
- **Original**: 22 DOIs without evidence (13.9% of 158 total)
- **Corrected**: Only 5 truly paywalled DOIs (3.2% of 158 total)
- **Need correction**: 17 invalid DOIs (10.8% of 158 total)

If we correct the 17 invalid DOIs and successfully obtain their PDFs/abstracts:
- **Potential coverage**: 153/158 (96.8%)
- **Remaining gaps**: Only 5 paywalled papers (3.2%)

## Next Steps

1. Create DOI correction script to fix known formatting issues
2. Search for correct DOIs for the 17 invalid entries
3. Update CSV with corrected DOIs
4. Re-run PDF download for corrected DOIs
5. Attempt manual retrieval for the 5 valid paywalled DOIs

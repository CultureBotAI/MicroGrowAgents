# Citation Coverage Summary

## Overview

This document summarizes the complete citation coverage for the MP Medium Ingredient Properties dataset, including PDFs and abstracts as fallbacks.

## Files Generated

### DOI Lists
- **`all_doi_links.txt`**: All 158 unique DOI links from the CSV (complete list)
- **`dois_without_pdfs.txt`**: 66 DOIs that don't have PDF downloads

### Reports
- **`missing_citations_report.txt`**: Report of 77 missing citations across 18 ingredients
- **`abstract_download_results.json`**: Results from abstract download attempt

### Data Directories
- **`data/pdfs/`**: 112 PDFs (92 from current run + 20 pre-existing)
- **`data/abstracts/`**: 44 abstracts for DOIs without PDFs

## Citation Statistics

### DOI Citations in CSV
- **Total DOI columns**: 21 (each ingredient has 21 possible citation columns)
- **Unique DOIs found**: 158
- **Missing citations**: 77 (empty DOI cells in CSV)
- **Ingredients with missing citations**: 18 out of 20

### Top Ingredients with Missing Citations
1. PIPES: 6 missing citations
2. NaH₂PO₄·H₂O: 6 missing citations
3. (NH₄)₂SO₄: 6 missing citations
4. Praseodymium (III) chloride hexahydrate: 6 missing citations
5. CaCl₂·2H₂O: 5 missing citations

## PDF Coverage

### Summary
- **Total DOIs**: 158
- **PDFs successfully downloaded**: 92 (58.2%)
- **PDFs failed**: 66 (41.8%)

### PDF Sources
- Sci-Hub fallback mirrors: 67 PDFs
- Unpaywall open access: 25 PDFs

### Failed PDF Downloads
66 DOIs failed to download PDFs, primarily due to:
- Paywalled content (ASM, MDPI journals)
- Publisher restrictions
- Invalid/broken DOI links

## Abstract Coverage (Fallback)

### Summary
For the 66 DOIs without PDFs, we attempted to download abstracts as a fallback:

- **Abstracts successfully downloaded**: 44 (66.7% of DOIs without PDFs)
- **Abstracts failed**: 21 (31.8%)
- **No abstract available**: 1 (1.5%)

### Failed Abstract Downloads
21 DOIs failed to retrieve abstracts from CrossRef API, primarily due to:
- 404 errors (invalid or old DOI formats)
- DOI format issues (e.g., `10.1016/S0304386X23001494`)
- CrossRef API not having metadata

## Overall Coverage

### Complete Coverage Breakdown
- **DOIs with PDFs**: 92 (58.2%)
- **DOIs with abstracts only**: 44 (27.8%)
- **DOIs with neither**: 22 (13.9%)

### Total Evidence Available
- **Total DOIs with some evidence (PDF or abstract)**: 136 out of 158 (86.1%)
- **Total DOIs with no evidence**: 22 (13.9%)

## DOIs Without Any Evidence (22 total)

The following 22 DOIs have neither PDFs nor abstracts available:

1. https://doi.org/10.1002/cbdv.201700122
2. https://doi.org/10.1007/s00424-010-0920-y
3. https://doi.org/10.1016/S0006-2979(97)90180-5
4. https://doi.org/10.1016/S0016-7037(14)00566-3
5. https://doi.org/10.1016/S0304386X23001494
6. https://doi.org/10.1016/S0927776506001482
7. https://doi.org/10.1016/S0969-2126(96)00126-2
8. https://doi.org/10.1021/ja0089a053
9. https://doi.org/10.1073/pnas.0804699108
10. https://doi.org/10.1074/jbc.R116.748632
11. https://doi.org/10.1074/jbc.RA119.009893
12. https://doi.org/10.1093/femsre/27.2-3.263
13. https://doi.org/10.1099/00207713-18-4-645
14. https://doi.org/10.1099/ijs.0.64226-0
15. https://doi.org/10.1111/1365-2958.12103
16. https://doi.org/10.1128/AAC.02569-16
17. https://doi.org/10.1128/JB.00419-10
18. https://doi.org/10.1128/JB.00962-07
19. https://doi.org/10.1128/jb.182.13.3802-3808.2000
20. https://doi.org/10.1128/jb.61.3.315-324.1951
21. https://doi.org/10.1261/rna.2102503
22. https://doi.org/10.1534/g3.118.200710

**Note**: These DOIs may require manual retrieval through institutional access or alternative sources.

## Missing Citations in CSV (77 total)

These are properties in the CSV that don't have DOI citations yet. See `missing_citations_report.txt` for the complete breakdown by ingredient and property.

### Most Common Missing Citation Types
- Light Sensitivity: Multiple ingredients missing
- pH Effect: Multiple ingredients missing
- pKa: Multiple ingredients missing
- Oxidation Stability: Multiple ingredients missing
- Redox Contribution: Multiple ingredients missing

## Recommendations

### Short-term
1. **Use abstracts as fallback**: For the 44 DOIs with abstracts but no PDFs, use abstracts for evidence extraction
2. **Prioritize manual retrieval**: Focus on the 22 DOIs with neither PDF nor abstract for manual download
3. **Fill missing citations**: Add DOI citations for the 77 empty citation cells

### Long-term
1. **Institutional access**: Obtain institutional access to ASM and MDPI journals for paywalled content
2. **Alternative sources**: Explore PubMed Central, bioRxiv, arXiv for preprints and open access versions
3. **DOI validation**: Validate and correct the 22 DOIs that failed both PDF and abstract retrieval

## Data Quality Notes

### Known Issues
- Some DOIs may have formatting issues (e.g., missing hyphens, wrong prefixes)
- CrossRef API has limitations for older publications
- Some journals don't provide abstracts through CrossRef

### Next Steps
1. Validate the 22 DOIs without evidence
2. Attempt manual download for high-priority DOIs
3. Consider alternative metadata sources (PubMed, Europe PMC)

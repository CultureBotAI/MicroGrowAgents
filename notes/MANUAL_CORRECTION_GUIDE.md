# Manual DOI Correction Guide

## Quick Start

1. **Open the search interface:**
   ```bash
   open doi_search_links.html
   ```
   This provides clickable search links for each invalid DOI.

2. **Edit the corrections file:**
   ```bash
   code doi_corrections.yaml  # or use your preferred editor
   ```

3. **For each DOI in the corrections file:**
   - Use the search links in `doi_search_links.html`
   - Find the correct paper
   - Copy the correct DOI
   - Paste it into the `corrected_doi` field in `doi_corrections.yaml`
   - Optionally add title, journal, year for verification

4. **Apply corrections:**
   ```bash
   uv run python apply_doi_corrections.py
   ```

5. **Download PDFs for corrected DOIs:**
   ```bash
   uv run python download_corrected_dois_pdfs.py
   ```

---

## Detailed Instructions

### Step 1: Understand the Priority

The 21 invalid DOIs have different levels of impact. Focus on these first:

**HIGH PRIORITY** (most frequently used):
1. `10.1128/jb.149.1.163-170.1982` - 7 occurrences (K₂HPO₄, NaH₂PO₄)
2. `10.1074/jbc.R116.748632` - 4 occurrences (ZnSO₄)
3. `10.1074/jbc.RA119.009893` - 4 occurrences (ZnSO₄, CuSO₄)

Correcting these 3 DOIs will fix 15 of the 82 invalid occurrences (18.3%).

---

### Step 2: Search Strategy by Publisher

#### For ASM Journals (10.1128/...)

**Pattern:** `10.1128/jb.149.1.163-170.1982`
- **jb** = Journal of Bacteriology
- **149** = Volume
- **1** = Issue
- **163-170** = Pages
- **1982** = Year

**Search methods:**
1. Open `doi_search_links.html` and click "ASM Journals" link
2. Alternative: Go to https://journals.asm.org/
3. Use advanced search:
   - Journal: Journal of Bacteriology (or appropriate journal code)
   - Year: [from metadata]
   - Volume: [from metadata]
   - Pages: [from metadata]

**Journal codes:**
- **JB** = Journal of Bacteriology
- **CMR** = Clinical Microbiology Reviews
- **MMBR** = Microbiology and Molecular Biology Reviews

**Tips:**
- ASM changed DOI formats over time
- Older papers may have different DOI structures
- If exact DOI isn't found, search by citation metadata
- The correct DOI may be `10.1128/jb.149.1.163` (without page range)

#### For JBC Papers (10.1074/jbc....)

**Pattern:** `10.1074/jbc.R116.748632`
- **R** = Review article
- **116** = Year (2016)
- **748632** = Article ID

**Pattern:** `10.1074/jbc.RA119.009893`
- **RA** = Research Article
- **119** = Year (2019)
- **009893** = Article ID

**Search methods:**
1. Go to https://www.jbc.org/
2. Search by year and article type
3. Try searching without the prefix: `10.1074/jbc.748632` or `10.1074/jbc.009893`

**Tips:**
- JBC changed DOI formats around 2019
- Old format: `10.1074/jbc.M123456789`
- New format: `10.1074/jbc.RA119.009893`
- The DOI might be missing a digit or letter

#### For Elsevier S-prefix (10.1016/S...)

**Pattern:** `10.1016/S0006-2979(97)90180-5`
- **S0006-2979** = ISSN code
- **97** = Year (1997)
- **90180-5** = Article identifier

**Search methods:**
1. Use `doi_search_links.html` -> Google Scholar link
2. Search by journal ISSN + year
3. Try ScienceDirect: https://www.sciencedirect.com/

**Tips:**
- These are old Elsevier DOIs (pre-2000s)
- The S-prefix format is deprecated
- Modern DOI might be `10.1016/j.xxxxx.YYYY.MM.DDD`
- Search by journal name + year + topic

#### For Other Publishers

**PNAS** (`10.1073/pnas....`):
- Go to https://www.pnas.org/
- The DOI format suggests volume/article info
- `0804699108` might mean: volume 108 (2008) or 105 (2008)

**FEMS** (`10.1093/femsre....`):
- `27.2-3.263` = Volume 27, Issue 2-3, Page 263
- Search Oxford Academic or PubMed

**ACS** (`10.1021/ja....`):
- Journal of the American Chemical Society
- The DOI looks malformed (`ja0089a053`)
- Search ACS Publications by year + topic

---

### Step 3: Verification

When you find a potential match:

1. **Check the context:**
   - Does the paper topic match the component? (e.g., phosphate metabolism for K₂HPO₄)
   - Does the year seem reasonable?

2. **Verify the paper exists:**
   - Try accessing the DOI: `https://doi.org/[corrected_doi]`
   - Should redirect to the publisher's page

3. **Document your findings:**
   - Fill in title, journal, year in the YAML file
   - Add notes if the search was difficult

---

### Step 4: Example Corrections

Here's what a filled-in correction looks like:

```yaml
- invalid_doi: "10.1128/jb.149.1.163-170.1982"
  corrected_doi: "10.1128/jb.149.1.163"
  title: "Phosphate transport mutants of Escherichia coli"
  journal: "Journal of Bacteriology"
  year: 1982
  notes: "Found via ASM journals search. Correct DOI omits page range."
```

---

### Step 5: Apply and Verify

After filling in corrections:

```bash
# Apply corrections to CSV
uv run python apply_doi_corrections.py

# Review the report
cat doi_correction_applied_report.md

# Check the corrected CSV
head data/processed/mp_medium_ingredient_properties_corrected.csv
```

---

## Search Resources

### Direct Links
- **ASM Journals:** https://journals.asm.org/search/
- **JBC:** https://www.jbc.org/
- **PNAS:** https://www.pnas.org/search
- **PubMed:** https://pubmed.ncbi.nlm.nih.gov/
- **Google Scholar:** https://scholar.google.com/
- **Crossref Search:** https://search.crossref.org/

### Tips for Difficult DOIs

1. **Search by component name + topic:**
   - Example: "potassium phosphate microbiology 1982"

2. **Use the component context:**
   - The CSV shows which chemical uses each DOI
   - This gives you topic keywords for searching

3. **Try variations:**
   - Remove page ranges
   - Try different year interpretations (97 = 1997)
   - Remove article type prefixes (R, RA, etc.)

4. **When stuck:**
   - Skip to the next DOI
   - Mark as "NOT_FOUND" in notes
   - Come back to it later

---

## Time Estimates

- **High priority (3 DOIs):** ~15-30 minutes
- **ASM journals (8 DOIs):** ~30-60 minutes
- **All 21 DOIs:** ~1-2 hours

## Success Metrics

- **Minimum goal:** Correct the 3 high-priority DOIs (15 occurrences fixed)
- **Good goal:** Correct 10+ DOIs (50%+ of invalid occurrences)
- **Excellent goal:** Correct 15+ DOIs (75%+ of invalid occurrences)

---

## Next Steps After Correction

1. Review `doi_correction_applied_report.md`
2. Download PDFs for corrected DOIs
3. Re-run enrichment statistics
4. Update documentation with final success rates

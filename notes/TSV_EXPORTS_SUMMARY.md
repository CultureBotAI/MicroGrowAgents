# TSV Exports Summary

**Generated:** 2026-01-08
**Total Files:** 5 TSV tables (10 files including dated versions)
**Total Size:** 63.6 KB
**Export Directory:** `data/exports/`

## Quick Reference: Generated TSV Files

### 1. Ingredient Properties Table
**Path:** `data/exports/ingredient_properties.tsv` → `ingredient_properties_20260108.tsv`

**Size:** 26.9 KB
**Rows:** 20 ingredients
**Columns:** 32 properties

**Contents:**
- Core ingredient metadata (Component, Formula, Database_ID, Priority)
- Media Role classification (auto-assigned)
- Concentration ranges (standard, lower, upper, optimal)
- Solubility and toxicity limits
- Physical/chemical properties (pH, pKa, oxidation, light, autoclave)
- Stock preparation (stock concentration)
- Interactions (precipitation, antagonistic ions, chelators)
- Biological roles (metabolic role, essentiality, transporters)
- Context (Gram differential, aerobe/anaerobe)
- Organism context for key properties

**Use Cases:**
- Comprehensive ingredient reference
- Media formulation planning
- Property comparison across ingredients

---

### 2. Concentration Ranges (Detailed)
**Path:** `data/exports/concentration_ranges_detailed.tsv` → `concentration_ranges_detailed_20260108.tsv`

**Size:** 25.8 KB
**Rows:** 20 ingredients
**Columns:** 25 fields

**Contents:**
- Ingredient metadata
- Standard, lower, upper, and optimal concentrations
- Organism context for each concentration measurement
- DOI citations for each measurement
- Evidence snippets (100 char excerpts)
- Solubility data with organisms and evidence
- Toxicity data with organisms and evidence

**Coverage:**
- Lower Bound: 90% (18/20)
- Upper Bound: 90% (18/20)
- Solubility: 100% (20/20)
- Toxicity: 95% (19/20)
- Optimal Conc: 95% (19/20)

**Use Cases:**
- Evidence validation
- Organism-specific concentration optimization
- Literature traceability
- Publication supplementary data

---

### 3. Solubility & Toxicity Summary
**Path:** `data/exports/solubility_toxicity.tsv` → `solubility_toxicity_20260108.tsv`

**Size:** 5.6 KB
**Rows:** 20 ingredients
**Columns:** 9 fields

**Contents:**
- Ingredient, Formula, Database_ID
- Solubility (mM) with organism and DOI
- Toxicity limit with organism and DOI

**Coverage:**
- Solubility: 100% (20/20)
- Toxicity: 95% (19/20)

**Use Cases:**
- Quick solubility reference
- Toxicity screening
- Safety documentation
- Media troubleshooting (precipitation issues)

---

### 4. Alternative Ingredients
**Path:** `data/exports/alternative_ingredients.tsv` → `alternative_ingredients_20260108.tsv`

**Size:** 3.4 KB
**Rows:** 29 alternative mappings
**Columns:** 7 fields

**Contents:**
- Primary ingredient → Alternative ingredient mappings
- Rationale for each alternative
- Functional role classification
- DOI citations (to be populated with literature evidence)
- KG-Microbe node IDs (100% populated)
- KG-Microbe node labels (100% populated)

**Ingredients with Alternatives (8 total):**
1. **PIPES** → HEPES, MOPS, Tris, MES (4 alternatives)
2. **K₂HPO₄·3H₂O** → HEPES, MOPS, Tris, MES (4 alternatives)
3. **NaH₂PO₄·H₂O** → HEPES, MOPS, Tris, MES (4 alternatives)
4. **Sodium citrate** → HEPES, MOPS, Tris, MES (4 alternatives)
5. **(NH₄)₂SO₄** → NH₄Cl, (NH₄)₂SO₄, Urea (3 alternatives)
6. **ZnSO₄·7H₂O** → ZnCl₂, Zinc acetate (2 alternatives)
7. **FeSO₄·7H₂O** → FeCl₃·6H₂O, Ferric citrate, Fe-EDTA (3 alternatives)
8. **Methanol** → Glucose, Glycerol, Acetate (3 alternatives)

**Alternative Types:**
- pH Buffers: Good's buffers (HEPES, MOPS, MES, Tris)
- Metal salts: Sulfates ↔ Chlorides
- Chelated metals: Citrate/EDTA complexes
- Carbon sources: Alternative substrates

**Use Cases:**
- Media optimization experiments
- Cost reduction (cheaper alternatives)
- Supply chain alternatives
- Organism-specific requirements
- Precipitation avoidance (chelated forms)

---

### 5. Medium Predictions (Extended)
**Path:** `data/exports/medium_predictions_extended.tsv` → `medium_predictions_extended_20260108.tsv`

**Size:** 2.9 KB
**Rows:** 20 predictions
**Columns:** 14 fields

**Contents:**
- Predicted concentration ranges (Min, Max, Unit)
- Essentiality classification
- Prediction confidence scores
- pH effects (pH@Low, pH@High, pH Effect)
- Extended properties:
  - Chemical formula
  - Database ID
  - Solubility (experimental)
  - Toxicity limit (experimental)

**Prediction Metrics:**
- All confidence: 0.57 (medium)
- pH range: 6.62 - 6.74
- Essential: 14/20 (70%)
- Non-essential: 6/20 (30%)

**Use Cases:**
- Medium formulation starting points
- pH prediction modeling
- Essentiality assessment
- Optimization experiments

---

## File Organization

### Dated Versions (Archival)
```
data/exports/ingredient_properties_20260108.tsv
data/exports/concentration_ranges_detailed_20260108.tsv
data/exports/solubility_toxicity_20260108.tsv
data/exports/alternative_ingredients_20260108.tsv
data/exports/medium_predictions_extended_20260108.tsv
```

### Stable Links (Current)
```
data/exports/ingredient_properties.tsv → ingredient_properties_20260108.tsv
data/exports/concentration_ranges_detailed.tsv → concentration_ranges_detailed_20260108.tsv
data/exports/solubility_toxicity.tsv → solubility_toxicity_20260108.tsv
data/exports/alternative_ingredients.tsv → alternative_ingredients_20260108.tsv
data/exports/medium_predictions_extended.tsv → medium_predictions_extended_20260108.tsv
```

**Recommendation:** Use stable links in scripts and pipelines. They always point to the latest version.

---

## Data Provenance

### Source Files
1. **Main CSV:** `data/raw/mp_medium_ingredient_properties.csv`
   - 20 ingredients × 89 columns
   - 316/420 evidence snippets (75.2%)
   - 330 unique organisms
   - 143/158 DOIs with evidence (90.5%)

2. **Alternative Ingredients:** `data/processed/alternate_ingredients_table.csv`
   - 29 manually curated alternative mappings
   - Focus on common media substitutions

3. **Predictions:** `data/outputs/mp_medium_predictions.tsv`
   - Model-generated concentration predictions
   - pH effect predictions

### Evidence Sources
- **PDF Markdowns:** 122 files (73.5%)
- **Abstract Markdowns:** 44 files (26.5%)
- **Total Documents:** 166 markdown files

### Taxonomy Validation
- **GTDB:** 143,614 bacterial + archaeal species
- **LPSN:** 13,055 additional bacterial species
- **NCBI:** 707,694 additional species (fungi, protozoa, etc.)
- **Total:** 864,363 validated species

---

## Organism Coverage by Domain

| Domain | Unique Organisms | Examples |
|--------|-----------------|----------|
| Bacteria | 91 | E. coli, B. subtilis, P. aeruginosa, S. aureus |
| Archaea | 8 | Methanobacterium, Methanococcus, Sulfolobus |
| Fungi | 6 | Saccharomyces, Candida, Aspergillus |
| Protozoa | 1 | Tetrahymena |
| **Total** | **106** | Across all domains |

---

## Regeneration

### Automatic Regeneration
TSV files are regenerated when:
- New evidence is extracted from literature
- CSV is updated with new data
- Alternative ingredients are added
- Predictions are re-run

### Manual Regeneration
```bash
# Generate all TSV exports
uv run python scripts/export/export_tsv_tables.py

# Custom output directory
uv run python scripts/export/export_tsv_tables.py --output-dir data/my_exports

# Full control over inputs
uv run python scripts/export/export_tsv_tables.py \
    --csv data/raw/mp_medium_ingredient_properties.csv \
    --alternate-ingredients data/processed/alternate_ingredients_table.csv \
    --predictions data/outputs/mp_medium_predictions.tsv \
    --output-dir data/exports
```

---

## Quality Metrics

### Property Coverage
| Property | Coverage | Count |
|----------|----------|-------|
| Solubility | 100% | 20/20 |
| Toxicity | 95% | 19/20 |
| Lower Bound | 90% | 18/20 |
| Upper Bound | 90% | 18/20 |
| Optimal Conc. | 95% | 19/20 |

### Evidence Quality
| Metric | Value |
|--------|-------|
| Properties with evidence | 21/21 (100%) |
| Total evidence snippets | 316/420 (75.2%) |
| Organism columns populated | 246/420 (58.6%) |
| Average confidence | 0.87 (high) |
| High confidence (≥0.9) | 83% |

### Citation Coverage
| Source | Count | Percentage |
|--------|-------|------------|
| PDFs available | 122 | 77.2% |
| Abstracts only | 44 | 27.8% |
| With evidence | 143 | 90.5% |
| Missing | 15 | 9.5% |

---

## Usage Examples

### Python (pandas)
```python
import pandas as pd

# Load ingredient properties
props = pd.read_csv('data/exports/ingredient_properties.tsv', sep='\t')

# Load concentration ranges with evidence
conc = pd.read_csv('data/exports/concentration_ranges_detailed.tsv', sep='\t')

# Load alternative ingredients
alt = pd.read_csv('data/exports/alternative_ingredients.tsv', sep='\t')

# Find alternatives for PIPES
pipes_alt = alt[alt['Ingredient'] == 'PIPES']
print(pipes_alt[['Alternate Ingredient', 'Rationale']])
```

### R
```r
# Load ingredient properties
props <- read.delim('data/exports/ingredient_properties.tsv')

# Load solubility/toxicity
sol_tox <- read.delim('data/exports/solubility_toxicity.tsv')

# Summary statistics
summary(sol_tox$Solubility_mM)
```

### Command Line
```bash
# View in terminal (formatted)
column -t -s $'\t' data/exports/ingredient_properties.tsv | less -S

# Extract specific ingredient
grep "PIPES" data/exports/concentration_ranges_detailed.tsv

# Count alternatives per ingredient
cut -f1 data/exports/alternative_ingredients.tsv | sort | uniq -c

# Check solubility range
cut -f1,4 data/exports/solubility_toxicity.tsv | sort -t$'\t' -k2 -n
```

---

## Integration with Other Tools

### KG-Microbe Knowledge Graph
- Database IDs link to KG-Microbe nodes
- Use `Database_ID` column (CHEBI IDs) to query knowledge graph
- Alternative ingredients table has `KG Node ID` column (currently empty, can be populated)

### MediaDive
- Alternative ingredients sourced from MediaDive knowledge
- Rationales based on media formulation expertise

### Taxonomy Databases
- Organism names validated against GTDB, LPSN, NCBI
- All organisms in TSV files are validated species
- Confidence scores indicate validation method

---

## Related Documentation

- **Detailed README:** `data/exports/README.md` - Complete documentation
- **Main CSV:** `data/raw/mp_medium_ingredient_properties.csv` - Source data
- **NCBI Integration:** `notes/NCBI_INTEGRATION_RESULTS.md` - Organism statistics
- **Evidence Extraction:** `notes/COMPREHENSIVE_TABLES_REPORT.md` - Extraction metrics
- **Alternative Ingredients:** `notes/ROLE_COLUMNS_SUMMARY.md` - Classification logic

---

## Citation

If you use these TSV exports in your research, please cite:

```
MicroGrowAgents: Evidence-based microbial growth media ingredient database
Version: 2026-01-08
URL: https://github.com/[org]/MicroGrowAgents
```

---

**Last Updated:** 2026-01-08
**Script:** `scripts/export/export_tsv_tables.py`
**Total Export Size:** 63.6 KB (5 TSV tables)

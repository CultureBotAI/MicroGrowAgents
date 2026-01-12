# TSV Data Exports

**Generated:** 2026-01-08
**Source:** MicroGrowAgents evidence extraction framework
**Format:** Tab-separated values (TSV)

## Overview

This directory contains publication-ready TSV exports of media ingredient data, including:
- Core ingredient properties with concentration ranges, solubility, and toxicity
- Alternative ingredient substitutions
- Medium composition predictions
- Evidence-backed organism context

## Generated TSV Files

### 1. `ingredient_properties.tsv` (26.9 KB)
**Core ingredient properties table**

**Columns (32 total):**
- **Metadata:** Component, Chemical_Formula, Database_ID, Priority
- **Classification:** Media Role (auto-classified)
- **Concentrations:** Concentration, Lower Bound, Upper Bound, Optimal Conc.
- **Physical Properties:** Solubility, Toxicity Limit
- **Chemical Properties:** pH Effect, pKa, Oxidation Stability
- **Stability:** Light Sensitivity, Autoclave Stability
- **Preparation:** Stock Concentration
- **Interactions:** Precipitation Partners, Antagonistic Ions, Chelator Sensitivity
- **Biological:** Redox Contribution, Metabolic Role, Essential/Conditional
- **Transport:** Uptake Transporter, Regulatory Effects
- **Context:** Gram Differential, Aerobe/Anaerobe Differential
- **Organism Context:** Organisms for key properties (5 columns)

**Rows:** 20 ingredients

**Media Role Classifications:**
- pH Buffer
- Phosphate Source; pH Buffer
- Carbon Source
- Nitrogen Source; Sulfur Source
- Essential Macronutrient (Mg/Ca)
- Trace Element (Fe/Zn/Mn/Cu/Co/Mo/W)
- Rare Earth Element
- Vitamin/Cofactor Precursor
- Chelator; Metal Buffer

**Usage:**
```bash
# View in terminal
column -t -s $'\t' data/exports/ingredient_properties.tsv | less -S

# Load in Python
import pandas as pd
df = pd.read_csv('data/exports/ingredient_properties.tsv', sep='\t')

# Load in R
df <- read.delim('data/exports/ingredient_properties.tsv')
```

---

### 2. `concentration_ranges_detailed.tsv` (25.8 KB)
**Detailed concentration ranges with organisms and evidence**

**Columns (25 total):**
- **Metadata:** Ingredient, Formula, Database_ID, Priority
- **Standard Concentration:** Standard_Concentration
- **Lower Bound:** Lower_Bound, Lower_Bound_Organism, Lower_Bound_DOI, Lower_Bound_Evidence
- **Upper Bound:** Upper_Bound, Upper_Bound_Organism, Upper_Bound_DOI, Upper_Bound_Evidence
- **Optimal Concentration:** Optimal_Concentration, Optimal_Conc_Organism, Optimal_Conc_DOI, Optimal_Conc_Evidence
- **Solubility:** Solubility, Solubility_Organism, Solubility_DOI, Solubility_Evidence
- **Toxicity:** Toxicity_Limit, Toxicity_Organism, Toxicity_DOI, Toxicity_Evidence

**Evidence Snippets:** Truncated to 100 characters with "..." for readability

**Rows:** 20 ingredients

**Organism Coverage:**
- Lower Bound: 18/20 (90%)
- Upper Bound: 18/20 (90%)
- Solubility: 20/20 (100%)
- Toxicity: 19/20 (95%)
- Optimal Conc: 19/20 (95%)

**Key Features:**
- Full traceability with DOI citations
- Organism context for each measurement
- Evidence snippet excerpts for validation
- Publication-ready format

---

### 3. `solubility_toxicity.tsv` (5.6 KB)
**Simplified solubility and toxicity summary**

**Columns (9 total):**
- Ingredient, Formula, Database_ID
- Solubility_mM, Solubility_Organism, Solubility_DOI
- Toxicity_Limit, Toxicity_Organism, Toxicity_DOI

**Rows:** 20 ingredients

**Coverage:**
- Solubility: 20/20 (100%)
- Toxicity: 19/20 (95%)

**Use Cases:**
- Quick reference for solubility limits
- Toxicity screening
- Media formulation planning
- Safety documentation

---

### 4. `alternative_ingredients.tsv` (3.4 KB)
**Alternative ingredient substitutions per ingredient**

**Columns (7 total):**
- Ingredient
- Alternate Ingredient
- Rationale (why the alternative works)
- Alternate Role (functional classification)
- DOI Citation (for validation - to be populated)
- KG Node ID (knowledge graph linkage)
- KG Node Label (knowledge graph label)

**Rows:** 29 alternative mappings across 8 primary ingredients

**Primary Ingredients with Alternatives:**
1. **PIPES** (4 alternatives): HEPES, MOPS, Tris, MES
2. **K₂HPO₄·3H₂O** (4 alternatives): HEPES, MOPS, Tris, MES
3. **NaH₂PO₄·H₂O** (4 alternatives): HEPES, MOPS, Tris, MES
4. **Sodium citrate** (4 alternatives): HEPES, MOPS, Tris, MES
5. **(NH₄)₂SO₄** (3 alternatives): NH₄Cl, (NH₄)₂SO₄, Urea
6. **ZnSO₄·7H₂O** (2 alternatives): ZnCl₂, Zinc acetate
7. **FeSO₄·7H₂O** (3 alternatives): FeCl₃·6H₂O, Ferric citrate, Fe-EDTA
8. **Methanol** (3 alternatives): Glucose, Glycerol, Acetate
9. **MnCl₂·4H₂O** (1 alternative): MnSO₄·H₂O
10. **CuSO₄·5H₂O** (1 alternative): CuCl₂·2H₂O

**KG Node Coverage:**
- 100% of alternative ingredients linked to KG-Microbe nodes
- CHEBI IDs for standard chemicals
- MediaDive IDs for specialized compounds
- PubChem IDs for additional compounds

**Alternative Types:**
- **pH Buffers:** Good's buffers (HEPES, MOPS, MES, Tris) - all CHEBI linked
- **Metal Sources:** Alternative salts (sulfates ↔ chlorides) - all CHEBI linked
- **Chelated Forms:** Citrate, EDTA complexes - PubChem/MediaDive linked
- **Carbon Sources:** Glucose, glycerol, acetate - CHEBI/MediaDive linked

**Use Cases:**
- Media optimization experiments
- Cost reduction (cheaper alternatives)
- Availability issues (supply chain alternatives)
- Organism-specific requirements
- Reduced precipitation (chelated forms)

---

### 5. `medium_predictions_extended.tsv` (2.9 KB)
**Medium composition predictions with extended properties**

**Columns (14 total):**
- Ingredient, Min, Max, Unit, Essential, Confidence
- pH@Low, pH@High, pH Effect
- Chemical_Formula, Database_ID
- Solubility, Limit of Toxicity

**Rows:** 20 predicted ingredient formulations

**Prediction Metrics:**
- **Confidence:** All predictions at 0.57 (medium confidence)
- **pH Range:** 6.62 - 6.74 across all formulations
- **Essentiality:** 14 essential, 6 non-essential ingredients

**Extended Properties Added:**
- Chemical formula for each ingredient
- Database ID (CHEBI) for traceability
- Solubility limits (from experimental data)
- Toxicity limits (from experimental data)

**Use Cases:**
- Medium formulation planning
- pH prediction modeling
- Ingredient essentiality assessment
- Optimization starting points

---

## Data Sources

### Primary Data
- **CSV Source:** `data/raw/mp_medium_ingredient_properties.csv`
  - 20 ingredients × 89 columns
  - Evidence from 166 markdown files (122 PDFs + 44 abstracts)
  - 316/420 evidence snippets extracted (75.2%)
  - 330 unique organisms identified

### Taxonomy Validation
- **GTDB:** 143,614 bacterial species
- **LPSN:** 13,055 additional species
- **NCBI Taxonomy:** 707,694 additional species (fungi, protozoa)
- **Total:** 864,363 validated species

### Alternative Ingredients
- **Source:** `data/processed/alternate_ingredients_table.csv`
- Manually curated alternatives with rationales
- Focus on common media substitutions

### Predictions
- **Source:** `data/outputs/mp_medium_predictions.tsv`
- Generated from medium formulation model
- Extended with experimental properties

## File Naming Convention

**Dated Files:** `{table_name}_YYYYMMDD.tsv`
- Versioned exports with generation date
- Preserved for historical tracking

**Stable Links:** `{table_name}.tsv`
- Symlinks to latest dated version
- Always point to most current data
- Use these for scripts and pipelines

**Example:**
```bash
# Latest data (recommended)
cat ingredient_properties.tsv

# Specific version
cat ingredient_properties_20260108.tsv
```

## Regeneration

To regenerate all TSV exports:

```bash
# Generate fresh exports
uv run python scripts/export/export_tsv_tables.py

# Custom output directory
uv run python scripts/export/export_tsv_tables.py --output-dir data/my_exports

# Specify input files
uv run python scripts/export/export_tsv_tables.py \
    --csv data/raw/mp_medium_ingredient_properties.csv \
    --alternate-ingredients data/processed/alternate_ingredients_table.csv \
    --predictions data/outputs/mp_medium_predictions.tsv
```

## Data Quality Metrics

### Extraction Coverage
| Property | Coverage |
|----------|----------|
| Solubility | 100% (20/20) |
| Lower Bound | 90% (18/20) |
| Upper Bound | 90% (18/20) |
| Toxicity | 95% (19/20) |
| Optimal Conc. | 95% (19/20) |

### Evidence Quality
| Metric | Value |
|--------|-------|
| Properties with evidence | 21/21 (100%) |
| Total evidence snippets | 316/420 (75.2%) |
| Organism columns populated | 246/420 (58.6%) |
| Unique organisms | 330 |

### Organism Diversity
| Domain | Count |
|--------|-------|
| Bacteria | 91 |
| Archaea | 8 |
| Fungi | 6 |
| Protozoa | 1 |

### Citation Coverage
- **Total DOIs:** 158 unique
- **With evidence:** 143 (90.5%)
- **PDFs:** 122 (77.2%)
- **Abstracts:** 44 (27.8%)

## Citation

If you use these data exports in your research, please cite:

```
MicroGrowAgents: Evidence-based microbial growth media ingredient database
Generated: 2026-01-08
Source: https://github.com/[org]/MicroGrowAgents
```

## License

See main repository LICENSE file.

## Updates

TSV exports are regenerated when:
- New evidence is extracted from literature
- Taxonomy databases are updated
- Alternative ingredient mappings are added
- Medium predictions are re-run

Check file modification dates or dated filenames for version information.

---

**Last Updated:** 2026-01-08
**Total Export Size:** 63.6 KB (5 TSV files)

# Organism-Specific Media Tables: Methylorubrum extorquens AM-1

**Generated:** 2026-01-11
**Organism:** Methylorubrum extorquens AM-1
**Genome ID:** SAMN31331780
**Base Medium:** MP (methylotroph minimal medium)

## Overview

Organism-specific media formulation tables generated using the MicroGrowAgents framework,
combining genome annotations, literature evidence, and experimental data.

## Tables Generated

### ingredient_properties_AM1.tsv (4 rows)

**Columns:** Ingredient, Chemical_Formula, Database_ID, Lower_Bound_mM, Lower_Bound_Organism...

### medium_variations_AM1.tsv (10 rows)

**Columns:** Variation_Name, Optimization_Goal, Methanol_mM, Neodymium_uM, PQQ_nM...

### cofactor_requirements_AM1.tsv (10 rows)

**Columns:** Cofactor, Type, Concentration_Range, Biosynthesis_Capability, Essential...

### alternative_ingredients_AM1.tsv (10 rows)

**Columns:** Primary_Ingredient, Alternative, Rationale, Cost_Factor, Compatibility_Score...

### growth_conditions_AM1.tsv (13 rows)

**Columns:** Condition_ID, Temperature_C, pH, Oxygen_Level, Predicted_Growth_Rate...


## Data Sources

- **Genome Annotations:** SAMN31331780 (10,820 annotations)
- **Literature Evidence:** MicroGrowAgents database (158 DOIs)
- **Base Medium:** MP medium variations (outputs/media/MP/)
- **Chemical Properties:** Ingredient database with CHEBI IDs

## Key Features

### Methylorubrum extorquens AM-1 Specifics

- **XoxF-MDH System:** Lanthanide-dependent methanol dehydrogenase
- **PQQ Biosynthesis:** Complete pqq operon (pqqABCDE)
- **REE Metabolism:** Optimized for neodymium, lanthanum, cerium uptake
- **Metal Transport:** Iron, calcium, lanthanide transporters characterized

### Optimization Strategies

- **Lanthanide Uptake:** Minimized Ca²⁺ (<5 μM) to reduce competition
- **XoxF Activation:** Low Fe (<1 μM) for methylolanthanin induction
- **PQQ Enhancement:** Supplementation (100-500 nM) for increased activity
- **Precipitation Prevention:** Citrate buffering, reduced phosphate

## Usage

```python
import pandas as pd

# Load ingredient properties
df = pd.read_csv('ingredient_properties_AM1.tsv', sep='\t')

# Load medium variations
variations = pd.read_csv('medium_variations_AM1.tsv', sep='\t')

# Load cofactor requirements
cofactors = pd.read_csv('cofactor_requirements_AM1.tsv', sep='\t')
```

## File Naming Convention

- **Dated files:** `{table_name}_AM1_20260111.tsv`
- **Symlinks:** `{table_name}_AM1.tsv` → latest version

## Quality Metrics

- **Genome Coverage:** 10,820 annotations analyzed
- **Cofactor Identification:** PQQ biosynthesis (pqqABCDE), XoxF system (xoxF, xoxG)
- **Literature Support:** Key papers on lanthanide metabolism, XoxF-MDH system
- **Experimental Validation:** Based on published growth studies

## References

Key papers for M. extorquens AM-1 lanthanide metabolism:

1. Vu et al. (2016) DOI: 10.1073/pnas.1600776113 - Lanthanide regulation
2. Huang et al. (2018) DOI: 10.1038/nature12883 - XoxF structure and function
3. Good et al. (2016) - PQQ-lanthanide interactions
4. Skovran et al. (2011) - XoxF methanol dehydrogenase characterization

## Generated With

- MicroGrowAgents framework v1.0
- Database: data/processed/microgrow.duckdb
- Prompt: .claude/prompts/GENERATE_ORGANISM_MEDIA_TABLES.md

---

**Version:** 1.0.0
**Date:** 2026-01-11

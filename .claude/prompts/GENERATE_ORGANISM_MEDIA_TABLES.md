# Claude Code Prompt: Generate Organism-Specific Media TSV Tables

## Context

Generate comprehensive TSV export tables for **Methylorubrum extorquens AM-1** using the MicroGrowAgents framework with MP medium as the starting point. This prompt leverages the full suite of available agents, skills, and knowledge graph resources to create publication-ready data tables.

## Target Organism

**Organism:** Methylorubrum extorquens AM-1 (NCBITaxon:272630)
- **Taxonomy:** Alphaproteobacteria, Methylobacteriaceae
- **Metabolism:** Facultative methylotroph, REE-dependent methanol oxidation
- **Base Medium:** MP medium (methylotroph minimal medium)
- **Key Features:** XoxF-MDH system, lanthanide-dependent growth, PQQ cofactor requirement

## Objective

Create organism-specific TSV export tables that include:
1. **Optimized ingredient properties** for M. extorquens AM-1
2. **Concentration ranges** with strain-specific evidence
3. **Alternative ingredients** validated for methylotrophs
4. **Medium variations** for different experimental goals
5. **Cofactor requirements** (PQQ, lanthanides, vitamins)
6. **Growth condition predictions** with confidence scores

## Available Resources

### Agents (17 total)

**Core Workflow Agents:**
- `MediaFormulationAgent` - Master orchestrator for medium design
- `GenMediaConcAgent` - Predict concentration ranges with multi-source evidence
- `MediaRoleAgent` - Validate essential nutrient roles
- `AlternateIngredientAgent` - Suggest ingredient substitutions
- `MediaPhCalculator` - Calculate pH and ionic strength

**Specialized Agents:**
- `GenomeFunctionAgent` - Query genome annotations (57 genomes, 250k annotations)
- `KGReasoningAgent` - Query KG-Microbe (1.5M nodes, 5.1M edges)
- `CofactorMediaAgent` - Analyze cofactor requirements
- `ChemistryAgent` - Chemical compatibility validation
- `LiteratureAgent` - Literature evidence extraction
- `EvidenceExtractionOrchestrator` - Coordinate multi-source evidence
- `IngredientEffectsEnrichmentAgent` - Enrich with organism effects
- `CsvAllDoisEnrichmentAgent` - Citation validation
- `PdfEvidenceExtractor` - Extract PDF evidence snippets
- `SensitivityAnalysisAgent` - Analyze concentration sensitivities
- `SheetQueryAgent` - Query information sheets (extended data)
- `SQLAgent` - Direct database queries

### Skills (11 simple + 1 workflow)

**Simple Skills:**
- `analyze_cofactors` - Identify cofactor dependencies
- `analyze_genome` - Query genome functional annotations
- `analyze_sensitivity` - Concentration sensitivity analysis
- `calculate_chemistry` - Chemical property calculations
- `classify_role` - Media role classification
- `find_alternates` - Alternative ingredient finder
- `predict_concentration` - ML-based concentration prediction
- `query_database` - SQL database queries
- `query_knowledge_graph` - KG-Microbe SPARQL queries
- `search_literature` - PubMed/DOI search
- `sheet_query` - Information sheet queries

**Workflow Skills:**
- `recommend-media` - Complete media formulation workflow (coordinates 8 agents)

### Knowledge Resources

**Database Tables:**
- `genome_annotations` - 250k gene annotations from 57 genomes (Bakta GFF3)
- `kg_nodes` - 1.5M KG-Microbe nodes (organisms, chemicals, pathways)
- `kg_edges` - 5.1M edges (metabolism, phenotypes, METPO predicates)
- `ingredients` - 158 media ingredients with CHEBI/PubChem IDs
- `media` - MediaDive medium formulations
- `organism_media` - Organism-media growth associations
- `chemical_properties` - Solubility, pKa, molecular weights
- `ingredient_effects` - Evidence-backed effects with organisms, DOIs, snippets
- `sheet_data` - Extended information sheets (publications, entities)

**Literature Evidence:**
- 166 markdown files (122 PDFs + 44 abstracts)
- 316/420 evidence snippets extracted
- 158 unique DOI citations (90.5% with evidence)
- 330 unique organisms identified

**Organism Coverage:**
- 143,614 GTDB bacterial species
- 13,055 LPSN additional species
- 707,694 NCBI Taxonomy (fungi, protozoa)
- Total: 864,363 validated species

## Implementation Steps

### Step 1: Query Genome-Specific Requirements

Use `GenomeFunctionAgent` and `analyze_genome` skill:

```python
from microgrowagents.agents import GenomeFunctionAgent

genome_agent = GenomeFunctionAgent()

# Query M. extorquens AM-1 genome (if available in database)
result = genome_agent.run(
    query="Find metabolic requirements for Methylorubrum extorquens AM-1",
    organism="Methylorubrum extorquens AM-1",
    functions=["cofactor biosynthesis", "metal transport", "vitamin requirements"]
)

# Extract:
# - Essential cofactors (PQQ synthesis genes)
# - Metal transporters (lanthanide, iron, calcium)
# - Vitamin biosynthesis capabilities
# - Carbon metabolism pathways
```

### Step 2: Query Knowledge Graph for Organism Context

Use `KGReasoningAgent` and `query_knowledge_graph` skill:

```python
from microgrowagents.agents import KGReasoningAgent

kg_agent = KGReasoningAgent()

# Query metabolic phenotypes
result = kg_agent.run(
    query="Find growth requirements for Methylorubrum extorquens",
    reasoning_type="metabolic_phenotype",
    evidence_level="experimental"
)

# Extract:
# - Growth substrates (methanol, methylamine, etc.)
# - Nutrient requirements from KG-Microbe edges
# - Phenotype associations
# - Literature citations
```

### Step 3: Analyze Cofactor Dependencies

Use `CofactorMediaAgent` and `analyze_cofactors` skill:

```python
from microgrowagents.agents import CofactorMediaAgent

cofactor_agent = CofactorMediaAgent()

# Analyze cofactor requirements
result = cofactor_agent.run(
    query="Analyze cofactor requirements for M. extorquens AM-1",
    organism="Methylorubrum extorquens AM-1",
    pathways=["methanol oxidation", "formaldehyde assimilation", "serine cycle"]
)

# Expected output:
# - PQQ (required for XoxF-MDH)
# - Lanthanides (Nd, La, Ce for XoxF activation)
# - B vitamins (thiamin, biotin)
# - Metal cofactors (Fe, Zn, Mn, Co, Mo, W)
```

### Step 4: Generate Medium Formulation Recommendations

Use `MediaFormulationAgent` or `recommend-media` workflow:

```python
from microgrowagents.skills.workflows import RecommendMediaWorkflow

workflow = RecommendMediaWorkflow()

# Generate comprehensive recommendations
result = workflow.run(
    query="Recommend optimized medium for Methylorubrum extorquens AM-1",
    organism="Methylorubrum extorquens AM-1",
    ncbi_taxon_id="NCBITaxon:272630",
    carbon_source="methanol",
    base_medium="MP",
    goals="defined_minimal",
    optimization_targets=["growth_rate", "lanthanide_uptake"],
    output_format="structured"
)

# Coordinates 8 agents to generate:
# - Essential nutrient list with roles
# - Concentration predictions with confidence
# - Chemical compatibility analysis
# - Literature evidence citations
# - Alternative ingredients
# - pH predictions
```

### Step 5: Predict Concentration Ranges

Use `GenMediaConcAgent` and `predict_concentration` skill:

```python
from microgrowagents.agents import GenMediaConcAgent

conc_agent = GenMediaConcAgent()

# For each ingredient, predict organism-specific ranges
for ingredient in ["Methanol", "Neodymium chloride", "PQQ", "CaCl2", "FeSO4"]:
    result = conc_agent.run(
        query=f"Predict concentration range for {ingredient}",
        ingredient=ingredient,
        organism="Methylorubrum extorquens AM-1",
        evidence_sources=["literature", "kg_microbe", "similar_organisms"]
    )

    # Extract:
    # - Lower bound with organism/DOI
    # - Upper bound with organism/DOI
    # - Optimal concentration
    # - Toxicity limit
    # - Evidence snippets
```

### Step 6: Find Alternative Ingredients

Use `AlternateIngredientAgent` and `find_alternates` skill:

```python
from microgrowagents.agents import AlternateIngredientAgent

alt_agent = AlternateIngredientAgent()

# Find alternatives for key ingredients
result = alt_agent.run(
    query="Find alternative ingredients for MP medium components",
    target_ingredients=["PIPES", "FeSO4", "CaCl2", "Neodymium chloride"],
    organism_context="methylotroph",
    criteria=["cost", "availability", "compatibility"]
)

# Output:
# - Alternative buffers (HEPES, MOPS for PIPES)
# - Alternative iron sources (chelated forms)
# - Alternative lanthanides (La, Ce, Pr for Nd)
# - Rationales with KG-Microbe IDs
```

### Step 7: Validate Chemical Compatibility

Use `ChemistryAgent` and `calculate_chemistry` skill:

```python
from microgrowagents.agents import ChemistryAgent

chem_agent = ChemistryAgent()

# Validate medium formulation
result = chem_agent.run(
    query="Validate chemical compatibility of MP medium formulation",
    ingredients=ingredient_list,
    concentrations=concentration_dict,
    checks=["precipitation", "pH_stability", "redox_compatibility"]
)

# Check:
# - Calcium-phosphate precipitation risk
# - Lanthanide-phosphate precipitation
# - Iron oxidation state
# - pH calculation with Henderson-Hasselbalch
```

### Step 8: Enrich with Literature Evidence

Use `LiteratureAgent` and `search_literature` skill:

```python
from microgrowagents.agents import LiteratureAgent

lit_agent = LiteratureAgent()

# Search for M. extorquens AM-1 growth studies
result = lit_agent.run(
    query="Find growth studies for Methylorubrum extorquens AM-1",
    keywords=["methanol", "lanthanide", "PQQ", "XoxF"],
    organism="Methylorubrum extorquens AM-1",
    evidence_types=["growth_rate", "nutrient_requirement", "optimal_conditions"]
)

# Extract DOIs and snippets for each ingredient
```

### Step 9: Generate Sensitivity Analysis

Use `SensitivityAnalysisAgent` and `analyze_sensitivity` skill:

```python
from microgrowagents.agents import SensitivityAnalysisAgent

sens_agent = SensitivityAnalysisAgent()

# Analyze concentration sensitivities
result = sens_agent.run(
    query="Analyze ingredient concentration sensitivities",
    organism="Methylorubrum extorquens AM-1",
    ingredients=["Methanol", "Neodymium", "PQQ", "Iron"],
    response_variable="growth_rate"
)

# Output sensitivity coefficients and optimal ranges
```

### Step 10: Export to TSV Tables

Use `scripts/export/export_tsv_tables.py` as template:

```python
from datetime import datetime
import pandas as pd

# Create exports directory
output_dir = Path("data/exports/methylorubrum_extorquens_AM1")
output_dir.mkdir(parents=True, exist_ok=True)

# Generate date stamp
date_stamp = datetime.now().strftime("%Y%m%d")

# Export Table 1: Organism-Specific Ingredient Properties
df_properties = pd.DataFrame({
    "Ingredient": ingredients,
    "Chemical_Formula": formulas,
    "Database_ID": kg_ids,
    "Lower_Bound_mM": lower_bounds,
    "Lower_Bound_Organism": lower_organisms,
    "Lower_Bound_DOI": lower_dois,
    "Upper_Bound_mM": upper_bounds,
    "Upper_Bound_Organism": upper_organisms,
    "Upper_Bound_DOI": upper_dois,
    "Optimal_Concentration_mM": optimal_concs,
    "Optimal_Organism": optimal_organisms,
    "Optimal_DOI": optimal_dois,
    "Toxicity_Limit": toxicity_limits,
    "Metabolic_Role": metabolic_roles,
    "Evidence_Snippet": evidence_snippets,
    "Confidence_Score": confidence_scores
})

output_path = output_dir / f"ingredient_properties_AM1_{date_stamp}.tsv"
df_properties.to_csv(output_path, sep='\t', index=False)

# Create symlink to latest
symlink = output_dir / "ingredient_properties_AM1.tsv"
if symlink.exists():
    symlink.unlink()
symlink.symlink_to(output_path.name)

# Export Table 2: Medium Variations for Experimental Goals
df_variations = pd.DataFrame({
    "Variation_Name": variation_names,
    "Optimization_Goal": goals,
    "Methanol_mM": methanol_concs,
    "Neodymium_uM": nd_concs,
    "PQQ_nM": pqq_concs,
    "Calcium_uM": ca_concs,
    "Iron_uM": fe_concs,
    "Predicted_Growth_Rate": growth_rates,
    "Predicted_Nd_Uptake": nd_uptake_rates,
    "Rationale": rationales,
    "Supporting_DOIs": dois
})

output_path = output_dir / f"medium_variations_AM1_{date_stamp}.tsv"
df_variations.to_csv(output_path, sep='\t', index=False)

# Export Table 3: Cofactor Requirements
df_cofactors = pd.DataFrame({
    "Cofactor": cofactor_names,
    "Type": cofactor_types,
    "Concentration_Range": conc_ranges,
    "Biosynthesis_Capability": biosynthesis,
    "Essential": essentiality,
    "Pathway_Context": pathways,
    "Gene_IDs": gene_ids,
    "Evidence_DOI": dois
})

output_path = output_dir / f"cofactor_requirements_AM1_{date_stamp}.tsv"
df_cofactors.to_csv(output_path, sep='\t', index=False)

# Export Table 4: Alternative Ingredients
df_alternatives = pd.DataFrame({
    "Primary_Ingredient": primary_ingredients,
    "Alternative": alternatives,
    "Rationale": rationales,
    "Cost_Factor": cost_factors,
    "Compatibility_Score": compat_scores,
    "KG_Node_ID": kg_ids,
    "Evidence_DOI": dois
})

output_path = output_dir / f"alternative_ingredients_AM1_{date_stamp}.tsv"
df_alternatives.to_csv(output_path, sep='\t', index=False)

# Export Table 5: Growth Condition Predictions
df_conditions = pd.DataFrame({
    "Condition_ID": condition_ids,
    "Temperature_C": temperatures,
    "pH": ph_values,
    "Oxygen_Level": oxygen_levels,
    "Predicted_Growth_Rate": growth_rates,
    "Predicted_Biomass": biomass,
    "Confidence": confidence_scores,
    "Evidence_Count": evidence_counts,
    "Supporting_DOIs": dois
})

output_path = output_dir / f"growth_conditions_AM1_{date_stamp}.tsv"
df_conditions.to_csv(output_path, sep='\t', index=False)

print(f"\n✓ Generated 5 TSV tables in {output_dir}")
```

## Expected Output Tables

### Table 1: Organism-Specific Ingredient Properties
**File:** `ingredient_properties_AM1_YYYYMMDD.tsv`

**Columns (16):**
- Ingredient, Chemical_Formula, Database_ID
- Lower_Bound_mM, Lower_Bound_Organism, Lower_Bound_DOI, Lower_Bound_Evidence
- Upper_Bound_mM, Upper_Bound_Organism, Upper_Bound_DOI, Upper_Bound_Evidence
- Optimal_Concentration_mM, Optimal_Organism, Optimal_DOI
- Toxicity_Limit, Metabolic_Role, Confidence_Score

**Expected Rows:** ~25-30 ingredients
- Methanol (125-250 mM)
- Neodymium chloride (10-100 μM)
- PQQ (100-500 nM)
- Calcium chloride (<10 μM, minimized for lanthanide uptake)
- Iron sulfate (0.5-1.0 μM, low for methylolanthanin induction)
- Plus standard nutrients: N, P, K, Mg, trace elements, vitamins

### Table 2: Medium Variations for Experimental Goals
**File:** `medium_variations_AM1_YYYYMMDD.tsv`

**Columns (10):**
- Variation_Name, Optimization_Goal
- Methanol_mM, Neodymium_uM, PQQ_nM, Calcium_uM, Iron_uM
- Predicted_Growth_Rate, Predicted_Nd_Uptake, Rationale, Supporting_DOIs

**Expected Rows:** 6-10 variations
- Baseline (standard MP medium)
- High Growth (optimized methanol, balanced nutrients)
- High Lanthanide Uptake (low Ca, low Fe, high Nd)
- XoxF-Optimized (high PQQ, low Fe, high lanthanide)
- Cost-Optimized (reduced REE, minimal cofactors)
- Production Scale (practical concentrations, stability)

### Table 3: Cofactor Requirements
**File:** `cofactor_requirements_AM1_YYYYMMDD.tsv`

**Columns (8):**
- Cofactor, Type, Concentration_Range, Biosynthesis_Capability
- Essential, Pathway_Context, Gene_IDs, Evidence_DOI

**Expected Rows:** ~15-20 cofactors
- PQQ (essential, XoxF-MDH cofactor)
- Lanthanides (essential for XoxF system)
- Thiamin (B1, can synthesize)
- Biotin (B7, can synthesize)
- Fe-S clusters, Heme, Molybdopterin, etc.

### Table 4: Alternative Ingredients
**File:** `alternative_ingredients_AM1_YYYYMMDD.tsv`

**Columns (7):**
- Primary_Ingredient, Alternative, Rationale
- Cost_Factor, Compatibility_Score, KG_Node_ID, Evidence_DOI

**Expected Rows:** ~20-30 alternatives
- PIPES → HEPES, MOPS (pH buffers)
- Neodymium → Lanthanum, Cerium (alternative REEs)
- FeSO4 → Fe-EDTA (chelated iron)
- Standard nutrient alternatives

### Table 5: Growth Condition Predictions
**File:** `growth_conditions_AM1_YYYYMMDD.tsv`

**Columns (8):**
- Condition_ID, Temperature_C, pH, Oxygen_Level
- Predicted_Growth_Rate, Predicted_Biomass
- Confidence, Evidence_Count, Supporting_DOIs

**Expected Rows:** ~10-15 conditions
- Temperature range: 25-37°C (optimum ~30°C)
- pH range: 6.5-7.5 (optimum ~6.8-7.0)
- Oxygen: aerobic, microaerobic conditions
- With/without lanthanides

## Quality Metrics

### Data Completeness
- **Ingredient Coverage:** ≥90% with organism-specific evidence
- **DOI Citations:** ≥80% with M. extorquens or methylotroph evidence
- **Confidence Scores:** All predictions with calculated confidence (0.0-1.0)
- **Evidence Snippets:** ≥70% with extracted evidence text

### Validation Criteria
- **Chemical Compatibility:** No predicted precipitation at standard concentrations
- **pH Stability:** Predicted pH within 6.5-7.5 range
- **Organism Specificity:** ≥50% evidence from M. extorquens or close relatives
- **Literature Support:** All essential ingredients with ≥1 DOI citation

### Expected Performance
- **Agent Execution Time:** 5-10 minutes for complete workflow
- **Database Queries:** ~20-30 queries across KG-Microbe and genome tables
- **Literature Searches:** ~15-20 PubMed queries
- **Total Output Size:** ~100-200 KB (5 TSV files)

## Deliverables

1. **TSV Tables (5 files):**
   - `ingredient_properties_AM1_YYYYMMDD.tsv`
   - `medium_variations_AM1_YYYYMMDD.tsv`
   - `cofactor_requirements_AM1_YYYYMMDD.tsv`
   - `alternative_ingredients_AM1_YYYYMMDD.tsv`
   - `growth_conditions_AM1_YYYYMMDD.tsv`

2. **Symlinks (5 files):**
   - `ingredient_properties_AM1.tsv` → latest
   - `medium_variations_AM1.tsv` → latest
   - `cofactor_requirements_AM1.tsv` → latest
   - `alternative_ingredients_AM1.tsv` → latest
   - `growth_conditions_AM1.tsv` → latest

3. **Documentation:**
   - `README.md` - Complete documentation of tables, sources, and usage
   - `METHODOLOGY.md` - Agent workflow and evidence integration methodology
   - `CITATIONS.md` - Complete bibliography with DOI links

4. **Metadata:**
   - Generation timestamp
   - Agent versions used
   - Database versions (genome count, KG-Microbe stats)
   - Confidence score distributions
   - Evidence source breakdown

## Success Criteria

✅ **Complete:** All 5 TSV tables generated with ≥90% data completeness
✅ **Validated:** Chemical compatibility checked, no critical conflicts
✅ **Evidence-Based:** ≥80% of values supported by organism-specific evidence
✅ **Publication-Ready:** Proper formatting, documentation, and citations
✅ **Reproducible:** Clear methodology, version tracking, provenance metadata

## Usage Example

```bash
# Run the complete workflow
uv run python -c "
from microgrowagents.skills.workflows import RecommendMediaWorkflow
from scripts.export.export_organism_tables import export_organism_media_tables

# Generate recommendations
workflow = RecommendMediaWorkflow()
result = workflow.run(
    query='Generate comprehensive medium tables for M. extorquens AM-1',
    organism='Methylorubrum extorquens AM-1',
    ncbi_taxon_id='NCBITaxon:272630',
    base_medium='MP',
    output_format='structured'
)

# Export to TSV
export_organism_media_tables(
    organism='Methylorubrum extorquens AM-1',
    workflow_result=result,
    output_dir='data/exports/methylorubrum_extorquens_AM1'
)
"

# Verify outputs
ls -lh data/exports/methylorubrum_extorquens_AM1/
cat data/exports/methylorubrum_extorquens_AM1/README.md
```

## Notes

- **Organism Availability:** Check if M. extorquens AM-1 genome is loaded in `genome_annotations` table
- **Alternative Organisms:** If not available, use closely related strains or methylotrophs
- **Evidence Quality:** Prioritize experimental evidence over computational predictions
- **Version Control:** Date-stamp all files and maintain version history
- **Provenance:** Enable provenance tracking to record all agent decisions

## References

- MP Medium: Minimal medium for methylotrophs (mediadive.medium:MP)
- M. extorquens AM-1 genome: NCBITaxon:272630, GenBank: CP001510
- KG-Microbe: 1.5M nodes, 5.1M edges from merged databases
- MicroGrowAgents framework: 17 agents, 11 skills, hybrid provenance system

---

**Version:** 1.0.0
**Date:** 2026-01-11
**Author:** MicroGrowAgents Framework
**Status:** Ready for implementation

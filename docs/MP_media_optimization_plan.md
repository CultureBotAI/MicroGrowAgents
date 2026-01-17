# MP Medium Optimization for M. extorquens AM-1 Growth and Neodymium Depletion

## Overview

This plan provides step-by-step instructions for using the MicroGrowAgents framework to optimize MP medium for:
- **Primary goal**: Supporting Methylobacterium extorquens AM-1 growth
- **Secondary goal**: Enabling Neodymium (Nd³⁺) depletion from solution

The framework has extensive capabilities for this task including:
- Lanthanide-specific data (XoxF enzyme, methylolanthanin lanthanophore, Nd optimal concentrations)
- Genome-informed optimization for M. extorquens
- Multi-agent workflows for media formulation
- Biosorption process data relevant to Nd uptake

## Background: Why M. extorquens AM-1 is Ideal for Nd Depletion

From the sheets_cmm data exploration:

1. **XoxF enzyme system**: M. extorquens produces lanthanide-dependent methanol dehydrogenase (XoxF, KEGG:K23995) that preferentially binds Nd³⁺ and other lanthanides over Ca²⁺

2. **Methylolanthanin production**: This organism produces a lanthanophore (hydroxamate-type siderophore) with high affinity for La/Ce/Nd, enhancing uptake

3. **Optimal Nd concentration**: Data shows 2 μM Nd³⁺ is optimal for growth (from ingredient_properties_20260108.tsv)

4. **Biosorption capability**: Related process data (BP-001) shows M. extorquens achieves 45 mg Eu³⁺/g biomass (lanthanides behave similarly)

5. **Methylotrophic metabolism**: Growth on methanol provides simple carbon source, reducing medium complexity

## Step-by-Step Instructions

### Phase 1: Query Organism-Specific Requirements

Use GenomeFunctionAgent to understand M. extorquens AM-1's genetic capabilities and requirements.

#### Step 1.1: Detect Auxotrophies

```python
from microgrowagents.agents.genome_function_agent import GenomeFunctionAgent
from pathlib import Path

# Initialize agent with database
db_path = Path("data/processed/microgrow.duckdb")
genome_agent = GenomeFunctionAgent(db_path)

# Detect what M. extorquens cannot synthesize
auxotrophy_result = genome_agent.detect_auxotrophies(
    query="detect auxotrophies for Methylobacterium extorquens AM-1",
    organism="Methylobacterium extorquens"
)

print(auxotrophy_result)
```

**Expected output**: Essential amino acids, vitamins, or cofactors that must be supplemented

#### Step 1.2: Query Methanol Dehydrogenase Enzymes

```python
# Find methanol dehydrogenases (XoxF vs MxaF)
enzyme_result = genome_agent.find_enzymes(
    query="find methanol dehydrogenase enzymes in M. extorquens",
    organism="Methylobacterium extorquens",
    ec_number="1.1.2.7"  # Methanol dehydrogenase
)

print(f"Found {len(enzyme_result['data']['enzymes'])} methanol dehydrogenases")
```

**Key distinction**:
- **XoxF** (lanthanide-dependent): Requires Nd³⁺/La³⁺
- **MxaF** (calcium-dependent): Requires Ca²⁺

For Nd depletion, you want to favor XoxF expression.

#### Step 1.3: Query Cofactor Requirements

```python
# Find all cofactor requirements
cofactor_result = genome_agent.find_cofactor_requirements(
    query="find cofactor requirements for M. extorquens methanol metabolism",
    organism="Methylobacterium extorquens"
)

print(cofactor_result)
```

**Expected cofactors**:
- PQQ (pyrroloquinoline quinone) - essential for methanol dehydrogenases
- Lanthanides (Nd³⁺, La³⁺, Ce³⁺) - for XoxF
- B vitamins (B12 for C1 metabolism)

### Phase 2: Query Lanthanide-Specific Data

Use SheetQuerySkill to access extensive lanthanide metabolism data from sheets_cmm.

#### Step 2.1: Query Neodymium Chemical Data

```python
from microgrowagents.skills.simple.sheet_query import SheetQuerySkill

# Initialize skill
sheet_skill = SheetQuerySkill(db_path)

# Look up Neodymium compound data
nd_result = sheet_skill.run(
    collection_id="cmm",
    query_type="entity_lookup",
    entity_name="neodymium",
    output_format="evidence_report"
)

print(nd_result)
```

**What you'll find**:
- Chemical properties of Nd³⁺
- Optimal concentration ranges (2 μM for growth)
- Solubility and precipitation concerns
- Compatible buffer systems

#### Step 2.2: Query XoxF Gene Data

```python
# Cross-reference XoxF with related entities
xoxf_result = sheet_skill.run(
    collection_id="cmm",
    query_type="cross_reference",
    source_entity_id="K23995",  # XoxF KEGG ID
    output_format="evidence_report"
)

print(xoxf_result)
```

**What you'll find**:
- XoxF enzyme properties
- Cofactor binding (Nd³⁺ vs Ca²⁺ affinity)
- Related pathways (methanol oxidation, formaldehyde assimilation)
- Publications with experimental conditions

#### Step 2.3: Search Lanthanide Metabolism Publications

```python
# Full-text search in 120+ publications
pub_result = sheet_skill.run(
    collection_id="cmm",
    query_type="publication_search",
    keyword="neodymium methylobacterium",
    output_format="markdown"
)

print(pub_result)
```

**What you'll find**:
- Growth curves with different lanthanides
- Optimal Nd concentrations
- Synergistic effects with other media components
- Biosorption/bioaccumulation data

### Phase 3: Optimize MP Medium Formulation

Use OptimizeMediumWorkflow or MediaFormulationAgent to generate optimized formulation.

#### Option A: Optimize Existing MP Medium (Recommended)

```python
from microgrowagents.skills.workflows.optimize_medium import OptimizeMediumWorkflow

# Initialize workflow
workflow = OptimizeMediumWorkflow(db_path)

# Optimize MP medium for M. extorquens with Nd
result = workflow.run(
    medium_name="MP medium",
    organism="Methylobacterium extorquens AM-1",
    optimization_goal="growth",  # Prioritize growth (Nd depletion follows)
    additional_context="""
    Optimize for:
    1. Lanthanide-dependent growth (favor XoxF over MxaF)
    2. Neodymium biosorption/bioaccumulation
    3. Methylolanthanin production (lanthanophore for Nd uptake)

    Known optimal conditions:
    - 2 μM Nd³⁺ (neodymium chloride)
    - 0.5-1% methanol as carbon source
    - pH 7.0, 30°C, aerobic
    - PQQ supplementation (0.5-1 mg/L) if needed
    """
)

print(result)
```

**Expected output**:
- Complete optimized medium formulation with concentrations
- Rationale for each ingredient
- Cost analysis
- Predicted growth rate

#### Option B: Design New Medium from Scratch

```python
from microgrowagents.skills.workflows.recommend_media import RecommendMediaWorkflow

workflow = RecommendMediaWorkflow(db_path)

result = workflow.run(
    query="Design defined medium for M. extorquens with neodymium depletion",
    organism="Methylobacterium extorquens AM-1",
    growth_conditions={
        "temperature": 30,
        "pH": 7.0,
        "oxygen": "aerobic",
        "carbon_source": "methanol"
    },
    formulation_goals=[
        "defined",  # Chemically defined, no complex ingredients
        "lanthanide_optimized",  # Favor XoxF pathway
        "cost_effective"
    ],
    special_requirements=[
        "2 μM neodymium chloride",
        "PQQ supplementation",
        "methylolanthanin production support"
    ]
)

print(result)
```

#### Option C: Direct Agent Query (Most Flexible)

```python
from microgrowagents.agents.media_formulation_agent import MediaFormulationAgent

agent = MediaFormulationAgent(db_path)

result = agent.run(
    query="""
    Optimize MP medium for Methylobacterium extorquens AM-1 to achieve:
    1. Maximum growth rate
    2. Maximum neodymium depletion from solution

    Starting conditions:
    - Standard MP medium base
    - Initial Nd concentration: 50 μM (adjust based on your system)
    - Target final Nd: <5 μM after 48h

    Consider:
    - XoxF vs MxaF expression (favor XoxF)
    - Methylolanthanin production
    - Calcium-lanthanide competition
    - PQQ availability
    """,
    organism="Methylobacterium extorquens AM-1",
    base_medium="MP medium"
)

print(result)
```

### Phase 4: Analyze Concentration Recommendations

Use GenMediaConcAgent to predict optimal concentration ranges.

```python
from microgrowagents.agents.gen_media_conc_agent import GenMediaConcAgent

conc_agent = GenMediaConcAgent(db_path)

# Get Nd³⁺ concentration recommendation
nd_conc = conc_agent.run(
    query="optimal neodymium concentration for Methylobacterium extorquens growth",
    organism="Methylobacterium extorquens",
    ingredient="neodymium chloride",
    role="RARE_EARTH_ELEMENT"
)

print(f"Recommended Nd³⁺ range: {nd_conc}")
```

### Phase 5: Interpret and Verify Results

#### Step 5.1: Review Ingredient Roles

```python
from microgrowagents.agents.media_role_agent import MediaRoleAgent

role_agent = MediaRoleAgent(db_path)

# Verify all ingredients have correct roles
for ingredient in optimized_medium['ingredients']:
    role_result = role_agent.run(
        query=f"classify role of {ingredient['name']}",
        ingredient_name=ingredient['name'],
        context="methylotrophic growth with lanthanide cofactors"
    )
    print(f"{ingredient['name']}: {role_result['data']['role']}")
```

**Expected roles**:
- Methanol → CARBON_SOURCE
- Nd³⁺ → RARE_EARTH_ELEMENT (cofactor)
- PQQ → COFACTOR
- Methylolanthanin precursors → CHELATOR/SIDEROPHORE

#### Step 5.2: Validate Against Literature

```python
# Cross-check recommendations against publications
validation_result = sheet_skill.run(
    collection_id="cmm",
    query_type="publication_search",
    keyword="methylobacterium extorquens neodymium growth",
    output_format="evidence_report"
)

# Compare recommended concentrations with published data
print(validation_result)
```

### Phase 6: Export and Use Formulation

#### Step 6.1: Export to Standard Format

```python
# Export optimized medium to TSV
import pandas as pd

ingredients_df = pd.DataFrame(result['data']['formulation']['ingredients'])
ingredients_df.to_csv('optimized_MP_medium_for_Nd_depletion.tsv',
                      sep='\t', index=False)

print("Exported to: optimized_MP_medium_for_Nd_depletion.tsv")
```

#### Step 6.2: Generate Preparation Protocol

```python
# Get step-by-step preparation instructions
protocol = agent.generate_protocol(
    formulation=result['data']['formulation'],
    volume=1000,  # mL
    include_sterilization=True
)

print(protocol)
```

## Key Considerations for Nd Depletion

### 1. Calcium-Lanthanide Competition

**Problem**: Ca²⁺ competes with Nd³⁺ for XoxF binding and suppresses XoxF expression

**Solution**: Minimize Ca²⁺ in base medium (<10 μM) to favor lanthanide-dependent pathway

```python
# Check Ca²⁺ concentration in optimized medium
ca_ingredients = [ing for ing in result['data']['formulation']['ingredients']
                  if 'calcium' in ing['name'].lower()]
if ca_ingredients:
    print(f"WARNING: High Ca²⁺ may suppress XoxF expression")
```

### 2. Methylolanthanin Production

**Enhancement**: Methylolanthanin enhances Nd uptake by 10-100x

**Requirements**:
- Iron limitation (induces siderophore production)
- Proper carbon/nitrogen ratio
- Aerobic conditions

```python
# Verify Fe limitation in medium
fe_ingredients = [ing for ing in result['data']['formulation']['ingredients']
                  if 'iron' in ing['name'].lower() or 'Fe' in ing['name']]
# Target: <1 μM Fe to induce methylolanthanin production
```

### 3. pH and Solubility

**Issue**: Lanthanides precipitate as hydroxides at pH >8

**Solution**: Maintain pH 6.5-7.5, use citrate or acetate buffers (not phosphate - forms insoluble Nd-phosphate)

### 4. Biosorption vs Bioaccumulation

**Biosorption** (passive, cell surface binding):
- Fast (minutes to hours)
- Reversible
- ~45 mg Nd/g dry biomass (based on Eu data)

**Bioaccumulation** (active, intracellular):
- Slower (hours to days)
- Irreversible
- Higher capacity
- Requires metabolically active cells

For maximum Nd depletion, optimize for both.

## Expected Results

### Optimized MP Medium Formulation (Example)

Based on framework data, expect recommendations similar to:

```
OPTIMIZED MP MEDIUM FOR M. EXTORQUENS AM-1 (1 L)

CARBON & ENERGY:
- Methanol: 5 mL (0.5% v/v)

LANTHANIDE COFACTOR:
- Neodymium chloride (NdCl₃·6H₂O): 2 μM (0.71 mg/L)
  [Adjust based on initial contamination level]

NITROGEN:
- (NH₄)₂SO₄: 1.0 g/L

PHOSPHORUS:
- K₂HPO₄: 0.7 g/L (LOW - avoid Nd precipitation)

SULFUR:
- MgSO₄·7H₂O: 0.2 g/L

TRACE ELEMENTS:
- Fe-EDTA: 0.5 mg/L (LOW - induces methylolanthanin)
- PQQ (pyrroloquinoline quinone): 1 mg/L
- B12 (cyanocobalamin): 0.1 mg/L
- Biotin: 0.02 mg/L
- Thiamine: 0.1 mg/L

CALCIUM (MINIMIZED):
- CaCl₂: <10 μM (CRITICAL: Keep low to favor XoxF)

BUFFER:
- Citrate buffer (pH 7.0): 10 mM
  [NOT phosphate - prevents Nd precipitation]

CONDITIONS:
- pH: 7.0
- Temperature: 30°C
- Agitation: 150 rpm (aerobic)
- Inoculum: 1-2% (mid-log phase)

GROWTH EXPECTATIONS:
- Lag phase: 6-12 h
- Exponential phase: 12-36 h
- Max OD600: 1.5-2.0
- Nd depletion: >80% after 48h (from 50 μM → <10 μM)
```

### Performance Metrics to Track

1. **Growth rate**: OD600 every 4-6 hours
2. **Nd depletion**: ICP-MS or ICP-OES at 0, 24, 48 hours
3. **Cell-associated Nd**: Digest biomass, measure by ICP
4. **XoxF expression**: qRT-PCR or Western blot
5. **Methylolanthanin production**: HPLC-MS (if available)

## Troubleshooting

### Poor Growth (<OD600 0.5 after 48h)

**Check**:
- [ ] PQQ supplementation adequate (0.5-1 mg/L)
- [ ] Methanol concentration (0.5% optimal, toxic >2%)
- [ ] Calcium contamination (<10 μM)
- [ ] pH stability (should stay 6.8-7.2)

**Solution**: Run GenomeFunctionAgent auxotrophy detection, add missing vitamins

### Low Nd Depletion (<50% after 48h)

**Check**:
- [ ] Iron concentration (should be <1 μM to induce methylolanthanin)
- [ ] Phosphate concentration (high phosphate precipitates Nd)
- [ ] Cell density (higher biomass = more Nd uptake)
- [ ] pH (Nd precipitates at pH >8)

**Solution**: Query bioprocess data for BP-001 (Eu biosorption) to compare conditions

### Nd Precipitation

**Symptoms**: Cloudy solution, low dissolved Nd despite no uptake

**Solution**:
- Lower pH to 6.5
- Switch from phosphate to citrate buffer
- Add 0.1% citrate as Nd chelator (keeps soluble)

## CLI Alternative

For quick queries without Python scripting:

```bash
# Query organism requirements
python -m microgrowagents.agents.genome_function_agent \
  --query "detect auxotrophies" \
  --organism "Methylobacterium extorquens"

# Query lanthanide data
python -m microgrowagents.skills.simple.sheet_query \
  --collection-id cmm \
  --query-type entity_lookup \
  --entity-name neodymium \
  --output-format markdown

# Optimize medium
python -m microgrowagents.skills.workflows.optimize_medium \
  --medium-name "MP medium" \
  --organism "Methylobacterium extorquens AM-1" \
  --optimization-goal growth
```

## Critical Files Referenced

### Agents:
- `src/microgrowagents/agents/genome_function_agent.py` - Organism-specific requirements
- `src/microgrowagents/agents/media_formulation_agent.py` - Medium optimization
- `src/microgrowagents/agents/gen_media_conc_agent.py` - Concentration predictions
- `src/microgrowagents/agents/media_role_agent.py` - Ingredient role classification

### Skills:
- `src/microgrowagents/skills/simple/sheet_query.py` - Query sheets_cmm data
- `src/microgrowagents/skills/workflows/optimize_medium.py` - Optimization workflow
- `src/microgrowagents/skills/workflows/recommend_media.py` - New medium design

### Data Files:
- `data/sheets_cmm/BER_CMM_Data_for_AI_chemicals_extended.tsv` - Nd and lanthanide data
- `data/sheets_cmm/BER_CMM_Data_for_AI_genes_and_proteins_extended.tsv` - XoxF gene data
- `data/sheets_cmm/BER_CMM_Data_for_AI_bioprocesses_extended.tsv` - Biosorption data
- `data/sheets_cmm/publications/` - 120+ publications on lanthanide metabolism
- `data/exports/ingredient_properties_20260108.tsv` - M. extorquens requirements

### Database:
- `data/processed/microgrow.duckdb` - Main database with all query capabilities

## Verification

To verify the framework capabilities are loaded:

```python
# Check database connection
from pathlib import Path
import duckdb

db_path = Path("data/processed/microgrow.duckdb")
assert db_path.exists(), "Database not found - run initialization scripts"

conn = duckdb.connect(str(db_path))

# Check sheets_cmm data loaded
result = conn.execute("SELECT COUNT(*) FROM sheet_data WHERE table_id LIKE 'cmm_%'").fetchone()
print(f"CMM entities loaded: {result[0]}")

# Check publications loaded
result = conn.execute("SELECT COUNT(*) FROM sheet_publications WHERE collection_id = 'cmm'").fetchone()
print(f"CMM publications loaded: {result[0]}")

conn.close()
```

**Expected output**:
- CMM entities loaded: ~1,763
- CMM publications loaded: ~118

## Summary

To optimize MP medium for M. extorquens AM-1 growth and Nd depletion:

1. **Query organism requirements** (GenomeFunctionAgent) → Identify auxotrophies, cofactors
2. **Query lanthanide data** (SheetQuerySkill) → Get optimal Nd concentrations, XoxF data
3. **Optimize formulation** (OptimizeMediumWorkflow) → Generate complete recipe
4. **Verify recommendations** (MediaRoleAgent + literature cross-check)
5. **Export and prepare** → TSV export + preparation protocol

**Key optimization principles**:
- Minimize Ca²⁺ (<10 μM) to favor XoxF over MxaF
- Induce methylolanthanin (Fe limitation)
- Prevent Nd precipitation (citrate buffer, pH 6.5-7.5)
- Supplement PQQ (0.5-1 mg/L)
- Use 2 μM Nd³⁺ as starting point

**Expected outcomes**:
- Growth: OD600 1.5-2.0 in 48h
- Nd depletion: >80% (50 μM → <10 μM in 48h)
- Biosorption capacity: ~40-50 mg Nd/g dry biomass

The framework contains extensive data to support this application - 120+ publications on lanthanide metabolism, optimal concentration data, enzyme systems, and validated biosorption processes.

# Claude Code Prompt: Generate Latin Hypercube 96-Well Plate Design

## Context

Generate a comprehensive Latin Hypercube Sampling (LHS) experimental design for 3× 96-well plates targeting **Methylorubrum extorquens AM-1** lanthanide metabolism studies using the corrected MP medium design.

## Experimental Specifications

### Plates & Layout
- **Plates:** 3× 96-well deep well plates
- **Fill volume:** 0.5 mL per well
- **Conditions per plate:** ~80 unique medium formulations
- **Controls per plate:**
  - Negative control (no inoculum): 1-2 wells
  - Media control (standard MP medium): 1-2 wells
  - Total controls: 4-6 wells per plate, 12-18 total
- **Total unique conditions:** ~240 medium variants

### Growth & Sampling
- **Duration:** 48 hours
- **Sampling timepoints:** 8h, 24h, 32h
- **Measurements:**
  - OD₆₀₀ (growth/biomass)
  - Arsenazo III assay (lanthanide uptake - Nd³⁺ quantification)
- **Organism:** Methylorubrum extorquens AM-1 (SAMN31331780)

## Objective

Create a complete experimental design package including:

1. **Discretized LHS design** - Bin 9 continuous concentration ranges into suitable levels
2. **240 unique medium formulations** - With both varied and fixed components
3. **96-well plate layouts** - 3 plates with controls and condition assignments
4. **Stock solution recipes** - For preparing each unique medium
5. **Plate preparation protocol** - Step-by-step instructions
6. **Data collection templates** - For OD and arsenazo measurements
7. **Analysis plan** - Response surface modeling approach

## Available Resources

### Design Inputs (Use These Files)

**Latin Hypercube Design (CORRECTED):**
- **Varied components:** `data/designs/MP_latinhypercube/MP_latinhypercube_list_ranges_REVISED_FINAL.txt`
  - 9 components with corrected concentration ranges
  - K₂HPO₄, NaH₂PO₄, (NH₄)₂SO₄, Citrate, CoCl₂, NdCl₃, Succinate, Methanol, PQQ

- **Fixed components:** `data/designs/MP_latinhypercube/fixed_concentrations_FINAL.txt`
  - 11 components held constant
  - PIPES, MgCl₂, ZnSO₄, MnCl₂, FeSO₄, Mo, Cu, W, Thiamin, Biotin
  - CaCl₂ excluded (Ca-free design)

**Design Documentation:**
- `data/designs/MP_latinhypercube/DESIGN_REVIEW_REPORT_CORRECTED.md` (technical details)
- `data/designs/MP_latinhypercube/FINAL_SUMMARY.md` (quick reference)

**Organism Data:**
- `data/exports/methylorubrum_extorquens_AM1/` (genome-based cofactor requirements)

### Agents (17 total)

**Workflow Orchestration:**
- `MediaFormulationAgent` - Master orchestrator for medium design
- `RecommendMediaWorkflow` - Complete workflow (8 agents)

**Concentration & Chemistry:**
- `GenMediaConcAgent` - Predict optimal concentration ranges
- `MediaPhCalculator` - Calculate pH, ionic strength, osmolarity
- `ChemistryAgent` - Chemical compatibility validation
- `SensitivityAnalysisAgent` - Analyze concentration sensitivities

**Genome & Knowledge:**
- `GenomeFunctionAgent` - Query M. extorquens genome (10,820 annotations)
- `KGReasoningAgent` - Query KG-Microbe (if available)

**Support:**
- `MediaRoleAgent` - Validate nutrient roles
- `AlternateIngredientAgent` - Suggest alternatives if needed
- `CofactorMediaAgent` - Analyze cofactor requirements
- `SQLAgent` - Direct database queries

### Skills (11 simple + 1 workflow)

**Simple Skills:**
- `query_database` - SQL queries to ingredients, genome_annotations, chemical_properties
- `predict_concentration` - Predict concentration ranges with ML
- `calculate_chemistry` - pH, osmolarity, solubility calculations
- `analyze_sensitivity` - Concentration sensitivity analysis
- `classify_role` - Ingredient role classification
- `find_alternates` - Alternative ingredient suggestions
- `search_literature` - Literature evidence retrieval

**Workflow:**
- `recommend-media` - Complete workflow coordinating 8 agents

### Database Resources

**Tables Available:**
- `genome_annotations` - 10,820 annotations for M. extorquens AM-1
- `ingredients` - Chemical properties, CHEBI IDs
- `ingredient_effects` - Concentration ranges, organism evidence
- `chemical_properties` - pH, pKa, solubility, molecular weight
- `provenance_*` - Provenance tracking tables

## Implementation Steps

### CRITICAL: Enable Provenance Tracking

**Before executing any agents:**

```python
from microgrowagents.agents import MediaFormulationAgent

# ✅ CORRECT: Enable provenance tracking
agent = MediaFormulationAgent(enable_provenance=True)
result = agent.execute("your query")

# ❌ INCORRECT: run() does NOT enable provenance
# agent.run("...") # No provenance files generated!
```

**All agent executions MUST use:**
1. `enable_provenance=True` parameter
2. `agent.execute()` method instead of `agent.run()`

---

### Step 1: Load and Validate LHS Design

Load the corrected 9-component design:

```python
import pandas as pd
from pathlib import Path

# Load varied components (9 total)
lhs_file = Path("data/designs/MP_latinhypercube/MP_latinhypercube_list_ranges_REVISED_FINAL.txt")
varied_df = pd.read_csv(lhs_file, sep='\t', comment='#')

print(f"Varied components: {len(varied_df)}")
print(varied_df[['Component', 'Lower_Bound', 'Upper_Bound', 'Unit']])

# Load fixed components (11 total)
fixed_file = Path("data/designs/MP_latinhypercube/fixed_concentrations_FINAL.txt")
fixed_df = pd.read_csv(fixed_file, sep='\t', comment='#')

print(f"Fixed components: {len(fixed_df)}")
print(fixed_df[['Component', 'Fixed_Concentration', 'Unit']])
```

**Expected output:**
- 9 varied components with concentration ranges
- 11 fixed components with single concentrations
- Validation: All essential nutrients present

---

### Step 2: Discretize Concentration Ranges

**Challenge:** 9 continuous ranges need discretization into bins.

**Approach:** Use logarithmic binning for wide ranges, linear for narrow:

```python
import numpy as np

def discretize_concentration_range(component, lower, upper, unit, n_levels=4):
    """
    Discretize concentration range into n levels.

    Args:
        component: Component name
        lower: Lower bound
        upper: Upper bound
        unit: Concentration unit
        n_levels: Number of discrete levels (2-5 recommended)

    Returns:
        List of discrete concentrations
    """
    # Determine if log or linear spacing
    log_ratio = upper / lower if lower > 0 else float('inf')

    if log_ratio > 10:
        # Wide range → logarithmic spacing
        if lower == 0:
            # Include zero as first level
            levels = [0] + list(np.logspace(np.log10(upper/100), np.log10(upper), n_levels-1))
        else:
            levels = np.logspace(np.log10(lower), np.log10(upper), n_levels)
    else:
        # Narrow range → linear spacing
        levels = np.linspace(lower, upper, n_levels)

    return levels.tolist()

# Discretize all 9 varied components
discretized = {}

for _, row in varied_df.iterrows():
    component = row['Component']
    lower = row['Lower_Bound']
    upper = row['Upper_Bound']
    unit = row['Unit']

    # Adjust n_levels based on component importance
    if component in ['NdCl₃·6H₂O', 'Methanol', 'PQQ']:
        n_levels = 5  # More levels for critical components
    elif component in ['Succinate']:
        n_levels = 3  # Fewer levels for optional components
    else:
        n_levels = 4  # Standard

    discretized[component] = {
        'levels': discretize_concentration_range(component, lower, upper, unit, n_levels),
        'unit': unit,
        'n_levels': n_levels
    }

    print(f"{component}: {n_levels} levels")
    print(f"  {discretized[component]['levels']} {unit}")
```

**Expected discretization:**
- K₂HPO₄: 4 levels (0.5, 2, 7, 20 mM)
- NaH₂PO₄: 4 levels (0.5, 2, 7, 20 mM)
- (NH₄)₂SO₄: 4 levels (1, 10, 30, 100 mM)
- Citrate: 4 levels (0.01, 0.1, 1, 10 mM)
- CoCl₂: 4 levels (0.01, 0.1, 1, 100 µM)
- **NdCl₃**: 5 levels (0.5, 1, 2, 5, 10 µM) ← Critical
- Succinate: 3 levels (0, 50, 150 mM)
- **Methanol**: 5 levels (15, 50, 125, 300, 500 mM) ← Critical
- **PQQ**: 5 levels (0, 100, 250, 500, 1000 nM) ← Critical

**Total combinations:** 4×4×4×4×4×5×3×5×5 = **384,000 possible**
**Need:** 240 conditions → **Sample from full factorial space**

---

### Step 3: Generate Latin Hypercube Samples

Use Latin Hypercube Sampling to efficiently explore the discretized space:

```python
from scipy.stats.qmc import LatinHypercube
from itertools import product

# Option A: Sample from discretized levels (recommended)
def generate_lhs_from_discrete(discretized, n_samples=240, seed=42):
    """
    Generate LHS samples from discretized concentration levels.

    Strategy:
    1. Generate continuous LHS in [0, 1]
    2. Map to discrete level indices
    3. Retrieve actual concentrations
    """
    n_components = len(discretized)
    components = list(discretized.keys())

    # Generate LHS in unit hypercube
    sampler = LatinHypercube(d=n_components, seed=seed)
    lhs_continuous = sampler.random(n=n_samples)

    # Map to discrete levels
    samples = []
    for sample in lhs_continuous:
        condition = {}
        for i, component in enumerate(components):
            levels = discretized[component]['levels']
            # Map [0, 1] to level index
            level_idx = int(sample[i] * len(levels))
            if level_idx >= len(levels):
                level_idx = len(levels) - 1

            condition[component] = {
                'concentration': levels[level_idx],
                'unit': discretized[component]['unit']
            }
        samples.append(condition)

    return pd.DataFrame(samples)

# Generate 240 samples
lhs_samples = generate_lhs_from_discrete(discretized, n_samples=240, seed=42)
print(f"Generated {len(lhs_samples)} unique medium formulations")

# Option B: Continuous LHS then round to nearest discrete level
# (Alternative if Option A produces duplicates)
```

**Validation:**
- Check for duplicates (remove if any)
- Verify all samples meet design constraints
- Ensure good space-filling properties

---

### Step 4: Apply Design Constraints

Validate each sample against chemical compatibility constraints:

```python
def validate_sample(sample):
    """
    Check chemical compatibility constraints.

    Returns:
        (valid: bool, reason: str)
    """
    # Extract concentrations
    k2hpo4 = sample['K₂HPO₄·3H₂O']['concentration']
    nah2po4 = sample['NaH₂PO₄·H₂O']['concentration']
    citrate = sample['Sodium citrate']['concentration']
    nd = sample['NdCl₃·6H₂O']['concentration']

    total_phosphate = k2hpo4 + nah2po4

    # Constraint 1: High P + High Nd → Need high citrate
    if total_phosphate > 10 and nd > 5:
        if citrate < 1:
            return False, "Precipitation risk: High P + High Nd + Low citrate"

    # Constraint 2: Minimum buffering capacity
    if total_phosphate < 2 and citrate < 0.1:
        return False, "Insufficient buffering capacity"

    # Constraint 3: Osmolarity (rough estimate)
    # Approximate osmolarity from major salts
    osmolarity = (k2hpo4 + nah2po4) * 3  # Phosphates dissociate
    osmolarity += sample['(NH₄)₂SO₄']['concentration'] * 3  # Ammonium sulfate
    osmolarity += citrate * 4  # Citrate dissociation

    if osmolarity > 500:
        return False, f"Hyperosmotic: {osmolarity:.0f} mOsm"

    # Constraint 4: C:N ratio
    methanol = sample['Methanol']['concentration']
    succinate = sample['Succinate']['concentration']
    ammonium = sample['(NH₄)₂SO₄']['concentration']

    cn_ratio = (methanol + succinate) / ammonium if ammonium > 0 else 999
    if not (5 < cn_ratio < 50):
        return False, f"C:N ratio out of range: {cn_ratio:.1f}"

    return True, "Valid"

# Apply constraints
valid_samples = []
invalid_samples = []

for idx, sample in lhs_samples.iterrows():
    valid, reason = validate_sample(sample)
    if valid:
        valid_samples.append(sample)
    else:
        invalid_samples.append({'sample_id': idx, 'reason': reason})

print(f"Valid samples: {len(valid_samples)}/{len(lhs_samples)}")
print(f"Invalid samples: {len(invalid_samples)}")

# If <240 valid, regenerate or relax constraints
if len(valid_samples) < 240:
    print("⚠️ Need to regenerate with different seed or relax constraints")
else:
    # Take first 240
    lhs_samples_final = pd.DataFrame(valid_samples[:240])
```

**Expected:** 230-250 valid samples (>95% pass rate)

---

### Step 5: Add Fixed Components

Add the 11 fixed components to create complete medium formulations:

```python
def add_fixed_components(lhs_samples, fixed_df):
    """
    Add fixed components to all LHS samples.

    Returns:
        Complete medium formulations (varied + fixed)
    """
    complete_formulations = []

    for idx, sample in lhs_samples.iterrows():
        formulation = {
            'condition_id': f"LHS_{idx+1:03d}",
            'varied_components': sample.to_dict(),
            'fixed_components': {}
        }

        # Add each fixed component
        for _, row in fixed_df.iterrows():
            component = row['Component']
            concentration = row['Fixed_Concentration']
            unit = row['Unit']

            formulation['fixed_components'][component] = {
                'concentration': concentration,
                'unit': unit,
                'note': row.get('Role', '')
            }

        complete_formulations.append(formulation)

    return complete_formulations

complete_media = add_fixed_components(lhs_samples_final, fixed_df)
print(f"Complete formulations: {len(complete_media)}")
print(f"Components per formulation: {len(complete_media[0]['varied_components']) + len(complete_media[0]['fixed_components'])}")
```

**Expected:** 240 complete formulations with 20 components each (9 varied + 11 fixed)

---

### Step 6: Assign to 96-Well Plates

Create plate layouts with controls:

```python
def assign_to_plates(formulations, n_plates=3, controls_per_plate=4):
    """
    Assign formulations to 96-well plate layout.

    96-well plate: 8 rows (A-H) × 12 columns (1-12)

    Controls:
    - Negative control (no inoculum): 2 wells per plate
    - Media control (standard MP): 2 wells per plate

    Returns:
        List of plate layouts with well assignments
    """
    wells_per_plate = 96
    conditions_per_plate = wells_per_plate - controls_per_plate

    plates = []

    for plate_num in range(n_plates):
        plate = {
            'plate_id': f"Plate_{plate_num+1}",
            'layout': {},
            'controls': {}
        }

        # Assign controls to corners
        # A1, A12: Negative controls (no inoculum)
        # H1, H12: Media controls (standard MP)
        plate['controls']['A1'] = {'type': 'negative', 'description': 'No inoculum'}
        plate['controls']['A12'] = {'type': 'negative', 'description': 'No inoculum'}
        plate['controls']['H1'] = {'type': 'media', 'description': 'Standard MP medium'}
        plate['controls']['H12'] = {'type': 'media', 'description': 'Standard MP medium'}

        # Assign conditions to remaining wells
        start_idx = plate_num * conditions_per_plate
        end_idx = start_idx + conditions_per_plate

        condition_idx = 0
        for row in 'ABCDEFGH':
            for col in range(1, 13):
                well = f"{row}{col}"

                # Skip control wells
                if well in plate['controls']:
                    continue

                # Assign condition
                global_idx = start_idx + condition_idx
                if global_idx < len(formulations):
                    plate['layout'][well] = {
                        'condition_id': formulations[global_idx]['condition_id'],
                        'formulation': formulations[global_idx]
                    }
                    condition_idx += 1

        plates.append(plate)
        print(f"Plate {plate_num+1}: {condition_idx} conditions + {len(plate['controls'])} controls")

    return plates

plate_layouts = assign_to_plates(complete_media, n_plates=3, controls_per_plate=4)
```

**Expected layout:**
```
Plate 1: 92 conditions + 4 controls (A1, A12, H1, H12)
Plate 2: 92 conditions + 4 controls
Plate 3: 56 conditions + 4 controls (240 total conditions)
```

---

### Step 7: Calculate Stock Solutions

Generate stock solution recipes for efficient preparation:

```python
def calculate_stock_solutions(complete_media, stock_multiplier=10):
    """
    Calculate stock solutions for each ingredient.

    Strategy:
    - Create 10× concentrated stocks
    - Group formulations by similar concentrations
    - Minimize number of pipetting steps

    Returns:
        Stock solution recipes and dilution schemes
    """
    # Collect all unique concentrations per component
    component_concentrations = {}

    for formulation in complete_media:
        for component, details in formulation['varied_components'].items():
            if component not in component_concentrations:
                component_concentrations[component] = set()
            component_concentrations[component].add(details['concentration'])

    # Create stock solutions
    stocks = {}
    for component, concentrations in component_concentrations.items():
        stocks[component] = {
            'unique_levels': sorted(concentrations),
            'n_levels': len(concentrations),
            'stock_concentrations': [c * stock_multiplier for c in sorted(concentrations)]
        }

    return stocks

stock_solutions = calculate_stock_solutions(complete_media)

# Print stock solution summary
for component, details in stock_solutions.items():
    print(f"\n{component}:")
    print(f"  Unique levels: {details['n_levels']}")
    print(f"  Concentrations: {details['unique_levels']}")
```

---

### Step 8: Export Plate Layouts and Protocols

Generate output files for experimental execution:

```python
import json
from datetime import datetime

output_dir = Path("data/exports/lhs_plate_design_96well")
output_dir.mkdir(exist_ok=True)

# Export 1: Plate layouts (CSV for each plate)
for plate in plate_layouts:
    plate_file = output_dir / f"{plate['plate_id']}_layout.csv"

    # Create 8×12 grid
    layout_df = pd.DataFrame(index=list('ABCDEFGH'), columns=range(1, 13))

    # Fill with condition IDs
    for well, details in plate['layout'].items():
        row = well[0]
        col = int(well[1:])
        layout_df.loc[row, col] = details['condition_id']

    # Fill controls
    for well, details in plate['controls'].items():
        row = well[0]
        col = int(well[1:])
        layout_df.loc[row, col] = f"CTRL_{details['type'].upper()}"

    layout_df.to_csv(plate_file)
    print(f"Exported: {plate_file}")

# Export 2: Complete formulations (JSON)
formulations_file = output_dir / "complete_formulations.json"
with open(formulations_file, 'w') as f:
    json.dump(complete_media, f, indent=2)

# Export 3: Stock solutions (TSV)
stock_file = output_dir / "stock_solutions.tsv"
# ... (create TSV with stock recipes)

# Export 4: Pipetting protocol (CSV)
pipetting_file = output_dir / "pipetting_protocol.csv"
# ... (create well-by-well pipetting instructions)

# Export 5: Data collection template (CSV)
data_template_file = output_dir / "data_collection_template.csv"
# ... (create template for OD + arsenazo measurements)

print(f"\nAll files exported to: {output_dir}")
```

---

### Step 9: Generate Preparation Protocol

Create step-by-step laboratory protocol:

```python
def generate_protocol(plate_layouts, stock_solutions, output_dir):
    """
    Generate markdown protocol for plate preparation.
    """
    protocol = f"""# 96-Well Plate Preparation Protocol
## Latin Hypercube Design for M. extorquens AM-1

**Date Generated:** {datetime.now().strftime('%Y-%m-%d')}
**Plates:** {len(plate_layouts)}
**Conditions:** {sum(len(p['layout']) for p in plate_layouts)}
**Controls:** {sum(len(p['controls']) for p in plate_layouts)}

---

## Materials Required

### Plates
- 3× 96-well deep well plates (0.5 mL working volume)
- Plate sealers (breathable for aerobic growth)

### Stock Solutions (Prepare Day Before)

#### Fixed Components (Same in all wells):
- PIPES buffer (20 mM stock)
- MgCl₂·6H₂O (5 mM stock)
- Trace metal mix (10× concentrated)
- Vitamin mix (10× concentrated)

#### Varied Components (Multiple stocks per component):
"""

    for component, details in stock_solutions.items():
        protocol += f"\n**{component}:**\n"
        for level in details['unique_levels']:
            protocol += f"  - {level} {details['unit']} working concentration\n"

    protocol += """

---

## Preparation Steps

### Day 1: Prepare Stock Solutions

1. **Fixed component stocks:**
   ```
   PIPES: Dissolve in DI water, adjust pH to 6.8, filter sterilize
   MgCl₂: Prepare 5 mM stock, autoclave
   Trace metals: Mix according to fixed_concentrations_FINAL.txt, filter sterilize
   Vitamins: Prepare fresh, filter sterilize (do not autoclave)
   ```

2. **Varied component stocks:**
   - Prepare multiple concentration levels per component
   - Use stock_solutions.tsv for exact amounts
   - Filter sterilize all stocks (0.22 µm)

3. **M. extorquens AM-1 culture:**
   - Start overnight culture in standard MP medium
   - Target OD₆₀₀ = 0.5-0.8 by next morning

### Day 2: Plate Setup

1. **Thaw/warm all stock solutions** to room temperature

2. **Prepare base medium** (common to all wells):
   - Mix fixed components
   - Adjust to 90% of final volume

3. **Aliquot to wells using pipetting protocol:**
   - Follow pipetting_protocol.csv
   - Add varied components to each well
   - Final volume: 450 µL (leaving room for inoculum)

4. **Add inoculum:**
   - Dilute overnight culture to OD₆₀₀ = 0.1
   - Add 50 µL per well → Final OD₆₀₀ = 0.01
   - Skip for negative control wells (A1, A12 per plate)

5. **Seal plates** with breathable film

6. **Incubate:**
   - Temperature: 30°C
   - Shaking: 200 rpm
   - Duration: 48 hours

### Days 3-4: Sampling & Measurements

**Timepoints:** 8h, 24h, 32h

**For each timepoint:**

1. **OD₆₀₀ measurement:**
   - Transfer 100 µL to clear 96-well plate
   - Read at 600 nm
   - Return to growth plate if needed

2. **Arsenazo III assay (Nd³⁺ quantification):**
   - Transfer 50 µL culture to new 96-well plate
   - Centrifuge 3000g, 10 min
   - Transfer 40 µL supernatant to arsenazo plate
   - Add 160 µL arsenazo reagent (100 µM in acetate buffer pH 3.5)
   - Incubate 5 min
   - Read at 652 nm
   - Calculate [Nd³⁺] from standard curve

3. **Record data:**
   - Use data_collection_template.csv
   - Note: Plate ID, Well ID, Timepoint, OD₆₀₀, A₆₅₂

---

## Quality Control

- [ ] All stock solutions filter-sterilized
- [ ] Negative controls show no growth (OD₆₀₀ < 0.1)
- [ ] Media controls grow to expected OD₆₀₀ (0.8-1.2 at 24h)
- [ ] No contamination observed
- [ ] Replicates have CV < 15% (if included)

---

## Expected Outcomes

**Growth patterns:**
- Low methanol + Low Nd → Slower growth
- High methanol + High Nd → Maximum growth (OD₆₀₀ ~2.0 at 48h)
- High succinate → Nd-independent growth possible

**Lanthanide uptake:**
- High Nd + Low Ca + Low Fe → Maximum uptake (70-90% depletion)
- High citrate → Reduced uptake (chelation)
- High phosphate → Reduced uptake (precipitation)

**Response surface:**
- Identify optimal Nd concentration for max uptake
- Determine Nd × Citrate interaction effects
- Map PQQ × Nd synergistic effects on growth

---

## Data Analysis

See: `analysis_plan.md` for details

**Statistical approach:**
- Gaussian Process Regression (GPR) for response surfaces
- Factor interaction analysis
- Visualization: 3D response surfaces, heatmaps

"""

    protocol_file = output_dir / "preparation_protocol.md"
    with open(protocol_file, 'w') as f:
        f.write(protocol)

    print(f"Protocol generated: {protocol_file}")
    return protocol

protocol = generate_protocol(plate_layouts, stock_solutions, output_dir)
```

---

### Step 10: Validate Complete Design

Final validation using agents (optional but recommended):

```python
from microgrowagents.agents import MediaPhCalculator, ChemistryAgent

# Validate pH and osmolarity for sample formulations
ph_agent = MediaPhCalculator(enable_provenance=True)
chem_agent = ChemistryAgent(enable_provenance=True)

# Check 10 random formulations
import random
sample_formulations = random.sample(complete_media, 10)

for formulation in sample_formulations:
    condition_id = formulation['condition_id']

    # Calculate pH
    ph_result = ph_agent.execute(f"Calculate pH for {condition_id}")

    # Check chemical compatibility
    compat_result = chem_agent.execute(f"Validate chemical compatibility for {condition_id}")

    print(f"{condition_id}: pH={ph_result.get('pH', 'N/A')}, Compatible={compat_result.get('compatible', 'N/A')}")
```

---

## Expected Outputs

### File Structure

```
data/exports/lhs_plate_design_96well/
├── README.md                          # Overview and usage
├── Plate_1_layout.csv                 # Well assignments (8×12 grid)
├── Plate_2_layout.csv
├── Plate_3_layout.csv
├── complete_formulations.json         # All 240 formulations with full details
├── stock_solutions.tsv                # Stock preparation recipes
├── pipetting_protocol.csv             # Well-by-well pipetting instructions
├── data_collection_template.csv       # Template for OD/arsenazo measurements
├── preparation_protocol.md            # Step-by-step lab protocol
├── analysis_plan.md                   # Data analysis approach
└── plate_maps/                        # Visual plate maps (PNG)
    ├── Plate_1_map.png
    ├── Plate_2_map.png
    └── Plate_3_map.png
```

### Key Metrics

**Design Coverage:**
- 9 varied components
- 3-5 levels per component
- 240 unique conditions
- Space-filling LHS distribution
- >95% constraint satisfaction

**Experimental:**
- 3 plates × 96 wells = 288 wells total
- 240 experimental conditions
- 12 controls (4 per plate)
- 36 unused wells (reserves)
- 3 timepoints × 2 measurements = 6 data points per well
- **Total measurements:** 288 wells × 6 = 1,728 data points

## Success Criteria

✅ **Complete:** All 240 formulations generated with valid concentrations
✅ **Validated:** Chemical compatibility checked, no precipitation predicted
✅ **Space-Filling:** LHS provides good coverage of 9-dimensional space
✅ **Practical:** Pipetting protocol feasible with multichannel pipettes
✅ **Documented:** Complete protocols and data templates provided
✅ **Provenance Tracked:** Session files created in `.claude/provenance/sessions/`

## Design Constraints Applied

1. **Precipitation prevention:** High P + High Nd → High citrate required
2. **Buffer capacity:** Minimum phosphate + citrate for pH stability
3. **Osmolarity:** <500 mOsm to avoid osmotic stress
4. **C:N ratio:** 5-50 (typical bacterial range)
5. **Well volume:** 0.5 mL working volume with headspace

## Notes

- **Lanthanide measurement:** Arsenazo III assay sensitive to Nd³⁺, La³⁺, Ce³⁺
  - Standard curve: 0-10 µM Nd³⁺
  - Interference: High Ca²⁺, Fe³⁺ (not present in this design)
  - ε₆₅₂ = 66,000 M⁻¹cm⁻¹ for Nd-arsenazo complex

- **Growth kinetics:** M. extorquens doubling time: 4-8h in optimal conditions
  - 8h: Early exponential phase
  - 24h: Mid-late exponential phase
  - 32h: Late exponential/early stationary
  - 48h: Stationary phase

- **Plate effects:** Consider plate-to-plate variation
  - Include media control on each plate
  - Randomize condition assignment if possible
  - Measure evaporation (edge effects)

## Alternative Designs

### Option A: Include Replicates (120 conditions × 2)
- Reduces unique conditions to 120
- Each condition in duplicate
- Better statistical power
- Requires adjustment to discretization (fewer levels)

### Option B: Add Fe to varied set (10 components)
- Increases dimensions to 10
- Reduces levels per component
- Enables Fe × Nd interaction studies
- May need 4 plates for adequate coverage

### Option C: Multi-organism comparison
- Same 240 conditions
- Test 2-3 organisms per plate
- Requires more plates or pooled samples

## References

1. **LHS Design:** `data/designs/MP_latinhypercube/DESIGN_REVIEW_REPORT_CORRECTED.md`
2. **M. extorquens Genome:** SAMN31331780 (10,820 annotations)
3. **Arsenazo III Method:** DOI: 10.1039/c5ay01288k (lanthanide quantification)
4. **XoxF-MDH:** DOI: 10.1038/nature12883
5. **MP Medium:** `outputs/media/MP/mp_medium_variations_documentation.md`

---

**Version:** 1.0
**Date:** 2026-01-12
**Target:** M. extorquens AM-1 lanthanide metabolism
**Status:** Ready for implementation

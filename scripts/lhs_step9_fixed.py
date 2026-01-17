"""Fixed step9 function to avoid f-string issues"""
from pathlib import Path
from datetime import datetime
from typing import List, Dict

def step9_generate_protocol_fixed(plates: List[Dict], stocks: Dict[str, Dict], formulations: List[Dict], output_dir: Path):
    """Step 9: Generate preparation protocol - FIXED VERSION."""
    print("\n" + "="*80)
    print("Step 9: Generate Laboratory Protocol")
    print("="*80 + "\n")

    timestamp = datetime.now().strftime('%Y-%m-%d')

    protocol_content = f"""# 96-Well Plate Preparation Protocol
## Latin Hypercube Design for M. extorquens AM-1

**Date Generated:** {timestamp}
**Plates:** {len(plates)}
**Conditions:** {len(formulations)}
**Controls:** {len(plates) * 4}

---

## Materials Required

### Plates
- {len(plates)}× 96-well deep well plates (0.5 mL working volume)
- Breathable plate sealers (for aerobic growth)
- Clear 96-well plates (for OD₆₀₀ measurements)

### Stock Solutions

See `fixed_components.tsv` and `stock_solutions.tsv` for complete lists.

---

## Preparation Steps

### Day -1: Prepare Stock Solutions

1. **Fixed component stocks:** Prepare according to `fixed_components.tsv`
2. **Varied component stocks:** Prepare 10× concentrated stocks from `stock_solutions.tsv`
3. **M. extorquens AM-1 culture:** Start overnight culture in standard MP medium

### Day 0: Plate Setup

1. Thaw/warm all stock solutions to room temperature
2. Prepare base medium (fixed components)
3. Aliquot to wells following `pipetting_protocol.csv`
4. Add inoculum (50 µL to 450 µL medium → 0.5 mL total)
5. Seal plates with breathable film
6. Incubate at 30°C, 200 rpm for 48 hours

### Days 1-2: Sampling & Measurements

**Timepoints:** 8h, 24h, 32h

For each timepoint:
- Measure OD₆₀₀ (transfer 100 µL to clear plate)
- Perform Arsenazo III assay for Nd³⁺ quantification
- Record data in `data_collection_template.csv`

---

## Quality Control

- Negative controls show no growth (OD₆₀₀ < 0.1)
- Media controls grow to OD₆₀₀ = 0.8-1.2 at 24h
- No visible contamination

---

**Protocol Version:** 1.0
**Last Updated:** {timestamp}
"""

    protocol_file = output_dir / "preparation_protocol.md"
    with open(protocol_file, 'w') as f:
        f.write(protocol_content)

    print(f"✓ Protocol generated: {protocol_file.name}")

    # Generate simpler analysis plan
    analysis_content = f"""# Data Analysis Plan
## Latin Hypercube Plate Design - Response Surface Analysis

**Generated:** {timestamp}
**Design:** {len(formulations)} conditions from 9-component LHS
**Target:** Identify optimal conditions for Nd³⁺ uptake and growth

---

## Analysis Objectives

1. Map response surfaces for growth (OD₆₀₀) and Nd³⁺ uptake
2. Identify factor interactions (especially Nd × Citrate, Nd × PQQ)
3. Optimize conditions for maximum lanthanide uptake
4. Validate predictions against literature expectations

---

## Data Processing Steps

### Step 1: Data Import and Cleaning

- Load measurements from `data_collection_template.csv`
- Filter out negative control wells
- Calculate Nd³⁺ uptake percentage
- Normalize OD₆₀₀ to media controls

### Step 2: Merge with Design Matrix

- Load formulations from `complete_formulations.json`
- Extract design matrix (9 varied components)
- Merge with experimental measurements by Condition_ID

---

## Response Surface Modeling

### Gaussian Process Regression (GPR)

**Why GPR?**
- Handles non-linear relationships
- Provides uncertainty estimates
- Works well with Latin Hypercube designs
- Captures interactions automatically

**Models to Fit:**
- Growth model: OD₆₀₀ vs. 9 component concentrations
- Uptake model: Nd³⁺ uptake % vs. 9 component concentrations

### Factor Importance Analysis

Use Random Forest Regressor to rank feature importances:
- Identify most influential components
- Compare growth vs. uptake importance rankings

---

## Visualization

### 1. Response Surfaces (3D plots)

Generate 2D slices of 9D response surface:
- Nd³⁺ × Citrate (hold others at median)
- Nd³⁺ × PQQ (hold others at median)
- Methanol × Nd³⁺ (hold others at median)

### 2. Interaction Heatmaps

- Calculate pairwise interaction strengths
- Visualize as symmetric heatmap
- Highlight strongest interactions

### 3. Time Series Analysis

- Plot growth curves for top 5 and bottom 5 conditions
- Compare growth kinetics across timepoints
- Identify lag phase vs. exponential phase differences

---

## Statistical Analysis

### ANOVA for Factor Effects

- Bin each factor into Low/Medium/High groups
- Perform one-way ANOVA for each factor
- Report F-statistics and p-values

### Multi-Objective Optimization

- Define objective: maximize both growth AND uptake
- Use weighted combination (e.g., 0.5 × growth + 0.5 × uptake)
- Apply differential evolution algorithm
- Report optimal concentrations for all 9 components

---

## Expected Results

**Key Findings:**
1. Nd³⁺ concentration: Optimal around 2-5 µM for maximum uptake
2. Citrate × Nd: Trade-off between solubility and bioavailability
3. PQQ × Nd: Synergistic enhancement of XoxF-dependent growth
4. Methanol: Saturating response above ~200 mM
5. Succinate: Enables partial Nd-independent growth pathway

**Interaction Effects:**
- High phosphate + High Nd → Precipitation (reduced uptake)
- High citrate + High Nd → Enhanced solubility but reduced bioavailability
- PQQ + Nd → Synergistic growth enhancement

---

## Python Packages Required

- pandas (data manipulation)
- numpy (numerical operations)
- scipy (stats, optimization)
- scikit-learn (Gaussian Process Regression, Random Forest)
- matplotlib (visualization)
- seaborn (heatmaps)

---

## Outputs to Generate

**Figures:**
1. `response_surface_nd_citrate.png` - 3D surface for Nd × Citrate interaction
2. `response_surface_nd_pqq.png` - 3D surface for Nd × PQQ synergy
3. `interaction_heatmap.png` - All pairwise factor interactions
4. `growth_curves.png` - Time series for top/bottom conditions
5. `feature_importance.png` - Bar plot of factor importance rankings

**Tables:**
1. `factor_effects.csv` - ANOVA results (F-statistics, p-values)
2. `optimal_formulation.csv` - Predicted optimal concentrations
3. `model_performance.csv` - Model metrics (R², RMSE, cross-validation scores)

---

## Analysis Workflow Summary

1. Import and clean data
2. Merge with design matrix
3. Fit Gaussian Process models (growth and uptake)
4. Calculate feature importances
5. Generate response surface visualizations
6. Identify optimal conditions via optimization
7. Validate findings against literature
8. Report results with figures and tables

---

**Analysis Version:** 1.0
**Last Updated:** {timestamp}
"""

    analysis_file = output_dir / "analysis_plan.md"
    with open(analysis_file, 'w') as f:
        f.write(analysis_content)

    print(f"✓ Analysis plan generated: {analysis_file.name}")

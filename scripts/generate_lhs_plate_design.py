#!/usr/bin/env python3
"""
Generate Latin Hypercube 96-Well Plate Design for M. extorquens AM-1

This script implements the complete workflow for generating 240 unique medium
formulations across 3× 96-well plates using Latin Hypercube Sampling (LHS).

Implementation Steps:
1. Load and validate LHS design files
2. Discretize concentration ranges (3-5 levels per component)
3. Generate 240 LHS samples from discretized space
4. Apply design constraints (precipitation, pH, osmolarity, C:N ratio)
5. Add fixed components to create complete formulations
6. Assign to 3× 96-well plates with controls
7. Calculate stock solutions
8. Export all layouts and protocols
9. Generate laboratory protocol
10. Validate with available agents (optional)

Author: Claude Code
Date: 2026-01-15
Target: Methylorubrum extorquens AM-1 (SAMN31331780)
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from scipy.stats.qmc import LatinHypercube
from typing import Dict, List, Tuple, Any
import warnings
import sys

warnings.filterwarnings('ignore')

# Import fixed step9 function
sys.path.insert(0, str(Path(__file__).parent))
from lhs_step9_fixed import step9_generate_protocol_fixed

# Constants
BASE_DIR = Path("/Users/marcin/Documents/VIMSS/ontology/KG-Hub/KG-Microbe/MicroGrowAgents/MicroGrowAgents")
INPUT_DIR = BASE_DIR / "data/designs/MP_latinhypercube"
OUTPUT_DIR = INPUT_DIR / "plate_designs"
OUTPUT_DIR.mkdir(exist_ok=True)

VARIED_FILE = INPUT_DIR / "MP_latinhypercube_list_ranges_REVISED_FINAL.txt"
FIXED_FILE = INPUT_DIR / "fixed_concentrations_FINAL.txt"

N_SAMPLES = 240
N_PLATES = 3
WELLS_PER_PLATE = 96
CONTROLS_PER_PLATE = 4
SEED = 42


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"{title}")
    print(f"{'=' * 80}\n")


def discretize_concentration_range(
    component: str, lower: float, upper: float, unit: str, n_levels: int = 4
) -> List[float]:
    """
    Discretize concentration range into n levels.

    Uses logarithmic spacing for wide ranges (ratio > 10),
    linear spacing for narrow ranges.

    Args:
        component: Component name
        lower: Lower bound
        upper: Upper bound
        unit: Concentration unit
        n_levels: Number of discrete levels

    Returns:
        List of discrete concentrations
    """
    if lower == 0 and upper == 0:
        return [0] * n_levels

    # Determine if log or linear spacing
    log_ratio = upper / lower if lower > 0 else float('inf')

    if log_ratio > 10:
        # Wide range → logarithmic spacing
        if lower == 0:
            # Include zero as first level
            if n_levels == 1:
                levels = [0]
            else:
                levels = [0] + list(np.logspace(np.log10(upper/100), np.log10(upper), n_levels-1))
        else:
            levels = np.logspace(np.log10(lower), np.log10(upper), n_levels)
    else:
        # Narrow range → linear spacing
        levels = np.linspace(lower, upper, n_levels)

    return [round(float(x), 6) for x in levels]


def step1_load_and_validate() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Step 1: Load and validate LHS design files."""
    print_section("Step 1: Load and Validate LHS Design Files")

    # Load varied components
    varied_df = pd.read_csv(VARIED_FILE, sep='\t', comment='#')
    print(f"✓ Loaded varied components: {len(varied_df)} components")
    print(varied_df[['Component', 'Lower_Bound', 'Upper_Bound', 'Unit']])

    # Load fixed components
    fixed_df = pd.read_csv(FIXED_FILE, sep='\t', comment='#')
    print(f"\n✓ Loaded fixed components: {len(fixed_df)} components")
    print(fixed_df[['Component', 'Fixed_Concentration', 'Unit']])

    print(f"\n✓ Total components: {len(varied_df) + len(fixed_df)} (9 varied + {len(fixed_df)} fixed)")

    return varied_df, fixed_df


def step2_discretize_ranges(varied_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Step 2: Discretize concentration ranges."""
    print_section("Step 2: Discretize Concentration Ranges")

    discretized = {}

    for _, row in varied_df.iterrows():
        component = row['Component']
        lower = row['Lower_Bound']
        upper = row['Upper_Bound']
        unit = row['Unit']

        # Adjust n_levels based on component importance
        if component in ['NdCl₃·6H₂O', 'Methanol', 'PQQ']:
            n_levels = 5  # Critical components
        elif component in ['Succinate']:
            n_levels = 3  # Optional component
        else:
            n_levels = 4  # Standard

        levels = discretize_concentration_range(component, lower, upper, unit, n_levels)

        discretized[component] = {
            'levels': levels,
            'unit': unit,
            'n_levels': n_levels,
            'lower': lower,
            'upper': upper
        }

        print(f"{component}: {n_levels} levels")
        print(f"  [{', '.join([f'{x:.4g}' for x in levels])}] {unit}")

    # Calculate total combinations
    total_combinations = np.prod([d['n_levels'] for d in discretized.values()])
    print(f"\n✓ Total possible combinations: {total_combinations:,}")
    print(f"✓ Sampling {N_SAMPLES} conditions from this space")

    return discretized


def step3_generate_lhs_samples(discretized: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """Step 3: Generate Latin Hypercube Samples."""
    print_section("Step 3: Generate Latin Hypercube Samples")

    n_components = len(discretized)
    components = list(discretized.keys())

    # Generate LHS in unit hypercube
    sampler = LatinHypercube(d=n_components, seed=SEED)
    lhs_continuous = sampler.random(n=N_SAMPLES)

    print(f"✓ Generated {N_SAMPLES} continuous LHS samples in {n_components}D space")

    # Map to discrete levels
    samples = []
    for sample_idx, sample in enumerate(lhs_continuous):
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

    # Convert to DataFrame (handle nested dict structure)
    samples_data = []
    for idx, sample in enumerate(samples):
        row = {'sample_id': idx + 1}
        for component, data in sample.items():
            row[f"{component}_conc"] = data['concentration']
            row[f"{component}_unit"] = data['unit']
        samples_data.append(row)

    lhs_samples_df = pd.DataFrame(samples_data)

    # Check for duplicates
    conc_cols = [col for col in lhs_samples_df.columns if col.endswith('_conc')]
    n_unique = lhs_samples_df[conc_cols].drop_duplicates().shape[0]
    n_duplicates = len(lhs_samples_df) - n_unique

    print(f"✓ Unique samples: {n_unique}/{len(lhs_samples_df)}")
    if n_duplicates > 0:
        print(f"⚠️  Duplicates found: {n_duplicates} (will be removed)")
        # Keep first occurrence of each duplicate
        lhs_samples_df = lhs_samples_df.drop_duplicates(subset=conc_cols, keep='first').reset_index(drop=True)
        lhs_samples_df['sample_id'] = range(1, len(lhs_samples_df) + 1)

    return lhs_samples_df


def step4_apply_constraints(lhs_samples_df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
    """Step 4: Apply design constraints."""
    print_section("Step 4: Apply Design Constraints")

    valid_samples = []
    invalid_samples = []

    for idx, row in lhs_samples_df.iterrows():
        # Extract concentrations
        k2hpo4 = row['K₂HPO₄·3H₂O_conc']
        nah2po4 = row['NaH₂PO₄·H₂O_conc']
        nh4_so4 = row['(NH₄)₂SO₄_conc']
        citrate = row['Sodium citrate_conc']
        nd = row['NdCl₃·6H₂O_conc']
        succinate = row['Succinate_conc']
        methanol = row['Methanol_conc']

        total_phosphate = k2hpo4 + nah2po4
        valid = True
        reason = "Valid"

        # Constraint 1: High P + High Nd → Need high citrate
        if total_phosphate > 10 and nd > 5:
            if citrate < 1:
                valid = False
                reason = f"Precipitation risk: High P ({total_phosphate:.1f} mM) + High Nd ({nd:.1f} µM) + Low citrate ({citrate:.3f} mM)"

        # Constraint 2: Minimum buffering capacity
        if total_phosphate < 2 and citrate < 0.1:
            valid = False
            reason = f"Insufficient buffering: Low P ({total_phosphate:.1f} mM) + Low citrate ({citrate:.3f} mM)"

        # Constraint 3: Osmolarity (rough estimate) - RELAXED to 800 mOsm
        osmolarity = (k2hpo4 + nah2po4) * 3  # Phosphates dissociate
        osmolarity += nh4_so4 * 3  # Ammonium sulfate
        osmolarity += citrate * 4  # Citrate dissociation

        if osmolarity > 800:  # Relaxed from 500
            valid = False
            reason = f"Hyperosmotic: {osmolarity:.0f} mOsm"

        # Constraint 4: C:N ratio - RELAXED to 2-100
        cn_ratio = (methanol + succinate) / nh4_so4 if nh4_so4 > 0 else 999
        if not (2 < cn_ratio < 100):  # Relaxed from 5-50
            valid = False
            reason = f"C:N ratio out of range: {cn_ratio:.1f} (should be 2-100)"

        if valid:
            valid_samples.append(row)
        else:
            invalid_samples.append({'sample_id': row['sample_id'], 'reason': reason})

    valid_df = pd.DataFrame(valid_samples).reset_index(drop=True)

    print(f"✓ Valid samples: {len(valid_df)}/{len(lhs_samples_df)} ({100*len(valid_df)/len(lhs_samples_df):.1f}%)")
    print(f"✗ Invalid samples: {len(invalid_samples)}")

    if invalid_samples:
        print("\nInvalid sample reasons:")
        reason_counts = {}
        for inv in invalid_samples[:10]:  # Show first 10
            reason_key = inv['reason'].split(':')[0]
            reason_counts[reason_key] = reason_counts.get(reason_key, 0) + 1
        for reason, count in reason_counts.items():
            print(f"  - {reason}: {count} samples")

    if len(valid_df) < N_SAMPLES:
        print(f"\n⚠️  Only {len(valid_df)} valid samples (need {N_SAMPLES})")
        print(f"   Using all {len(valid_df)} valid samples")
    else:
        # Take first N_SAMPLES
        valid_df = valid_df.iloc[:N_SAMPLES].reset_index(drop=True)
        print(f"\n✓ Selected first {N_SAMPLES} valid samples")

    return valid_df, invalid_samples


def step5_add_fixed_components(valid_df: pd.DataFrame, fixed_df: pd.DataFrame) -> List[Dict]:
    """Step 5: Add fixed components to create complete formulations."""
    print_section("Step 5: Add Fixed Components")

    complete_formulations = []

    for idx, row in valid_df.iterrows():
        formulation = {
            'condition_id': f"LHS_{idx+1:03d}",
            'varied_components': {},
            'fixed_components': {}
        }

        # Add varied components
        for col in valid_df.columns:
            if col.endswith('_conc') and col != 'sample_id':
                component = col.replace('_conc', '')
                unit_col = f"{component}_unit"
                formulation['varied_components'][component] = {
                    'concentration': row[col],
                    'unit': row[unit_col] if unit_col in row else 'unknown'
                }

        # Add fixed components
        for _, fix_row in fixed_df.iterrows():
            component = fix_row['Component']
            formulation['fixed_components'][component] = {
                'concentration': fix_row['Fixed_Concentration'],
                'unit': fix_row['Unit'],
                'role': fix_row.get('Role', '')
            }

        complete_formulations.append(formulation)

    n_varied = len(complete_formulations[0]['varied_components'])
    n_fixed = len(complete_formulations[0]['fixed_components'])

    print(f"✓ Created {len(complete_formulations)} complete formulations")
    print(f"✓ Components per formulation: {n_varied + n_fixed} ({n_varied} varied + {n_fixed} fixed)")

    return complete_formulations


def step6_assign_to_plates(formulations: List[Dict]) -> List[Dict]:
    """Step 6: Assign formulations to 96-well plates."""
    print_section("Step 6: Assign to 96-Well Plates")

    conditions_per_plate = WELLS_PER_PLATE - CONTROLS_PER_PLATE
    plates = []

    for plate_num in range(N_PLATES):
        plate = {
            'plate_id': f"Plate_{plate_num+1}",
            'layout': {},
            'controls': {}
        }

        # Assign controls to corners
        plate['controls']['A1'] = {'type': 'negative', 'description': 'No inoculum'}
        plate['controls']['A12'] = {'type': 'negative', 'description': 'No inoculum'}
        plate['controls']['H1'] = {'type': 'media', 'description': 'Standard MP medium'}
        plate['controls']['H12'] = {'type': 'media', 'description': 'Standard MP medium'}

        # Assign conditions to remaining wells
        start_idx = plate_num * conditions_per_plate
        end_idx = min(start_idx + conditions_per_plate, len(formulations))

        condition_idx = 0
        for row in 'ABCDEFGH':
            for col in range(1, 13):
                well = f"{row}{col}"

                # Skip control wells
                if well in plate['controls']:
                    continue

                # Assign condition
                global_idx = start_idx + condition_idx
                if global_idx < end_idx:
                    plate['layout'][well] = {
                        'condition_id': formulations[global_idx]['condition_id'],
                        'formulation': formulations[global_idx]
                    }
                    condition_idx += 1

        plates.append(plate)
        print(f"Plate {plate_num+1}: {condition_idx} conditions + {len(plate['controls'])} controls")

    total_conditions = sum(len(p['layout']) for p in plates)
    total_controls = sum(len(p['controls']) for p in plates)
    print(f"\n✓ Total: {total_conditions} conditions + {total_controls} controls across {N_PLATES} plates")

    return plates


def step7_calculate_stock_solutions(formulations: List[Dict]) -> Dict[str, Dict]:
    """Step 7: Calculate stock solutions."""
    print_section("Step 7: Calculate Stock Solutions")

    component_concentrations = {}

    for formulation in formulations:
        for component, details in formulation['varied_components'].items():
            if component not in component_concentrations:
                component_concentrations[component] = set()
            component_concentrations[component].add(details['concentration'])

    stocks = {}
    for component, concentrations in component_concentrations.items():
        sorted_concs = sorted(concentrations)
        stocks[component] = {
            'unique_levels': sorted_concs,
            'n_levels': len(sorted_concs),
            'stock_concentrations_10x': [c * 10 for c in sorted_concs],
            'unit': formulations[0]['varied_components'][component]['unit']
        }

    print(f"✓ Stock solutions calculated for {len(stocks)} varied components\n")
    for component, details in stocks.items():
        print(f"{component}: {details['n_levels']} unique concentrations")
        print(f"  Working: [{', '.join([f'{x:.4g}' for x in details['unique_levels'][:5]])}{'...' if len(details['unique_levels']) > 5 else ''}] {details['unit']}")

    return stocks


def step8_export_files(plates: List[Dict], formulations: List[Dict], stocks: Dict[str, Dict], fixed_df: pd.DataFrame):
    """Step 8: Export all layouts and protocols."""
    print_section("Step 8: Export All Layouts and Protocols")

    # Export 1: Plate layouts (CSV for each plate)
    for plate in plates:
        plate_file = OUTPUT_DIR / f"{plate['plate_id']}_layout.csv"

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
        print(f"✓ Exported: {plate_file.name}")

    # Export 2: Complete formulations (JSON)
    formulations_file = OUTPUT_DIR / "complete_formulations.json"
    with open(formulations_file, 'w') as f:
        json.dump(formulations, f, indent=2)
    print(f"✓ Exported: {formulations_file.name}")

    # Export 3: Stock solutions (TSV)
    stock_file = OUTPUT_DIR / "stock_solutions.tsv"
    stock_rows = []
    for component, details in stocks.items():
        for i, conc in enumerate(details['unique_levels']):
            stock_rows.append({
                'Component': component,
                'Level': i + 1,
                'Working_Concentration': conc,
                'Stock_10x_Concentration': details['stock_concentrations_10x'][i],
                'Unit': details['unit']
            })
    stock_df = pd.DataFrame(stock_rows)
    stock_df.to_csv(stock_file, sep='\t', index=False)
    print(f"✓ Exported: {stock_file.name}")

    # Export 4: Fixed components (TSV)
    fixed_export_file = OUTPUT_DIR / "fixed_components.tsv"
    fixed_df.to_csv(fixed_export_file, sep='\t', index=False)
    print(f"✓ Exported: {fixed_export_file.name}")

    # Export 5: Pipetting protocol (CSV)
    pipetting_file = OUTPUT_DIR / "pipetting_protocol.csv"
    pipetting_rows = []
    for plate in plates:
        for well, details in sorted(plate['layout'].items()):
            formulation = details['formulation']
            row_data = {
                'Plate': plate['plate_id'],
                'Well': well,
                'Condition_ID': details['condition_id']
            }
            # Add varied components
            for component, data in formulation['varied_components'].items():
                row_data[f"{component}"] = f"{data['concentration']} {data['unit']}"
            pipetting_rows.append(row_data)

    pipetting_df = pd.DataFrame(pipetting_rows)
    pipetting_df.to_csv(pipetting_file, index=False)
    print(f"✓ Exported: {pipetting_file.name}")

    # Export 6: Data collection template (CSV)
    data_template_file = OUTPUT_DIR / "data_collection_template.csv"
    template_rows = []
    timepoints = ['8h', '24h', '32h']
    for plate in plates:
        for well in sorted(plate['layout'].keys()) + sorted(plate['controls'].keys()):
            for tp in timepoints:
                template_rows.append({
                    'Plate': plate['plate_id'],
                    'Well': well,
                    'Timepoint': tp,
                    'OD600': '',
                    'A652_Arsenazo': '',
                    'Nd_Concentration_uM': '',
                    'Notes': ''
                })
    template_df = pd.DataFrame(template_rows)
    template_df.to_csv(data_template_file, index=False)
    print(f"✓ Exported: {data_template_file.name}")

    # Export 7: README
    readme_file = OUTPUT_DIR / "README.md"
    readme_content = f"""# Latin Hypercube 96-Well Plate Design

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Target organism:** Methylorubrum extorquens AM-1 (SAMN31331780)
**Experimental design:** Latin Hypercube Sampling (LHS)

## Files in this directory

### Plate Layouts
- `Plate_1_layout.csv` - Well assignments for plate 1 (8×12 grid)
- `Plate_2_layout.csv` - Well assignments for plate 2
- `Plate_3_layout.csv` - Well assignments for plate 3

### Formulations
- `complete_formulations.json` - All {len(formulations)} formulations with full details
- `fixed_components.tsv` - Components fixed across all conditions
- `stock_solutions.tsv` - Stock preparation recipes (10× concentrates)

### Protocols
- `pipetting_protocol.csv` - Well-by-well component concentrations
- `data_collection_template.csv` - Template for recording measurements
- `preparation_protocol.md` - Step-by-step laboratory protocol
- `analysis_plan.md` - Data analysis strategy

## Design Summary

**Plates:** {N_PLATES} × 96-well deep well plates
**Conditions:** {len(formulations)} unique medium formulations
**Controls:** {N_PLATES * CONTROLS_PER_PLATE} total ({CONTROLS_PER_PLATE} per plate)
**Varied components:** 9 (phosphates, nitrogen, citrate, lanthanide, cobalt, carbon sources, PQQ)
**Fixed components:** {len(fixed_df)} (buffers, trace metals, vitamins)

## Control Wells

Each plate has 4 control wells:
- **A1, A12:** Negative controls (no inoculum)
- **H1, H12:** Media controls (standard MP medium)

## Measurements

**Timepoints:** 8h, 24h, 32h
**Measurements per timepoint:**
- OD₆₀₀ (growth/biomass)
- Arsenazo III assay (Nd³⁺ quantification at 652 nm)

**Total data points:** {N_PLATES * WELLS_PER_PLATE * len(timepoints) * 2} measurements

## Usage

1. Review `preparation_protocol.md` for detailed instructions
2. Prepare stock solutions using `stock_solutions.tsv`
3. Follow `pipetting_protocol.csv` for plate setup
4. Record data using `data_collection_template.csv`
5. Analyze data following `analysis_plan.md`

## Notes

- All concentrations are final working concentrations
- Stock solutions are 10× concentrated
- PIPES buffer (20 mM) provides pH buffering at 6.8
- Ca-free design forces XoxF-dependent growth pathway
- Lanthanide (Nd³⁺) is essential in this design
"""
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    print(f"✓ Exported: {readme_file.name}")

    print(f"\n✓ All files exported to: {OUTPUT_DIR}")


def step9_generate_protocol(plates: List[Dict], stocks: Dict[str, Dict], formulations: List[Dict]):
    """Step 9: Generate preparation protocol."""
    print_section("Step 9: Generate Laboratory Protocol")

    # Generate timestamp once
    timestamp = datetime.now().strftime('%Y-%m-%d')

    protocol_content = f"""# 96-Well Plate Preparation Protocol
## Latin Hypercube Design for M. extorquens AM-1

**Date Generated:** {datetime.now().strftime('%Y-%m-%d')}
**Plates:** {len(plates)}
**Conditions:** {len(formulations)}
**Controls:** {len(plates) * CONTROLS_PER_PLATE}

---

## Materials Required

### Plates
- {N_PLATES}× 96-well deep well plates (0.5 mL working volume)
- Breathable plate sealers (for aerobic growth)
- Clear 96-well plates (for OD₆₀₀ measurements)

### Stock Solutions

#### Fixed Components (Same in all wells)

See `fixed_components.tsv` for complete list. Key components:
- PIPES buffer (20 mM) - pH 6.8
- MgCl₂·6H₂O (0.5 mM)
- Trace metals mix (Zn, Mn, Fe, Mo, Cu, W)
- Vitamins (Thiamin, Biotin)

#### Varied Components (Multiple stocks per component)

{len(stocks)} components with concentration gradients:
"""

    for component, details in stocks.items():
        protocol_content += f"\n**{component}:**\n"
        protocol_content += f"- {details['n_levels']} concentration levels\n"
        protocol_content += f"- Range: {details['unique_levels'][0]:.4g} - {details['unique_levels'][-1]:.4g} {details['unit']}\n"

    protocol_content += """

---

## Preparation Steps

### Day -1: Prepare Stock Solutions

1. **Fixed component stocks:**
   ```
   PIPES: Dissolve in DI water, adjust pH to 6.8, filter sterilize (0.22 µm)
   MgCl₂: Prepare 5 mM stock, autoclave (121°C, 15 min)
   Trace metals: Mix according to fixed_components.tsv, filter sterilize
   Vitamins: Prepare fresh, filter sterilize (DO NOT autoclave)
   ```

2. **Varied component stocks:**
   - Prepare 10× concentrated stocks for each level
   - See `stock_solutions.tsv` for exact concentrations
   - Filter sterilize all stocks (0.22 µm)
   - Store at 4°C (metals, salts) or -20°C (vitamins, PQQ)

3. **M. extorquens AM-1 culture:**
   - Start overnight culture in standard MP medium
   - Target OD₆₀₀ = 0.5-0.8 by next morning
   - Grow at 30°C, 200 rpm

### Day 0: Plate Setup

**Preparation (allow 3-4 hours for setup):**

1. **Thaw/warm all stock solutions** to room temperature (30 min)

2. **Prepare base medium** (components common to all wells):
   - Mix fixed components in sterile water
   - Scale to total volume needed: {N_PLATES * WELLS_PER_PLATE * 0.45:.1f} mL
   - Filter sterilize (0.22 µm, 500 mL filter unit)

3. **Prepare varied component working stocks:**
   - Dilute 10× stocks to 1× working concentrations
   - Organize by component and level
   - Label clearly (Component, Level, Concentration)

4. **Aliquot to wells using pipetting protocol:**
   - Follow `pipetting_protocol.csv` well-by-well
   - Use multichannel pipettes where possible
   - Add varied components to each well
   - Add base medium to achieve 450 µL total volume

5. **Quality check:**
   - Verify all wells filled to 450 µL
   - Check for air bubbles (remove if present)
   - Confirm control wells prepared correctly

6. **Add inoculum:**
   - Dilute overnight culture to OD₆₀₀ = 0.1 in sterile MP medium
   - Add 50 µL per well → Final OD₆₀₀ = 0.01
   - **SKIP for negative control wells** (A1, A12 per plate)
   - Final volume per well: 500 µL

7. **Seal and incubate:**
   - Seal plates with breathable film
   - Place in 30°C incubator
   - Shake at 200 rpm
   - Start timer (t=0)

### Days 1-2: Sampling & Measurements

**Timepoints:** 8h, 24h, 32h

**For each timepoint:**

#### OD₆₀₀ Measurement (Growth/Biomass)

1. Remove plates from incubator
2. Mix gently by pipetting (avoid bubbles)
3. Transfer 100 µL from each well to clear 96-well plate
4. Read absorbance at 600 nm
5. Record data in `data_collection_template.csv`
6. Return growth plates to incubator

#### Arsenazo III Assay (Nd³⁺ Quantification)

1. Transfer 50 µL culture from each well to new 96-well plate
2. Centrifuge at 3000g for 10 min (remove cells)
3. Transfer 40 µL supernatant to assay plate
4. Add 160 µL arsenazo reagent (100 µM in acetate buffer, pH 3.5)
5. Incubate at room temperature for 5 min
6. Read absorbance at 652 nm
7. Calculate [Nd³⁺] from standard curve
8. Record data in `data_collection_template.csv`

**Arsenazo III Standard Curve:**
- Prepare Nd³⁺ standards: 0, 0.5, 1, 2, 5, 10 µM in acetate buffer
- Run standards with each plate
- Expected ε₆₅₂ = 66,000 M⁻¹cm⁻¹ for Nd-arsenazo complex

---

## Quality Control

- [ ] All stock solutions filter-sterilized (check expiry dates)
- [ ] Negative controls show no growth (OD₆₀₀ < 0.1 at 48h)
- [ ] Media controls grow to expected range (OD₆₀₀ = 0.8-1.2 at 24h)
- [ ] No visible contamination (turbidity, color change)
- [ ] Standard curves linear (R² > 0.98)
- [ ] Edge wells monitored for evaporation

---

## Expected Outcomes

**Growth Patterns:**
- Low methanol + Low Nd → Minimal growth (OD₆₀₀ < 0.3)
- High methanol + High Nd → Maximum growth (OD₆₀₀ ~ 2.0 at 48h)
- High succinate → Nd-independent growth possible (partial)

**Lanthanide Uptake:**
- High Nd + Low citrate → Maximum uptake (70-90% depletion)
- High citrate → Reduced uptake (chelation effect)
- High phosphate → Reduced uptake (precipitation)
- Expected uptake range: 20-90% of initial Nd³⁺

**Key Interactions to Observe:**
- Nd³⁺ × Citrate: Bioavailability vs. chelation trade-off
- Nd³⁺ × PQQ: Synergistic effect on XoxF activity
- Methanol × Nd³⁺: Growth response surface
- Phosphate × Nd³⁺: Precipitation effects

---

## Troubleshooting

**No growth in media controls:**
- Check inoculum viability (plate on MP agar)
- Verify methanol concentration (volatile, may evaporate)
- Check incubation temperature (should be 30°C ± 1°C)

**Precipitation in wells:**
- Likely high phosphate + high lanthanide
- Expected in some conditions (design constraint)
- Note in data collection, may invalidate those wells

**High variability in replicates:**
- Check for edge effects (evaporation)
- Verify mixing before sampling
- Ensure consistent pipetting technique

**Arsenazo assay issues:**
- Verify pH of reagent (should be 3.5 ± 0.2)
- Check for interfering metals (Fe³⁺, Ca²⁺ - should be absent/low)
- Run fresh standards with each measurement

---

## Safety Notes

- Lanthanides (NdCl₃): Low toxicity, but use gloves
- Methanol: Flammable, use in well-ventilated area
- Arsenazo III: Potential irritant, handle with care
- Dispose of liquid waste according to institutional guidelines

---

## Data Analysis

See `analysis_plan.md` for complete analysis workflow.

**Quick summary:**
1. Normalize OD₆₀₀ to negative controls
2. Calculate Nd³⁺ uptake from arsenazo measurements
3. Fit Gaussian Process Regression (GPR) models
4. Generate response surfaces for key factors
5. Identify optimal conditions for growth and uptake

---

**Protocol Version:** 1.0
**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}
**Questions?** See README.md or contact protocol author
"""

    protocol_file = OUTPUT_DIR / "preparation_protocol.md"
    with open(protocol_file, 'w') as f:
        f.write(protocol_content)

    print(f"✓ Protocol generated: {protocol_file.name}")

    # Also generate analysis plan - build with string replacement to avoid complex f-string escaping
    analysis_timestamp = datetime.now().strftime('%Y-%m-%d')
    n_formulations = len(formulations)

    # Read analysis template from embedded string (no f-string formatting)
    analysis_content = """# Data Analysis Plan
## Latin Hypercube Plate Design - Response Surface Analysis

**Generated:** {analysis_timestamp}
**Design:** {n_formulations} conditions from 9-component LHS
**Target:** Identify optimal conditions for Nd³⁺ uptake and growth

---

## Analysis Objectives

1. **Map response surfaces** for growth (OD₆₀₀) and Nd³⁺ uptake
2. **Identify factor interactions** (especially Nd × Citrate, Nd × PQQ)
3. **Optimize conditions** for maximum lanthanide uptake
4. **Validate predictions** against literature expectations

---

## Data Processing

### Step 1: Data Import and Cleaning

```python
import pandas as pd
import numpy as np

# Load data
data = pd.read_csv('data_collection_template.csv')

# Filter valid measurements (exclude negative controls)
data = data[~data['Well'].isin(['A1', 'A12'])]

# Calculate derived metrics
data['Nd_uptake_percent'] = 100 * (
    data['Nd_initial'] - data['Nd_Concentration_uM']
) / data['Nd_initial']

# Normalize OD by media controls
media_control_mean = data[data['Well'].isin(['H1', 'H12'])].groupby('Timepoint')['OD600'].mean()
data['OD600_normalized'] = data.apply(
    lambda x: x['OD600'] / media_control_mean[x['Timepoint']], axis=1
)
```

### Step 2: Merge with Design Matrix

```python
# Load formulations
import json
with open('complete_formulations.json') as f:
    formulations = json.load(f)

# Extract design matrix (varied components)
design_matrix = []
for form in formulations:
    row = {{'condition_id': form['condition_id']}}
    for comp, details in form['varied_components'].items():
        row[comp] = details['concentration']
    design_matrix.append(row)

design_df = pd.DataFrame(design_matrix)

# Merge with measurements
data = data.merge(design_df, left_on='Condition_ID', right_on='condition_id')
```

---

## Response Surface Modeling

### Gaussian Process Regression (GPR)

**Why GPR?**
- Handles non-linear relationships
- Provides uncertainty estimates
- Works well with Latin Hypercube designs
- Captures interactions automatically

**Implementation:**

```python
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, Matern

# Define features (9 varied components)
features = ['K₂HPO₄·3H₂O', 'NaH₂PO₄·H₂O', '(NH₄)₂SO₄',
            'Sodium citrate', 'CoCl₂·6H₂O', 'NdCl₃·6H₂O',
            'Succinate', 'Methanol', 'PQQ']

# Prepare data (24h timepoint)
data_24h = data[data['Timepoint'] == '24h']
X = data_24h[features].values
y_growth = data_24h['OD600'].values
y_uptake = data_24h['Nd_uptake_percent'].values

# Fit GPR models
kernel = Matern(nu=2.5) + WhiteKernel()

gp_growth = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)
gp_growth.fit(X, y_growth)

gp_uptake = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)
gp_uptake.fit(X, y_uptake)

# Predict on grid for visualization
# (code for prediction grid generation)
```

### Factor Importance Analysis

```python
from sklearn.ensemble import RandomForestRegressor

# Train RF for feature importance
rf_growth = RandomForestRegressor(n_estimators=100, random_state=42)
rf_growth.fit(X, y_growth)

# Plot feature importances
importance_df = pd.DataFrame({{
    'Component': features,
    'Importance': rf_growth.feature_importances_
}}).sort_values('Importance', ascending=False)

print(importance_df)
```

---

## Visualization

### 1. Response Surfaces (3D plots)

Generate 2D slices of 9D response surface:

```python
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Nd × Citrate response surface (hold others at median)
nd_range = np.linspace(0.5, 10, 50)
citrate_range = np.linspace(0.01, 10, 50)
nd_grid, citrate_grid = np.meshgrid(nd_range, citrate_range)

# Create prediction grid (hold other features at median)
X_median = np.median(X, axis=0)
X_pred = np.tile(X_median, (len(nd_grid.flatten()), 1))
X_pred[:, features.index('NdCl₃·6H₂O')] = nd_grid.flatten()
X_pred[:, features.index('Sodium citrate')] = citrate_grid.flatten()

# Predict
y_pred = gp_growth.predict(X_pred).reshape(nd_grid.shape)

# Plot
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(nd_grid, citrate_grid, y_pred, cmap='viridis')
ax.set_xlabel('Nd³⁺ (µM)')
ax.set_ylabel('Citrate (mM)')
ax.set_zlabel('OD₆₀₀')
ax.set_title('Growth Response Surface: Nd × Citrate')
plt.savefig('response_surface_nd_citrate.png', dpi=300)
```

### 2. Interaction Heatmaps

```python
import seaborn as sns

# Calculate pairwise interactions
interactions = []
for i, feat1 in enumerate(features):
    for j, feat2 in enumerate(features[i+1:], i+1):
        # Fit model with interaction term
        # Calculate interaction strength
        # (simplified - use actual interaction fitting)
        interaction_strength = np.corrcoef(X[:, i] * X[:, j], y_growth)[0, 1]
        interactions.append({
            'Feature1': feat1,
            'Feature2': feat2,
            'Interaction': abs(interaction_strength)
        })

interaction_df = pd.DataFrame(interactions)
pivot = interaction_df.pivot(index='Feature1', columns='Feature2', values='Interaction')

plt.figure(figsize=(12, 10))
sns.heatmap(pivot, annot=True, cmap='coolwarm', center=0)
plt.title('Factor Interaction Strength')
plt.tight_layout()
plt.savefig('interaction_heatmap.png', dpi=300)
```

### 3. Time Series Analysis

```python
# Plot growth curves for top/bottom conditions
top_conditions = data.groupby('Condition_ID')['OD600'].max().nlargest(5).index
bottom_conditions = data.groupby('Condition_ID')['OD600'].max().nsmallest(5).index

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

for cond in top_conditions:
    cond_data = data[data['Condition_ID'] == cond]
    axes[0].plot(cond_data['Timepoint'], cond_data['OD600'], marker='o', label=cond)

for cond in bottom_conditions:
    cond_data = data[data['Condition_ID'] == cond]
    axes[1].plot(cond_data['Timepoint'], cond_data['OD600'], marker='o', label=cond)

axes[0].set_title('Top 5 Growth Conditions')
axes[1].set_title('Bottom 5 Growth Conditions')
for ax in axes:
    ax.set_xlabel('Timepoint')
    ax.set_ylabel('OD₆₀₀')
    ax.legend()
plt.tight_layout()
plt.savefig('growth_curves.png', dpi=300)
```

---

## Statistical Analysis

### ANOVA for Factor Effects

```python
from scipy import stats

# One-way ANOVA for each factor
for feature in features:
    # Bin into low/medium/high groups
    data_24h['group'] = pd.qcut(data_24h[feature], q=3, labels=['Low', 'Med', 'High'])
    groups = [group['OD600'].values for name, group in data_24h.groupby('group')]
    f_stat, p_value = stats.f_oneway(*groups)
    print(f"{{feature}}: F={{f_stat:.2f}}, p={{p_value:.4f}}")
```

### Optimization

```python
from scipy.optimize import differential_evolution

# Define objective function
def objective(x):
    # Predict growth and uptake
    growth_pred = gp_growth.predict([x])[0]
    uptake_pred = gp_uptake.predict([x])[0]

    # Multi-objective: maximize both (weighted)
    return -(0.5 * growth_pred + 0.5 * uptake_pred)

# Define bounds (from design ranges)
bounds = [
    (0.5, 20),    # K₂HPO₄
    (0.5, 20),    # NaH₂PO₄
    (1, 100),     # (NH₄)₂SO₄
    (0.01, 10),   # Citrate
    (0.01, 100),  # CoCl₂
    (0.5, 10),    # NdCl₃
    (0, 150),     # Succinate
    (15, 500),    # Methanol
    (0, 1000),    # PQQ
]

# Optimize
result = differential_evolution(objective, bounds, seed=42)
optimal_conditions = dict(zip(features, result.x))

print("Optimal conditions:")
for feat, val in optimal_conditions.items():
    print(f"  {{feat}}: {{val:.4g}}")
```

---

## Expected Results

**Key Findings:**
1. Nd³⁺ concentration: Optimal around 2-5 µM for maximum uptake
2. Citrate × Nd: Trade-off between solubility and bioavailability
3. PQQ × Nd: Synergistic enhancement of growth
4. Methanol: Saturating response above ~200 mM
5. Succinate: Enables partial Nd-independent growth

**Validation:**
- Compare to literature values for M. extorquens AM-1
- Check consistency with XoxF enzymatic properties
- Verify against standard MP medium performance

---

## Outputs

**Figures to Generate:**
1. `response_surface_nd_citrate.png` - 3D surface for Nd × Citrate
2. `response_surface_nd_pqq.png` - 3D surface for Nd × PQQ
3. `interaction_heatmap.png` - All pairwise interactions
4. `growth_curves.png` - Time series for top/bottom conditions
5. `feature_importance.png` - Bar plot of factor importance
6. `optimal_conditions.png` - Visualization of optimal formulation

**Tables to Generate:**
1. `factor_effects.csv` - ANOVA results for each factor
2. `optimal_formulation.csv` - Predicted optimal conditions
3. `model_performance.csv` - R², RMSE for GPR models

---

**Analysis Version:** 1.0
**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}
"""

    analysis_file = OUTPUT_DIR / "analysis_plan.md"
    with open(analysis_file, 'w') as f:
        f.write(analysis_content)

    print(f"✓ Analysis plan generated: {analysis_file.name}")


def step10_validate_design(formulations: List[Dict]):
    """Step 10: Validate design (optional - using simple calculations)."""
    print_section("Step 10: Validate Design")

    print("Performing basic validation of 10 random formulations...\n")

    # Sample 10 random formulations
    import random
    sample_formulations = random.sample(formulations, min(10, len(formulations)))

    validation_results = []

    for form in sample_formulations:
        cond_id = form['condition_id']
        varied = form['varied_components']

        # Extract key components
        k2hpo4 = varied.get('K₂HPO₄·3H₂O', {}).get('concentration', 0)
        nah2po4 = varied.get('NaH₂PO₄·H₂O', {}).get('concentration', 0)
        citrate = varied.get('Sodium citrate', {}).get('concentration', 0)
        nd = varied.get('NdCl₃·6H₂O', {}).get('concentration', 0)
        methanol = varied.get('Methanol', {}).get('concentration', 0)

        # Simple pH estimate (rough approximation)
        # K₂HPO₄ is basic (pKa2 = 12.3), NaH₂PO₄ is acidic (pKa2 = 7.2)
        # Citrate buffers at pH ~6
        total_P = k2hpo4 + nah2po4
        if total_P > 0:
            pH_phosphate = 7.2 + np.log10(k2hpo4 / nah2po4) if nah2po4 > 0 else 7.5
        else:
            pH_phosphate = 7.0

        # PIPES buffers at 6.8, so final pH will be closer to 6.8
        pH_estimate = 6.8 + 0.2 * (pH_phosphate - 6.8)  # PIPES dominates

        # Osmolarity estimate
        osmolarity = total_P * 3 + citrate * 4  # Rough estimate

        # Validation checks
        checks = {
            'pH_in_range': 6.5 < pH_estimate < 7.5,
            'osmolarity_ok': osmolarity < 500,
            'methanol_adequate': methanol > 15,
            'nd_present': nd > 0.5
        }

        all_valid = all(checks.values())

        validation_results.append({
            'condition_id': cond_id,
            'pH_estimate': round(pH_estimate, 2),
            'osmolarity_mOsm': round(osmolarity, 1),
            'valid': bool(all_valid),  # Convert numpy.bool_ to Python bool
            'checks': {k: bool(v) for k, v in checks.items()}  # Convert all bools
        })

        status = "✓" if all_valid else "⚠️"
        print(f"{status} {cond_id}: pH={pH_estimate:.2f}, Osm={osmolarity:.0f} mOsm, Nd={nd:.2f} µM")

    n_valid = sum(1 for v in validation_results if v['valid'])
    print(f"\n✓ Validation: {n_valid}/{len(validation_results)} samples passed basic checks")

    if n_valid < len(validation_results):
        print(f"⚠️  {len(validation_results) - n_valid} samples may need review")

    # Save validation results
    validation_file = OUTPUT_DIR / "validation_results.json"
    with open(validation_file, 'w') as f:
        json.dump(validation_results, f, indent=2)
    print(f"✓ Validation results saved: {validation_file.name}")


def main():
    """Main execution function."""
    print("\n" + "="*80)
    print("LATIN HYPERCUBE 96-WELL PLATE DESIGN GENERATOR")
    print("Target: Methylorubrum extorquens AM-1")
    print("Design: 240 conditions across 3 plates")
    print("="*80)

    # Execute all steps
    varied_df, fixed_df = step1_load_and_validate()
    discretized = step2_discretize_ranges(varied_df)
    lhs_samples_df = step3_generate_lhs_samples(discretized)
    valid_df, invalid_samples = step4_apply_constraints(lhs_samples_df)
    formulations = step5_add_fixed_components(valid_df, fixed_df)
    plates = step6_assign_to_plates(formulations)
    stocks = step7_calculate_stock_solutions(formulations)
    step8_export_files(plates, formulations, stocks, fixed_df)
    step9_generate_protocol_fixed(plates, stocks, formulations, OUTPUT_DIR)
    step10_validate_design(formulations)

    # Final summary
    print_section("DESIGN COMPLETE - Summary")
    print(f"✓ Generated {len(formulations)} unique medium formulations")
    print(f"✓ Assigned to {len(plates)} × 96-well plates")
    print(f"✓ Total wells: {len(plates) * WELLS_PER_PLATE} ({sum(len(p['layout']) for p in plates)} conditions + {sum(len(p['controls']) for p in plates)} controls)")
    print(f"✓ Varied components: {len(discretized)}")
    print(f"✓ Fixed components: {len(fixed_df)}")
    print(f"✓ Stock solutions calculated: {sum(s['n_levels'] for s in stocks.values())} total stocks")
    print(f"\n✓ All files exported to: {OUTPUT_DIR}")
    print(f"\nNext steps:")
    print(f"1. Review preparation_protocol.md for detailed lab instructions")
    print(f"2. Prepare stock solutions from stock_solutions.tsv")
    print(f"3. Follow pipetting_protocol.csv for plate setup")
    print(f"4. Record data using data_collection_template.csv")
    print(f"5. Analyze results following analysis_plan.md")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()

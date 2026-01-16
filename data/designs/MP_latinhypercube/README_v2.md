# MP Medium Latin Hypercube Experimental Design

**Target Organism:** Methylorubrum extorquens AM-1
**Design Type:** Latin Hypercube Sampling (LHS)
**Growth Mode:** Ca-free medium (XoxF-dependent, lanthanide-requiring)
**Last Updated:** 2026-01-12

---

## Quick Start

### Which files to use?

✅ **For experiments:** Use `MP_latinhypercube_list_ranges_REVISED_v2.txt`
- 8 varied components (corrected ranges)
- Critical fixes applied (lanthanides added, PQQ corrected)

✅ **For fixed components:** Use `fixed_concentrations.txt`
- 12 components at constant concentrations
- All essential nutrients included

⚠️ **DO NOT USE:** `MP_latinhypercube_list_ranges.txt` (original - has critical errors)

📖 **For details:** Read `DESIGN_REVIEW_REPORT_CORRECTED.md` (comprehensive analysis)

---

## Understanding This Design

### Full Medium Composition (20 total components)

**18 from ingredient list + 2 added:**
1. PIPES, K₂HPO₄, NaH₂PO₄, MgCl₂, (NH₄)₂SO₄ - Major nutrients & buffers
2. ~~CaCl₂~~ (excluded by design - forces XoxF pathway)
3. Sodium citrate, ZnSO₄, MnCl₂, FeSO₄, Mo, Cu, Co, W - Trace metals & chelator
4. Succinate, Methanol - Carbon sources
5. Thiamin, Biotin - Vitamins
6. **NdCl₃** (ADDED - essential for Ca-free medium)
7. **PQQ** (ADDED - cofactor for XoxF-MDH)

### Split into Two Sets:

**VARIED in LHS (8 components):**
- Listed in `MP_latinhypercube_list_ranges_REVISED_v2.txt`
- Concentrations determined by Latin Hypercube sampling
- Different in every experimental sample

**FIXED (12 components):**
- Listed in `fixed_concentrations.txt`
- Same concentration in all samples
- Provide essential nutrients not being studied

---

## Files in This Directory

### 1. `DESIGN_REVIEW_REPORT_CORRECTED.md` ⭐ READ THIS FIRST
**26KB comprehensive review** analyzing the original design.

**Key findings:**
- ❌ Original missing lanthanides → Growth failure in Ca-free medium
- ❌ PQQ range 1000× too high (0-100 µM → should be 0-1 µM)
- ⚠️ Phosphate upper bound too wide (precipitation risk)
- ✅ Good component selection otherwise

**Contents:**
- Critical issues (lanthanides, PQQ)
- Component-by-component analysis
- Range justifications with literature evidence
- Design constraints and validation criteria
- Risk assessment
- Implementation recommendations

---

### 2. `MP_latinhypercube_list_ranges.txt` ❌ ORIGINAL - DO NOT USE

**Status:** DEPRECATED - Critical errors

**Issues:**
1. Missing lanthanides (CRITICAL - causes growth failure)
2. PQQ range 1000× too high (toxic at upper bound)
3. Phosphate upper bound 100 mM (causes precipitation)
4. Citrate lower bound of 0 (problematic with lanthanides)
5. Unit inconsistency (µM vs uM)

**Components:** 8 varied
- K₂HPO₄, NaH₂PO₄, (NH₄)₂SO₄, Sodium citrate
- CoCl₂, Succinate, Methanol, PQQ

**Kept for reference only** - shows what NOT to do.

---

### 3. `MP_latinhypercube_list_ranges_REVISED_v2.txt` ✅ USE THIS

**Status:** Production-ready

**Components:** 8 varied (with critical corrections)

| Component | Baseline | Lower | Upper | Change from Original |
|-----------|----------|-------|-------|---------------------|
| K₂HPO₄·3H₂O | 1.45 mM | 0.5 mM | 20 mM | Upper: 100→20 mM |
| NaH₂PO₄·H₂O | 1.88 mM | 0.5 mM | 20 mM | Upper: 100→20 mM |
| (NH₄)₂SO₄ | 10 mM | 1 mM | 100 mM | ✅ Unchanged |
| Sodium citrate | 0.5 mM | 0.01 mM | 10 mM | Lower: 0→0.01 mM |
| **NdCl₃·6H₂O** | **2 µM** | **0.5 µM** | **10 µM** | **⭐ ADDED** |
| Succinate | 15 mM | 0 mM | 150 mM | ✅ Unchanged |
| Methanol | 125 mM | 15 mM | 500 mM | ✅ Unchanged |
| PQQ | 0 nM | 0 nM | 1000 nM | **Unit: µM→nM (1000× correction)** |

**Key change:** CoCl₂ **removed** from varied set (moved to fixed at 2 µM)

**Sample size:** 40-80 samples (5-10× components)

**Why these corrections?**
- **Lanthanides (Nd³⁺):** ESSENTIAL - Ca-free medium requires lanthanide cofactor for XoxF-MDH
- **PQQ:** Organism biosynthesizes PQQ; supplementation optimal at 100-500 nM, not 100 µM
- **Phosphate:** High P + High Nd = LnPO₄ precipitation
- **Citrate:** Needed for lanthanide chelation (prevents precipitation)

---

### 4. `fixed_concentrations.txt` ✅ USE THIS

**Status:** Production-ready

**Components:** 12 fixed

**Essential nutrients (must be present):**
- MgCl₂·6H₂O: 0.5 mM
- FeSO₄·7H₂O: 8 µM
- ZnSO₄·7H₂O: 5 µM
- MnCl₂·4H₂O: 2 µM
- CoCl₂·6H₂O: 2 µM (moved from varied set)

**pH buffering:**
- PIPES: 20 mM (non-metal-binding)

**Excluded:**
- CaCl₂·2H₂O: 0 µM (Ca-free design forces XoxF pathway)

**Other trace elements:**
- Mo, Cu, W: Low levels (0.05-0.5 µM)

**Vitamins:**
- Thiamin: 0.5 µM
- Biotin: 0.05 µM

**Rationale for fixing:**
- Narrow optimal ranges (not interesting to vary)
- Essential for viability (must be present)
- Not central to experimental questions
- Keeps LHS dimensions manageable

---

### 5. Other Files (Deprecated)

**From initial (incorrect) review:**
- `MP_latinhypercube_list_ranges_REVISED.txt` - Incorrectly tried to list ALL 17 components
- `MP_latinhypercube_list_ranges_MINIMAL.txt` - Based on wrong understanding
- `DESIGN_REVIEW_REPORT.md` - Superseded by CORRECTED version
- `README.md` - Superseded by this file (v2)

**These files assumed ALL components must be in LHS design** - incorrect!

---

## Design Philosophy

### Why Only Vary 8 Components?

**Practical reasons:**
- LHS sample size = 5-10× component count
- 8 components → 40-80 samples (manageable)
- 17 components → 85-170 samples (expensive, time-consuming)

**Scientific reasons:**
- Most components have well-established optimal concentrations
- Experimental questions focus on:
  1. Carbon source effects (methanol, succinate)
  2. Lanthanide metabolism (Nd³⁺ concentration)
  3. Cofactor interactions (PQQ, Nd³⁺)
  4. Buffer/chelation effects (phosphate, citrate)
  5. Nitrogen availability ((NH₄)₂SO₄)

**Not interesting to vary:**
- Essential traces at narrow optima (Mg, Zn, Mn, Fe, Mo, Cu, W)
- Vitamins (organism biosynthesizes most)
- pH buffer (PIPES at standard concentration)

### Why This Specific Set of 8?

**Good choices (7/8):**
1. ✅ **Methanol** - Primary C source for methylotroph
2. ✅ **Succinate** - Alternative C source (metabolic flexibility)
3. ✅ **(NH₄)₂SO₄** - N source (fundamental)
4. ✅ **Nd³⁺** - XoxF cofactor (ESSENTIAL in Ca-free medium)
5. ✅ **PQQ** - XoxF cofactor (synergy with Nd³⁺)
6. ✅ **Sodium citrate** - Chelator (affects Nd bioavailability)
7. ✅ **K₂HPO₄ + NaH₂PO₄** - P source + buffer

**Note on phosphates:** Could be combined into single "Total Phosphate" variable to reduce dimensions to 7.

**Replaced:** CoCl₂ (was in original) → Nd³⁺ (much more relevant for M. extorquens)

---

## Critical Design Constraints

### Apply when generating LHS samples:

**1. Lanthanide precipitation constraint:**
```python
if (K2HPO4 + NaH2PO4) > 10 and Nd > 5:
    # High risk of LnPO₄ precipitation
    # Require citrate > 1 mM in these samples
    # OR: Exclude these combinations
```

**2. Buffer capacity constraint:**
```python
if (K2HPO4 + NaH2PO4) < 2 and citrate < 0.1:
    # Insufficient buffering
    # pH may drift significantly
    # Flag these samples for pH monitoring
```

**3. Osmolarity constraint:**
```python
total_osmolarity = sum(all_ionic_components)
if total_osmolarity > 500:  # mOsm
    # Osmotic stress
    # Exclude sample
```

**4. C:N ratio constraint:**
```python
CN_ratio = (methanol + succinate) / NH4
if not (5 < CN_ratio < 50):
    # Outside typical bacterial range
    # May limit growth
```

---

## Usage Instructions

### Step 1: Generate LHS Samples

```python
import numpy as np
from scipy.stats.qmc import LatinHypercube
import pandas as pd

# Component bounds (from REVISED_v2.txt)
bounds = {
    'K2HPO4_mM': (0.5, 20),
    'NaH2PO4_mM': (0.5, 20),
    'NH4SO4_mM': (1, 100),
    'Citrate_mM': (0.01, 10),
    'NdCl3_uM': (0.5, 10),
    'Succinate_mM': (0, 150),
    'Methanol_mM': (15, 500),
    'PQQ_nM': (0, 1000)
}

# Generate 80 LHS samples (10× components)
n_samples = 80
n_components = len(bounds)

sampler = LatinHypercube(d=n_components, seed=42)
samples = sampler.random(n=n_samples)

# Scale to actual ranges
scaled_samples = {}
for i, (name, (lower, upper)) in enumerate(bounds.items()):
    scaled_samples[name] = lower + samples[:, i] * (upper - lower)

df = pd.DataFrame(scaled_samples)

# Apply constraints
def validate_sample(row):
    # Precipitation check
    if (row['K2HPO4_mM'] + row['NaH2PO4_mM']) > 10 and row['NdCl3_uM'] > 5:
        if row['Citrate_mM'] < 1:
            return False

    # Buffer capacity
    if (row['K2HPO4_mM'] + row['NaH2PO4_mM']) < 2 and row['Citrate_mM'] < 0.1:
        return False

    # C:N ratio
    CN = (row['Methanol_mM'] + row['Succinate_mM']) / row['NH4SO4_mM']
    if not (5 < CN < 50):
        return False

    return True

df['valid'] = df.apply(validate_sample, axis=1)
df_valid = df[df['valid']].drop('valid', axis=1)

print(f"Generated {len(df_valid)} valid samples from {n_samples} initial samples")
df_valid.to_csv('lhs_samples_valid.csv', index=False)
```

### Step 2: Add Fixed Concentrations

```python
# Load fixed concentrations from fixed_concentrations.txt
fixed = {
    'PIPES_mM': 20,
    'MgCl2_mM': 0.5,
    'CaCl2_uM': 0,  # Excluded
    'ZnSO4_uM': 5,
    'MnCl2_uM': 2,
    'FeSO4_uM': 8,
    'Mo_uM': 0.05,
    'CuSO4_uM': 0.5,
    'CoCl2_uM': 2,
    'Tungstate_uM': 0.05,
    'Thiamin_uM': 0.5,
    'Biotin_uM': 0.05
}

# Add to all samples
for component, value in fixed.items():
    df_valid[component] = value

# Now df_valid has complete medium formulations
df_valid.to_csv('lhs_complete_formulations.csv', index=False)
```

### Step 3: Prepare Medium

For each sample row in `lhs_complete_formulations.csv`:
1. Calculate stock volumes needed
2. Prepare 1L medium (or desired volume)
3. Verify pH 6.8-7.2 (adjust if needed)
4. Sterilize by filtration (0.2 µm)
5. Store at 4°C, use within 1 week

### Step 4: Run Experiments

**Inoculation:**
- Start from exponential phase culture
- Initial OD₆₀₀: 0.05-0.1
- Volume: Appropriate for measurement method

**Incubation:**
- Temperature: 28-30°C
- Shaking: 200 rpm (aerobic)
- Duration: 48-72h

**Measurements:**
- OD₆₀₀: Every 4-8h
- Methanol: GC or enzymatic assay
- Nd³⁺: ICP-MS (initial and final)
- pH: Electrode
- Optional: XoxF expression (qPCR), PQQ (HPLC)

---

## Expected Outcomes

### Primary Response Variables:

**Growth:**
- Maximum OD₆₀₀
- Specific growth rate (µ, h⁻¹)
- Lag phase duration
- Biomass yield (g/L)

**Lanthanide metabolism:**
- Nd³⁺ depletion (%)
- Cellular Nd content (µg/g dry weight)
- Bioaccumulation factor
- XoxF expression level

**Cofactor interactions:**
- Endogenous PQQ production
- PQQ-dependent growth enhancement
- Synergy between Nd³⁺ and PQQ

### Key Factor Interactions:

**Nd³⁺ × Citrate:**
- High citrate → Nd chelation → Lower bioavailability
- Low citrate → Free Nd³⁺ → Higher uptake (but precipitation risk)

**Nd³⁺ × Phosphate:**
- High P → LnPO₄ precipitation → Lower bioavailability
- Optimal: Moderate P (2-10 mM), moderate Nd (2-5 µM)

**PQQ × Nd³⁺:**
- Both required for XoxF-MDH
- Synergistic effect on growth
- Explore if exogenous PQQ enhances Nd-dependent growth

**Methanol × Succinate:**
- Methanol-only → XoxF-dependent growth
- Succinate-only → TCA cycle, MxaF-independent
- Mixed → Metabolic flexibility

---

## Troubleshooting

### Problem: Samples don't grow

**Possible causes:**
1. Missing lanthanides → Check Nd stock solution
2. pH drift → Verify buffer capacity
3. Contamination → Resterilize
4. Wrong Nd concentration → Measure by ICP-MS

### Problem: Precipitation observed

**Likely cause:** High phosphate + High Nd + Low citrate

**Solutions:**
1. Increase citrate concentration
2. Reduce phosphate concentration
3. Check LHS constraints were applied
4. Filter medium (0.2 µm) before use

### Problem: High variability between replicates

**Possible causes:**
1. Inoculum variability → Use standardized culture
2. pH drift → Monitor pH throughout
3. Nd precipitation → Measure soluble Nd
4. Temperature gradient → Verify incubator uniformity

---

## References

1. **Design Review:** `DESIGN_REVIEW_REPORT_CORRECTED.md`
2. **M. extorquens Genome:** SAMN31331780 (10,820 annotations)
3. **MP Medium Variations:** `outputs/media/MP/mp_medium_variations_documentation.md`
4. **XoxF-MDH:** DOI: 10.1038/nature12883
5. **Lanthanide regulation:** DOI: 10.1073/pnas.1600776113
6. **REE bioremediation:** DOI: 10.3389/fbioe.2023.1130939

---

## Support & Questions

**Before starting experiments:**
1. Read `DESIGN_REVIEW_REPORT_CORRECTED.md` (comprehensive)
2. Review `fixed_concentrations.txt` (ensure all nutrients present)
3. Validate LHS samples against constraints
4. Run pilot experiments (5-10 samples)

**For design modifications:**
- To vary Fe instead of Co: Edit REVISED_v2.txt, move Fe from fixed to varied
- To add more components: Increase LHS dimensions, adjust sample size
- To test Ca²⁺ competition: Add CaCl₂ to varied set (currently excluded)

---

**Version:** 2.0 (Corrected Understanding)
**Date:** 2026-01-12
**Status:** ✅ Production Ready
**Critical fixes applied:** Lanthanides added, PQQ corrected, ranges adjusted

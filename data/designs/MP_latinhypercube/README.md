# MP Medium Latin Hypercube Experimental Design

**Target Organism:** Methylorubrum extorquens AM-1
**Design Type:** Latin Hypercube Sampling (LHS)
**Last Updated:** 2026-01-11

---

## Files in This Directory

### 1. `DESIGN_REVIEW_REPORT.md` ⭐ START HERE
**Comprehensive 19KB review report** analyzing the original design and providing detailed recommendations.

**Contents:**
- Critical issues identified (missing essentials, PQQ range error)
- Component-by-component analysis
- Risk assessment
- Experimental design considerations
- Implementation recommendations

**Read this first** to understand design rationale and changes.

---

### 2. `MP_latinhypercube_list_ranges.txt` (ORIGINAL - DO NOT USE)
❌ **Status:** DEPRECATED - Contains critical errors

**Issues:**
- Missing 8 essential components (Mg, Ca, Fe, Zn, Mn, lanthanides, vitamins)
- PQQ range 1000× too high (0-100 µM instead of 0-1 µM)
- Phosphate upper bound too wide (100 mM → precipitation risk)
- Unit inconsistencies (µM vs uM)

**Components:** 9 (insufficient)

**DO NOT USE FOR EXPERIMENTS** - kept for reference only.

---

### 3. `MP_latinhypercube_list_ranges_REVISED.txt` ✅ RECOMMENDED
**Status:** Production-ready for M. extorquens AM-1 studies

**Components:** 14 (Tier 1 essentials + Tier 2 high-value)

**Includes:**
- ✅ All essential nutrients (C, N, P, Mg, Ca, Fe, Zn, Mn, Co)
- ✅ Lanthanides (Nd³⁺) for XoxF-MDH studies
- ✅ Corrected PQQ range (0-1000 nM, not 100 µM)
- ✅ Vitamins (Thiamin)
- ✅ Physiologically relevant ranges

**Sample size:** 70-140 samples (5-10× component count)

**Use this design for:**
- Complete nutritional coverage
- Lanthanide metabolism studies (M. extorquens specialty)
- XoxF vs. MxaF pathway investigation
- Publication-quality experiments

**Format:**
```
Component	Baseline	Lower	Upper	Unit	Notes
K₂HPO₄·3H₂O	1.45	0.5	20	mM	Reduced upper bound
...
NdCl₃·6H₂O	2	0.5	10	µM	XoxF-MDH cofactor
PQQ	0	0	1000	nM	CORRECTED range
```

---

### 4. `MP_latinhypercube_list_ranges_MINIMAL.txt` (ALTERNATIVE)
**Status:** Functional but limited - for screening only

**Components:** 11 (Tier 1 essentials only)

**Includes:**
- ✅ All essential nutrients for viability
- ❌ NO lanthanides (cannot study XoxF)
- ❌ NO PQQ supplementation
- ❌ NO thiamin

**Sample size:** 55-110 samples

**Use this design when:**
- Budget/resources very limited
- Initial screening/feasibility testing
- Studying non-lanthanide aspects
- **NOT recommended for M. extorquens-specific research**

**Limitations:**
- Misses key metabolic features of M. extorquens AM-1
- Cannot explore Ca²⁺/Nd³⁺ competitive dynamics
- Suboptimal growth rates expected

---

## Quick Decision Guide

### Which design file should I use?

```
┌─ Do you have budget for 70-140 samples?
│
├─ YES → Use REVISED (14 components) ✅
│         Best for M. extorquens studies
│         Includes lanthanides (XoxF pathway)
│         Publication-quality data
│
└─ NO → Consider:
    │
    ├─ Studying lanthanide metabolism?
    │  └─ YES → Find more budget!
    │            Lanthanides are essential for this organism
    │
    └─ NO → Use MINIMAL (11 components)
             Basic screening only
             Limited scientific value
```

---

## Key Changes from Original Design

| Issue | Original | Revised | Impact |
|-------|----------|---------|--------|
| PQQ range | 0-100 µM | 0-1000 nM | **CRITICAL** - was 1000× too high |
| Magnesium | Missing | 0.1-2 mM | **ESSENTIAL** - growth fails without |
| Iron | Missing | 0.5-20 µM | **ESSENTIAL** - electron transport |
| Zinc | Missing | 1-20 µM | **ESSENTIAL** - PQQ biosynthesis |
| Manganese | Missing | 0.5-10 µM | **ESSENTIAL** - SOD enzyme |
| Calcium | Missing | 1-100 µM | **HIGH VALUE** - XoxF/MxaF switch |
| Neodymium | Missing | 0.5-10 µM | **HIGH VALUE** - XoxF cofactor |
| Thiamin | Missing | 0.1-2 µM | **BENEFICIAL** - growth support |
| Phosphate max | 100 mM | 20 mM | Prevents precipitation |
| Citrate min | 0 | 0.01 mM | Ensures buffering |
| Unit notation | Mixed (µM, uM) | Standardized (µM) | Clarity |

---

## Usage Instructions

### 1. Select Design File
Choose REVISED (recommended) or MINIMAL (budget-constrained)

### 2. Generate LHS Samples
Use statistical software (R, Python, MATLAB):

```python
import numpy as np
from scipy.stats.qmc import LatinHypercube

# For REVISED design (14 components)
n_components = 14
n_samples = 70  # 5× components (or 140 for 10×)

# Generate LHS samples [0, 1]
sampler = LatinHypercube(d=n_components)
samples = sampler.random(n=n_samples)

# Scale to actual ranges (example for methanol: 15-500 mM)
methanol_col = 4  # Column index
methanol_samples = 15 + samples[:, methanol_col] * (500 - 15)
```

### 3. Validate Design
Check constraints before running experiments:
- No [Phosphate] > 10 mM when [Nd³⁺] > 5 µM (precipitation risk)
- [Mg²⁺] ≥ 0.1 mM in all samples (viability)
- pH buffers (citrate + phosphate) present
- Total osmolarity < 500 mOsm

### 4. Prepare Media
Follow standard MP medium preparation protocols with LHS-sampled concentrations.

### 5. Run Experiments
Measure response variables:
- Growth: OD₆₀₀, specific growth rate (µ)
- Lanthanide uptake: Nd³⁺ depletion (%), cellular content
- Gene expression: xoxF, mxaF (qPCR)
- Metabolites: PQQ, methylolanthanin

---

## Design Constraints

**Chemical compatibility:**
1. Avoid high phosphate + high lanthanides (precipitation)
2. Low Ca²⁺ forces XoxF pathway; high Ca²⁺ allows MxaF
3. Low Fe (<1 µM) induces lanthanophore production

**Physiological constraints:**
1. pH: 6.5-7.5 (maintained by citrate/phosphate)
2. Osmolarity: <500 mOsm
3. C:N ratio: 5:1 to 50:1
4. Total phosphorus: 1-100 mM

---

## References

1. **Design Review:** `DESIGN_REVIEW_REPORT.md` (this directory)
2. **Organism-Specific Data:** `data/exports/methylorubrum_extorquens_AM1/`
3. **MP Medium Variations:** `outputs/media/MP/mp_medium_variations_documentation.md`
4. **Genome Analysis:** SAMN31331780 (10,820 annotations)

**Key Papers:**
- XoxF-MDH: DOI: 10.1038/nature12883
- Lanthanide regulation: DOI: 10.1073/pnas.1600776113
- REE bioremediation: DOI: 10.3389/fbioe.2023.1130939

---

## Support

For questions or issues:
1. Read `DESIGN_REVIEW_REPORT.md` (comprehensive explanations)
2. Check organism-specific tables in `data/exports/methylorubrum_extorquens_AM1/`
3. Consult MicroGrowAgents agents for design validation

---

**Version:** 2.0
**Date:** 2026-01-11
**Status:** ✅ Production Ready (REVISED design)

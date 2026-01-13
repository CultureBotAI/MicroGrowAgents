# Latin Hypercube Design - Final Summary

**Date:** 2026-01-12
**Status:** ✅ READY FOR EXPERIMENTS

---

## Files to Use

### For Experiments:

✅ **`MP_latinhypercube_list_ranges_REVISED_FINAL.txt`**
- 9 varied components (corrected ranges)
- **Use this file** to generate LHS samples

✅ **`fixed_concentrations_FINAL.txt`**
- 11 fixed components (constant in all samples)
- **Use this file** for base medium composition

✅ **`DESIGN_REVIEW_REPORT_CORRECTED.md`**
- Complete technical review and justifications
- Read for understanding design decisions

---

## Critical Changes from Original

### Original Design (`MP_latinhypercube_list_ranges.txt`):
❌ 8 varied components
❌ Missing lanthanides → Would cause **complete growth failure**
❌ PQQ range 1000× too high (0-100 µM)
❌ Phosphate range too wide (0.1-100 mM)
❌ Citrate lower bound = 0 (problematic)

### Final Design (`MP_latinhypercube_list_ranges_REVISED_FINAL.txt`):
✅ **9 varied components** (added NdCl₃, kept CoCl₂)
✅ **Lanthanides added:** NdCl₃·6H₂O 0.5-10 µM
✅ **PQQ corrected:** 0-1000 nM (was 0-100 µM)
✅ **Phosphate reduced:** 0.5-20 mM (was 0.1-100 mM)
✅ **Citrate raised:** 0.01-10 mM (was 0-10 mM)

---

## The 9 Varied Components

| # | Component | Range | Why Vary? |
|---|-----------|-------|-----------|
| 1 | K₂HPO₄·3H₂O | 0.5-20 mM | P source, buffer |
| 2 | NaH₂PO₄·H₂O | 0.5-20 mM | P source, buffer |
| 3 | (NH₄)₂SO₄ | 1-100 mM | N source |
| 4 | Sodium citrate | 0.01-10 mM | Chelator, buffer |
| 5 | **CoCl₂·6H₂O** | 0.01-100 µM | **B12/methylotrophy** |
| 6 | **NdCl₃·6H₂O** | 0.5-10 µM | **XoxF cofactor (CRITICAL)** |
| 7 | Succinate | 0-150 mM | Alternative C source |
| 8 | Methanol | 15-500 mM | Primary C source |
| 9 | PQQ | 0-1000 nM | XoxF cofactor |

**Sample size needed:** 45-90 samples (5-10× components)

---

## The 11 Fixed Components

| Component | Concentration | Role |
|-----------|---------------|------|
| PIPES | 20 mM | pH buffer |
| MgCl₂·6H₂O | 0.5 mM | Essential (ribosome) |
| **CaCl₂·2H₂O** | **0** | **Excluded (Ca-free design)** |
| ZnSO₄·7H₂O | 5 µM | PQQ biosynthesis |
| MnCl₂·4H₂O | 2 µM | Superoxide dismutase |
| FeSO₄·7H₂O | 8 µM | Electron transport |
| (NH₄)₆Mo₇O₂₄·4H₂O | 0.05 µM | Molybdopterin |
| CuSO₄·5H₂O | 0.5 µM | Oxidases |
| Na₂WO₄·2H₂O | 0.05 µM | Mo alternative |
| Thiamin·HCl | 0.5 µM | TPP cofactor |
| Biotin | 0.05 µM | Carboxylase |

---

## Why These Changes Are Critical

### 1. Adding NdCl₃ (ESSENTIAL):
**Without lanthanides:**
- Ca-free medium has no functional methanol dehydrogenase
- XoxF requires Nd³⁺, La³⁺, or Ce³⁺ cofactor
- Cells **cannot grow on methanol** → experiment fails

**With lanthanides:**
- XoxF-MDH functions
- Studies lanthanide-dependent metabolism
- Relevant for REE bioremediation applications

### 2. Keeping CoCl₂ (VALUABLE):
- Studies B12 biosynthesis effects
- Relevant for methylotrophy
- Co and Nd metabolism can interact
- Only adds ~10 more samples (marginal cost)

### 3. Correcting PQQ (SAFETY):
**Original 0-100 µM:**
- Organism makes its own PQQ
- High levels (>1 µM) likely inhibitory
- Wasteful and potentially toxic

**Corrected 0-1000 nM:**
- 0 nM = rely on biosynthesis
- 100-500 nM = optimal supplementation range
- 1000 nM = maximum beneficial level

### 4. Reducing Phosphate (CHEMISTRY):
**Original 100 mM:**
- Causes lanthanide phosphate precipitation (LnPO₄)
- Hyperosmotic stress
- Physiologically irrelevant

**Corrected 20 mM:**
- Sufficient buffering
- No precipitation risk
- Matches published MP medium formulations

---

## Quick Start for Experiments

### Step 1: Generate LHS Samples
```python
import numpy as np
from scipy.stats.qmc import LatinHypercube

# 9 components, 72 samples (8× components)
sampler = LatinHypercube(d=9, seed=42)
samples = sampler.random(n=72)

# Scale to ranges from REVISED_FINAL.txt
# ... (see full code in README_v2.md)
```

### Step 2: Apply Design Constraints
- Check precipitation risk: High P + High Nd → Require high citrate
- Check buffer capacity: Low P + Low citrate → Flag for pH monitoring
- Check osmolarity: <500 mOsm
- Check C:N ratio: 5-50

### Step 3: Add Fixed Concentrations
- Add all 11 fixed components from `fixed_concentrations_FINAL.txt`
- Every sample gets same fixed concentrations

### Step 4: Prepare and Run
- Mix stocks to target concentrations
- Verify pH 6.8-7.2
- Inoculate M. extorquens AM-1
- Measure growth, Nd uptake, gene expression

---

## What to Commit

**Production files (commit these):**
- ✅ `MP_latinhypercube_list_ranges_REVISED_FINAL.txt`
- ✅ `fixed_concentrations_FINAL.txt`
- ✅ `DESIGN_REVIEW_REPORT_CORRECTED.md`
- ✅ `FINAL_SUMMARY.md` (this file)

**Keep for reference (optional to commit):**
- `MP_latinhypercube_list_ranges.txt` (original - shows what NOT to do)
- Other REVISED/MINIMAL files (from initial incorrect review)

**Can delete (superseded):**
- `DESIGN_REVIEW_REPORT.md` (first version, based on wrong understanding)
- `README.md` (first version, incorrect)
- Files with "v2" in middle of development

---

## Key Takeaways

1. **9 components varied** (not 8): Added NdCl₃, kept CoCl₂
2. **Lanthanides are ESSENTIAL** for Ca-free medium
3. **PQQ corrected** to physiologically relevant range
4. **Phosphate reduced** to prevent precipitation
5. **Sample size: 45-90** (manageable)

---

## Questions Answered

**Q: Why not replace CoCl₂ with NdCl₃?**
A: Both are valuable! Co for B12/methylotrophy, Nd for XoxF/lanthanide studies. Worth the extra ~10 samples.

**Q: Why vary both K₂HPO₄ and NaH₂PO₄?**
A: Original design choice. Could combine into "Total Phosphate" to reduce to 8 dimensions, but keeping separate maintains consistency with original intent.

**Q: Can I use the original design file?**
A: **NO** - It's missing lanthanides and will cause complete growth failure.

**Q: What if I want to vary Fe too?**
A: Move FeSO₄ from fixed to varied (0.5-20 µM). Low Fe induces lanthanophore production, enhances Nd uptake. Increases to 10 components → 50-100 samples.

---

**Version:** 2.1 FINAL
**Date:** 2026-01-12
**Status:** ✅ Ready for LHS sample generation and experiments

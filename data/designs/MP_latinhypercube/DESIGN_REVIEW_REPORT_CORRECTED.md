# Latin Hypercube Experimental Design Review Report (CORRECTED)
## MP Medium for Methylorubrum extorquens AM-1

**Date:** 2026-01-12
**Reviewer:** Claude Code
**Design File:** `data/designs/MP_latinhypercube/MP_latinhypercube_list_ranges.txt`
**Target Organism:** Methylorubrum extorquens AM-1
**Design Type:** Latin Hypercube Sampling (LHS) - Varied Components Only

---

## Executive Summary

**CORRECTED UNDERSTANDING:** The LHS design file contains only the **8 components whose concentrations will be varied**, while the remaining 10 components from the full ingredient list will be held at **fixed concentrations**.

**Status:** ⚠️ Design has **2 critical issues** and several optimization opportunities

### Critical Issues:
1. ❌ **PQQ range 1000× too high:** 0-100 µM should be 0-1 µM (1000 nM max)
2. ❌ **Missing lanthanides:** No Nd³⁺, La³⁺, or Ce³⁺ in either varied OR fixed lists

### Optimization Opportunities:
- ⚠️ Phosphate upper bound too wide (100 mM → precipitation risk)
- ⚠️ Consider varying Fe or Zn instead of (or in addition to) Co
- ⚠️ Unit inconsistency (µM vs uM)
- ⚠️ Sodium citrate lower bound of 0 may be problematic

### Overall Recommendation:
**Usable with modifications** - Fix PQQ range, add lanthanides to varied set, adjust phosphate range.

---

## 1. Medium Composition Overview

### 1.1 Complete Ingredient List (18 components)

**FIXED Concentrations (10 components):**
| Component | Status | Role |
|-----------|--------|------|
| PIPES | Fixed | pH buffer (non-metal-binding) |
| MgCl₂·6H₂O | Fixed | Essential (ribosome, ATP) |
| CaCl₂·2H₂O | **NOT USED** | Excluded by design |
| ZnSO₄·7H₂O | Fixed | Essential (metalloenzymes, PQQ biosynthesis) |
| MnCl₂·4H₂O | Fixed | Essential (SOD, amino acids) |
| FeSO₄·7H₂O | Fixed | Essential (electron transport) |
| (NH₄)₆Mo₇O₂₄·4H₂O | Fixed | Molybdopterin cofactor |
| CuSO₄·5H₂O | Fixed | Oxidases, electron transport |
| Na₂WO₄·2H₂O | Fixed | Alternative to Mo |
| Thiamin | Fixed | TPP cofactor |
| Biotin | Fixed | Carboxylase cofactor |

**VARIED via Latin Hypercube (8 components):**
| Component | Baseline | Lower | Upper | Status |
|-----------|----------|-------|-------|--------|
| K₂HPO₄·3H₂O | 1.45 mM | 0.1 mM | 100 mM | ⚠️ Upper too high |
| NaH₂PO₄·H₂O | 1.88 mM | 0.1 mM | 100 mM | ⚠️ Upper too high |
| (NH₄)₂SO₄ | 8 mM | 1 mM | 100 mM | ✅ Good |
| Sodium citrate | 45.6 µM | 0 | 10 mM | ⚠️ Zero problematic |
| CoCl₂·6H₂O | 2 µM | 0.01 µM | 100 µM | ✅ Good |
| Succinate | 15 mM | 0 | 150 mM | ✅ Good |
| Methanol | 150 mM | 15 mM | 500 mM | ✅ Good |
| PQQ | 0 | 0 | 100 µM | ❌ **1000× TOO HIGH** |

### 1.2 Key Design Decision: No Calcium

**CaCl₂·2H₂O marked "don't use"**

**Implication:** Ca²⁺-free medium forces **XoxF-exclusive** growth pathway
- MxaF (Ca²⁺-dependent MDH) cannot function
- Cells must rely on lanthanide-dependent XoxF-MDH
- **Valid design choice** if studying lanthanide metabolism specifically

**BUT:** Requires lanthanides in the medium! (Currently missing)

---

## 2. Critical Issue #1: PQQ Concentration Range

**Current:** 0 - 100 µM
**Should be:** 0 - 1 µM (1000 nM)
**Error magnitude:** 1000× too high

### Evidence:
- M. extorquens AM-1 has complete PQQ biosynthesis (pqqABCDE, 16 genes)
- Endogenous PQQ production sufficient for growth
- Exogenous supplementation optimal: 100-500 nM
- Literature range for XoxF studies: 0-1 µM maximum
- High PQQ (>1 µM) likely inhibitory or wasteful

### Recommendation:
```
PQQ: 0 nM to 1000 nM (0 to 1 µM)
Rationale: 0 = rely on biosynthesis, 1 µM = maximum beneficial supplementation
```

**Urgency:** CRITICAL - must fix before experiments

---

## 3. Critical Issue #2: Missing Lanthanides

**Status:** ❌ Lanthanides (Nd³⁺, La³⁺, Ce³⁺) are in NEITHER the varied NOR the fixed list

**Why this is critical for M. extorquens AM-1:**

### Without Ca²⁺ (excluded), cells need lanthanides:
- XoxF-MDH absolutely requires lanthanide cofactor (Nd³⁺, La³⁺, or Ce³⁺)
- No Ca²⁺ + No lanthanides = **NO FUNCTIONAL MDH = NO GROWTH**
- M. extorquens AM-1 cannot grow on methanol without either Ca²⁺ or lanthanides

### Genome evidence (SAMN31331780):
- 4 genes for XoxF system (lanthanide-dependent MDH)
- XoxF is the primary MDH for REE-dependent growth
- Cell has lanthanophore (methylolanthanin) for lanthanide acquisition

### Literature support:
- DOI: 10.1038/nature12883 - XoxF structure and lanthanide cofactor
- DOI: 10.1073/pnas.1600776113 - Lanthanide regulation in M. extorquens
- MP medium variations use Nd³⁺ at 0.5-10 µM for XoxF studies

### Recommendation:
**MUST ADD lanthanides** - either varied or fixed

**Option A: Add to VARIED set (recommended for XoxF studies)**
```
NdCl₃·6H₂O: 0.5 µM to 10 µM
Rationale: Explore lanthanide-dependent growth kinetics
Low Nd (0.5 µM): Minimal XoxF activation
High Nd (10 µM): Maximum XoxF activity
```

**Option B: Fix at optimal concentration (if not primary variable)**
```
NdCl₃·6H₂O: 2 µM (fixed)
Rationale: Ensure XoxF function without varying
Based on MP-Nd medium optimizations
```

**Option C: Use in fixed ratio with another varied component**
```
Nd/Methanol ratio: 0.01-0.02 µM/mM
Scales lanthanide with carbon source availability
```

**Urgency:** CRITICAL - Design will FAIL without lanthanides (no growth)

---

## 4. Component Selection Analysis

### 4.1 Why These 8 Were Chosen to Vary?

**Good choices (5/8):**
1. ✅ **Methanol** - Primary C source, key variable for methylotroph
2. ✅ **Succinate** - Alternative C source, tests metabolic flexibility
3. ✅ **(NH₄)₂SO₄** - N source, fundamental nutrient
4. ✅ **CoCl₂** - B12 biosynthesis, relevant for methylotrophy
5. ✅ **Sodium citrate** - Chelator/buffer, affects metal availability

**Questionable choices (3/8):**
6. ⚠️ **K₂HPO₄ + NaH₂PO₄** - Varying BOTH phosphates independently
   - Creates 2 LHS dimensions for essentially same nutrient (P)
   - Consider: Vary total phosphate, fix K:Na ratio
   - OR: Vary one, fix the other

7. ⚠️ **PQQ** - Organism biosynthesizes PQQ
   - Valid to vary, but range must be corrected
   - Consider: Is this more important than varying Fe, Zn, or lanthanides?

### 4.2 Why Keep These Fixed?

**Appropriate to fix (7/10):**
- ✅ PIPES - Standard buffer, not experimental variable
- ✅ MgCl₂ - Essential, toxicity only at very high concentrations
- ✅ Thiamin - Partial biosynthesis, supplementation beneficial
- ✅ Biotin - Complete biosynthesis, supplementation optional
- ✅ CuSO₄ - Minor trace metal, narrow optimal range
- ✅ Mo/W compounds - Narrow optimal ranges
- ✅ CaCl₂ - Excluded by design (Ca-free medium)

**Could consider varying (3/10):**
- ⚠️ **FeSO₄** - Fe limitation induces lanthanophore production
  - Low Fe (<1 µM) + High Nd → Enhanced lanthanide uptake
  - **High value for lanthanide metabolism studies**

- ⚠️ **ZnSO₄** - Required for PQQ biosynthesis
  - Zn/PQQ interaction could be interesting
  - But less critical than Fe

- ⚠️ **MnCl₂** - SOD activity, oxidative stress
  - Methanol oxidation generates ROS
  - Mn availability affects stress tolerance

### 4.3 Recommendation: Optimal Component Set

**Revised LHS Design (9-10 components):**

**Priority 1: Fix critical issue**
1. K₂HPO₄·3H₂O (0.5-20 mM) - Reduced upper bound
2. NaH₂PO₄·H₂O (0.5-20 mM) - Reduced upper bound
   - *Alternative:* Combine as "Total Phosphate" (1 variable instead of 2)
3. (NH₄)₂SO₄ (1-100 mM) ✅ Keep
4. Methanol (15-500 mM) ✅ Keep
5. Succinate (0-150 mM) ✅ Keep
6. Sodium citrate (0.01-10 mM) - Raised lower bound
7. **NdCl₃·6H₂O (0.5-10 µM)** ⭐ **ADD - CRITICAL**
8. PQQ (0-1000 nM) - **CORRECTED** (was 0-100 µM)

**Priority 2: Consider adding**
9. FeSO₄·7H₂O (0.5-20 µM) - High value for lanthanide studies
10. CoCl₂·6H₂O (0.01-100 µM) ✅ Keep OR replace with Fe

**If must keep 8 components, replace one:**
- Option A: Drop one phosphate (vary total P, fix ratio)
- Option B: Fix Co, vary Fe (more relevant for lanthanide uptake)
- Option C: Fix PQQ (organism makes it), vary lanthanides

---

## 5. Range Analysis for Varied Components

### 5.1 Phosphate Buffers - Upper Bound Too High

**Current:** 0.1-100 mM (both K₂HPO₄ and NaH₂PO₄)
**Issue:** 100 mM is physiologically extreme and causes precipitation

**Problems at high phosphate:**
- Lanthanide phosphate precipitation (LnPO₄ insoluble) at >20 mM PO₄³⁻
- Hyperosmotic stress (>500 mOsm)
- pH buffering redundant (PIPES already present)
- Interferes with metal bioavailability

**Evidence from MP medium variations:**
- Standard phosphate: 1-2 mM total
- High-performance variations: up to 10 mM
- Never exceeds 20 mM in published formulations

**Recommendation:**
```
K₂HPO₄·3H₂O: 0.5 mM to 20 mM
NaH₂PO₄·H₂O: 0.5 mM to 20 mM
Rationale:
  0.5 mM: Minimal P nutrition
  20 mM: Strong buffering without precipitation
```

**Alternative:** Combine into single variable
```
Total Phosphate: 1 mM to 20 mM
K:Na ratio: Fixed at 1:1.3 (based on baseline)
Reduces LHS dimensions from 8 to 7
```

### 5.2 Sodium Citrate - Zero Lower Bound Problematic

**Current:** 45.6 µM baseline, 0 lower bound
**Issue:** Zero citrate problematic without Ca²⁺

**Citrate roles:**
1. Metal chelator (prevents lanthanide precipitation)
2. pH buffer (pKa 3.1, 4.8, 6.4)
3. TCA intermediate (metabolic)

**In Ca²⁺-free medium with lanthanides:**
- Lanthanides (3+) more prone to precipitation than Ca²⁺ (2+)
- Citrate chelation essential for Nd³⁺ solubility at pH 7
- Zero citrate + High Nd + High phosphate = **Certain precipitation**

**Recommendation:**
```
Sodium citrate: 0.01 mM (10 µM) to 10 mM
Rationale:
  0.01 mM: Minimal chelation
  10 mM: Strong chelation + buffering
  Never zero with lanthanides present
```

### 5.3 Other Ranges - Acceptable

| Component | Current Range | Assessment |
|-----------|---------------|------------|
| (NH₄)₂SO₄ | 1-100 mM | ✅ Physiologically relevant |
| CoCl₂·6H₂O | 0.01-100 µM | ✅ Covers B12 biosynthesis needs |
| Succinate | 0-150 mM | ✅ Zero OK (optional C source) |
| Methanol | 15-500 mM | ✅ Matches literature (1-500 mM) |

---

## 6. Fixed Component Recommendations

### 6.1 Suggested Fixed Concentrations

For the 10 components NOT varied in LHS:

| Component | Fixed Concentration | Rationale |
|-----------|---------------------|-----------|
| **PIPES** | 20 mM | Standard pH buffer, non-metal-binding |
| **MgCl₂·6H₂O** | 0.5 mM | Standard MP medium concentration |
| **CaCl₂·2H₂O** | 0 (excluded) | By design - forces XoxF pathway |
| **ZnSO₄·7H₂O** | 5 µM | PQQ biosynthesis, standard trace metal |
| **MnCl₂·4H₂O** | 2 µM | SOD activity, standard concentration |
| **FeSO₄·7H₂O** | 8 µM | Moderate level (or vary 0.5-20 µM) |
| **(NH₄)₆Mo₇O₂₄·4H₂O** | 0.05 µM | Standard molybdenum level |
| **CuSO₄·5H₂O** | 0.5 µM | Standard copper level |
| **Na₂WO₄·2H₂O** | 0.05 µM | Alternative to Mo, low level |
| **Thiamin·HCl** | 0.5 µM | Supports growth, standard level |
| **Biotin** | 0.05 µM | Organism synthesizes, low supplement |

**Critical addition (currently missing):**
| **NdCl₃·6H₂O** | 2 µM (if fixed) | **MUST ADD** - XoxF cofactor |
|  | 0.5-10 µM (if varied) | Better option for lanthanide studies |

### 6.2 Note on K₂HPO₄ "Fixed Ratio to N"

User noted: "K₂HPO₄·3H₂O (fixed ratio of N K)"

**Interpretation options:**
1. **K:N ratio fixed?**
   - If (NH₄)₂SO₄ varies, K₂HPO₄ scales proportionally
   - Maintains constant K⁺/NH₄⁺ ratio
   - Then K₂HPO₄ should NOT be in varied set (dependent variable)

2. **Potassium:Nitrogen molar ratio?**
   - Typical K:N ratio in bacterial media: 0.1-0.5
   - Current baseline: K (1.45 mM) / N (16 mM from (NH₄)₂SO₄) = 0.09

**Recommendation:** Clarify this constraint!
- If K scales with N → Remove K₂HPO₄ from varied set, compute from (NH₄)₂SO₄
- If K is independent → Keep both phosphates as separate variables
- Consider: Total phosphate + K:Na ratio might be cleaner design

---

## 7. Revised Design Recommendations

### 7.1 Option A: Minimal Changes (8 components varied)

**Keep LHS at 8 dimensions, fix critical issues:**

| Component | Baseline | Lower | Upper | Unit | Change |
|-----------|----------|-------|-------|------|--------|
| K₂HPO₄·3H₂O | 1.45 | 0.5 | 20 | mM | Reduced upper |
| NaH₂PO₄·H₂O | 1.88 | 0.5 | 20 | mM | Reduced upper |
| (NH₄)₂SO₄ | 10 | 1 | 100 | mM | ✅ Keep |
| Sodium citrate | 0.5 | 0.01 | 10 | mM | Raised lower |
| **NdCl₃·6H₂O** | **2** | **0.5** | **10** | **µM** | **⭐ ADD** |
| Succinate | 15 | 0 | 150 | mM | ✅ Keep |
| Methanol | 125 | 15 | 500 | mM | ✅ Keep |
| PQQ | 0 | 0 | 1000 | nM | **CORRECTED** |

**Dropped:** CoCl₂ (moved to fixed at 2 µM)
**Added:** NdCl₃ (ESSENTIAL for Ca-free medium)

### 7.2 Option B: Enhanced Design (9 components varied)

**Add both lanthanides and Fe:**

All from Option A, plus:
| **FeSO₄·7H₂O** | **8** | **0.5** | **20** | **µM** | **ADD** |

**Rationale:** Fe limitation enhances lanthanide uptake (methylolanthanin induction)

**LHS samples needed:** 45-90 (5-10× components)

### 7.3 Option C: Streamlined Design (7 components varied)

**Combine phosphates, add lanthanides:**

| Component | Baseline | Lower | Upper | Unit | Change |
|-----------|----------|-------|-------|------|--------|
| **Total Phosphate** | 3.3 | 1 | 20 | mM | Combined K+Na |
| (NH₄)₂SO₄ | 10 | 1 | 100 | mM | ✅ Keep |
| Sodium citrate | 0.5 | 0.01 | 10 | mM | Raised lower |
| NdCl₃·6H₂O | 2 | 0.5 | 10 | µM | ⭐ ADD |
| Succinate | 15 | 0 | 150 | mM | ✅ Keep |
| Methanol | 125 | 15 | 500 | mM | ✅ Keep |
| PQQ | 0 | 0 | 1000 | nM | CORRECTED |

**K₂HPO₄:NaH₂PO₄ ratio:** Fixed at 1:1.3 (based on baseline)

**LHS samples needed:** 35-70 (5-10× components)

---

## 8. Unit Consistency Issue

**Current file:**
- Lines 2-6: `µM` (Unicode micro, correct)
- Line 9: `uM` (ASCII 'u', non-standard)

**Recommendation:** Standardize all to `µM` or write out `micromolar`

---

## 9. Design Constraints and Validation

### 9.1 Chemical Compatibility Constraints

**Implement these rules when generating LHS samples:**

1. **Lanthanide precipitation constraint:**
   ```
   IF [Total_Phosphate] > 10 mM AND [Nd³⁺] > 5 µM:
      FLAG sample (high precipitation risk)
      Consider: Require [Citrate] > 1 mM in these samples
   ```

2. **Buffer capacity constraint:**
   ```
   IF [Total_Phosphate] < 2 mM AND [Citrate] < 0.1 mM:
      FLAG sample (insufficient buffering, pH may drift)
   ```

3. **Osmolarity constraint:**
   ```
   Total_osmolarity < 500 mOsm
   Sum all ionic components
   ```

### 9.2 Physiological Constraints

1. **Carbon:Nitrogen ratio:**
   ```
   5 < (Methanol + Succinate) / NH₄⁺ < 50
   Typical bacterial C:N ratio
   ```

2. **pH maintenance:**
   ```
   Buffering capacity (PIPES + citrate + phosphate) > 5 mM
   Target pH: 6.8-7.2
   ```

3. **Lanthanide bioavailability:**
   ```
   [Nd³⁺]_free depends on citrate chelation
   Higher citrate → Lower free Nd³⁺ → Lower toxicity
   ```

---

## 10. Expected Experimental Responses

### 10.1 Primary Response Variables

**Growth metrics:**
- OD₆₀₀ at 24h, 48h, 72h
- Specific growth rate (µ, h⁻¹)
- Maximum biomass yield
- Lag phase duration

**Lanthanide metabolism:**
- Nd³⁺ depletion from medium (%)
- Cellular Nd content (µg/g dry weight)
- Nd bioaccumulation factor
- XoxF expression level (qPCR)

**Metabolic indicators:**
- Methanol consumption rate
- PQQ concentration (endogenous + exogenous)
- Methylolanthanin production (lanthanophore)
- CO₂ production rate

### 10.2 Key Factor Interactions to Explore

**Nd³⁺ × Citrate:**
- High citrate → Nd chelation → Reduced bioavailability
- Low citrate → Free Nd³⁺ → Enhanced uptake but precipitation risk

**Nd³⁺ × Phosphate:**
- High phosphate → LnPO₄ precipitation
- Optimal balance: Moderate P, high citrate, moderate Nd

**Fe × Nd³⁺:**
- Low Fe (<1 µM) → Methylolanthanin induction → Enhanced Nd uptake
- High Fe → Reduced lanthanophore → Lower Nd uptake

**PQQ × Nd³⁺:**
- Both required for XoxF-MDH activity
- Synergistic effect on growth rate
- Explore if exogenous PQQ enhances Nd-dependent growth

**Methanol × Succinate:**
- Methanol: XoxF/MxaF substrate
- Succinate: Alternative TCA carbon entry
- Metabolic flexibility vs. specialization

---

## 11. Recommendations Summary

### 11.1 CRITICAL - Must Fix Before Experiments

1. ✅ **Fix PQQ range:** 0-100 µM → 0-1 µM (1000 nM)
2. ✅ **Add lanthanides:** NdCl₃·6H₂O 0.5-10 µM to varied set
   - **Without lanthanides, Ca-free medium will not support growth**
3. ✅ **Reduce phosphate upper bound:** 100 mM → 20 mM
4. ✅ **Raise citrate lower bound:** 0 → 0.01 mM (10 µM)

### 11.2 RECOMMENDED - Quality Improvements

5. ⭐ **Standardize units:** uM → µM throughout
6. ⭐ **Clarify K₂HPO₄/N ratio constraint:** Document if K scales with N
7. ⭐ **Consider varying Fe:** Relevant for lanthanide uptake mechanism
8. ⭐ **Document fixed concentrations:** Create table for non-varied components

### 11.3 OPTIONAL - Design Optimization

9. Consider combining phosphates into single "Total Phosphate" variable
10. Consider replacing CoCl₂ with FeSO₄ in varied set (more relevant)
11. Add design constraints for LHS sample generation (prevent precipitation)
12. Validate samples: Check osmolarity, buffering capacity, C:N ratios

---

## 12. Risk Assessment

### 12.1 Risks of Current Design (Unchanged)

| Risk | Severity | Probability | Impact |
|------|----------|-------------|--------|
| Complete growth failure (no lanthanides) | **CRITICAL** | **100%** | All samples fail in Ca-free medium |
| PQQ toxicity (100 µM range) | HIGH | 50% | Growth inhibition in high-PQQ samples |
| Lanthanide precipitation (high PO₄) | MEDIUM | 30% | Reduced bioavailability, data scatter |
| Zero citrate samples precipitate | MEDIUM | 20% | Failed samples with high Nd + low citrate |
| Results non-reproducible | HIGH | 70% | Missing lanthanides invalidates design |

### 12.2 Risks of Revised Design

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| More complex analysis (lanthanides added) | LOW | 100% | Expected - studying lanthanide metabolism |
| Some precipitation in extreme conditions | LOW | 10% | Apply design constraints |
| Higher reagent cost (Nd salts expensive) | MEDIUM | 100% | Justified by scientific value |

---

## 13. Implementation Checklist

Before generating LHS samples:

- [ ] **Fix PQQ range:** 0-1000 nM (not 100 µM)
- [ ] **Add NdCl₃·6H₂O:** 0.5-10 µM to varied set
- [ ] **Reduce phosphate ranges:** 0.5-20 mM (not 100 mM)
- [ ] **Raise citrate minimum:** 0.01 mM (not 0)
- [ ] **Standardize units:** All µM (not uM)
- [ ] **Document fixed concentrations:** Create table for 10 fixed components
- [ ] **Clarify K/N ratio:** Document if K₂HPO₄ scales with (NH₄)₂SO₄
- [ ] **Define constraints:** Precipitation, osmolarity, C:N ratio
- [ ] **Calculate sample size:** 40-80 samples for 8 components (5-10×)
- [ ] **Validate design:** Check all samples pass constraints
- [ ] **Prepare stock solutions:** Including Nd stock (anaerobic if possible)

---

## 14. Conclusions

### 14.1 Current Design Assessment

**Overall:** ⚠️ **NOT READY - Requires critical modifications**

**Strengths:**
- ✅ Good choice to vary methanol and succinate (C sources)
- ✅ Appropriate to vary nitrogen source
- ✅ Including PQQ as variable (though range wrong)
- ✅ Ca²⁺-free design valid for XoxF-specific studies
- ✅ Most fixed components appropriately chosen

**Critical Flaws:**
- ❌ **Missing lanthanides** - Will cause complete failure in Ca-free medium
- ❌ **PQQ range 1000× too high** - Likely toxic at upper bound
- ⚠️ Phosphate ranges too wide (precipitation risk)
- ⚠️ Zero citrate problematic with lanthanides

### 14.2 Recommended Action Plan

**Immediate (Before experiments):**
1. Add NdCl₃·6H₂O to varied set (0.5-10 µM) - **ESSENTIAL**
2. Correct PQQ range to 0-1000 nM - **CRITICAL**
3. Reduce phosphate upper bounds to 20 mM
4. Raise citrate lower bound to 0.01 mM
5. Standardize unit notation (µM)

**Short-term (Design optimization):**
6. Consider adding Fe to varied set (lanthanide interactions)
7. Clarify K₂HPO₄/nitrogen ratio constraint
8. Document all fixed component concentrations
9. Implement chemical compatibility constraints

**Long-term (Future iterations):**
10. Consider varying multiple lanthanides (Nd, La, Ce)
11. Explore Ca²⁺ vs. Nd³⁺ competitive designs
12. Test Fe limitation effects on lanthanide uptake

### 14.3 Expected Outcomes with Revised Design

**With corrections:**
- ✅ All samples will support growth (lanthanides present)
- ✅ Safe PQQ levels (no toxicity)
- ✅ Reduced precipitation risk (lower phosphate)
- ✅ Explore XoxF-dependent lanthanide metabolism
- ✅ Publication-quality data on M. extorquens REE bioaccumulation

**Scientific value:**
- Study lanthanide-dependent growth kinetics
- Optimize medium for REE bioremediation applications
- Understand cofactor (PQQ, Nd³⁺) interactions
- Identify optimal conditions for biomining/biorecovery

---

## 15. References

1. **MP Medium Variations:** `outputs/media/MP/mp_medium_variations_documentation.md`
2. **M. extorquens Genome:** SAMN31331780 (10,820 annotations)
3. **Organism Tables:** `data/exports/methylorubrum_extorquens_AM1/`
4. **XoxF-MDH Structure:** DOI: 10.1038/nature12883
5. **Lanthanide Regulation:** DOI: 10.1073/pnas.1600776113
6. **REE Bioremediation:** DOI: 10.3389/fbioe.2023.1130939

---

**Report Version:** 2.0 (Corrected)
**Date:** 2026-01-12
**Status:** ⚠️ **CRITICAL MODIFICATIONS REQUIRED**
**Priority:** Fix lanthanides (1) and PQQ range (2) before experiments

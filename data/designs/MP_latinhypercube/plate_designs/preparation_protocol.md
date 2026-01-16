# 96-Well Plate Preparation Protocol
## Latin Hypercube Design for M. extorquens AM-1

**Date Generated:** 2026-01-15
**Plates:** 3
**Conditions:** 129
**Controls:** 12

---

## Materials Required

### Plates
- 3× 96-well deep well plates (0.5 mL working volume)
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
**Last Updated:** 2026-01-15

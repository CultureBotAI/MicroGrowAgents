# Latin Hypercube 96-Well Plate Design

**Generated:** 2026-01-15 20:43:47
**Target organism:** Methylorubrum extorquens AM-1 (SAMN31331780)
**Experimental design:** Latin Hypercube Sampling (LHS)

## Files in this directory

### Plate Layouts
- `Plate_1_layout.csv` - Well assignments for plate 1 (8×12 grid)
- `Plate_2_layout.csv` - Well assignments for plate 2
- `Plate_3_layout.csv` - Well assignments for plate 3

### Formulations
- `complete_formulations.json` - All 129 formulations with full details
- `fixed_components.tsv` - Components fixed across all conditions
- `stock_solutions.tsv` - Stock preparation recipes (10× concentrates)

### Protocols
- `pipetting_protocol.csv` - Well-by-well component concentrations
- `data_collection_template.csv` - Template for recording measurements
- `preparation_protocol.md` - Step-by-step laboratory protocol
- `analysis_plan.md` - Data analysis strategy

## Design Summary

**Plates:** 3 × 96-well deep well plates
**Conditions:** 129 unique medium formulations
**Controls:** 12 total (4 per plate)
**Varied components:** 9 (phosphates, nitrogen, citrate, lanthanide, cobalt, carbon sources, PQQ)
**Fixed components:** 11 (buffers, trace metals, vitamins)

## Control Wells

Each plate has 4 control wells:
- **A1, A12:** Negative controls (no inoculum)
- **H1, H12:** Media controls (standard MP medium)

## Measurements

**Timepoints:** 8h, 24h, 32h
**Measurements per timepoint:**
- OD₆₀₀ (growth/biomass)
- Arsenazo III assay (Nd³⁺ quantification at 652 nm)

**Total data points:** 1728 measurements

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

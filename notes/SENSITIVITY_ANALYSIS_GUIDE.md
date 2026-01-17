# Sensitivity Analysis Integration Guide

## Overview

The `sensitivity` command performs parameter sweep analysis on media formulations, calculating pH and salinity effects when varying ingredient concentrations. It's **fully integrated** with `gen-media-conc` to use evidence-based concentration predictions from the database.

## Integration Architecture

```
┌─────────────────────┐
│  gen-media-conc     │  Predicts LOW/DEFAULT/HIGH concentrations
│  (Evidence-based)   │  from database + literature
└──────────┬──────────┘
           │
           ├─── Option 1: Direct Integration (Automatic)
           │    └─> sensitivity uses GenMediaConcAgent internally
           │
           └─── Option 2: Pipeline Mode (Explicit)
                └─> JSON file → sensitivity --input-file
```

## Workflows

### 🎯 Workflow 1: Direct Mode (Recommended)

**For Medium Analysis:**
```bash
# Automatically uses database predictions via gen-media-conc
python run.py sensitivity "MP Medium (Methylotroph)"
python run.py sensitivity "LB medium"
```

**For Custom Ingredients:**
```bash
# Looks up each ingredient in database
python run.py sensitivity "PIPES,NaCl,glucose" --mode ingredients
```

**What happens internally:**
1. SensitivityAnalysisAgent calls GenMediaConcAgent
2. GenMediaConcAgent queries database + literature
3. Returns evidence-based LOW/HIGH/DEFAULT concentrations
4. Sensitivity analysis uses these predictions
5. Calculates pH & salinity at each concentration level

### 📊 Workflow 2: Pipeline Mode

**Step 1: Generate Predictions**
```bash
# Export gen-media-conc results to JSON
python run.py gen-media-conc "MP medium" --format json > mp_predictions.json 2>/dev/null
```

**Step 2: Run Sensitivity Analysis**
```bash
# Read from JSON and perform sensitivity sweep
python run.py sensitivity --input-file mp_predictions.json
```

**Step 3: Add Visualization**
```bash
# Generate plots
python run.py sensitivity --input-file mp_predictions.json \
  --plot --plot-output mp_sensitivity.png
```

**Why use pipeline mode?**
- Saves gen-media-conc results for later reuse
- Allows inspection/modification of predictions before sensitivity analysis
- Good for batch processing multiple media
- Reproducible workflows with saved intermediate files

### 📈 Workflow 3: Complete Analysis with Visualization

```bash
# Direct mode with full output
python run.py sensitivity "MP medium" \
  --plot --plot-output analysis.png \
  --format json --output results.json
```

Generates:
- `analysis.png` - 4-panel sensitivity plots
- `results.json` - Complete analysis results
- Console table output

### 🔄 Workflow 4: Batch Analysis

```bash
#!/bin/bash
# Analyze multiple media formulations

for medium in "MP medium" "LB medium" "M9 minimal medium"; do
  echo "Analyzing: $medium"

  # Generate predictions
  python run.py gen-media-conc "$medium" --format json 2>/dev/null > "${medium// /_}.json"

  # Run sensitivity analysis
  python run.py sensitivity --input-file "${medium// /_}.json" \
    --plot --plot-output "${medium// /_}_sensitivity.png"
done
```

## Output Formats

### Table Format (Default)
```bash
python run.py sensitivity "PIPES,NaCl" --mode ingredients
```

Output:
```
=== Sensitivity Analysis: PIPES,NaCl ===

BASELINE (All ingredients at DEFAULT):
  pH: 6.76
  Salinity: 13.69 g/L
  Ionic Strength: 0.0000 M
  Volume: 1000 mL

SENSITIVITY RESULTS:

ingredient concentration_level  concentration_value unit   ph  salinity  delta_ph  delta_salinity
     PIPES                 low                 10.0   mM 6.76      7.16       0.0           -6.53
     PIPES                high                100.0   mM 6.76     34.37       0.0           20.68
      NaCl                 low                 10.0   mM 6.76     10.15       0.0           -3.54
      NaCl                high                500.0   mM 6.76     38.78       0.0           25.09

SUMMARY:
  pH Range: 6.76 - 6.76
  Salinity Range: 7.16 - 38.78 g/L
  Most pH-sensitive ingredient: PIPES
  Most salinity-sensitive ingredient: NaCl
  Ingredients analyzed: 2
```

### JSON Format
```bash
python run.py sensitivity "PIPES,NaCl" --format json --output results.json
```

### YAML Format
```bash
python run.py sensitivity "PIPES,NaCl" --format yaml
```

### TSV Format (Spreadsheet-Compatible)
```bash
python run.py sensitivity "PIPES,NaCl" --format tsv --output results.tsv
```

## Visualization

The `--plot` flag generates a comprehensive 4-panel figure:

1. **pH Sensitivity Bar Chart** - Shows pH at LOW/HIGH for each ingredient
2. **Salinity Sensitivity Bar Chart** - Shows salinity at LOW/HIGH for each ingredient
3. **Delta Heatmap** - Color-coded changes from baseline (ΔpH and ΔSalinity)
4. **pH vs Salinity Scatter** - Relationship between pH and salinity across all conditions

```bash
python run.py sensitivity "MP medium" --plot --plot-output mp_analysis.png
```

## Command Options

```bash
python run.py sensitivity --help
```

**Arguments:**
- `QUERY` - Medium name or comma-separated ingredient list (optional if using --input-file)

**Options:**
- `--mode, -m` - Input mode: medium|ingredients|auto (default: auto)
- `--volume, -v` - Total volume in mL (default: 1000)
- `--db-path, -d` - Path to DuckDB database
- `--chebi-owl, -c` - Path to ChEBI OWL file
- `--input-file, -i` - Read gen-media-conc JSON output (pipeline mode)
- `--format, -f` - Output format: table|json|yaml|tsv (default: table)
- `--output, -o` - Output file path
- `--plot, -p` - Generate visualization plots
- `--plot-output` - Plot output path (default: sensitivity_plot.png)

## Understanding the Results

### Baseline
The baseline represents the media with **all ingredients at DEFAULT concentrations**. This is the reference point for all delta calculations.

### Sensitivity Results
For each ingredient:
- **LOW concentration**: Minimum safe/effective concentration
- **HIGH concentration**: Maximum safe concentration (below toxicity)
- **DEFAULT concentration**: Typical/optimal concentration (geometric mean of LOW/HIGH)

While varying one ingredient, **all others remain at DEFAULT**.

### Delta Values
- **delta_ph**: Change in pH from baseline when varying this ingredient
- **delta_salinity**: Change in salinity (g/L) from baseline
- **percent_change**: Percentage change from baseline

### Summary Statistics
- **pH Range**: [min, max] pH across all variations
- **Salinity Range**: [min, max] salinity across all variations
- **Most sensitive**: Ingredient causing largest absolute change

## Data Sources

The integration uses the following data hierarchy:

1. **Database** (via GenMediaConcAgent)
   - MediaDive data
   - MicroMediaParam properties
   - ingredient_effects table

2. **Literature** (via GenMediaConcAgent)
   - PubMed searches
   - Extracted concentration ranges

3. **Chemistry calculations** (via ChemistryAgent)
   - Molecular weight calculations
   - pKa estimation

4. **Fallback mock data** (when database unavailable)
   - Hardcoded values for common ingredients
   - Used only in testing/development

## Examples

### Example 1: Medium Analysis with Visualization
```bash
python run.py sensitivity "MP Medium (Methylotroph)" --plot
```

### Example 2: Custom Ingredients with Export
```bash
python run.py sensitivity "glucose,PIPES,MgSO4" \
  --mode ingredients \
  --format json \
  --output custom_analysis.json
```

### Example 3: Different Volume
```bash
# Analyze 500mL formulation
python run.py sensitivity "LB medium" --volume 500
```

### Example 4: Pipeline with Organism-Specific Predictions
```bash
# Step 1: Get organism-specific predictions
python run.py gen-media-conc "LB medium" \
  --organism "NCBITaxon:562" \
  --format json \
  2>/dev/null > lb_ecoli.json

# Step 2: Sensitivity analysis
python run.py sensitivity --input-file lb_ecoli.json --plot
```

## Technical Details

### Volume Calculation
Total volume = 1000mL (default) = ingredient volumes + distilled H₂O

For each ingredient:
- mass (g) = (concentration_mM / 1000) × molecular_weight × volume_L
- volume (mL) ≈ mass (g) / density (≈1 g/mL)
- water volume = 1000mL - Σ(ingredient volumes)

### pH Calculation
Uses **MediaPhCalculator** with:
- Henderson-Hasselbalch equation for buffers
- Weak acid/base calculations
- Salt pH effect corrections
- Ionic strength corrections (Davies equation)

### Salinity Calculation
Total dissolved solids (TDS) in g/L:
- Salinity = Σ(grams_per_liter) for all ingredients

### Concentration Defaults
- **DEFAULT** = geometric mean of LOW and HIGH (better for log-scale data)
- Or uses current concentration from database if available

## Troubleshooting

### "No ingredients found for query"
- Check medium name spelling
- Try `python run.py query "SELECT * FROM media WHERE name LIKE '%Medium%'"`
- Use `--mode ingredients` for custom lists

### "Using fallback mock data"
- Database not found or gen-media-conc query failed
- Check `--db-path` is correct
- Ensure database is loaded: `python run.py load-data`

### "Using default MW for ingredient"
- Molecular weight not in database
- Non-critical warning, uses reasonable default (100 g/mol)

### Pipeline mode JSON errors
- Ensure stderr is redirected: `2>/dev/null`
- Verify JSON is valid: `cat file.json | python -m json.tool`
- Check gen-media-conc succeeded: `"success": true` in JSON

## Best Practices

1. **Use direct mode** for quick analyses
2. **Use pipeline mode** for:
   - Batch processing
   - Reproducible workflows
   - Saving intermediate results

3. **Always specify organism** with gen-media-conc for organism-specific predictions

4. **Generate visualizations** for presentations and publications

5. **Export to JSON** for programmatic analysis

6. **Check baseline values** to ensure they match expectations

7. **Examine most sensitive ingredients** to identify critical formulation parameters

## Integration Benefits

✅ **Evidence-based predictions** from database + literature
✅ **Automatic data retrieval** via GenMediaConcAgent
✅ **Flexible workflows** (direct or pipeline)
✅ **Comprehensive output** (table, JSON, YAML, TSV, plots)
✅ **Organism-specific** predictions when needed
✅ **Reproducible** analyses with saved JSON files
✅ **Modular design** following Unix philosophy

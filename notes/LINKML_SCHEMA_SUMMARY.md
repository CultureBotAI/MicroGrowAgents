# LinkML Schema for Media Ingredients - Summary

## Overview

Created a comprehensive LinkML schema that models microbial growth media ingredients as structured objects, covering both **concentration data** and **effects data** from the MP medium ingredient properties CSV.

## Files Created

### 1. Schema Definition
**`src/microgrowagents/schema/media_ingredient.yaml`** (500+ lines)

Main LinkML schema with:
- **Classes**: `MediaIngredientCollection`, `MediaIngredient`, `ConcentrationData`, `StabilityData`, `BiologicalProperties`
- **46 Slots**: All fields from the CSV mapped to properly typed slots
- **4 Enumerations**: Controlled vocabularies for categorical data
- **1 Custom Type**: `DOI` with validation pattern

### 2. Example Data
**`src/microgrowagents/schema/media_ingredient_example.yaml`** (100+ lines)

Sample LinkML data showing:
- Methanol (CHEBI:17790)
- Methane (CHEBI:16811)
- Zinc sulfate (CHEBI:29105)
- Lithium chloride (CHEBI:30145)

### 3. Converter Utility
**`src/microgrowagents/utils/csv_to_linkml.py`** (430+ lines)

Python utility to convert CSV → LinkML format with:
- Column name mapping
- DOI list parsing
- Enum value normalization
- Data type conversion
- YAML/JSON output

### 4. Documentation
**`src/microgrowagents/schema/README.md`** (300+ lines)

Comprehensive guide covering:
- Schema structure
- Usage examples
- Validation instructions
- Integration with other systems

## Schema Structure

### MediaIngredient Object

Each ingredient is modeled as a comprehensive object with these property groups:

#### 1. Identification (4 fields)
```yaml
component: "Methanol"           # Required
chemical_formula: "CH4O"
database_id: "CHEBI:17790"      # Identifier, validated pattern
priority: 1
```

#### 2. Concentration Data (10 fields)
```yaml
concentration: "0.5% v/v"
solubility: "Miscible with water"
lower_bound: 0.1                # Float, units: mM
lower_bound_citation:           # List of DOIs
  - "https://doi.org/10.1128/AEM.02738-08"
upper_bound: 2.0
upper_bound_citation: [...]
limit_of_toxicity: 5.0
toxicity_citation: [...]
stock_concentration: "100 mM"
stock_concentration_citation: [...]
```

#### 3. Chemical Stability (10 fields)
```yaml
ph_effect: "Stable across pH 4-9"
ph_effect_citation: [...]
pka: 15.5
pka_citation: [...]
oxidation_state_stability: "Oxidizes readily in presence of oxygen"
oxidation_stability_citation: [...]
light_sensitivity: STABLE       # Enum
light_sensitivity_citation: [...]
autoclave_stability: STABLE     # Enum
autoclave_stability_citation: [...]
```

#### 4. Chemical Interactions (8 fields)
```yaml
precipitation_partners:         # List
  - "Phosphate"
  - "Carbonate"
precipitation_partners_citation: [...]
antagonistic_ions:             # List
  - "Calcium"
  - "Copper"
antagonistic_ions_citation: [...]
chelator_sensitivity: "Readily chelated by EDTA"
chelator_sensitivity_citation: [...]
redox_contribution: "Contributes to reducing potential"
redox_contribution_citation: [...]
```

#### 5. Biological Properties (8 fields)
```yaml
metabolic_role: "Carbon and energy source for methylotrophs"
metabolic_role_citation: [...]
essential_conditional: CONDITIONALLY_ESSENTIAL  # Enum
essential_conditional_citation: [...]
uptake_transporter: "Methanol dehydrogenase"
uptake_transporter_citation: [...]
regulatory_effects: "Induces methanol utilization genes"
regulatory_effects_citation: [...]
```

#### 6. Organism-Specific (6 fields)
```yaml
gram_differential: BOTH         # Enum
gram_differential_citation: [...]
aerobe_anaerobe_differential: "Primarily aerobic metabolism"
aerobe_anaerobe_citation: [...]
optimal_concentration_model_organisms: "0.5% for M. extorquens"
optimal_concentration_citation: [...]
```

## Key Features

### ✅ Comprehensive Data Model
- All 46 CSV columns mapped to typed slots
- Every data field can have citations (DOIs)
- Proper data types (string, float, integer)
- Units specified (mM for concentrations)

### ✅ Controlled Vocabularies
4 enumerations ensure data consistency:

1. **LightSensitivityEnum**: `STABLE`, `SENSITIVE`, `HIGHLY_SENSITIVE`, `UNKNOWN`
2. **AutoclaveStabilityEnum**: `STABLE`, `UNSTABLE`, `PARTIALLY_STABLE`, `FILTER_STERILIZE`, `UNKNOWN`
3. **EssentialityEnum**: `ESSENTIAL`, `CONDITIONALLY_ESSENTIAL`, `NON_ESSENTIAL`, `ORGANISM_SPECIFIC`, `UNKNOWN`
4. **GramDifferentialEnum**: `GRAM_POSITIVE_SPECIFIC`, `GRAM_NEGATIVE_SPECIFIC`, `BOTH`, `UNKNOWN`

### ✅ Data Validation
- DOI pattern validation: `^https://doi\.org/10\.\\d{4,9}/[-._;()/:A-Z0-9]+$`
- ChEBI ID pattern validation: `^CHEBI:\\d+$`
- Required fields enforced (`component`)
- Type checking (float, integer, string)

### ✅ Multivalued Fields
Properly handle lists:
- `precipitation_partners[]`
- `antagonistic_ions[]`
- All citation fields accept multiple DOIs

### ✅ Working Converter
Tested successfully on actual CSV data:
```bash
$ uv run python -m microgrowagents.utils.csv_to_linkml \
    data/raw/mp_medium_ingredient_properties.csv \
    -o media_ingredients.yaml

Converted 20 ingredients to media_ingredients.yaml
```

## Usage Examples

### Convert CSV to LinkML
```bash
# To YAML
uv run python -m microgrowagents.utils.csv_to_linkml \
    data/raw/mp_medium_ingredient_properties.csv \
    -o data/processed/media_ingredients.yaml

# To JSON
uv run python -m microgrowagents.utils.csv_to_linkml \
    data/raw/mp_medium_ingredient_properties.csv \
    -o data/processed/media_ingredients.json -f json
```

### Validate Data
```bash
# Install LinkML tools
pip install linkml linkml-runtime

# Validate
linkml-validate -s src/microgrowagents/schema/media_ingredient.yaml \
    data/processed/media_ingredients.yaml
```

### Generate Documentation
```bash
gen-markdown src/microgrowagents/schema/media_ingredient.yaml \
    > docs/schema.md
```

### Export to Other Formats
```bash
# JSON Schema (for APIs)
gen-json-schema src/microgrowagents/schema/media_ingredient.yaml \
    > api_schema.json

# Python dataclasses
gen-python src/microgrowagents/schema/media_ingredient.yaml \
    > datamodel.py

# SQL DDL
gen-sqla src/microgrowagents/schema/media_ingredient.yaml \
    > create_tables.sql

# OWL ontology
gen-owl src/microgrowagents/schema/media_ingredient.yaml \
    > media_ingredient.owl
```

## Programmatic Usage

```python
from microgrowagents.utils.csv_to_linkml import MediaIngredientCSVConverter
from pathlib import Path
import yaml

# Convert CSV to LinkML
converter = MediaIngredientCSVConverter(
    Path("data/raw/mp_medium_ingredient_properties.csv")
)
converter.save_yaml("output.yaml")

# Load and query data
with open("output.yaml") as f:
    data = yaml.safe_load(f)

# Find all essential ingredients
for ing in data["ingredients"]:
    if ing.get("essential_conditional") == "ESSENTIAL":
        print(f"{ing['component']}: {ing.get('metabolic_role', 'N/A')}")

# Find toxic ingredients
for ing in data["ingredients"]:
    tox = ing.get("limit_of_toxicity")
    if tox and tox < 1.0:  # Less than 1 mM
        print(f"⚠️ {ing['component']}: toxic at {tox} mM")
        if ing.get("toxicity_citation"):
            print(f"   Citations: {', '.join(ing['toxicity_citation'])}")
```

## Schema Benefits

### 1. **Standardization**
- Consistent field names across the dataset
- Controlled vocabularies prevent data entry errors
- Validated identifiers (ChEBI IDs, DOIs)

### 2. **Traceability**
- Every data point can have citations
- Multiple citations supported
- DOI validation ensures valid references

### 3. **Interoperability**
- Export to JSON Schema, SQL, OWL, RDF
- Compatible with Semantic Web tools
- Integration with knowledge graphs

### 4. **Machine-Readable**
- Typed fields enable automatic validation
- Enums enable automated processing
- Units enable unit conversion

### 5. **Extensibility**
- Easy to add new fields
- New enums can be added
- Backward compatible

## Test Results

✅ **Schema validated** - No LinkML errors
✅ **Example data validated** - Passes validation
✅ **Converter tested** - Successfully converted 20 ingredients
✅ **Output verified** - Proper YAML structure with all fields

### Sample Output Quality

From `/tmp/media_ingredients_test.yaml`:
```yaml
- component: PIPES
  database_id: CHEBI:39033
  concentration: 30 mM
  ph_effect: Stabilizes pH 6.1-7.5 at 20-40 mM
  ph_effect_citation:
  - https://doi.org/10.1021/bi00866a011
  metabolic_role: Non-metabolized pH buffer
  light_sensitivity: UNKNOWN
  essential_conditional: UNKNOWN
```

All fields properly mapped with:
- ✅ Correct data types
- ✅ Citation lists
- ✅ Enum values
- ✅ Clean formatting

## Next Steps

### Recommended Enhancements

1. **Add more enums** for other categorical fields
2. **Create validation rules** for concentration ranges
3. **Add cross-references** to other databases (PubChem, UniProt)
4. **Generate Python dataclasses** for type-safe code
5. **Create OWL ontology** for semantic reasoning
6. **Build DuckDB schema** from LinkML

### Integration Opportunities

1. **Knowledge Graph Integration** - Load into KG-Microbe
2. **API Development** - Use JSON Schema for REST API
3. **Database Loading** - Use SQL DDL to create tables
4. **Semantic Web** - Use OWL for ontology reasoning
5. **Type-Safe Code** - Use generated Python classes

## Summary Statistics

- **Schema**: 500+ lines, 4 classes, 46 slots, 4 enums, 1 custom type
- **Converter**: 430+ lines, handles all 46 CSV columns
- **Documentation**: 300+ lines with examples
- **Test Results**: 20/20 ingredients converted successfully
- **Coverage**: 100% of CSV columns mapped

The schema provides a **comprehensive, validated, machine-readable** representation of media ingredient data suitable for knowledge graph integration, API development, and semantic web applications.

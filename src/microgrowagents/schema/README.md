# MicroGrowAgents LinkML Schemas

LinkML schemas for MP (Methylotroph) medium data and media ingredient properties.

## Schema Files

### 1. mp_medium_schema.yaml ✅ CURRENT

**Complete schema for MP medium tables** covering all 4 data outputs:

- **mp_medium_ingredient_properties_with_roles.csv** (49 columns)
- **mp_medium_predictions.tsv** (9 columns)  
- **alternate_ingredients_table.csv** (7 columns)

**Classes:**
- `MPMediumDataset` - Root container for all MP medium data
- `MPMediumIngredient` - Full ingredient properties (maps to 49-column CSV)
- `ConcentrationPrediction` - Concentration predictions with pH effects
- `AlternateIngredient` - Alternative ingredient recommendations

**Enums:**
- `MediaRoleEnum` - 17 media roles (Carbon Source, Trace Elements, pH Buffer, etc.) ✅
- `ConcentrationUnitEnum` - Units (mM, M, g/L, mg/L, μg/L, %)
- `LightSensitivityEnum` - Light stability categories
- `AutoclaveStabilityEnum` - Autoclave stability categories
- `EssentialityEnum` - Essentiality classifications

**Key Features:**
- ✅ Media Role as enum (17 permissible values)
- ✅ All 49 columns mapped to slots
- ✅ DOI citations for all properties
- ✅ Solubility Citation (DOI) included
- ✅ Cellular Role + Cellular Role DOI
- ✅ ChEBI/biolink ontology mappings

---

## Media Role Enum Values

Based on actual MP medium ingredients:

| Enum Value | Description | ChEBI Mapping | Example |
|------------|-------------|---------------|---------|
| `CARBON_SOURCE` | Primary carbon and energy source | CHEBI:33284 | Methanol |
| `NITROGEN_SOURCE` | Nitrogen for amino acids | CHEBI:33273 | (NH₄)₂SO₄ |
| `PHOSPHATE_SOURCE` | Phosphate for nucleotides | CHEBI:26020 | K₂HPO₄ |
| `PH_BUFFER` | pH buffering (6.0-8.0) | CHEBI:35225 | PIPES |
| `TRACE_ELEMENT_FE` | Iron trace element | CHEBI:18248 | FeSO₄·7H₂O |
| `TRACE_ELEMENT_ZN` | Zinc trace element | CHEBI:27363 | ZnSO₄·7H₂O |
| `TRACE_ELEMENT_MN` | Manganese trace element | CHEBI:18291 | MnCl₂·4H₂O |
| `TRACE_ELEMENT_CU` | Copper trace element | CHEBI:28694 | CuSO₄·5H₂O |
| `TRACE_ELEMENT_CO` | Cobalt trace element | CHEBI:27638 | CoCl₂·6H₂O |
| `TRACE_ELEMENT_MO` | Molybdenum trace element | CHEBI:28685 | (NH₄)₆Mo₇O₂₄ |
| `ESSENTIAL_MACRONUTRIENT_MG` | Magnesium macronutrient | CHEBI:18420 | MgCl₂·6H₂O |
| `ESSENTIAL_MACRONUTRIENT_CA` | Calcium macronutrient | CHEBI:22984 | CaCl₂·2H₂O |
| `VITAMIN_COFACTOR_PRECURSOR` | Vitamin/cofactor | CHEBI:27027 | Biotin, Thiamin |
| `CHELATOR_METAL_BUFFER` | Chelating agent | CHEBI:38161 | Sodium citrate |
| `RARE_EARTH_ELEMENT` | Rare earth element | CHEBI:33319 | Dy, Nd, Pr |
| `NITROGEN_SULFUR_SOURCE` | Combined N+S source | - | (NH₄)₂SO₄ |
| `PHOSPHATE_PH_BUFFER` | Combined P+buffer | - | K₂HPO₄ |

---

## Usage

### Generate Python Dataclasses

```bash
uv run gen-python src/microgrowagents/schema/mp_medium_schema.yaml > \
  src/microgrowagents/schema/mp_medium_dataclasses.py
```

### Use in Python

```python
from microgrowagents.schema.mp_medium_dataclasses import (
    MPMediumIngredient,
    MediaRoleEnum,
)

ingredient = MPMediumIngredient(
    component="PIPES",
    media_role=[MediaRoleEnum.PH_BUFFER],
    chemical_formula="PIPES",
    kg_node_id="CHEBI:39033",
    concentration="30 mM",
    solubility="1000 mM",
    solubility_citation_doi=["https://doi.org/10.1021/bi00866a011"],
)
```

### Generate Other Formats

```bash
# Markdown docs
uv run gen-markdown src/microgrowagents/schema/mp_medium_schema.yaml > docs/schema.md

# JSON Schema
uv run gen-json-schema src/microgrowagents/schema/mp_medium_schema.yaml > schema.json

# SQL DDL  
uv run gen-sqla src/microgrowagents/schema/mp_medium_schema.yaml > schema_sqlalchemy.py
```

---

## All 49 Columns Mapped

| # | CSV Column | Schema Slot | Type |
|---|------------|-------------|------|
| 1 | Priority | priority | float |
| 2 | Component | component | string |
| 3 | Chemical_Formula | chemical_formula | string |
| 4 | Database_ID | kg_node_id | KG Node ID (CHEBI, PubChem, etc.) |
| 5 | Concentration | concentration | string |
| **6** | **Media Role** | **media_role** | **MediaRoleEnum (multivalued)** ✅ |
| **7** | **Media Role DOI** | **media_role_doi** | **DOI** ✅ |
| 8 | Solubility | solubility | string |
| **9** | **Solubility Citation (DOI)** | **solubility_citation_doi** | **DOI** ✅ |
| 10-49 | [All remaining columns] | [All mapped] | [With DOI citations] |

See schema file for complete mapping.

---

## Schema Version

**Version:** 1.1.0
**Last Updated:** 2026-01-10
**Status:** ✅ Production Ready

All 4 MP medium tables fully covered with LinkML schema including Media Role enum.

**Recent Changes:**
- Changed `database_id` to `kg_node_id` with support for multiple ID types (CHEBI, PubChem, CAS, MediaDive)
- Made `media_role` multivalued to support ingredients with multiple functional roles


# MicroGrowAgents

Agent-based system for microbial growth media analysis and prediction with advanced chemical property calculations.

[![Tests](https://github.com/CultureBotAI/MicroGrowAgents/workflows/Tests/badge.svg)](https://github.com/CultureBotAI/MicroGrowAgents/actions)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://CultureBotAI.github.io/MicroGrowAgents)

## Overview

MicroGrowAgents is a comprehensive toolkit for analyzing microbial growth media formulations. It combines database-driven ingredient predictions with advanced chemical property calculations to provide deep insights into media composition and suitability for different microorganisms.

### Key Features

- 🧪 **Media Concentration Predictions**: Predict concentration ranges for media ingredients using ML-based regression
- 🔬 **Advanced Chemistry Calculations**:
  - **Osmotic Properties**: Osmolarity, osmolality, water activity, growth categories
  - **Redox Properties**: Eh (redox potential), pE, electron balance, redox state classification
  - **Nutrient Ratios**: C:N:P ratios, Redfield deviation, limiting nutrient identification, trace metal analysis
  - **Thermodynamic Properties**: Gibbs free energy calculations (via eQuilibrator API)
- 📊 **Sensitivity Analysis**: Sweep ingredient concentrations to determine pH and salinity effects
- 🔍 **Media Comparison**: Compare ingredient compositions across different media
- 🌐 **External APIs**: Integration with PubChem, ChEBI, and eQuilibrator for chemical data enrichment
- 📈 **Visualization**: Generate plots for osmotic properties, nutrient ratios, and sensitivity analysis
- 🤖 **Media Formulation Recommendation**: AI-powered workflow that recommends new media formulations using KG-Microbe (1.5M nodes), literature evidence, and the MP medium database (158 ingredients, 90.5% citation coverage)
- 🧬 **Genome Function Interpretation**: Organism-specific media design using 57 Bakta-annotated genomes (667K features) with:
  - **Auxotrophy Detection**: Automatic identification of biosynthetic pathway gaps
  - **Enzyme Analysis**: EC number queries with wildcard support (1.1.*.* finds all CH-OH oxidoreductases)
  - **Cofactor Requirements**: Detection of essential cofactors that cannot be biosynthesized
  - **Transporter Analysis**: Concentration refinement based on nutrient uptake genes
  - See [docs/GENOME_FUNCTION.md](docs/GENOME_FUNCTION.md) for Claude Code agent examples
- 📚 **Sheet Query System**: Query extended information sheets with:
  - **4 Query Types**: Entity lookup, cross-reference, publication search, filtered queries
  - **3 Output Formats**: Markdown tables, JSON, evidence-rich reports
  - **Full-Text Search**: Search within publication markdown files with excerpts
  - **Cross-References**: Automatic linking between entities and publications
  - See [docs/SHEET_QUERY_SYSTEM.md](docs/SHEET_QUERY_SYSTEM.md) for complete guide

## Cofactor Analysis Data Sources

The CofactorMediaAgent integrates **6 major biological databases** and specialized literature:

### Primary Databases
- **[ChEBI](https://www.ebi.ac.uk/chebi/)** - Chemical identifiers for 44 cofactors ([DOI: 10.1093/nar/gkv1031](https://doi.org/10.1093/nar/gkv1031))
- **[KEGG](https://www.genome.jp/kegg/)** - 30+ biosynthesis pathway definitions ([DOI: 10.1093/nar/gkac963](https://doi.org/10.1093/nar/gkac963))
- **[BRENDA](https://www.brenda-enzymes.org/)** - EC-to-cofactor relationships ([DOI: 10.1093/nar/gky1048](https://doi.org/10.1093/nar/gky1048))
- **[ExplorEnz](https://www.enzyme-database.org/)** - Enzyme Commission nomenclature ([DOI: 10.1093/nar/gkn582](https://doi.org/10.1093/nar/gkn582))

### Knowledge Graph Integration
- **KG-Microbe** (1.5M nodes, 5.1M edges) - Enzyme-substrate relationships and pathway context
- Queries via `KGReasoningAgent` for multi-source evidence integration

### Reference Files
- `src/microgrowagents/data/cofactor_hierarchy.yaml` - 44 cofactors across 5 categories
- `src/microgrowagents/data/ec_to_cofactor_map.yaml` - 68 EC pattern mappings
- `data/processed/ingredient_cofactor_mapping.csv` - 13 MP medium cofactor providers

See [`docs/cofactor_data_sources.md`](docs/cofactor_data_sources.md) for detailed methodology and citations.

### Example: Cofactor Analysis for M. extorquens AM-1

Generate cofactor requirements table from Bakta genome annotations:

```bash
# Using Python API
uv run python -c "
from microgrowagents.agents import CofactorMediaAgent
from pathlib import Path

agent = CofactorMediaAgent(Path('data/processed/microgrow.duckdb'))
result = agent.run(
    query='Analyze cofactor requirements',
    organism='SAMN31331780',  # M. extorquens AM-1
    base_medium='MP'
)

# Save results
import pandas as pd
df = pd.DataFrame(result['data']['cofactor_table'])
df.to_csv('outputs/cofactor_analysis/cofactor_table_Methylorubrum_extorquens_AM1.csv')
"
```

**Results for M. extorquens AM-1** (from 110 EC numbers):
- **15 cofactors identified**
- **4 existing** in MP medium: TPP, Biotin, Fe-S clusters, Mg
- **11 missing**: PLP, THF, Coenzyme Q, NAD+, NADP+, ATP, CTP, GTP, UTP, CoA, SAM

Generated tables available at:
- CSV: `outputs/cofactor_analysis/cofactor_table_Methylorubrum_extorquens_AM1.csv`
- TSV: `outputs/cofactor_analysis/cofactor_table_Methylorubrum_extorquens_AM1.tsv`

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Quick Install

```bash
# Clone the repository
git clone https://github.com/CultureBotAI/MicroGrowAgents.git
cd MicroGrowAgents

# Install dependencies using uv
uv sync

# Verify installation
uv run python run.py --help
```

## Quick Start

### Generate Media Concentrations

Predict concentration ranges for a specific medium:

```bash
# Get MP medium concentrations
uv run python run.py gen-media-conc "MP medium"

# Get concentrations for custom ingredients
uv run python run.py gen-media-conc "glucose,NaCl,KH2PO4" --mode ingredients

# Export to JSON
uv run python run.py gen-media-conc "MP medium" --format json --output mp_medium.json
```

### Sensitivity Analysis

Analyze how ingredient concentration variations affect pH and salinity:

```bash
# Basic sensitivity analysis
uv run python run.py sensitivity "MP medium"

# With osmotic property calculations
uv run python run.py sensitivity "MP medium" --calculate-osmotic

# With all advanced properties
uv run python run.py sensitivity "MP medium" \
    --calculate-osmotic \
    --calculate-redox \
    --calculate-nutrients \
    --plot

# Custom parameters
uv run python run.py sensitivity "glucose,NH4Cl,KH2PO4" \
    --calculate-redox \
    --ph 6.5 \
    --temperature 37
```

### Advanced Chemistry Analysis

Calculate osmotic properties for a medium:

```python
from microgrowagents.chemistry.osmotic_properties import (
    calculate_osmolarity,
    calculate_water_activity
)

ingredients = [
    {"name": "NaCl", "concentration": 150.0, "molecular_weight": 58.44, "formula": "NaCl"},
    {"name": "KCl", "concentration": 5.0, "molecular_weight": 74.55, "formula": "KCl"}
]

# Calculate osmolarity
osm_result = calculate_osmolarity(ingredients, temperature=25.0)
print(f"Osmolarity: {osm_result['osmolarity']:.1f} mOsm/L")

# Calculate water activity
aw_result = calculate_water_activity(ingredients, temperature=25.0)
print(f"Water Activity: {aw_result['water_activity']:.4f}")
print(f"Growth Category: {aw_result['growth_category']}")
```

## Core Capabilities

### 1. Media Concentration Generation (`gen-media-conc`)

Predicts LOW, DEFAULT, and HIGH concentration ranges for media ingredients:

```bash
# Query by medium name
uv run python run.py gen-media-conc "MP medium"

# Query by ingredient list
uv run python run.py gen-media-conc "PIPES,NaCl,glucose" --mode ingredients

# With chemical data enrichment
uv run python run.py gen-media-conc "MP medium" --enrich pubchem
```

**Output includes:**
- Predicted concentration ranges (mM)
- Molecular weights
- Chemical formulas
- Confidence scores

### 2. Sensitivity Analysis (`sensitivity`)

Performs parameter sweep analysis by varying each ingredient between LOW and HIGH concentrations:

```bash
# Basic analysis (pH and salinity)
uv run python run.py sensitivity "MP medium"

# With advanced chemistry properties
uv run python run.py sensitivity "MP medium" --calculate-osmotic --calculate-nutrients

# Export results
uv run python run.py sensitivity "MP medium" --format json --output results.json

# Generate visualization
uv run python run.py sensitivity "MP medium" --plot --plot-output analysis.png
```

**Calculates:**
- pH changes
- Salinity (TDS and NaCl-equivalent)
- Ionic strength
- **Optional**: Osmotic properties, redox potential, nutrient ratios

### 3. Advanced Chemistry Properties

#### Osmotic Properties

Calculate osmolarity, osmolality, and water activity:

```bash
uv run python run.py sensitivity "MP medium" --calculate-osmotic
```

**Provides:**
- Osmolarity (mOsm/L)
- Osmolality (mOsm/kg)
- Water activity (aw)
- Growth category classification:
  - `most_bacteria` (aw > 0.98)
  - `halotolerant` (0.90 < aw ≤ 0.98)
  - `halophiles` (aw ≤ 0.90)
- Van't Hoff dissociation factors

**Example output:**
```json
{
  "osmotic_properties": {
    "osmolarity": 342.5,
    "osmolality": 339.8,
    "water_activity": 0.9938,
    "growth_category": "most_bacteria",
    "confidence": {"osmolarity": 0.85, "water_activity": 0.78}
  }
}
```

#### Redox Properties

Calculate redox potential (Eh), pE, and electron balance:

```bash
uv run python run.py sensitivity "glucose,NH4Cl" --calculate-redox --ph 7.0
```

**Calculates:**
- Eh (redox potential in mV)
- pE (electron activity)
- Redox state classification (oxidizing, reducing, intermediate)
- Electron donor/acceptor balance
- Standard redox couples (O2/H2O, NO3-/NO2-, SO42-/H2S, etc.)

**Uses Nernst equation:**
```
Eh = E0' + (59.16/n) × log([oxidized]/[reduced])  at 25°C
pH correction: Eh = E0 - (59.16/n) × pH
```

**Example output:**
```json
{
  "redox_properties": {
    "eh": 245.3,
    "pe": 4.15,
    "redox_state": "oxidizing",
    "electron_balance": {
      "total_donors": 240.0,
      "total_acceptors": 220.0,
      "balance": 8.3
    }
  }
}
```

#### Nutrient Ratios

Calculate C:N:P ratios and identify limiting nutrients:

```bash
uv run python run.py sensitivity "glucose,NH4Cl,KH2PO4" --calculate-nutrients
```

**Analyzes:**
- C:N:P molar ratios
- Limiting nutrient prediction
- Redfield ratio deviation (marine standard: 106:16:1)
- Trace metal ratios (Fe:P, Mn:P, Zn:P)
- Deficiencies and excesses

**Limiting nutrient criteria:**
- **P-limited**: C:P > 150 or N:P > 20
- **N-limited**: C:N > 20 or N:P < 10
- **C-limited**: C:N < 6.6
- **Balanced**: Near Redfield ratio

**Example output:**
```json
{
  "nutrient_ratios": {
    "c_mol": 60.0,
    "n_mol": 9.0,
    "p_mol": 0.6,
    "c_n_ratio": 6.67,
    "c_p_ratio": 100.0,
    "n_p_ratio": 15.0,
    "limiting_nutrient": "balanced",
    "redfield_deviation": 3.2,
    "trace_metals": {
      "fe_p_ratio": 0.015,
      "deficiencies": ["Co", "Mo"],
      "excesses": []
    }
  }
}
```

### 4. Media Comparison

Compare ingredient compositions between two media:

```bash
uv run python run.py compare-media "MP medium" "LB medium"
```

**Shows:**
- Common ingredients
- Unique ingredients to each medium
- Concentration differences

### 5. Media Formulation Recommendation (`recommend-media` workflow)

Recommend new media formulations using AI-powered multi-agent orchestration:

```python
from microgrowagents.skills.workflows import RecommendMediaWorkflow

# Initialize workflow
workflow = RecommendMediaWorkflow()

# Recommend organism-specific medium
result = workflow.run(
    query="Recommend medium for methanotrophic bacteria",
    organism="Methylococcus capsulatus",
    temperature=42.0,
    pH=6.8,
    carbon_source="methane",
    oxygen="aerobic",
    goals="defined,selective",
    output_format="markdown"
)
print(result)
```

**Features:**
- **Multi-source Evidence Integration**: Combines KG-Microbe, literature, and MP database
- **Organism-Specific**: Tailored to target organism metabolic requirements
- **Complete Formulation**: Ingredient list with concentrations, roles, and confidence scores
- **Chemical Compatibility**: Validates precipitation and antagonism risks
- **Alternative Ingredients**: Provides substitutes with rationales
- **Comprehensive Rationale**: Human-readable explanations for all decisions

**Example Goals:**
- `minimal` - Fewest ingredients, core nutrients only
- `defined` - All ingredients chemically defined, no undefined supplements
- `complex` - Rich nutrients, may include vitamins and cofactors
- `cost_effective` - Prioritizes inexpensive, common ingredients
- `high_yield` - Optimized for biomass/product formation
- `selective` - Includes selective agents or unusual nutrients

**Output includes:**
- Complete ingredient list with concentrations and ranges
- Predicted pH, ionic strength, and other properties
- Essential nutrient roles coverage
- Chemical compatibility notes
- Alternative ingredient suggestions
- Evidence from KG-Microbe, literature, and database
- Confidence scoring based on evidence quality

See `.claude/skills/recommend-media.md` for detailed documentation and examples.

### 6. Genome Function Interpretation

Organism-specific media design using Bakta-annotated genomes (57 genomes, 667,502 features):

**Key Capabilities:**

- **Auxotrophy Detection**: Automatically identify biosynthetic pathway gaps
- **Enzyme Queries**: EC number searches with wildcard support (e.g., `1.1.*.*`)
- **Cofactor Analysis**: Determine essential cofactors that cannot be biosynthesized
- **Transporter Analysis**: Find nutrient uptake genes for concentration refinement

**CLI Examples:**

```python
# Find oxidoreductase enzymes
from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent
from pathlib import Path

agent = KGReasoningAgent(Path('data/processed/microgrow.duckdb'))
result = agent.run('genome_enzymes SAMN00114986 1.1.*')
print(f"Found {result['data']['count']} enzymes")

# Detect auxotrophies
from microgrowagents.agents.genome_function_agent import GenomeFunctionAgent

agent = GenomeFunctionAgent(Path('data/processed/microgrow.duckdb'))
result = agent.detect_auxotrophies(query='detect auxotrophies', organism='SAMN00114986')
print(f"Detected {result['data']['summary']['auxotrophies_detected']} auxotrophies")
```

**Claude Code Agent Examples:**

See [docs/GENOME_FUNCTION.md](docs/GENOME_FUNCTION.md) for detailed examples including:
- Analyzing organism metabolic capabilities
- Comparing metabolic profiles of different organisms
- Designing organism-specific defined media
- Auxotrophy-guided media optimization
- Metabolic engineering context analysis

**Automatic Integration:**

Genome analysis is automatically integrated into:
- **MediaFormulationAgent**: Adds nutrients for detected auxotrophies
- **GenMediaConcAgent**: Refines concentrations based on transporter presence/affinity
- **KGReasoningAgent**: Adds `genome_enzymes`, `genome_auxotrophies`, `genome_transporters` queries

### 7. Integration Scripts

Standalone integration scripts for specific analyses:

```bash
# MP medium with osmotic properties
uv run python scripts/analyze_mp_medium_osmotic.py --plot --output-json results.json

# Generate visualization plots
uv run python scripts/analyze_mp_medium_osmotic.py --plot --plot-output mp_osmotic.png
```

## Advanced Usage

### Combining Multiple Property Calculations

Calculate all advanced properties simultaneously:

```bash
uv run python run.py sensitivity "MP medium" \
    --calculate-osmotic \
    --calculate-redox \
    --calculate-nutrients \
    --ph 7.0 \
    --temperature 30 \
    --format json \
    --output complete_analysis.json
```

### Pipeline Mode

Use `gen-media-conc` output as input to `sensitivity`:

```bash
# Step 1: Generate concentration predictions
uv run python run.py gen-media-conc "MP medium" --format json > predictions.json

# Step 2: Run sensitivity analysis on predictions
uv run python run.py sensitivity --input-file predictions.json --calculate-osmotic
```

### Python API

Use MicroGrowAgents programmatically:

```python
from microgrowagents.agents.sensitivity_analysis_agent import SensitivityAnalysisAgent

# Initialize agent
agent = SensitivityAnalysisAgent(db_path="data/microgrowdb.db")

# Run analysis with advanced properties
result = agent.run(
    query="MP medium",
    mode="medium",
    calculate_osmotic=True,
    calculate_redox=True,
    calculate_nutrients=True,
    temperature=37.0
)

# Access results
baseline = result["baseline"]
print(f"pH: {baseline['ph']}")
print(f"Osmolarity: {baseline['osmotic_properties']['osmolarity']} mOsm/L")
print(f"Limiting nutrient: {baseline['nutrient_ratios']['limiting_nutrient']}")
```

## Chemistry Modules

### Osmotic Properties

Module: `microgrowagents.chemistry.osmotic_properties`

**Functions:**
- `calculate_osmolarity(ingredients, temperature=25.0)` - Calculate osmolarity and osmolality
- `calculate_water_activity(ingredients, temperature=25.0, method="raoult")` - Calculate water activity
- `estimate_van_hoff_factor(formula, charge, name)` - Estimate dissociation factor

**Methods:**
- Raoult's law (dilute solutions)
- Robinson-Stokes (concentrated solutions)
- Bromley equation (high ionic strength)

### Redox Properties

Module: `microgrowagents.chemistry.redox_properties`

**Functions:**
- `calculate_redox_potential(ingredients, ph, temperature=25.0)` - Calculate Eh and pE
- `calculate_electron_balance(ingredients)` - Calculate electron donor/acceptor balance

**Constants:**
- Standard redox potentials (E0' at pH 7)
- Electron equivalents for common compounds

### Nutrient Ratios

Module: `microgrowagents.chemistry.nutrient_ratios`

**Functions:**
- `calculate_cnp_ratios(ingredients)` - Calculate C:N:P ratios and limiting nutrients
- `calculate_trace_metal_ratios(ingredients)` - Calculate trace metal requirements
- `parse_elemental_composition(formula)` - Parse chemical formulas

**References:**
- Redfield ratio (marine): C:N:P = 106:16:1
- Terrestrial microbes: C:N:P ≈ 60:7:1

### Thermodynamic Properties

Module: `microgrowagents.chemistry.thermodynamic_properties`

**Functions:**
- `calculate_gibbs_free_energy(reactants, products, ph=7.0)` - Calculate ΔG
- `calculate_formation_energy(compound)` - Calculate ΔGf°

**Data Sources:**
- eQuilibrator API (biochemical thermodynamics)
- Component Contribution method
- pH and ionic strength corrections

## Repository Structure

* [docs/](docs/) - MkDocs documentation
* [src/microgrowagents/](src/microgrowagents/) - Source code
  * [agents/](src/microgrowagents/agents/) - Agent implementations
  * [chemistry/](src/microgrowagents/chemistry/) - Chemistry calculation modules
  * [database/](src/microgrowagents/database/) - Database utilities
  * [api_clients/](src/microgrowagents/chemistry/api_clients/) - External API clients
* [tests/](tests/) - Pytest test suite (86 tests, >90% coverage)
* [scripts/](scripts/) - Integration and analysis scripts
* [data/](data/) - Database and cache files

## Development

### Running Tests

```bash
# Run all tests
just test

# Run specific test file
uv run pytest tests/test_chemistry/test_osmotic_properties.py -v

# Run with coverage
uv run pytest --cov=microgrowagents --cov-report=html
```

### Type Checking

```bash
just mypy
```

### Code Formatting

```bash
just format
```

### Documentation

```bash
# Serve documentation locally
just _serve

# Build documentation
mkdocs build
```

## Documentation Website

[https://CultureBotAI.github.io/MicroGrowAgents](https://CultureBotAI.github.io/MicroGrowAgents)

## Test Coverage

- **Osmotic Properties**: 21/21 tests, 20 doctests
- **Redox Properties**: 27/27 tests
- **Nutrient Ratios**: 27/27 tests
- **Sensitivity Analysis**: 11/11 integration tests
- **Total**: 86 tests passing across all modules

## External Dependencies

- **PubChem**: Chemical structure and property data
- **ChEBI**: Ontology-based chemical enrichment
- **eQuilibrator**: Biochemical thermodynamic calculations
- **NIST WebBook**: Inorganic thermodynamic data (planned)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass (`just test`)
5. Submit a pull request

## License

[Add license information]

## Credits

This project uses the template [monarch-project-copier](https://github.com/monarch-initiative/monarch-project-copier)

## Citation

If you use MicroGrowAgents in your research, please cite:

```
[Add citation information]
```

## Contact

For questions or issues, please open an issue on GitHub or contact [add contact information].

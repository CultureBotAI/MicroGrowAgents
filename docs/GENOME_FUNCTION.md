# Genome Function Interpretation

MicroGrowAgents includes comprehensive genome function interpretation capabilities using Bakta GFF3 annotations from 57 bacterial genomes (667,502 features).

## Overview

The genome function system provides organism-specific media formulation by:
- **Auxotrophy Detection**: Identifying missing biosynthetic pathways
- **Enzyme Analysis**: Querying EC numbers with wildcard support
- **Cofactor Requirements**: Determining essential cofactors that cannot be biosynthesized
- **Transporter Analysis**: Finding nutrient uptake genes for concentration refinement

## Data Source

- **57 Bakta-annotated genomes** from diverse bacteria
- **667,502 total features** (623,586 CDS, 7,236 tRNA, 660 rRNA)
- **100% organism linkage** to NCBI Taxonomy
- **Annotation coverage**: 14.8% EC, 18.6% GO, 10.7% KEGG, 24.2% COG

## CLI Usage

### Query Genome Enzymes

Find enzymes by EC number with wildcard support:

```bash
# Find all oxidoreductases (EC 1.*.*.*)
uv run python -c "
from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent
from pathlib import Path

agent = KGReasoningAgent(Path('data/processed/microgrow.duckdb'))
result = agent.run('genome_enzymes SAMN00114986 1.1.*')
print(f\"Found {result['data']['count']} enzymes\")
for enzyme in result['data']['enzymes'][:3]:
    print(f\"  {enzyme['gene_symbol']}: {enzyme['product']}\")
"
```

### Detect Auxotrophies

Identify metabolic auxotrophies from genome analysis:

```bash
uv run python -c "
from microgrowagents.agents.genome_function_agent import GenomeFunctionAgent
from pathlib import Path

agent = GenomeFunctionAgent(Path('data/processed/microgrow.duckdb'))
result = agent.detect_auxotrophies(
    query='detect auxotrophies',
    organism='SAMN00114986'
)

print(f\"Detected {result['data']['summary']['auxotrophies_detected']} auxotrophies\")
for aux in result['data']['auxotrophies']:
    print(f\"  {aux['pathway_name']}: {', '.join(aux['nutrients'])}\")
    print(f\"    Confidence: {aux['confidence']}, Completeness: {aux['completeness']:.1%}\")
"
```

### Find Transporters

Search for nutrient transporter genes:

```bash
uv run python -c "
from microgrowagents.agents.genome_function_agent import GenomeFunctionAgent
from pathlib import Path

agent = GenomeFunctionAgent(Path('data/processed/microgrow.duckdb'))
result = agent.find_transporters(
    query='find glucose transporters',
    organism='SAMN00114986',
    substrate='glucose'
)

print(f\"Found {len(result['data']['transporters'])} transporters\")
for transporter in result['data']['transporters'][:3]:
    print(f\"  {transporter['gene_symbol']}: {transporter['product']}\")
    print(f\"    Family: {transporter['family']}, Affinity: {transporter['affinity']}\")
"
```

## Claude Code Agent Examples

### Example 1: Analyze Organism's Metabolic Capabilities

**Prompt to Claude Code:**

```
Analyze the metabolic capabilities of SAMN00114986 genome:

1. Find all oxidoreductase enzymes (EC 1.*.*.*)
2. Detect any biosynthetic auxotrophies
3. Identify transporter genes for iron and glucose
4. Summarize the organism's metabolic profile

Use the GenomeFunctionAgent and provide a detailed report.
```

**What Claude Code will do:**
- Import and initialize GenomeFunctionAgent
- Call find_enzymes() with EC wildcard pattern
- Call detect_auxotrophies() for pathway analysis
- Call find_transporters() for iron and glucose
- Generate a structured markdown report with findings

### Example 2: Compare Two Organisms

**Prompt to Claude Code:**

```
Compare the metabolic capabilities of SAMN00114986 and SAMN00766392:

1. Compare their auxotrophy profiles
2. Compare their enzyme counts by EC class
3. Identify unique transporters in each organism
4. Generate a comparison table

Show which organism is more metabolically versatile.
```

**What Claude Code will do:**
- Run genome queries for both organisms in parallel
- Compare auxotrophies, enzymes, and transporters
- Calculate similarity metrics
- Generate side-by-side comparison table
- Provide recommendation on metabolic versatility

### Example 3: Design Organism-Specific Medium

**Prompt to Claude Code:**

```
Design a defined medium for SAMN02194963 using genome analysis:

1. Detect all auxotrophies from the genome
2. Identify essential cofactors that cannot be biosynthesized
3. Find transporter genes for key nutrients
4. Use MediaFormulationAgent to create formulation
5. Use GenMediaConcAgent to predict concentrations with transporter adjustments

Create a complete medium recipe with rationale.
```

**What Claude Code will do:**
- Run comprehensive genome analysis
- Detect auxotrophies automatically
- Identify required cofactors
- Query for transporter genes
- Integrate with MediaFormulationAgent to add auxotrophy supplements
- Refine concentrations based on transporter presence/affinity
- Generate complete medium formulation with evidence

### Example 4: Auxotrophy-Guided Media Optimization

**Prompt to Claude Code:**

```
I have a bacterial strain (SAMN05421681) that grows poorly on minimal medium.
Help me optimize the medium:

1. Detect auxotrophies from its genome
2. For each detected auxotrophy, recommend specific supplements
3. Find any missing cofactors
4. Check for transporter limitations
5. Generate an optimized medium formulation

Explain the reasoning for each recommendation.
```

**What Claude Code will do:**
- Analyze genome for biosynthetic pathway completeness
- Identify high-confidence auxotrophies
- Map auxotrophies to required nutrients
- Check cofactor biosynthesis capabilities
- Analyze transporter genes for uptake efficiency
- Create optimized formulation with detailed rationale
- Explain each supplement addition with genomic evidence

### Example 5: Metabolic Engineering Context

**Prompt to Claude Code:**

```
I want to engineer SAMN00114986 for increased production of L-methionine.
Analyze the genome to understand:

1. Current methionine biosynthesis pathway completeness
2. All enzymes involved (with EC numbers and locations)
3. Transporters for methionine precursors
4. Potential bottleneck enzymes
5. Required cofactors and their biosynthesis status

Suggest which genes might need overexpression.
```

**What Claude Code will do:**
- Check methionine pathway completeness
- List all pathway enzymes with genomic coordinates
- Identify precursor transporters
- Calculate pathway completeness scores
- Identify missing or low-copy enzymes
- Check cofactor dependencies
- Generate engineering recommendations with rationale

## Integration with Media Formulation

### Automatic Auxotrophy Supplementation

When using MediaFormulationAgent with an organism parameter, detected auxotrophies are automatically added:

```python
from microgrowagents.agents.media_formulation_agent import MediaFormulationAgent
from pathlib import Path

agent = MediaFormulationAgent(Path('data/processed/microgrow.duckdb'))

result = agent.run(
    query="Design minimal defined medium",
    organism="SAMN02194963",
    growth_conditions={"temperature": 37, "pH": 7.0},
    formulation_goals=["minimal", "defined"]
)

# result["data"]["formulation"] will automatically include:
# - Nutrients for detected auxotrophies (high/medium confidence)
# - Essential cofactors that cannot be biosynthesized
# - Evidence from genome analysis in rationale
```

### Transporter-Based Concentration Refinement

GenMediaConcAgent automatically refines concentrations based on transporter presence:

```python
from microgrowagents.agents.gen_media_conc_agent import GenMediaConcAgent
from pathlib import Path

agent = GenMediaConcAgent(Path('data/processed/microgrow.duckdb'))

result = agent.run(
    query="glucose,iron_sulfate,thiamine",
    mode="ingredients",
    organism="NCBITaxon:562"  # E. coli
)

# Concentrations are adjusted:
# - No transporter: +50% (passive diffusion needs higher concentration)
# - High-affinity transporter: -25% (efficient uptake)
# - Low/medium affinity: default range
```

## KG Reasoning Integration

Genome queries are integrated into KGReasoningAgent:

```python
from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent
from pathlib import Path

agent = KGReasoningAgent(Path('data/processed/microgrow.duckdb'))

# Query enzymes
result = agent.run("genome_enzymes SAMN00114986 2.7.*")

# Detect auxotrophies
result = agent.run("genome_auxotrophies SAMN02194963")

# Find transporters
result = agent.run("genome_transporters SAMN00114986 iron")
```

## Testing

Run comprehensive genome integration tests:

```bash
# Run all genome tests
uv run pytest tests/test_genome_integration.py -v

# Run specific test class
uv run pytest tests/test_genome_integration.py::TestGenomeFunctionAgent -v

# Run with coverage
uv run pytest tests/test_genome_integration.py --cov=microgrowagents.agents.genome_function_agent
```

## Data Loading

To reload genome data or add new genomes:

```bash
# Initialize genome schema
uv run python scripts/init_genome_schema.py

# Load all GFF3 files
uv run python scripts/load_genomes.py

# Test loading
uv run python scripts/test_genome_agent.py
```

## Architecture

The genome function system consists of:

1. **GFF3Parser** (`parsers/gff3_parser.py`): Parses Bakta GFF3 files
2. **NCBILookupService** (`services/ncbi_lookup.py`): Maps SAMN IDs to organisms
3. **GenomeDataLoader** (`database/genome_loader.py`): Batch loads genomes into DuckDB
4. **GenomeFunctionAgent** (`agents/genome_function_agent.py`): Core query interface
5. **Integration**: Automatic integration with media formulation and concentration agents

## Performance

- **Database**: 667,502 features with 9 indexes
- **Query time**: <100ms for most queries
- **Loading**: ~45 seconds for all 57 genomes (cached NCBI lookups)
- **Tests**: 17 comprehensive tests, all passing

## Limitations

- Pathway completeness uses simplified KEGG pathway definitions (3 pathways currently)
- Cofactor mapping is heuristic-based (EC class → cofactor)
- Transporter affinity is inferred from product descriptions
- Full implementation would integrate BRENDA, KEGG, and BioCyc databases

## Future Enhancements

- Expand pathway database to 35+ biosynthetic pathways
- Integrate BRENDA for comprehensive enzyme-cofactor mapping
- Add BioCyc pathway definitions for improved completeness scoring
- Implement transporter Km prediction from homology
- Support custom GFF3 file uploads
- Add comparative genomics visualizations

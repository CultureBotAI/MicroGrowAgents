# SheetQuery System Documentation

**Comprehensive information sheets query system for MicroGrowAgents**

## Overview

The SheetQuery system provides powerful querying capabilities for topic-specific extended data collections stored in `data/sheets_*` directories. It enables querying TSV files and full-text publication markdown files with evidence-rich reporting.

## Features

### 4 Query Types
1. **Entity Lookup**: Find entities by ID, name, or type
2. **Cross-Reference**: Find related entities across tables and publications
3. **Publication Search**: Full-text search within markdown publications
4. **Filtered Queries**: SQL-like filtering on any table

### 3 Output Formats
1. **Markdown Tables**: Formatted tables with DOI/PMID citation links
2. **JSON**: Clean structured data for programmatic use
3. **Evidence Reports**: Detailed reports with publication excerpts

### Database Schema
- **5 tables**: `sheet_collections`, `sheet_tables`, `sheet_data`, `sheet_publications`, `sheet_publication_references`
- **9 strategic indexes**: Optimized for all query types
- **EAV pattern**: Flexible JSON storage for variable schemas
- **Auto-increment IDs**: Using DuckDB sequences

## Quick Start

### 1. Initialize Schema

```bash
# Schema is automatically created when loading data
uv run python scripts/init_sheet_schema.py --database data/processed/microgrow.duckdb
```

### 2. Load Data

```bash
# Load CMM collection
uv run python scripts/load_sheets.py \
    --collection-id cmm \
    --sheets-dir data/sheets_cmm \
    --validate

# Expected output:
# Tables Loaded: 17
# Publications: 118
# Total Rows: 1,763
# References Created: 200+
```

### 3. Query Data

#### Python API (Agent)

```python
from microgrowagents.agents.sheet_query_agent import SheetQueryAgent

agent = SheetQueryAgent()

# Entity lookup
result = agent.entity_lookup(
    query="lookup europium",
    collection_id="cmm",
    entity_id="CHEBI:52927"
)

# Cross-reference
result = agent.cross_reference_query(
    query="find genes related to europium",
    collection_id="cmm",
    source_entity_id="CHEBI:52927",
    include_types=["gene"]
)

# Publication search
result = agent.publication_search(
    query="search for lanthanide studies",
    collection_id="cmm",
    keyword="lanthanide",
    include_excerpts=True
)

# Filtered query
result = agent.filtered_query(
    query="filter chemicals by formula",
    collection_id="cmm",
    table_name="chemicals",
    filter_conditions={"molecular_formula": "Eu3+"}
)
```

#### Python API (Skill)

```python
from microgrowagents.skills.simple.sheet_query import SheetQuerySkill

skill = SheetQuerySkill()

# Markdown output
result = skill.run(
    collection_id="cmm",
    query_type="entity_lookup",
    entity_id="CHEBI:52927",
    output_format="markdown"
)
print(result)

# JSON output
result = skill.run(
    collection_id="cmm",
    query_type="publication_search",
    keyword="europium",
    output_format="json"
)
import json
data = json.loads(result)

# Evidence report
result = skill.run(
    collection_id="cmm",
    query_type="cross_reference",
    source_entity_id="K23995",
    output_format="evidence_report"
)
print(result)
```

## Architecture

### Component Overview

```
SheetQuery System
├── Database Layer
│   ├── schema.py           # 5 tables + 9 indexes
│   ├── sheet_loader.py     # TSV + publication loading (661 lines)
│   └── init_sheet_schema.py # Schema initialization script
│
├── Agent Layer
│   └── sheet_query_agent.py  # 4 query types (655 lines)
│
├── Skill Layer
│   └── sheet_query.py        # 3 output formatters (541 lines)
│
└── Scripts
    └── load_sheets.py        # Data loading script (157 lines)
```

### Data Flow

```
1. Loading:
   TSV Files + Publications → SheetDataLoader → DuckDB (5 tables)

2. Querying:
   User Query → SheetQuerySkill → SheetQueryAgent → DuckDB
              → Format (MD/JSON/Report) → User

3. Cross-References:
   Entity → extract FK IDs → match publications → link via sheet_publication_references
```

## Database Schema Details

### Table 1: sheet_collections
Collection metadata registry
```sql
collection_id VARCHAR PRIMARY KEY    -- 'cmm', 'xyz'
collection_name VARCHAR NOT NULL     -- 'CMM Extended Data'
directory_path VARCHAR NOT NULL      -- 'data/sheets_cmm'
loaded_at TIMESTAMP
table_count INTEGER
total_rows INTEGER
```

### Table 2: sheet_tables
Table registry for each collection
```sql
table_id VARCHAR PRIMARY KEY         -- 'cmm_chemicals'
collection_id VARCHAR NOT NULL       -- FK to sheet_collections
table_name VARCHAR NOT NULL          -- 'chemicals'
source_file VARCHAR NOT NULL         -- 'BER_CMM_..._chemicals_extended.tsv'
row_count INTEGER
column_count INTEGER
columns_json TEXT                    -- JSON array of column names
```

### Table 3: sheet_data
Unified entity storage (EAV pattern)
```sql
id INTEGER PRIMARY KEY              -- Auto-increment via sequence
table_id VARCHAR NOT NULL           -- FK to sheet_tables
entity_id VARCHAR                   -- Primary ID (CHEBI:52927, K23995, etc.)
entity_name VARCHAR                 -- Primary name
entity_type VARCHAR                 -- 'chemical', 'gene', 'strain', etc.
data_json TEXT NOT NULL             -- Complete row as JSON
searchable_text TEXT                -- Concatenated text for full-text search
```

### Table 4: sheet_publications
Publication full-text index
```sql
id INTEGER PRIMARY KEY              -- Auto-increment
collection_id VARCHAR NOT NULL      -- FK to sheet_collections
file_name VARCHAR NOT NULL          -- 'PMID_24816778.md'
publication_id VARCHAR              -- 'pmid:24816778', 'doi:10.1038/...'
publication_type VARCHAR            -- 'pmid', 'doi', 'pmc'
title TEXT
full_text TEXT                      -- Complete markdown content
word_count INTEGER
```

### Table 5: sheet_publication_references
Cross-references between entities and publications
```sql
id INTEGER PRIMARY KEY              -- Auto-increment
publication_id INTEGER NOT NULL     -- FK to sheet_publications.id
table_id VARCHAR NOT NULL           -- FK to sheet_tables
entity_id VARCHAR NOT NULL          -- Entity referencing publication
reference_column VARCHAR            -- Column where reference appears (URL, DOI)
reference_value VARCHAR             -- Actual reference value
```

### Indexes (9 total)

**Entity Lookup** (Query Type 1):
- `idx_sheet_data_entity_id` - Fast ID lookups
- `idx_sheet_data_entity_name` - Name-based searches
- `idx_sheet_data_entity_type` - Type filtering

**Cross-Reference** (Query Type 2):
- `idx_sheet_data_composite` - (table_id, entity_type) compound index
- `idx_sheet_pub_refs_entity` - Entity→Publication links

**Publication Search** (Query Type 3):
- `idx_sheet_pubs_pub_id` - Publication ID lookups
- `idx_sheet_data_searchable` - Full-text search

**Filtered Queries** (Query Type 4):
- `idx_sheet_tables_collection` - Collection-based filtering
- `idx_sheet_data_table` - Table-based filtering

## Query Types in Detail

### 1. Entity Lookup

**Purpose**: Find entities by ID, name, or type

**Parameters**:
- `collection_id` (required): Collection to search
- `entity_id` (optional): Exact ID match
- `entity_name` (optional): Name match (exact or partial)
- `entity_type` (optional): Filter by type
- `exact_match` (optional): Boolean for partial name matching

**Example**:
```python
# By ID
result = agent.entity_lookup(
    query="lookup",
    collection_id="cmm",
    entity_id="CHEBI:52927"
)

# By name (partial)
result = agent.entity_lookup(
    query="find lanthanide",
    collection_id="cmm",
    entity_name="lanthanide",
    exact_match=False
)

# By type
result = agent.entity_lookup(
    query="all chemicals",
    collection_id="cmm",
    entity_type="chemical"
)
```

**Returns**:
```json
{
  "success": true,
  "data": {
    "entities": [{
      "entity_id": "CHEBI:52927",
      "entity_name": "Europium(III) cation",
      "entity_type": "chemical",
      "properties": {
        "chemical_id": "CHEBI:52927",
        "molecular_formula": "Eu3+",
        "molecular_weight": "151.964",
        "role": "TRL probe"
      }
    }]
  }
}
```

### 2. Cross-Reference Query

**Purpose**: Find entities related to a source entity and its publications

**Strategy**:
1. Retrieve source entity
2. Extract foreign key IDs from data_json (CHEBI, GO, KEGG, etc.)
3. Find entities with matching IDs
4. Search for entities referencing the source
5. Retrieve linked publications

**Parameters**:
- `collection_id` (required)
- `source_entity_id` (required)
- `include_types` (optional): Filter related entities by type

**Example**:
```python
result = agent.cross_reference_query(
    query="find entities related to XoxF",
    collection_id="cmm",
    source_entity_id="K23995",
    include_types=["chemical", "pathway"]
)
```

**Returns**:
```json
{
  "success": true,
  "data": {
    "source_entity": {
      "entity_id": "K23995",
      "entity_name": "XoxF methanol dehydrogenase",
      "entity_type": "gene"
    },
    "related_entities": [
      {
        "entity_id": "CHEBI:52927",
        "entity_name": "Europium(III) cation",
        "entity_type": "chemical",
        "relationship": "referenced_by_source"
      }
    ],
    "publications": [
      {
        "publication_id": "pmid:24816778",
        "publication_type": "pmid",
        "title": "Chemistry of Lanthanides..."
      }
    ]
  }
}
```

### 3. Publication Search

**Purpose**: Full-text search within publication markdown files

**Parameters**:
- `collection_id` (required)
- `keyword` or `keywords` (required): Search term(s)
- `max_results` (optional): Limit results (default: 50)
- `include_excerpts` (optional): Include text excerpts (default: True)

**Example**:
```python
result = agent.publication_search(
    query="search for europium studies",
    collection_id="cmm",
    keyword="europium",
    include_excerpts=True,
    max_results=10
)
```

**Returns**:
```json
{
  "success": true,
  "data": {
    "publications": [
      {
        "publication_id": "pmid:24816778",
        "publication_type": "pmid",
        "full_text": "...",
        "excerpt": "...lanthanides such as **europium** have emerged...",
        "entity_count": 5
      }
    ]
  }
}
```

### 4. Filtered Query

**Purpose**: SQL-like filtering on tables with JSON path extraction

**Supported Operators**:
- Equality: `{"property": "value"}`
- Contains: `{"property": {"$contains": "substring"}}`

**Parameters**:
- `collection_id` (required)
- `table_name` (optional): Specific table to filter
- `entity_type` (optional): Filter by entity type
- `filter_conditions` (optional): Dict of property filters

**Example**:
```python
# Simple equality
result = agent.filtered_query(
    query="filter by formula",
    collection_id="cmm",
    table_name="chemicals",
    filter_conditions={"molecular_formula": "Eu3+"}
)

# Contains operator
result = agent.filtered_query(
    query="filter genes",
    collection_id="cmm",
    table_name="genes_and_proteins",
    filter_conditions={
        "annotation": {"$contains": "dehydrogenase"}
    }
)

# Multiple conditions (AND logic)
result = agent.filtered_query(
    query="filter",
    collection_id="cmm",
    table_name="genes_and_proteins",
    filter_conditions={
        "organism": "NCBITaxon:469",
        "annotation": {"$contains": "methanol"}
    }
)
```

## Output Formats

### 1. Markdown Tables

**Best for**: Human-readable reports, documentation

**Features**:
- Formatted tables with pipe delimiters
- Clickable DOI/PMID citation links
- Limited to 50 entities per table for readability
- Includes section headers

**Example**:
```markdown
# Sheet Query Results: cmm

## Entities (5 found)

| ID | Name | Type | Properties |
|----|------|------|------------|
| CHEBI:52927 | Europium(III) cation | chemical | formula: Eu3+, MW: 151.964 |

## Publications (2 found)

### 1. [PMID:24816778](https://pubmed.ncbi.nlm.nih.gov/24816778/)

**Excerpt**: ...lanthanides such as **europium** have emerged...
```

### 2. JSON

**Best for**: Programmatic access, data pipelines

**Features**:
- Valid JSON with full data structures
- Includes execution metadata
- No data truncation

**Example**:
```json
{
  "success": true,
  "data": {
    "entities": [
      {
        "entity_id": "CHEBI:52927",
        "entity_name": "Europium(III) cation",
        "entity_type": "chemical",
        "properties": {
          "chemical_id": "CHEBI:52927",
          "molecular_formula": "Eu3+",
          "molecular_weight": "151.964"
        }
      }
    ],
    "count": 1
  },
  "metadata": {
    "query": "lookup chemical",
    "collection_id": "cmm",
    "execution_time": 0.05
  }
}
```

### 3. Evidence Reports

**Best for**: Detailed analysis, research reports

**Features**:
- Comprehensive entity details
- Grouped related entities by type
- Publication excerpts with context
- Structured sections with headers
- Publication links

**Example**:
```markdown
# Evidence Report: cmm

## Entity Details

**Chemical**: Europium(III) cation

**ID**: CHEBI:52927

### Properties

- **molecular_formula**: Eu3+
- **molecular_weight**: 151.964
- **role**: TRL assay probe

## Related Entities (3)

### Genes (2)

- **K23995**: XoxF methanol dehydrogenase
  - *referenced_by_source*
- **custom_xoxF_ma**: Lanthanide-dependent methanol dehydrogenase

## Publication Evidence

### 1. PMID:24816778

[View on PubMed](https://pubmed.ncbi.nlm.nih.gov/24816778/)

> Lanthanides such as **europium** and **terbium** have emerged
> as essential cofactors for bacterial enzymes involved in
> methanol metabolism...

**Referenced by**: 5 entities in this collection
```

## Testing

### Test Coverage: 91/91 tests passing (100%)

**Schema Tests** (8 tests):
- Table creation
- Index creation
- Data insertion
- Constraint validation

**Loader Tests** (20 tests):
- TSV loading
- Publication loading
- Entity type inference
- Publication ID extraction
- Cross-reference building
- Error handling

**Agent Tests** (27 tests):
- Entity lookup (7 tests)
- Cross-reference (3 tests)
- Publication search (5 tests)
- Filtered queries (5 tests)
- Query routing (5 tests)
- Error handling (2 tests)

**Skill Tests** (22 tests):
- Markdown output (3 tests)
- JSON output (3 tests)
- Evidence reports (3 tests)
- All query types (4 tests)
- Parameter validation (3 tests)
- Output switching (1 test)

**Integration Tests** (14 tests):
- End-to-end workflow
- Data integrity
- Publication citations
- Multiple collections
- Query performance
- Error recovery
- Output formats
- Data validation

### Running Tests

```bash
# All SheetQuery tests
uv run pytest tests/test_database/test_sheet_schema.py \
             tests/test_database/test_sheet_loader.py \
             tests/test_agents/test_sheet_query_agent.py \
             tests/test_skills/test_sheet_query_skill.py \
             tests/integration/test_sheet_query_integration.py -v

# Specific test categories
uv run pytest tests/test_database/test_sheet_loader.py -v  # Loader only
uv run pytest tests/test_agents/test_sheet_query_agent.py -v  # Agent only
uv run pytest tests/integration/ -v  # Integration only
```

## Performance

### Query Performance Benchmarks

**Entity Lookup by ID**: < 100ms (indexed)
**Cross-Reference Query**: < 500ms
**Publication Search**: < 1 second
**Filtered Query**: < 200ms

### Loading Performance

**CMM Collection** (17 TSV + 118 publications):
- Loading time: ~30 seconds
- Total rows: 1,763
- Database size: ~15 MB

### Optimization Features

1. **Strategic Indexes**: 9 indexes optimized for specific query patterns
2. **Batch Inserts**: 1000 rows per INSERT during loading
3. **JSON Storage**: Flexible schema without complex migrations
4. **Connection Pooling**: Reuse database connections

## Troubleshooting

### Common Issues

**Issue**: "Table does not exist" error
**Solution**: Run `scripts/init_sheet_schema.py` or load data with `--validate` flag

**Issue**: "Collection not found"
**Solution**: Verify collection_id matches loaded collection name

**Issue**: "Slow queries"
**Solution**: Ensure indexes exist (`SHOW INDEXES` in DuckDB)

**Issue**: "Connection error"
**Solution**: Ensure no stale connections; loader auto-closes after operations

### Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check loaded collections
conn = duckdb.connect("data/processed/microgrow.duckdb")
conn.execute("SELECT * FROM sheet_collections").fetchall()

# Check table counts
conn.execute("""
    SELECT collection_id, table_name, row_count
    FROM sheet_tables
    ORDER BY collection_id, table_name
""").fetchall()

# Check indexes
conn.execute("SHOW INDEXES").fetchall()
```

## Future Enhancements

Potential improvements:
1. **Query Language**: Natural language query parsing
2. **Advanced Filters**: Greater-than, less-than, IN operators
3. **Aggregations**: COUNT, GROUP BY on entity properties
4. **Export**: Direct export to CSV, Excel, PDF
5. **Caching**: Query result caching for frequent searches
6. **Fuzzy Search**: Approximate string matching for entity names

## License

Part of MicroGrowAgents project.

## Support

For issues or questions:
- GitHub Issues: https://github.com/monarch-initiative/MicroGrowAgents/issues
- Documentation: `docs/`

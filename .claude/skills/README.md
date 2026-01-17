# MicroGrowAgents Skills

Claude Code skills for microbial growth media analysis and prediction.

## Quick Start

The MicroGrowAgents library provides **9 skills** organized into three categories:

- **7 Simple Skills** - Single-agent wrappers for focused tasks
- **2 Workflow Skills** - Multi-agent orchestrations for complex analyses
- **3 Utility Skills** - Database and export helpers (coming soon)

All skills support both **markdown** (human-readable) and **JSON** (machine-readable) output formats.

## Available Skills

### Simple Skills (Single-Agent Wrappers)

#### 1. predict-concentration
Predict optimal concentration ranges for media ingredients.

```python
from microgrowagents.skills.simple import PredictConcentrationSkill

skill = PredictConcentrationSkill()
result = skill.run(
    query="glucose",
    unit="g/L",
    output_format="markdown"
)
print(result)
```

**Parameters:**
- `query` (required): Medium name or comma-separated ingredient list
- `mode` (optional): "medium" or "ingredients" (auto-detected)
- `organism` (optional): Organism for specific predictions
- `unit` (optional): "mM" or "g/L" (default: mM)

**Examples:**
- `predict-concentration glucose`
- `predict-concentration 'glucose,NaCl,KH2PO4'`
- `predict-concentration 'MP medium' --organism 'Escherichia coli'`

---

#### 2. find-alternates
Find alternative/substitute ingredients with similar function.

```python
from microgrowagents.skills.simple import FindAlternatesSkill

skill = FindAlternatesSkill()
result = skill.run(
    ingredient_name="FeSO4·7H2O",
    max_alternates=5,
    output_format="markdown"
)
print(result)
```

**Parameters:**
- `ingredient_name` (required): Ingredient to find alternates for
- `max_alternates` (optional): Maximum alternates to return (default: 5)

**Examples:**
- `find-alternates 'FeSO4·7H2O'`
- `find-alternates glucose --max_alternates 3`
- `find-alternates PIPES`

---

#### 3. analyze-sensitivity
Analyze effects of concentration variations on media chemistry.

```python
from microgrowagents.skills.simple import AnalyzeSensitivitySkill

skill = AnalyzeSensitivitySkill()
result = skill.run(
    query="glucose,NaCl,KH2PO4",
    calculate_osmotic=True,
    output_format="markdown"
)
print(result)
```

**Parameters:**
- `query` (required): Medium name or ingredient list
- `calculate_osmotic` (optional): Calculate osmotic properties (default: False)
- `calculate_redox` (optional): Calculate redox properties (default: False)
- `calculate_nutrients` (optional): Calculate nutrient ratios (default: False)

**Examples:**
- `analyze-sensitivity 'glucose,NaCl,KH2PO4'`
- `analyze-sensitivity 'MP medium' --calculate_osmotic true`

---

#### 4. classify-role
Classify media role/function of an ingredient.

```python
from microgrowagents.skills.simple import ClassifyRoleSkill

skill = ClassifyRoleSkill()
result = skill.run(
    ingredient_name="glucose",
    output_format="markdown"
)
print(result)
```

**Parameters:**
- `ingredient_name` (required): Ingredient to classify

**Examples:**
- `classify-role glucose`
- `classify-role 'NH4Cl'`
- `classify-role 'FeSO4·7H2O'`

---

#### 5. search-literature
Search scientific literature (PubMed and web).

```python
from microgrowagents.skills.simple import SearchLiteratureSkill

skill = SearchLiteratureSkill()
result = skill.run(
    query="glucose fermentation",
    max_results=10,
    output_format="markdown"
)
print(result)
```

**Parameters:**
- `query` (required): Search query
- `max_results` (optional): Maximum results (default: 10)

**Examples:**
- `search-literature 'glucose fermentation'`
- `search-literature 'iron toxicity bacteria'`

---

#### 6. query-database
Run SQL queries on the MicroGrow database.

```python
from microgrowagents.skills.simple import QueryDatabaseSkill

skill = QueryDatabaseSkill()
result = skill.run(
    query="SELECT * FROM media LIMIT 5",
    output_format="markdown"
)
print(result)
```

**Parameters:**
- `query` (required): SQL query string
- `max_rows` (optional): Maximum rows (default: 100)

**Examples:**
- `query-database 'SELECT * FROM media LIMIT 5'`
- `query-database 'SELECT COUNT(*) FROM kg_nodes'`

---

#### 7. calculate-chemistry
Perform chemical calculations (MW, pH, pKa, conversions).

```python
from microgrowagents.skills.simple import CalculateChemistrySkill

skill = CalculateChemistrySkill()
result = skill.run(
    operation="molecular_weight",
    compound="glucose",
    output_format="markdown"
)
print(result)
```

**Parameters:**
- `operation` (required): "molecular_weight", "ph", "pka", "convert_units"
- `compound` (required): Compound name or formula
- `concentration` (optional): For pH calculations
- `from_unit`, `to_unit` (optional): For conversions

**Examples:**
- `calculate-chemistry --operation molecular_weight --compound glucose`
- `calculate-chemistry --operation pka --compound 'acetic acid'`

---

### Workflow Skills (Multi-Agent Orchestrations)

#### 8. ingredient-report
Generate comprehensive ingredient report (role, concentration, chemistry, literature).

```python
from microgrowagents.skills.workflows import IngredientReportWorkflow

workflow = IngredientReportWorkflow()
result = workflow.run(
    ingredient="glucose",
    include_literature=True,
    output_format="markdown"
)
print(result)
```

**Orchestrates:** MediaRoleAgent → GenMediaConcAgent → ChemistryAgent → LiteratureAgent

**Parameters:**
- `ingredient` (required): Ingredient name
- `include_literature` (optional): Include literature search (default: True)
- `organism` (optional): For organism-specific predictions

**Examples:**
- `ingredient-report glucose`
- `ingredient-report 'FeSO4·7H2O' --include_literature false`

---

#### 9. optimize-medium
Optimize growth medium composition (cost, growth, stability).

```python
from microgrowagents.skills.workflows import OptimizeMediumWorkflow

workflow = OptimizeMediumWorkflow()
result = workflow.run(
    medium_name="MP medium",
    optimization_goal="cost",
    output_format="markdown"
)
print(result)
```

**Orchestrates:** SensitivityAnalysisAgent → AlternateIngredientAgent → GenMediaConcAgent

**Parameters:**
- `medium_name` (required): Medium name or ingredient list
- `optimization_goal` (required): "cost", "growth", or "stability"
- `organism` (optional): Target organism
- `max_alternates_per_ingredient` (optional): Max alternates per ingredient (default: 3)

**Examples:**
- `optimize-medium 'MP medium' --optimization_goal cost`
- `optimize-medium 'LB medium' --optimization_goal growth --organism 'E. coli'`

---

## Output Formats

All skills support three output formats via the `output_format` parameter:

### 1. Markdown (Default)
Human-readable tables with DOI citations.

```python
result = skill.run(query="glucose", output_format="markdown")
```

Output:
```
| Ingredient | Range (LOW - HIGH) | Default | Essential | Confidence |
| --- | --- | --- | --- | --- |
| glucose | 1 - 20 g/L | 10 g/L | Yes | 85.0% |

## References

1. [10.1021/acs.jced.8b00201](https://doi.org/10.1021/acs.jced.8b00201)
```

### 2. JSON
Machine-readable structured data.

```python
result = skill.run(query="glucose", output_format="json")
```

Output:
```json
{
  "success": true,
  "data": [...],
  "evidence": [...],
  "metadata": {...}
}
```

### 3. Both
Both formats combined.

```python
result = skill.run(query="glucose", output_format="both")
```

---

## Database Setup

Most skills require the MicroGrow database with KG-Microbe data.

### Auto-Initialization

Skills will **automatically initialize** the database if:
1. Database file doesn't exist
2. KG-Microbe data files exist in `data/raw/`

Required files:
- `data/raw/merged-kg_nodes.tsv`
- `data/raw/merged-kg_edges.tsv`

### Manual Initialization

```python
from microgrowagents.skills.db_handler import DatabaseHandler

handler = DatabaseHandler()
success = handler._initialize_database()
print(f"Database initialized: {success}")
```

---

## Troubleshooting

### "Database not initialized"

**Cause:** Database file missing or incomplete.

**Solution:**
1. Check if `data/raw/merged-kg_nodes.tsv` exists
2. Run database initialization:
   ```python
   from microgrowagents.skills.db_handler import DatabaseHandler
   handler = DatabaseHandler()
   handler._initialize_database()
   ```

### "Missing required parameter"

**Cause:** Required skill parameter not provided.

**Solution:** Check skill metadata for required parameters:
```python
skill = PredictConcentrationSkill()
metadata = skill.get_metadata()
for param in metadata.parameters:
    print(f"{param.name} (required: {param.required})")
```

### Import errors

**Cause:** Skills package not installed or outdated.

**Solution:**
```bash
uv sync
uv run python -c "from microgrowagents.skills import BaseSkill"
```

---

## Skill Development

To create a new skill:

1. **Inherit from BaseSkill:**
```python
from microgrowagents.skills.base_skill import BaseSkill, SkillMetadata, SkillParameter

class MySkill(BaseSkill):
    def get_metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="my-skill",
            description="Does something useful",
            category="simple",
            parameters=[...],
            examples=[...],
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        # Your skill logic here
        return {
            "success": True,
            "data": {...},
        }
```

2. **Add to package:**
- Place file in `src/microgrowagents/skills/simple/` (or `workflows/`)
- Add to `__init__.py`

3. **Write tests:**
- Create test file in `tests/test_skills/`
- Test with mock and real data

---

## Support

- **Documentation:** See individual skill files for detailed docstrings
- **Examples:** Check `examples/` directory for usage examples
- **Issues:** Report at GitHub repository

---

**Total Skills:** 9 (7 simple + 2 workflows)
**Framework Version:** 1.0.0
**Last Updated:** 2026-01-07

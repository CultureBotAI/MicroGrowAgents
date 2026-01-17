---
name: predict-concentration
description: Predict optimal concentration ranges for media ingredients
category: simple
requires_database: true
requires_internet: true
version: 1.0.0
---

# Predict Concentration Skill

Predict optimal concentration ranges for media ingredients based on literature evidence, chemical properties, database records, and rule-based heuristics.

## Usage

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

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | str | Yes | - | Medium name/ID OR comma-separated ingredient list |
| `mode` | str | No | auto-detect | Prediction mode: "medium" or "ingredients" |
| `organism` | str | No | None | NCBITaxon ID or organism name for specific predictions |
| `unit` | str | No | "mM" | Preferred output unit: "mM" or "g/L" |
| `output_format` | str | No | "markdown" | Output format: "markdown", "json", or "both" |

## Examples

### Basic Usage

```python
# Single ingredient
skill = PredictConcentrationSkill()
result = skill.run(query="glucose")
```

### Multiple Ingredients

```python
# Comma-separated list
result = skill.run(query="glucose,NaCl,KH2PO4")
```

### Organism-Specific

```python
# E. coli specific predictions
result = skill.run(
    query="glucose",
    organism="Escherichia coli",
    unit="g/L"
)
```

### From Medium Name

```python
# Extract concentrations from existing medium
result = skill.run(query="MP medium")
```

## Output Format

### Markdown Table

```
| Ingredient | Range (LOW - HIGH) | Default | Essential | Confidence |
| --- | --- | --- | --- | --- |
| glucose | 1 - 20 g/L | 10 g/L | Yes | 85.0% |
| NaCl | 0 - 10 g/L | 5 g/L | No | 75.0% |

## References

1. [10.1021/acs.jced.8b00201](https://doi.org/10.1021/acs.jced.8b00201) (confidence: 90.0%)
```

### JSON Output

```json
{
  "success": true,
  "data": [
    {
      "Ingredient": "glucose",
      "Range (LOW - HIGH)": "1 - 20 g/L",
      "Default": "10 g/L",
      "Essential": "Yes",
      "Confidence": "85.0%"
    }
  ],
  "evidence": [
    {
      "doi": "10.1021/acs.jced.8b00201",
      "confidence": 0.9
    }
  ],
  "metadata": {
    "prediction_method": "multi_source",
    "data_sources": ["kg_microbe", "pubchem", "pubmed"]
  }
}
```

## Data Sources

The skill integrates evidence from:

1. **KG-Microbe** - Knowledge graph with 1.5M nodes, 5.1M edges
2. **PubChem** - Chemical properties and molecular data
3. **PubMed** - Literature evidence for concentrations
4. **Database** - Historical media formulations

## Confidence Scores

Confidence indicates prediction reliability:

- **>80%**: Strong evidence from multiple sources
- **60-80%**: Moderate evidence, some uncertainty
- **<60%**: Limited evidence, use with caution

## Error Handling

### Database Not Found

```
Error: Database not initialized. Run 'initialize-database' first.

Troubleshooting:
- Run `initialize-database` to set up the database
- Ensure data files exist in `data/raw/`
- Check database permissions
```

**Solution:**
```python
from microgrowagents.skills.db_handler import DatabaseHandler
handler = DatabaseHandler()
handler._initialize_database()
```

### Invalid Query

```
Error: Empty query provided
```

**Solution:** Provide valid ingredient name or medium name in `query` parameter.

## Related Skills

- **find-alternates** - Find substitute ingredients
- **classify-role** - Classify ingredient function
- **analyze-sensitivity** - Analyze concentration effects
- **ingredient-report** - Comprehensive ingredient analysis (workflow)

## Implementation Details

**Wraps:** `GenMediaConcAgent`

**Agent Workflow:**
1. Parse query (medium name vs ingredient list)
2. Query database for existing records
3. Search PubMed for concentration ranges
4. Query PubChem for chemical properties
5. Apply rule-based heuristics (toxicity, osmotic pressure)
6. Aggregate evidence with confidence scoring
7. Return concentration ranges (LOW, DEFAULT, HIGH)

**Performance:** ~2-5 seconds per ingredient (depends on network latency for PubMed/PubChem)

## Citation

If you use this skill in your research, please cite:

```
MicroGrowAgents Skills Framework (2026)
https://github.com/monarch-initiative/microgrowagents
```

---

**Skill Type:** Simple (single-agent wrapper)
**Agent:** GenMediaConcAgent
**Version:** 1.0.0
**Last Updated:** 2026-01-07

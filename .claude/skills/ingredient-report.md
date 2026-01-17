---
name: ingredient-report
description: Generate comprehensive ingredient report (role, concentration, chemistry, literature)
category: workflow
requires_database: true
requires_internet: true
version: 1.0.0
---

# Ingredient Report Workflow

Generate a comprehensive multi-section report for an ingredient by orchestrating multiple agents.

## Workflow Overview

This workflow coordinates **4 agents** to produce a complete ingredient analysis:

1. **MediaRoleAgent** → Classify ingredient role
2. **GenMediaConcAgent** → Predict concentration ranges
3. **ChemistryAgent** → Calculate molecular properties
4. **LiteratureAgent** → Search scientific literature

## Usage

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

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `ingredient` | str | Yes | - | Ingredient name or chemical formula |
| `include_literature` | bool | No | True | Include literature search results |
| `organism` | str | No | None | Organism for organism-specific predictions |
| `output_format` | str | No | "markdown" | Output format: "markdown", "json", or "both" |

## Examples

### Basic Report

```python
workflow = IngredientReportWorkflow()
result = workflow.run(ingredient="glucose")
```

### Without Literature

```python
# Faster execution, skip literature search
result = workflow.run(
    ingredient="FeSO4·7H2O",
    include_literature=False
)
```

### Organism-Specific

```python
# E. coli specific predictions
result = workflow.run(
    ingredient="glucose",
    organism="Escherichia coli"
)
```

## Output Format

The workflow generates a **4-section report**:

### Section 1: Role Classification

```
## Role Classification

**Media Role:** Carbon Source
**Confidence:** 95.0%
**Rationale:** Glucose is a hexose monosaccharide that serves as primary carbon and energy source for microbial growth.
```

### Section 2: Concentration Prediction

```
## Concentration Ranges

| Range Type | Concentration | Essential | Confidence |
| --- | --- | --- | --- |
| LOW | 1 g/L | Yes | 85% |
| DEFAULT | 10 g/L | Yes | 85% |
| HIGH | 20 g/L | Yes | 85% |
```

### Section 3: Chemical Properties

```
## Chemical Properties

**Molecular Weight:** 180.16 g/mol
**Formula:** C₆H₁₂O₆
**pKa Values:** 12.28 (hydroxyl groups)
**Solubility:** Highly soluble in water (>900 g/L at 25°C)
```

### Section 4: Literature (Optional)

```
## Literature Evidence

1. [PMID:12345678] - *Glucose metabolism in E. coli*
2. [10.1021/example] - *Optimal glucose concentrations for bacterial growth*
```

## Full Example Output

```markdown
# Ingredient Report: Glucose

## Role Classification
**Media Role:** Carbon Source
**Confidence:** 95.0%

## Concentration Ranges
| Range Type | Concentration | Essential | Confidence |
| LOW | 1 g/L | Yes | 85% |
| DEFAULT | 10 g/L | Yes | 85% |
| HIGH | 20 g/L | Yes | 85% |

## Chemical Properties
**Molecular Weight:** 180.16 g/mol
**Formula:** C₆H₁₂O₆

## Literature Evidence
1. [10.1021/acs.jced.8b00201](https://doi.org/10.1021/acs.jced.8b00201)

---

*Metadata:*
- Workflow: ingredient_report
- Agents Used: MediaRoleAgent, GenMediaConcAgent, ChemistryAgent, LiteratureAgent
- Execution time: 4.23s
```

## Error Handling

The workflow includes **graceful degradation**:

- If one agent fails, others continue
- Partial results are still returned
- Errors are noted in the affected section

### Example: Partial Failure

If ChemistryAgent fails but others succeed:

```
## Chemical Properties
Error: PubChem API timeout

## Concentration Ranges
[... successful results ...]
```

## Performance

| Configuration | Execution Time |
|---------------|----------------|
| Without literature | ~2-3 seconds |
| With literature | ~4-6 seconds |
| Organism-specific | +1-2 seconds |

**Bottleneck:** Literature search (PubMed API calls)

**Optimization:** Set `include_literature=False` for faster results.

## Use Cases

### 1. Ingredient Validation
Before adding a new ingredient to a medium, generate a comprehensive report to understand:
- Its role in the medium
- Appropriate concentration ranges
- Chemical compatibility
- Literature precedent

### 2. Medium Troubleshooting
When a medium isn't performing as expected:
- Check if ingredients are at optimal concentrations
- Review chemical properties for compatibility issues
- Find literature on similar formulations

### 3. Recipe Development
When designing a new medium:
- Systematically analyze each ingredient
- Ensure concentrations are evidence-based
- Verify no chemical incompatibilities

### 4. Documentation
Generate standardized reports for:
- Lab notebooks
- Medium databases
- Publication supplementary materials

## Comparison with Simple Skills

| Task | Simple Skills | Ingredient Report Workflow |
|------|---------------|----------------------------|
| Get concentration | `predict-concentration` | ✓ Included |
| Get role | `classify-role` | ✓ Included |
| Get chemistry | `calculate-chemistry` | ✓ Included |
| Get literature | `search-literature` | ✓ Included |
| **Convenience** | 4 separate calls | **1 call** |
| **Evidence aggregation** | Manual | **Automatic** |
| **Citation formatting** | Per-skill | **Unified** |

**Advantage:** Single workflow call replaces 4 individual skill calls with unified evidence aggregation.

## Related Workflows

- **optimize-medium** - Multi-ingredient optimization

## Implementation Details

**Workflow Type:** Multi-agent orchestration

**Agent Execution:** Sequential with error handling

**Evidence Aggregation:** Collects citations from all agents, deduplicates, and formats as unified reference list

**Caching:** None (each run executes all agents fresh)

## Extending the Workflow

To add a new section:

```python
class CustomIngredientReport(IngredientReportWorkflow):
    def execute(self, **kwargs):
        # Call parent workflow
        result = super().execute(**kwargs)

        # Add custom section
        custom_data = self._my_custom_analysis(kwargs["ingredient"])
        result["data"]["sections"]["custom"] = custom_data

        return result
```

## Citation

If you use this workflow in your research:

```
MicroGrowAgents Skills Framework (2026)
Ingredient Report Workflow v1.0.0
https://github.com/monarch-initiative/microgrowagents
```

---

**Workflow Type:** Multi-agent orchestration
**Agents:** MediaRoleAgent, GenMediaConcAgent, ChemistryAgent, LiteratureAgent
**Version:** 1.0.0
**Last Updated:** 2026-01-07

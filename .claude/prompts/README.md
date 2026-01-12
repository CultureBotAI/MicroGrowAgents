# Claude Code Prompts

This directory contains comprehensive prompts for using the MicroGrowAgents framework with Claude Code skills and agents.

## Available Prompts

### GENERATE_ORGANISM_MEDIA_TABLES.md
**Purpose:** Generate organism-specific media formulation TSV tables

**Target:** Methylorubrum extorquens AM-1 with MP medium as base

**Output:** 5 publication-ready TSV tables
1. Organism-specific ingredient properties
2. Medium variations for experimental goals
3. Cofactor requirements
4. Alternative ingredients
5. Growth condition predictions

**Resources Used:**
- 17 agents (MediaFormulationAgent, GenomeFunctionAgent, KGReasoningAgent, etc.)
- 11 skills + 1 workflow (recommend-media)
- KG-Microbe (1.5M nodes, 5.1M edges)
- Genome annotations (57 genomes, 250k annotations)
- Literature evidence (166 files, 158 DOIs)

**Estimated Runtime:** 5-10 minutes
**Expected Output Size:** ~100-200 KB (5 TSV files + documentation)

## Usage

Each prompt file contains:
- **Context:** Background and objectives
- **Resources:** Available agents, skills, and data sources
- **Implementation Steps:** Detailed step-by-step instructions
- **Expected Outputs:** Table specifications and quality metrics
- **Success Criteria:** Validation checkpoints
- **Usage Examples:** Code snippets and commands

## How to Use

1. Read the prompt file to understand the workflow
2. Follow the implementation steps sequentially
3. Use the provided code examples as templates
4. Validate outputs against success criteria
5. Export results using the specified formats

## Adding New Prompts

When creating new prompts, include:
- Clear objective and context
- Complete resource inventory (agents, skills, data)
- Step-by-step implementation guide
- Expected output specifications
- Quality metrics and validation criteria
- Working code examples
- Version and date metadata

## See Also

- `.claude/skills/` - Claude Code skill definitions
- `src/microgrowagents/agents/` - Agent implementations
- `src/microgrowagents/skills/` - Skill implementations
- `data/exports/` - Example TSV export outputs
- `CLAUDE.md` - Project-wide Claude Code instructions

---

**Version:** 1.0.0
**Last Updated:** 2026-01-11

"""
MicroGrowAgents Skills Framework.

Provides Claude Code skills on top of the agent library:
- Simple skills: Single-agent wrappers (10 skills)
  - predict-concentration, find-alternates, analyze-sensitivity
  - classify-role, search-literature, query-database, calculate-chemistry
  - analyze-cofactors, analyze-genome, query-knowledge-graph
- Workflow skills: Multi-agent orchestrations (3 workflows)
  - recommend-media, optimize-medium, ingredient-report
- Utility skills: Database and export utilities (3 utilities)
  - initialize-database, export-results, validate-ingredient

Total: 16 skills

Usage:
    from microgrowagents.skills.simple import (
        PredictConcentrationSkill,
        AnalyzeCofactorsSkill,
        AnalyzeGenomeSkill,
        QueryKnowledgeGraphSkill,
    )
    from microgrowagents.skills.workflows import IngredientReportWorkflow
    from microgrowagents.skills.utilities import InitializeDatabaseSkill

    # Predict concentrations
    skill = PredictConcentrationSkill()
    result = skill.run(query="glucose", output_format="markdown")

    # Analyze cofactors from genome
    cofactor_skill = AnalyzeCofactorsSkill()
    result = cofactor_skill.run(organism="SAMN31331780", base_medium="MP")

    # Query knowledge graph
    kg_skill = QueryKnowledgeGraphSkill()
    result = kg_skill.run(query="Find media for Methylococcus capsulatus")
"""

from microgrowagents.skills.base_skill import (
    BaseSkill,
    SkillMetadata,
    SkillParameter,
)

__all__ = [
    "BaseSkill",
    "SkillMetadata",
    "SkillParameter",
]

__version__ = "1.0.0"

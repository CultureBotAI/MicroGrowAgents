"""
Simple skills - single-agent wrappers.

Each skill wraps one agent and provides a user-friendly interface.
"""

from microgrowagents.skills.simple.predict_concentration import PredictConcentrationSkill
from microgrowagents.skills.simple.find_alternates import FindAlternatesSkill
from microgrowagents.skills.simple.analyze_sensitivity import AnalyzeSensitivitySkill
from microgrowagents.skills.simple.classify_role import ClassifyRoleSkill
from microgrowagents.skills.simple.search_literature import SearchLiteratureSkill
from microgrowagents.skills.simple.query_database import QueryDatabaseSkill
from microgrowagents.skills.simple.calculate_chemistry import CalculateChemistrySkill
from microgrowagents.skills.simple.analyze_cofactors import AnalyzeCofactorsSkill
from microgrowagents.skills.simple.analyze_genome import AnalyzeGenomeSkill
from microgrowagents.skills.simple.query_knowledge_graph import QueryKnowledgeGraphSkill

__all__ = [
    "PredictConcentrationSkill",
    "FindAlternatesSkill",
    "AnalyzeSensitivitySkill",
    "ClassifyRoleSkill",
    "SearchLiteratureSkill",
    "QueryDatabaseSkill",
    "CalculateChemistrySkill",
    "AnalyzeCofactorsSkill",
    "AnalyzeGenomeSkill",
    "QueryKnowledgeGraphSkill",
]

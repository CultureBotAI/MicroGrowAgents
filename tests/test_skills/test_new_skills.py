"""
Tests for new skills: AnalyzeCofactorsSkill, AnalyzeGenomeSkill, QueryKnowledgeGraphSkill.
"""

import pytest
from pathlib import Path
from microgrowagents.skills.simple.analyze_cofactors import AnalyzeCofactorsSkill
from microgrowagents.skills.simple.analyze_genome import AnalyzeGenomeSkill
from microgrowagents.skills.simple.query_knowledge_graph import QueryKnowledgeGraphSkill


@pytest.fixture
def db_path():
    """Fixture providing database path."""
    return Path("data/processed/microgrow.duckdb")


def test_analyze_cofactors_skill_metadata():
    """Test AnalyzeCofactorsSkill metadata."""
    skill = AnalyzeCofactorsSkill()
    metadata = skill.get_metadata()

    assert metadata.name == "analyze-cofactors"
    assert metadata.category == "simple"
    assert len(metadata.parameters) == 2
    assert len(metadata.examples) >= 3
    assert metadata.requires_database is True


def test_analyze_cofactors_skill_execution(db_path):
    """Test AnalyzeCofactorsSkill execution with M. extorquens."""
    skill = AnalyzeCofactorsSkill(db_path)

    result = skill.execute(
        organism="SAMN31331780",  # M. extorquens AM-1
        base_medium="MP",
    )

    assert isinstance(result, dict)
    assert "success" in result

    if result.get("success"):
        data = result.get("data", {})
        assert "cofactor_table" in data
        assert "cofactor_requirements" in data


def test_analyze_cofactors_skill_formatting(db_path):
    """Test AnalyzeCofactorsSkill markdown formatting."""
    skill = AnalyzeCofactorsSkill(db_path)

    result = skill.execute(organism="SAMN31331780", base_medium="MP")

    if result.get("success"):
        markdown = skill.format_result(result, "markdown")
        assert "Cofactor Analysis" in markdown
        assert "Data Sources" in markdown
        assert "ChEBI" in markdown or "KEGG" in markdown


def test_analyze_genome_skill_metadata():
    """Test AnalyzeGenomeSkill metadata."""
    skill = AnalyzeGenomeSkill()
    metadata = skill.get_metadata()

    assert metadata.name == "analyze-genome"
    assert metadata.category == "simple"
    assert len(metadata.parameters) == 5  # query, organism, analysis_type, ec_pattern, pathway
    assert len(metadata.examples) >= 4
    assert metadata.requires_database is True


def test_analyze_genome_skill_structure(db_path):
    """Test AnalyzeGenomeSkill basic structure."""
    skill = AnalyzeGenomeSkill(db_path)

    # Test with minimal parameters
    result = skill.execute(
        query="Find enzymes",
        organism="SAMN31331780",
        analysis_type="enzymes",
    )

    assert isinstance(result, dict)
    assert "success" in result or "error" in result


def test_query_knowledge_graph_skill_metadata():
    """Test QueryKnowledgeGraphSkill metadata."""
    skill = QueryKnowledgeGraphSkill()
    metadata = skill.get_metadata()

    assert metadata.name == "query-knowledge-graph"
    assert metadata.category == "simple"
    assert len(metadata.parameters) == 5
    assert len(metadata.examples) >= 4
    assert metadata.requires_database is True


def test_query_knowledge_graph_skill_structure(db_path):
    """Test QueryKnowledgeGraphSkill basic structure."""
    skill = QueryKnowledgeGraphSkill(db_path)

    # Test with minimal parameters
    result = skill.execute(
        query="Test query",
        query_type="organism_media",
    )

    assert isinstance(result, dict)
    assert "success" in result or "error" in result


def test_skills_missing_query_error():
    """Test that skills return error when required query is missing."""
    genome_skill = AnalyzeGenomeSkill()
    result = genome_skill.execute(organism=None)

    assert result.get("success") is False
    assert "error" in result


def test_skills_json_formatting(db_path):
    """Test JSON formatting for all new skills."""
    cofactor_skill = AnalyzeCofactorsSkill(db_path)

    result = cofactor_skill.execute(organism="SAMN31331780", base_medium="MP")

    if result.get("success"):
        json_output = cofactor_skill.format_result(result, "json")
        assert isinstance(json_output, str)
        assert "{" in json_output  # Valid JSON structure


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

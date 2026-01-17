"""
Tests for BaseSkill class and metadata structures.
"""

import pytest
from microgrowagents.skills.base_skill import (
    BaseSkill,
    SkillMetadata,
    SkillParameter,
)


class MockSkill(BaseSkill):
    """Mock skill for testing."""

    def get_metadata(self) -> SkillMetadata:
        """Return test metadata."""
        return SkillMetadata(
            name="test-skill",
            description="Test skill for testing",
            category="simple",
            parameters=[
                SkillParameter(
                    name="query",
                    type="str",
                    description="Test query",
                    required=True,
                )
            ],
            examples=["test-skill glucose"],
            requires_database=False,
        )

    def execute(self, **kwargs):
        """Execute test logic."""
        query = kwargs.get("query")
        if not query:
            return {
                "success": False,
                "error": "Missing required parameter: query",
            }

        return {
            "success": True,
            "data": {"query": query, "result": "test_result"},
            "metadata": {"test_key": "test_value"},
            "evidence": [{"doi": "10.1234/test"}],
        }


class MockFailingSkill(BaseSkill):
    """Mock skill that always fails."""

    def get_metadata(self) -> SkillMetadata:
        """Return test metadata."""
        return SkillMetadata(
            name="failing-skill",
            description="Failing skill",
            category="simple",
            parameters=[],
            examples=[],
            requires_database=False,
        )

    def execute(self, **kwargs):
        """Always fail."""
        return {
            "success": False,
            "error": "Intentional failure for testing",
        }


def test_skill_parameter_creation():
    """Test SkillParameter dataclass creation."""
    param = SkillParameter(
        name="test_param",
        type="str",
        description="Test parameter",
        required=True,
    )

    assert param.name == "test_param"
    assert param.type == "str"
    assert param.required is True
    assert param.default is None


def test_skill_metadata_creation():
    """Test SkillMetadata dataclass creation."""
    metadata = SkillMetadata(
        name="test-skill",
        description="Test skill",
        category="simple",
        parameters=[],
        examples=["example 1"],
        requires_database=True,
    )

    assert metadata.name == "test-skill"
    assert metadata.category == "simple"
    assert metadata.requires_database is True
    assert metadata.version == "1.0.0"


def test_mock_skill_get_metadata():
    """Test mock skill metadata."""
    skill = MockSkill()
    metadata = skill.get_metadata()

    assert metadata.name == "test-skill"
    assert metadata.category == "simple"
    assert len(metadata.parameters) == 1
    assert metadata.parameters[0].name == "query"


def test_mock_skill_execute_success():
    """Test successful skill execution."""
    skill = MockSkill()
    result = skill.execute(query="glucose")

    assert result["success"] is True
    assert result["data"]["query"] == "glucose"
    assert "doi" in result["evidence"][0]


def test_mock_skill_execute_missing_param():
    """Test skill execution with missing parameter."""
    skill = MockSkill()
    result = skill.execute()

    assert result["success"] is False
    assert "Missing required parameter" in result["error"]


def test_skill_run_success():
    """Test skill.run() with successful execution."""
    skill = MockSkill()
    output = skill.run(query="glucose", output_format="markdown")

    assert isinstance(output, str)
    assert "glucose" in output or "test_result" in output


def test_skill_run_error():
    """Test skill.run() with error."""
    skill = MockFailingSkill()
    output = skill.run(output_format="markdown")

    assert isinstance(output, str)
    assert "Error" in output or "error" in output.lower()


def test_skill_run_json_format():
    """Test skill.run() with JSON output."""
    skill = MockSkill()
    output = skill.run(query="glucose", output_format="json")

    assert isinstance(output, str)
    assert "{" in output  # JSON object
    assert "success" in output


def test_format_citations():
    """Test citation formatting."""
    skill = MockSkill()
    evidence = [
        {"doi": "10.1234/test", "confidence": 0.95},
        {"pmid": "12345678"},
        {"kg_node": "CHEBI:12345", "kg_label": "Glucose"},
    ]

    citations = skill._format_citations(evidence)

    assert "doi.org/10.1234/test" in citations
    assert "pubmed.ncbi.nlm.nih.gov" in citations
    assert "CHEBI:12345" in citations
    assert "95.00%" in citations or "95%" in citations


def test_format_citations_empty():
    """Test citation formatting with empty list."""
    skill = MockSkill()
    citations = skill._format_citations([])

    assert citations == ""

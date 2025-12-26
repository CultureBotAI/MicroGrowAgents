"""Test BaseAgent class."""

import pytest
from pathlib import Path

from microgrowagents.agents.base_agent import BaseAgent


# Concrete implementation for testing
class TestAgent(BaseAgent):
    """Test agent implementation."""

    def run(self, query: str, **kwargs):
        """Test run method."""
        return {"success": True, "query": query, "kwargs": kwargs}


def test_base_agent_init():
    """Test BaseAgent initialization."""
    agent = TestAgent()
    assert agent.db_path == Path("data/processed/microgrow.duckdb")
    assert agent.results == {}


def test_base_agent_custom_db_path(tmp_path):
    """Test BaseAgent with custom database path."""
    db_path = tmp_path / "test.duckdb"
    agent = TestAgent(db_path)
    assert agent.db_path == db_path


def test_base_agent_run():
    """Test that run method must be implemented."""
    agent = TestAgent()
    result = agent.run("test query", param1="value1")
    assert result["success"] is True
    assert result["query"] == "test query"
    assert result["kwargs"]["param1"] == "value1"


def test_base_agent_validate_database(tmp_path):
    """Test database validation."""
    # Non-existent database
    agent = TestAgent(tmp_path / "nonexistent.duckdb")
    assert agent.validate_database() is False

    # Existing database
    db_path = tmp_path / "test.duckdb"
    db_path.touch()
    agent = TestAgent(db_path)
    assert agent.validate_database() is True


def test_base_agent_log(capsys):
    """Test logging functionality."""
    agent = TestAgent()
    agent.log("Test message")
    captured = capsys.readouterr()
    assert "TestAgent" in captured.out
    assert "INFO" in captured.out
    assert "Test message" in captured.out

    agent.log("Error message", level="ERROR")
    captured = capsys.readouterr()
    assert "ERROR" in captured.out

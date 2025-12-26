"""Test SQLAgent class."""

import pytest
from pathlib import Path
import duckdb
import pandas as pd

from microgrowagents.agents.sql_agent import SQLAgent
from microgrowagents.database.schema import create_schema


@pytest.fixture
def test_db(tmp_path):
    """Create test database with sample data."""
    db_path = tmp_path / "test.duckdb"
    conn = duckdb.connect(str(db_path))

    # Create schema
    create_schema(conn)

    # Insert test data
    conn.execute(
        """
        INSERT INTO media VALUES
        ('test:1', 'LB Medium', 'complex', 7.0, 7.4, 'Standard growth medium', 'test', NULL),
        ('test:2', 'M9 Minimal', 'defined', 7.2, 7.4, 'Minimal medium', 'test', NULL)
    """
    )

    conn.execute(
        """
        INSERT INTO ingredients VALUES
        ('CHEBI:17234', 'glucose', 'CHEBI:17234', NULL, NULL, NULL, 180.16, 'nutrient'),
        ('CHEBI:26710', 'NaCl', 'CHEBI:26710', NULL, NULL, NULL, 58.44, 'salt')
    """
    )

    conn.execute(
        """
        INSERT INTO media_ingredients VALUES
        (1, 'test:1', 'CHEBI:17234', 10.0, 'g/L', 10.0, 55.5, 'carbon_source'),
        (2, 'test:2', 'CHEBI:26710', 5.0, 'g/L', 5.0, 85.6, 'osmotic')
    """
    )

    conn.close()
    return db_path


def test_sql_agent_init(test_db):
    """Test SQLAgent initialization."""
    agent = SQLAgent(test_db)
    assert agent.db_path == test_db


def test_sql_agent_run_sql_query(test_db):
    """Test running a direct SQL query."""
    agent = SQLAgent(test_db)
    result = agent.run("SELECT * FROM media")

    assert result["success"] is True
    assert isinstance(result["data"], pd.DataFrame)
    assert len(result["data"]) == 2
    assert "sql" in result
    assert result["row_count"] == 2


def test_sql_agent_run_with_max_rows(test_db):
    """Test max_rows parameter."""
    agent = SQLAgent(test_db)
    result = agent.run("SELECT * FROM media", max_rows=1)

    assert result["success"] is True
    assert len(result["data"]) == 1


def test_sql_agent_natural_language(test_db):
    """Test natural language query matching."""
    agent = SQLAgent(test_db)

    # Test "ingredients for medium" pattern
    result = agent.run("ingredients for medium", params=["test:1"])

    assert result["success"] is True
    # Should match the template and execute


def test_sql_agent_get_media_info(test_db):
    """Test get_media_info helper method."""
    agent = SQLAgent(test_db)
    info = agent.get_media_info("test:1")

    assert info is not None
    assert info["name"] == "LB Medium"
    assert info["medium_type"] == "complex"


def test_sql_agent_get_ingredients_for_media(test_db):
    """Test get_ingredients_for_media helper method."""
    agent = SQLAgent(test_db)
    ingredients = agent.get_ingredients_for_media("test:1")

    assert isinstance(ingredients, pd.DataFrame)
    assert len(ingredients) == 1
    assert "glucose" in ingredients["name"].values


def test_sql_agent_search_media(test_db):
    """Test search_media helper method."""
    agent = SQLAgent(test_db)
    results = agent.search_media("LB")

    assert isinstance(results, pd.DataFrame)
    assert len(results) >= 1
    assert "LB Medium" in results["name"].values


def test_sql_agent_invalid_query(test_db):
    """Test handling of invalid SQL query."""
    agent = SQLAgent(test_db)
    result = agent.run("SELECT * FROM nonexistent_table")

    assert result["success"] is False
    assert "error" in result


def test_sql_agent_missing_database(tmp_path):
    """Test behavior with missing database."""
    agent = SQLAgent(tmp_path / "nonexistent.duckdb")
    result = agent.run("SELECT * FROM media")

    assert result["success"] is False
    assert "error" in result

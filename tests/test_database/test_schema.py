"""Test database schema creation."""

import duckdb
import pytest
from pathlib import Path

from microgrowagents.database.schema import create_schema, drop_schema


@pytest.fixture
def test_db(tmp_path):
    """Create test database."""
    db_path = tmp_path / "test.duckdb"
    conn = duckdb.connect(str(db_path))
    yield conn
    conn.close()


def test_create_schema(test_db):
    """Test schema creation."""
    create_schema(test_db)

    # Check that all tables exist
    tables = test_db.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()

    table_names = [t[0] for t in tables]

    expected_tables = [
        "media",
        "ingredients",
        "media_ingredients",
        "organisms",
        "organism_media",
        "chemical_properties",
        "ingredient_effects",
    ]

    for table in expected_tables:
        assert table in table_names, f"Table {table} not created"


def test_drop_schema(test_db):
    """Test schema dropping."""
    create_schema(test_db)
    drop_schema(test_db)

    # Check that tables are dropped
    tables = test_db.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()

    assert len(tables) == 0, "Tables should be dropped"


def test_schema_indexes(test_db):
    """Test that indexes are created."""
    create_schema(test_db)

    # Check for indexes
    indexes = test_db.execute(
        "SELECT index_name FROM information_schema.indexes WHERE table_schema = 'main'"
    ).fetchall()

    index_names = [i[0] for i in indexes]

    expected_indexes = [
        "idx_media_name",
        "idx_ingredient_name",
        "idx_media_ing_media",
        "idx_media_ing_ingredient",
    ]

    for index in expected_indexes:
        assert (
            index in index_names
        ), f"Index {index} not created"

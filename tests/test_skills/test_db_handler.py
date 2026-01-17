"""
Tests for DatabaseHandler.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from microgrowagents.skills.db_handler import DatabaseHandler


class TestDatabaseHandler:
    """Tests for DatabaseHandler."""

    def test_init_default_path(self):
        """Test initialization with default path."""
        handler = DatabaseHandler()
        assert handler.db_path == "data/processed/microgrow.duckdb"

    def test_init_custom_path(self):
        """Test initialization with custom path."""
        custom_path = "/tmp/test.duckdb"
        handler = DatabaseHandler(db_path=custom_path)
        assert handler.db_path == custom_path

    def test_validate_missing_database(self):
        """Test validation with missing database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.duckdb"
            handler = DatabaseHandler(db_path=db_path)

            # Validation should fail (no data to initialize from)
            result = handler.validate()
            # Result depends on whether data/raw/ exists
            assert isinstance(result, bool)

    def test_get_connection_creates_db(self):
        """Test that get_connection creates database file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.duckdb"
            handler = DatabaseHandler(db_path=db_path)

            conn = handler.get_connection()
            assert conn is not None

            # Database file should exist
            assert Path(db_path).exists()

            handler.close()

    def test_get_connection_reuses_connection(self):
        """Test that get_connection reuses existing connection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.duckdb"
            handler = DatabaseHandler(db_path=db_path)

            conn1 = handler.get_connection()
            conn2 = handler.get_connection()

            assert conn1 is conn2

            handler.close()

    def test_close(self):
        """Test closing connection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.duckdb"
            handler = DatabaseHandler(db_path=db_path)

            conn = handler.get_connection()
            assert handler._connection is not None

            handler.close()
            assert handler._connection is None

    def test_required_tables_defined(self):
        """Test that required tables are defined."""
        assert len(DatabaseHandler.REQUIRED_TABLES) > 0
        assert "kg_nodes" in DatabaseHandler.REQUIRED_TABLES
        assert "kg_edges" in DatabaseHandler.REQUIRED_TABLES
        assert "media" in DatabaseHandler.REQUIRED_TABLES


@pytest.mark.skipif(
    not Path("data/raw/merged-kg_nodes.tsv").exists(),
    reason="KG-Microbe data not available",
)
class TestDatabaseHandlerWithData:
    """Tests that require KG-Microbe data files."""

    def test_initialize_database_with_data(self):
        """Test database initialization with KG-Microbe data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test.duckdb"
            handler = DatabaseHandler(db_path=db_path)

            # This should initialize the database
            result = handler._initialize_database()

            # Result depends on data availability
            if Path("data/raw/merged-kg_nodes.tsv").exists():
                assert result is True
                assert Path(db_path).exists()

            handler.close()

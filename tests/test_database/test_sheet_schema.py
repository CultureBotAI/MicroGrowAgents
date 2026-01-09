"""Test database schema creation for information sheets."""

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


def test_create_sheet_tables(test_db):
    """Test that all 5 sheet tables are created."""
    create_schema(test_db)

    # Check that all tables exist
    tables = test_db.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()

    table_names = [t[0] for t in tables]

    # Expected sheet tables
    expected_sheet_tables = [
        "sheet_collections",
        "sheet_tables",
        "sheet_data",
        "sheet_publications",
        "sheet_publication_references",
    ]

    for table in expected_sheet_tables:
        assert table in table_names, f"Table {table} not created"


def test_sheet_collections_structure(test_db):
    """Test sheet_collections table has correct columns."""
    create_schema(test_db)

    columns = test_db.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'sheet_collections'
        ORDER BY column_name
        """
    ).fetchall()

    column_names = [c[0] for c in columns]

    expected_columns = [
        "collection_id",
        "collection_name",
        "directory_path",
        "loaded_at",
        "table_count",
        "total_rows",
        "description",
    ]

    for col in expected_columns:
        assert col in column_names, f"Column {col} not in sheet_collections"


def test_sheet_data_structure(test_db):
    """Test sheet_data table has correct columns."""
    create_schema(test_db)

    columns = test_db.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'sheet_data'
        ORDER BY column_name
        """
    ).fetchall()

    column_names = [c[0] for c in columns]

    expected_columns = [
        "id",
        "table_id",
        "row_id",
        "entity_id",
        "entity_name",
        "entity_type",
        "data_json",
        "searchable_text",
    ]

    for col in expected_columns:
        assert col in column_names, f"Column {col} not in sheet_data"


def test_sheet_data_indexes(test_db):
    """Test that all 9 sheet indexes are created."""
    create_schema(test_db)

    # Check for indexes
    indexes = test_db.execute(
        """
        SELECT index_name
        FROM duckdb_indexes()
        WHERE table_name IN (
            'sheet_collections', 'sheet_tables', 'sheet_data',
            'sheet_publications', 'sheet_publication_references'
        )
        """
    ).fetchall()

    index_names = [i[0] for i in indexes]

    expected_indexes = [
        "idx_sheet_data_entity_id",
        "idx_sheet_data_entity_name",
        "idx_sheet_data_entity_type",
        "idx_sheet_data_composite",
        "idx_sheet_pub_refs_entity",
        "idx_sheet_pubs_pub_id",
        "idx_sheet_data_searchable",
        "idx_sheet_tables_collection",
        "idx_sheet_data_table",
    ]

    for index in expected_indexes:
        assert index in index_names, f"Index {index} not created"


def test_sheet_tables_can_be_dropped(test_db):
    """Test that sheet tables can be dropped."""
    create_schema(test_db)

    # Verify tables exist
    tables_before = test_db.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name LIKE 'sheet_%'
        """
    ).fetchall()

    assert len(tables_before) == 5, "Should have 5 sheet tables before drop"

    # Drop all tables
    drop_schema(test_db)

    # Verify all tables are dropped
    tables_after = test_db.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
        """
    ).fetchall()

    assert len(tables_after) == 0, "All tables should be dropped"


def test_sheet_data_insert(test_db):
    """Test that we can insert data into sheet_data table."""
    create_schema(test_db)

    # Insert test data
    test_db.execute(
        """
        INSERT INTO sheet_collections (collection_id, collection_name, directory_path)
        VALUES ('test_cmm', 'Test CMM Collection', '/test/path')
        """
    )

    test_db.execute(
        """
        INSERT INTO sheet_tables (table_id, collection_id, table_name, source_file, row_count)
        VALUES ('test_cmm_chemicals', 'test_cmm', 'chemicals', 'test.tsv', 5)
        """
    )

    test_db.execute(
        """
        INSERT INTO sheet_data (
            id, table_id, row_id, entity_id, entity_name, entity_type, data_json
        )
        VALUES (
            1, 'test_cmm_chemicals', 1, 'CHEBI:52927', 'Europium', 'chemical',
            '{"chemical_id": "CHEBI:52927", "chemical_name": "Europium"}'
        )
        """
    )

    # Verify insert
    result = test_db.execute(
        "SELECT entity_id, entity_name FROM sheet_data WHERE entity_type = 'chemical'"
    ).fetchone()

    assert result[0] == "CHEBI:52927"
    assert result[1] == "Europium"


def test_sheet_publications_insert(test_db):
    """Test that we can insert publications."""
    create_schema(test_db)

    test_db.execute(
        """
        INSERT INTO sheet_collections (collection_id, collection_name, directory_path)
        VALUES ('test_cmm', 'Test CMM', '/test/path')
        """
    )

    test_db.execute(
        """
        INSERT INTO sheet_publications (
            id, collection_id, file_name, publication_id, publication_type,
            title, full_text, word_count
        )
        VALUES (
            1, 'test_cmm', 'PMID_12345.md', 'pmid:12345', 'pmid',
            'Test Publication', 'Full text content here', 100
        )
        """
    )

    # Verify insert
    result = test_db.execute(
        "SELECT publication_id, title FROM sheet_publications WHERE publication_type = 'pmid'"
    ).fetchone()

    assert result[0] == "pmid:12345"
    assert result[1] == "Test Publication"


def test_sheet_cross_references(test_db):
    """Test that we can create cross-references between entities and publications."""
    create_schema(test_db)

    # Insert collection
    test_db.execute(
        """
        INSERT INTO sheet_collections (collection_id, collection_name, directory_path)
        VALUES ('test_cmm', 'Test', '/test')
        """
    )

    # Insert table
    test_db.execute(
        """
        INSERT INTO sheet_tables (table_id, collection_id, table_name, source_file, row_count)
        VALUES ('test_cmm_chemicals', 'test_cmm', 'chemicals', 'test.tsv', 1)
        """
    )

    # Insert publication
    test_db.execute(
        """
        INSERT INTO sheet_publications (
            id, collection_id, file_name, publication_id, publication_type
        )
        VALUES (1, 'test_cmm', 'PMID_12345.md', 'pmid:12345', 'pmid')
        """
    )

    # Insert cross-reference
    test_db.execute(
        """
        INSERT INTO sheet_publication_references (
            id, publication_id, table_id, entity_id, reference_column
        )
        VALUES (1, 1, 'test_cmm_chemicals', 'CHEBI:52927', 'DOI')
        """
    )

    # Verify cross-reference
    result = test_db.execute(
        """
        SELECT entity_id, reference_column
        FROM sheet_publication_references
        WHERE publication_id = 1
        """
    ).fetchone()

    assert result[0] == "CHEBI:52927"
    assert result[1] == "DOI"

"""Test SheetDataLoader for loading TSV and publication markdown files."""

import json
from pathlib import Path

import duckdb
import pytest

from microgrowagents.database.schema import create_schema
from microgrowagents.database.sheet_loader import SheetDataLoader


@pytest.fixture
def test_db(tmp_path):
    """Create test database with schema."""
    db_path = tmp_path / "test_sheets.duckdb"
    conn = duckdb.connect(str(db_path))
    create_schema(conn)
    conn.close()
    return db_path


@pytest.fixture
def test_sheets_dir():
    """Path to test fixtures directory."""
    return Path("tests/fixtures/sheets_test")


class TestSheetDataLoader:
    """Test SheetDataLoader initialization and basic functionality."""

    def test_loader_initialization(self, test_db):
        """Test loader can be initialized with database path."""
        loader = SheetDataLoader(test_db)
        assert loader.db_path == test_db

    def test_loader_database_connection(self, test_db):
        """Test loader can connect to database."""
        loader = SheetDataLoader(test_db)
        # Should not raise exception
        loader._connect()
        loader._close()


class TestTSVLoading:
    """Test TSV file loading functionality."""

    def test_infer_entity_type_from_filename(self, test_db):
        """Test entity type inference from filename."""
        loader = SheetDataLoader(test_db)

        # Test various filename patterns
        assert loader._infer_entity_type("chemicals_extended.tsv") == "chemical"
        assert loader._infer_entity_type("BER_CMM_chemicals_extended.tsv") == "chemical"
        assert loader._infer_entity_type("genes_and_proteins_extended.tsv") == "gene"
        assert loader._infer_entity_type("BER_TEST_genes_and_proteins_extended.tsv") == "gene"
        assert loader._infer_entity_type("strains_extended.tsv") == "strain"
        assert loader._infer_entity_type("publications_extended.tsv") == "publication"
        assert loader._infer_entity_type("pathways_extended.tsv") == "pathway"
        assert loader._infer_entity_type("assays_extended.tsv") == "assay"
        assert loader._infer_entity_type("unknown_data.tsv") == "unknown"

    def test_extract_entity_id_and_name(self, test_db):
        """Test extraction of entity ID and name from row data."""
        loader = SheetDataLoader(test_db)

        # Chemical entity
        chemical_row = {
            "chemical_id": "CHEBI:52927",
            "chemical_name": "Europium(III) cation",
            "formula": "Eu3+"
        }
        entity_id, entity_name = loader._extract_entity_id_and_name(chemical_row, "chemical")
        assert entity_id == "CHEBI:52927"
        assert entity_name == "Europium(III) cation"

        # Gene entity
        gene_row = {
            "gene or protein id": "K23995",
            "annotation": "XoxF methanol dehydrogenase",
            "EC": "1.1.1.244"
        }
        entity_id, entity_name = loader._extract_entity_id_and_name(gene_row, "gene")
        assert entity_id == "K23995"
        assert entity_name == "XoxF methanol dehydrogenase"

    def test_load_single_tsv_chemicals(self, test_db, test_sheets_dir):
        """Test loading single chemicals TSV file."""
        loader = SheetDataLoader(test_db)

        tsv_path = test_sheets_dir / "BER_TEST_chemicals_extended.tsv"
        result = loader._load_tsv_table("test_cmm", tsv_path)

        assert result["success"] is True
        assert result["table_name"] == "chemicals"
        assert result["row_count"] == 5
        assert result["entity_type"] == "chemical"

        # Verify data in database
        conn = duckdb.connect(str(test_db))
        rows = conn.execute("SELECT COUNT(*) FROM sheet_data WHERE entity_type = 'chemical'").fetchone()
        assert rows[0] == 5

        # Verify specific entity
        entity = conn.execute(
            "SELECT entity_id, entity_name FROM sheet_data WHERE entity_id = 'CHEBI:52927'"
        ).fetchone()
        assert entity[0] == "CHEBI:52927"
        assert entity[1] == "Europium(III) cation"

        conn.close()

    def test_load_single_tsv_genes(self, test_db, test_sheets_dir):
        """Test loading single genes TSV file."""
        loader = SheetDataLoader(test_db)

        tsv_path = test_sheets_dir / "BER_TEST_genes_and_proteins_extended.tsv"
        result = loader._load_tsv_table("test_cmm", tsv_path)

        assert result["success"] is True
        assert result["table_name"] == "genes_and_proteins"
        assert result["row_count"] == 5
        assert result["entity_type"] == "gene"

        # Verify data in database
        conn = duckdb.connect(str(test_db))
        rows = conn.execute("SELECT COUNT(*) FROM sheet_data WHERE entity_type = 'gene'").fetchone()
        assert rows[0] == 5

        # Verify specific gene
        entity = conn.execute(
            "SELECT entity_id, entity_name FROM sheet_data WHERE entity_id = 'K23995'"
        ).fetchone()
        assert entity[0] == "K23995"
        assert "methanol dehydrogenase" in entity[1].lower()

        conn.close()

    def test_data_json_contains_all_columns(self, test_db, test_sheets_dir):
        """Test that data_json contains all columns from TSV."""
        loader = SheetDataLoader(test_db)

        tsv_path = test_sheets_dir / "BER_TEST_chemicals_extended.tsv"
        loader._load_tsv_table("test_cmm", tsv_path)

        # Verify JSON contains all columns
        conn = duckdb.connect(str(test_db))
        data_json = conn.execute(
            "SELECT data_json FROM sheet_data WHERE entity_id = 'CHEBI:52927'"
        ).fetchone()[0]

        data = json.loads(data_json)
        assert "chemical_id" in data
        assert "chemical_name" in data
        assert "molecular_formula" in data
        assert "molecular_weight" in data
        assert "chebi_id" in data
        assert data["chemical_id"] == "CHEBI:52927"
        assert data["molecular_formula"] == "Eu3+"

        conn.close()

    def test_searchable_text_built_from_text_columns(self, test_db, test_sheets_dir):
        """Test that searchable_text is built from text columns."""
        loader = SheetDataLoader(test_db)

        tsv_path = test_sheets_dir / "BER_TEST_chemicals_extended.tsv"
        loader._load_tsv_table("test_cmm", tsv_path)

        # Verify searchable_text contains key terms
        conn = duckdb.connect(str(test_db))
        searchable = conn.execute(
            "SELECT searchable_text FROM sheet_data WHERE entity_id = 'CHEBI:52927'"
        ).fetchone()[0]

        assert searchable is not None
        assert "europium" in searchable.lower()
        assert "lanthanide" in searchable.lower()
        assert "chebi:52927" in searchable.lower()

        conn.close()


class TestPublicationLoading:
    """Test publication markdown file loading."""

    def test_extract_publication_id_from_pmid(self, test_db):
        """Test extracting PMID from filename."""
        loader = SheetDataLoader(test_db)

        pub_id, pub_type = loader._extract_publication_id("PMID_24816778.md")
        assert pub_id == "pmid:24816778"
        assert pub_type == "pmid"

    def test_extract_publication_id_from_doi(self, test_db):
        """Test extracting DOI from filename."""
        loader = SheetDataLoader(test_db)

        pub_id, pub_type = loader._extract_publication_id("doi_10_1038-nature16174.md")
        assert pub_id == "doi:10.1038/nature16174"
        assert pub_type == "doi"

    def test_extract_publication_id_from_pmc(self, test_db):
        """Test extracting PMC ID from filename."""
        loader = SheetDataLoader(test_db)

        pub_id, pub_type = loader._extract_publication_id("PMC6764073.md")
        assert pub_id == "pmc:6764073"
        assert pub_type == "pmc"

    def test_load_single_publication(self, test_db, test_sheets_dir):
        """Test loading single publication markdown file."""
        loader = SheetDataLoader(test_db)

        pub_path = test_sheets_dir / "publications" / "PMID_24816778.md"
        result = loader._load_single_publication("test_cmm", pub_path)

        assert result["success"] is True
        assert result["publication_id"] == "pmid:24816778"
        assert result["publication_type"] == "pmid"

        # Verify in database
        conn = duckdb.connect(str(test_db))
        pub = conn.execute(
            "SELECT publication_id, publication_type, word_count FROM sheet_publications WHERE publication_id = 'pmid:24816778'"
        ).fetchone()

        assert pub[0] == "pmid:24816778"
        assert pub[1] == "pmid"
        assert pub[2] > 0  # Has word count

        conn.close()

    def test_publication_full_text_stored(self, test_db, test_sheets_dir):
        """Test that full text is stored correctly."""
        loader = SheetDataLoader(test_db)

        pub_path = test_sheets_dir / "publications" / "PMID_24816778.md"
        loader._load_single_publication("test_cmm", pub_path)

        # Verify full text
        conn = duckdb.connect(str(test_db))
        full_text = conn.execute(
            "SELECT full_text FROM sheet_publications WHERE publication_id = 'pmid:24816778'"
        ).fetchone()[0]

        assert full_text is not None
        assert "lanthanides" in full_text.lower()
        assert "europium" in full_text.lower()
        assert "methanol" in full_text.lower()

        conn.close()

    def test_load_publications_directory(self, test_db, test_sheets_dir):
        """Test loading all publications from directory."""
        loader = SheetDataLoader(test_db)

        pubs_dir = test_sheets_dir / "publications"
        result = loader._load_publications("test_cmm", pubs_dir)

        assert result["success"] is True
        assert result["publications_loaded"] == 2  # PMID + DOI files

        # Verify in database
        conn = duckdb.connect(str(test_db))
        count = conn.execute("SELECT COUNT(*) FROM sheet_publications").fetchone()[0]
        assert count == 2

        conn.close()


class TestCrossReferences:
    """Test building cross-references between entities and publications."""

    def test_build_publication_references(self, test_db, test_sheets_dir):
        """Test building references from TSV URL columns to publications."""
        loader = SheetDataLoader(test_db)

        # Load TSV data with URLs
        tsv_path = test_sheets_dir / "BER_TEST_chemicals_extended.tsv"
        loader._load_tsv_table("test_cmm", tsv_path)

        # Load publications
        pubs_dir = test_sheets_dir / "publications"
        loader._load_publications("test_cmm", pubs_dir)

        # Build cross-references
        refs_created = loader._build_publication_references("test_cmm")

        assert refs_created > 0

        # Verify references exist
        conn = duckdb.connect(str(test_db))
        count = conn.execute("SELECT COUNT(*) FROM sheet_publication_references").fetchone()[0]
        assert count > 0

        # Verify specific reference
        ref = conn.execute(
            """
            SELECT entity_id, reference_column
            FROM sheet_publication_references
            WHERE entity_id = 'CHEBI:52927'
            """
        ).fetchone()

        assert ref is not None
        assert ref[0] == "CHEBI:52927"

        conn.close()


class TestCollectionLoading:
    """Test complete collection loading workflow."""

    def test_load_collection(self, test_db, test_sheets_dir):
        """Test loading complete collection (TSV + publications)."""
        loader = SheetDataLoader(test_db)

        result = loader.load_collection("test_cmm", test_sheets_dir)

        assert result["success"] is True
        assert result["collection_id"] == "test_cmm"
        assert result["tables_loaded"] == 2  # chemicals + genes
        assert result["publications_loaded"] == 2
        assert result["total_rows"] == 10  # 5 chemicals + 5 genes

        # Verify collection metadata in database
        conn = duckdb.connect(str(test_db))
        collection = conn.execute(
            "SELECT collection_id, table_count, total_rows FROM sheet_collections WHERE collection_id = 'test_cmm'"
        ).fetchone()

        assert collection[0] == "test_cmm"
        assert collection[1] == 2  # 2 tables
        assert collection[2] == 10  # 10 total rows

        conn.close()

    def test_validate_loading(self, test_db, test_sheets_dir):
        """Test validation after loading."""
        loader = SheetDataLoader(test_db)

        loader.load_collection("test_cmm", test_sheets_dir)
        validation = loader.validate_loading("test_cmm")

        assert validation["success"] is True
        assert validation["tables_loaded"] == 2
        assert validation["total_rows"] == 10
        assert validation["publications_loaded"] == 2
        assert validation["entity_counts"]["chemical"] == 5
        assert validation["entity_counts"]["gene"] == 5
        assert validation["references_created"] > 0


class TestErrorHandling:
    """Test error handling in loader."""

    def test_load_nonexistent_directory(self, test_db):
        """Test loading from non-existent directory."""
        loader = SheetDataLoader(test_db)

        result = loader.load_collection("test", Path("/nonexistent/path"))

        assert result["success"] is False
        assert "error" in result

    def test_load_empty_directory(self, test_db, tmp_path):
        """Test loading from empty directory."""
        loader = SheetDataLoader(test_db)
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = loader.load_collection("test", empty_dir)

        # Should succeed but load nothing
        assert result["success"] is True
        assert result["tables_loaded"] == 0

    def test_load_malformed_tsv(self, test_db, tmp_path):
        """Test handling malformed TSV file."""
        loader = SheetDataLoader(test_db)

        # Create malformed TSV
        bad_tsv = tmp_path / "bad_chemicals.tsv"
        bad_tsv.write_text("not\tvalid\ttsv\ndata")

        result = loader._load_tsv_table("test", bad_tsv)

        # Should handle gracefully (pandas can read it, so it succeeds)
        # Pandas successfully parses this as a TSV with 3 columns and 1 row
        assert result["success"] is True

#!/usr/bin/env python3
"""
Initialize information sheets tables in DuckDB database.

This script creates the schema for storing extended information sheets
from data/sheets_* directories (e.g., data/sheets_cmm).

Creates 5 tables:
- sheet_collections: Metadata registry for each sheets_* directory
- sheet_tables: Metadata for each TSV file
- sheet_data: Unified storage for TSV data (EAV pattern with JSON)
- sheet_publications: Full-text index of markdown publications
- sheet_publication_references: Cross-references between entities and publications

Usage:
    python scripts/init_sheet_schema.py
"""

import logging
import sys
from pathlib import Path

import duckdb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def create_sheet_tables(db_path: Path):
    """Create information sheets tables in database."""
    logger.info(f"Connecting to database: {db_path}")
    conn = duckdb.connect(str(db_path))

    # Create sheet_collections table
    logger.info("Creating sheet_collections table...")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sheet_collections (
            collection_id VARCHAR PRIMARY KEY,         -- 'cmm', 'xyz', etc.
            collection_name VARCHAR NOT NULL,          -- 'CMM Extended Data'
            directory_path VARCHAR NOT NULL,           -- 'data/sheets_cmm'
            loaded_at TIMESTAMP,                       -- When collection was loaded
            table_count INTEGER,                       -- Number of TSV tables loaded
            total_rows INTEGER,                        -- Total data rows across all tables
            description TEXT                           -- Collection description
        )
    """)

    # Create sheet_tables table
    logger.info("Creating sheet_tables table...")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sheet_tables (
            table_id VARCHAR PRIMARY KEY,              -- 'cmm_chemicals', 'cmm_genes'
            collection_id VARCHAR NOT NULL,            -- FK to sheet_collections
            table_name VARCHAR NOT NULL,               -- 'chemicals', 'genes_and_proteins'
            source_file VARCHAR NOT NULL,              -- 'BER_CMM_Data_for_AI_chemicals_extended.tsv'
            row_count INTEGER,                         -- Number of rows in table
            column_count INTEGER,                      -- Number of columns
            columns_json TEXT,                         -- JSON array of column names
            loaded_at TIMESTAMP                        -- When table was loaded
        )
    """)

    # Create sheet_data table with sequence for auto-increment
    logger.info("Creating sheet_data table...")
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS sheet_data_seq START 1;

        CREATE TABLE IF NOT EXISTS sheet_data (
            id INTEGER PRIMARY KEY DEFAULT nextval('sheet_data_seq'),
            table_id VARCHAR NOT NULL,                 -- FK to sheet_tables
            row_id INTEGER NOT NULL,                   -- Row number within source table
            entity_id VARCHAR,                         -- Primary ID (chemical_id, gene_id, etc.)
            entity_name VARCHAR,                       -- Primary name (chemical_name, gene_symbol, etc.)
            entity_type VARCHAR,                       -- 'chemical', 'gene', 'strain', 'publication'
            data_json TEXT NOT NULL,                   -- Complete row as JSON (all columns)
            searchable_text TEXT                       -- Concatenated text for full-text search
        )
    """)

    # Create sheet_publications table with sequence
    logger.info("Creating sheet_publications table...")
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS sheet_publications_seq START 1;

        CREATE TABLE IF NOT EXISTS sheet_publications (
            id INTEGER PRIMARY KEY DEFAULT nextval('sheet_publications_seq'),
            collection_id VARCHAR NOT NULL,            -- FK to sheet_collections
            file_name VARCHAR NOT NULL,                -- 'PMID_24816778.md'
            publication_id VARCHAR,                    -- 'pmid:24816778', 'doi:10.1038/...'
            publication_type VARCHAR,                  -- 'pmid', 'doi', 'pmc', 'arxiv'
            title TEXT,                                -- Publication title
            authors TEXT,                              -- Authors
            year INTEGER,                              -- Publication year
            journal TEXT,                              -- Journal name
            abstract TEXT,                             -- Abstract
            full_text TEXT,                            -- Complete markdown content
            word_count INTEGER,                        -- Word count
            loaded_at TIMESTAMP                        -- When loaded
        )
    """)

    # Create sheet_publication_references table with sequence
    logger.info("Creating sheet_publication_references table...")
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS sheet_publication_references_seq START 1;

        CREATE TABLE IF NOT EXISTS sheet_publication_references (
            id INTEGER PRIMARY KEY DEFAULT nextval('sheet_publication_references_seq'),
            publication_id INTEGER NOT NULL,           -- FK to sheet_publications.id
            table_id VARCHAR NOT NULL,                 -- FK to sheet_tables
            entity_id VARCHAR NOT NULL,                -- Entity referencing this publication
            reference_column VARCHAR,                  -- Column where reference appears
            reference_value VARCHAR                    -- Actual reference value
        )
    """)

    # Create indexes
    logger.info("Creating indexes...")

    indexes = [
        # Entity lookup indexes (Query Type 1)
        "CREATE INDEX IF NOT EXISTS idx_sheet_data_entity_id ON sheet_data(entity_id)",
        "CREATE INDEX IF NOT EXISTS idx_sheet_data_entity_name ON sheet_data(entity_name)",
        "CREATE INDEX IF NOT EXISTS idx_sheet_data_entity_type ON sheet_data(entity_type)",
        # Cross-reference indexes (Query Type 2)
        "CREATE INDEX IF NOT EXISTS idx_sheet_data_composite ON sheet_data(table_id, entity_type)",
        "CREATE INDEX IF NOT EXISTS idx_sheet_pub_refs_entity ON sheet_publication_references(entity_id)",
        # Full-text search indexes (Query Type 3)
        "CREATE INDEX IF NOT EXISTS idx_sheet_pubs_pub_id ON sheet_publications(publication_id)",
        "CREATE INDEX IF NOT EXISTS idx_sheet_data_searchable ON sheet_data(searchable_text)",
        # Collection/table lookups (Query Type 4)
        "CREATE INDEX IF NOT EXISTS idx_sheet_tables_collection ON sheet_tables(collection_id)",
        "CREATE INDEX IF NOT EXISTS idx_sheet_data_table ON sheet_data(table_id)"
    ]

    for idx_sql in indexes:
        conn.execute(idx_sql)
        # Extract table name from index SQL for logging
        parts = idx_sql.split(' ON ')
        if len(parts) > 1:
            logger.info(f"  Index: {parts[1].split('(')[0].strip()}")

    conn.close()
    logger.info("Sheet schema initialization complete!")


def main():
    """Main entry point."""
    db_path = Path("data/processed/microgrow.duckdb")

    logger.info("=" * 80)
    logger.info("INITIALIZING INFORMATION SHEETS SCHEMA")
    logger.info("=" * 80)
    logger.info(f"Database: {db_path}")
    logger.info("")
    logger.info("Creating 5 tables:")
    logger.info("  1. sheet_collections - Collection metadata")
    logger.info("  2. sheet_tables - TSV table metadata")
    logger.info("  3. sheet_data - Unified data storage (EAV + JSON)")
    logger.info("  4. sheet_publications - Publication full-text index")
    logger.info("  5. sheet_publication_references - Entity-publication cross-refs")
    logger.info("")
    logger.info("Creating 9 indexes for query performance")
    logger.info("")

    try:
        create_sheet_tables(db_path)
        logger.info("")
        logger.info("=" * 80)
        logger.info("SUCCESS: Sheet schema initialized")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Run: python scripts/load_sheets.py")
        logger.info("  2. Load data from: data/sheets_cmm/")
        return 0
    except Exception as e:
        logger.error(f"Error initializing schema: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

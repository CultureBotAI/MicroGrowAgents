#!/usr/bin/env python
"""
Load Information Sheets into Database.

Loads TSV files and publication markdown files from data/sheets_* directories
into the DuckDB database for querying.

Usage:
    python scripts/load_sheets.py --collection-id cmm --sheets-dir data/sheets_cmm
    python scripts/load_sheets.py --collection-id cmm --sheets-dir data/sheets_cmm --database custom.duckdb

Author: MicroGrowAgents Team
"""

import argparse
import logging
import sys
from pathlib import Path

import duckdb

from microgrowagents.database.sheet_loader import SheetDataLoader
from microgrowagents.database.schema import create_schema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for loading sheets data."""
    parser = argparse.ArgumentParser(
        description='Load information sheets into database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Load CMM collection
  python scripts/load_sheets.py --collection-id cmm --sheets-dir data/sheets_cmm

  # Load with custom database
  python scripts/load_sheets.py --collection-id cmm --sheets-dir data/sheets_cmm --database custom.duckdb

  # Load with validation
  python scripts/load_sheets.py --collection-id cmm --sheets-dir data/sheets_cmm --validate
        '''
    )

    parser.add_argument(
        '--collection-id',
        type=str,
        required=True,
        help='Collection identifier (e.g., "cmm", "xyz")'
    )

    parser.add_argument(
        '--sheets-dir',
        type=Path,
        required=True,
        help='Path to sheets directory (e.g., data/sheets_cmm)'
    )

    parser.add_argument(
        '--database',
        type=Path,
        default=Path('data/processed/microgrow.duckdb'),
        help='Path to DuckDB database (default: data/processed/microgrow.duckdb)'
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='Run validation after loading'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate inputs
    if not args.sheets_dir.exists():
        logger.error(f"Sheets directory does not exist: {args.sheets_dir}")
        sys.exit(1)

    # Create database parent directory if needed
    args.database.parent.mkdir(parents=True, exist_ok=True)

    # Ensure schema exists
    logger.info(f"Initializing database schema: {args.database}")
    conn = duckdb.connect(str(args.database))
    create_schema(conn)
    conn.close()

    # Initialize loader
    logger.info(f"Initializing SheetDataLoader for database: {args.database}")
    loader = SheetDataLoader(args.database)

    # Load collection
    logger.info(f"Loading collection '{args.collection_id}' from {args.sheets_dir}")
    logger.info("=" * 80)

    result = loader.load_collection(args.collection_id, args.sheets_dir)

    logger.info("=" * 80)

    if not result["success"]:
        logger.error(f"Loading failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

    # Print summary
    logger.info("\nLoading Summary:")
    logger.info(f"  Collection ID:      {result['collection_id']}")
    logger.info(f"  Tables Loaded:      {result['tables_loaded']}")
    logger.info(f"  Publications:       {result['publications_loaded']}")
    logger.info(f"  Total Rows:         {result['total_rows']}")
    logger.info(f"  References Created: {result['references_created']}")

    # Validate if requested
    if args.validate:
        logger.info("\nRunning validation...")
        logger.info("=" * 80)

        validation = loader.validate_loading(args.collection_id)

        logger.info("=" * 80)

        if not validation["success"]:
            logger.error("Validation failed")
            sys.exit(1)

        logger.info("\nValidation Summary:")
        logger.info(f"  Tables Loaded:      {validation['tables_loaded']}")
        logger.info(f"  Total Rows:         {validation['total_rows']}")
        logger.info(f"  Publications:       {validation['publications_loaded']}")
        logger.info(f"  References:         {validation['references_created']}")

        if validation.get('entity_counts'):
            logger.info("\n  Entity Counts by Type:")
            for entity_type, count in sorted(validation['entity_counts'].items()):
                logger.info(f"    {entity_type:15s} {count:6d}")

        logger.info("\n✓ Validation passed!")

    logger.info("\n✓ Loading completed successfully!")
    logger.info(f"\nDatabase: {args.database}")
    logger.info(f"Collection: {args.collection_id}")


if __name__ == '__main__':
    main()

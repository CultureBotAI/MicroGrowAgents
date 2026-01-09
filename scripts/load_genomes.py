#!/usr/bin/env python3
"""
Load all Bakta GFF3 files into DuckDB database.

Usage:
    python scripts/load_genomes.py
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from microgrowagents.database.genome_loader import GenomeDataLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    """Load all genomes into database."""
    # Paths
    db_path = Path("data/processed/microgrow.duckdb")
    gff3_dir = Path("data/bakta_cmm")

    logger.info("=" * 80)
    logger.info("LOADING BAKTA GFF3 FILES INTO DUCKDB")
    logger.info("=" * 80)
    logger.info(f"Database: {db_path}")
    logger.info(f"GFF3 Directory: {gff3_dir}")
    logger.info("")

    # Check if directory exists
    if not gff3_dir.exists():
        logger.error(f"GFF3 directory not found: {gff3_dir}")
        return 1

    # Count GFF3 files
    gff3_files = list(gff3_dir.glob("*.gff3"))
    logger.info(f"Found {len(gff3_files)} GFF3 files")
    logger.info("")

    try:
        # Initialize loader
        loader = GenomeDataLoader(db_path=db_path)

        # Load all genomes
        logger.info("Starting genome loading...")
        stats = loader.load_all_genomes(gff3_dir=gff3_dir, use_cache=True)

        logger.info("")
        logger.info("=" * 80)
        logger.info("LOADING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Genomes processed: {stats['genomes_processed']}")
        logger.info(f"Genomes successful: {stats['genomes_successful']}")
        logger.info(f"Genomes failed: {stats['genomes_failed']}")
        logger.info(f"Total features: {stats['total_features']:,}")
        logger.info(f"NCBI lookups successful: {stats['ncbi_lookups_successful']}")
        logger.info(f"NCBI lookups failed: {stats['ncbi_lookups_failed']}")
        logger.info("")

        # Validate loading
        logger.info("Validating loaded data...")
        validation = loader.validate_loading()

        logger.info("")
        logger.info("=" * 80)
        logger.info("VALIDATION RESULTS")
        logger.info("=" * 80)
        logger.info(f"Genomes loaded: {validation['genomes_loaded']}")
        logger.info(f"Total features: {validation['total_features']:,}")
        logger.info("")

        if "features_by_type" in validation:
            logger.info("Features by type:")
            for feature_type, count in validation["features_by_type"].items():
                logger.info(f"  {feature_type}: {count:,}")
            logger.info("")

        if "annotation_coverage" in validation:
            logger.info("Annotation coverage:")
            cov = validation["annotation_coverage"]
            logger.info(f"  Total CDS: {cov['total_cds']:,}")
            logger.info(f"  EC coverage: {cov['ec_coverage']}")
            logger.info(f"  GO coverage: {cov['go_coverage']}")
            logger.info(f"  KEGG coverage: {cov['kegg_coverage']}")
            logger.info(f"  COG coverage: {cov['cog_coverage']}")
            logger.info("")

        if "organism_linkage" in validation:
            logger.info(f"Organism linkage: {validation['organism_linkage']}")
            logger.info("")

        # Close connection
        loader.close()

        logger.info("=" * 80)
        logger.info("SUCCESS: All genomes loaded and validated")
        logger.info("=" * 80)

        return 0

    except Exception as e:
        logger.error(f"Error during loading: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Initialize genome tables in DuckDB database.

Usage:
    python scripts/init_genome_schema.py
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


def create_genome_tables(db_path: Path):
    """Create genome tables in database."""
    logger.info(f"Connecting to database: {db_path}")
    conn = duckdb.connect(str(db_path))

    # Create genome_metadata table
    logger.info("Creating genome_metadata table...")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS genome_metadata (
            genome_id VARCHAR PRIMARY KEY,              -- SAMN00114986 (BioSample ID)
            organism_id VARCHAR,                        -- Link to organisms.id (NCBITaxon)
            organism_name VARCHAR,                      -- E.g., "Escherichia coli K-12"
            biosample_id VARCHAR,                       -- SAMN ID (same as genome_id)
            assembly_size INTEGER,                      -- Total genome size in bp
            contig_count INTEGER,                       -- Number of contigs/scaffolds
            gene_count INTEGER,                         -- Total genes annotated
            cds_count INTEGER,                          -- Protein-coding genes (CDS features)
            trna_count INTEGER,                         -- tRNA genes
            rrna_count INTEGER,                         -- rRNA genes
            ncrna_count INTEGER,                        -- Other ncRNA genes
            annotation_tool VARCHAR,                    -- "Bakta"
            annotation_version VARCHAR,                 -- "v1.9.4"
            annotation_database VARCHAR,                -- "v5.1, full"
            annotation_date DATE,                       -- Date annotated
            metadata_json TEXT                          -- Flexible JSON for extra fields
        )
    """)

    # Create genome_annotations table
    logger.info("Creating genome_annotations table...")
    conn.execute("""
        CREATE SEQUENCE IF NOT EXISTS genome_annotations_seq START 1;

        CREATE TABLE IF NOT EXISTS genome_annotations (
            id INTEGER PRIMARY KEY DEFAULT nextval('genome_annotations_seq'),
            genome_id VARCHAR NOT NULL,                 -- REFERENCES genome_metadata(genome_id)
            feature_id VARCHAR NOT NULL,                -- PJIGLD_00005 (unique within genome)
            feature_type VARCHAR NOT NULL,              -- CDS, tRNA, rRNA, ncRNA, tmRNA, CRISPR, region
            contig_id VARCHAR,                          -- contig00001
            start_pos INTEGER,                          -- Start position on contig
            end_pos INTEGER,                            -- End position on contig
            strand VARCHAR,                             -- +, -, ?
            locus_tag VARCHAR,                          -- Systematic locus tag
            gene_symbol VARCHAR,                        -- Gene name (e.g., "fur", "hemolysin")
            product TEXT,                               -- Product description
            ec_numbers TEXT,                            -- Comma-separated: "2.3.2.30,1.1.1.1"
            go_terms TEXT,                              -- Comma-separated GO IDs: "0005575,0008150"
            kegg_ids TEXT,                              -- Comma-separated KEGG IDs: "K22310,K00001"
            cog_ids TEXT,                               -- Comma-separated COG IDs: "COG2202,COG0001"
            cog_categories TEXT,                        -- Comma-separated COG categories: "T,E"
            protein_id VARCHAR,                         -- RefSeq/UniRef ID (WP_017839628.1)
            dbxref TEXT,                                -- Full Dbxref string for reference
            source VARCHAR,                             -- Pyrodigal, tRNAscan-SE, Infernal, PILER-CR
            score DOUBLE,                               -- Prediction score (if available)
            phase INTEGER                               -- Reading frame phase (0, 1, 2 for CDS)
        )
    """)

    # Create indexes
    logger.info("Creating indexes...")

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_genome_meta_organism ON genome_metadata(organism_id)",
        "CREATE INDEX IF NOT EXISTS idx_genome_ann_genome ON genome_annotations(genome_id)",
        "CREATE INDEX IF NOT EXISTS idx_genome_ann_type ON genome_annotations(feature_type)",
        "CREATE INDEX IF NOT EXISTS idx_genome_ann_gene ON genome_annotations(gene_symbol)",
        "CREATE INDEX IF NOT EXISTS idx_genome_ann_product ON genome_annotations(product)",
        "CREATE INDEX IF NOT EXISTS idx_genome_ann_ec ON genome_annotations(ec_numbers)",
        "CREATE INDEX IF NOT EXISTS idx_genome_ann_go ON genome_annotations(go_terms)",
        "CREATE INDEX IF NOT EXISTS idx_genome_ann_kegg ON genome_annotations(kegg_ids)",
        "CREATE INDEX IF NOT EXISTS idx_genome_ann_cog ON genome_annotations(cog_ids)"
    ]

    for idx_sql in indexes:
        conn.execute(idx_sql)
        logger.info(f"  {idx_sql.split('ON')[1].split('(')[0].strip()}")

    conn.close()
    logger.info("Genome schema initialization complete!")


def main():
    """Main entry point."""
    db_path = Path("data/processed/microgrow.duckdb")

    logger.info("=" * 80)
    logger.info("INITIALIZING GENOME SCHEMA")
    logger.info("=" * 80)
    logger.info(f"Database: {db_path}")
    logger.info("")

    try:
        create_genome_tables(db_path)
        logger.info("")
        logger.info("=" * 80)
        logger.info("SUCCESS: Genome schema initialized")
        logger.info("=" * 80)
        return 0
    except Exception as e:
        logger.error(f"Error initializing schema: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

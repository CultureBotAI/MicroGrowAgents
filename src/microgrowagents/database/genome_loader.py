"""
Genome Data Loader for Bakta GFF3 files.

Loads genome annotations from Bakta GFF3 files into DuckDB database.
Integrates with GFF3Parser and NCBILookupService.

Author: MicroGrowAgents Team
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import duckdb
import pandas as pd

from microgrowagents.parsers.gff3_parser import GFF3Parser
from microgrowagents.services.ncbi_lookup import NCBILookupService

logger = logging.getLogger(__name__)


class GenomeDataLoader:
    """
    Load Bakta GFF3 files into DuckDB database.

    Coordinates GFF3 parsing, NCBI organism lookup, and database loading.

    Example:
        >>> loader = GenomeDataLoader(db_path="data/processed/microgrow.duckdb")
        >>> loader.load_all_genomes(gff3_dir="data/bakta_cmm")
        >>> stats = loader.validate_loading()
        >>> stats["genomes_loaded"]
        57
    """

    def __init__(self, db_path: Path):
        """
        Initialize Genome Data Loader.

        Args:
            db_path: Path to DuckDB database
        """
        self.db_path = Path(db_path)
        self.conn = duckdb.connect(str(self.db_path))
        self.parser = GFF3Parser()
        self.ncbi = NCBILookupService()

        logger.info(f"GenomeDataLoader initialized with database: {db_path}")

    def load_all_genomes(
        self,
        gff3_dir: Path,
        use_cache: bool = True,
        limit: Optional[int] = None
    ) -> Dict:
        """
        Load all GFF3 files from directory.

        Args:
            gff3_dir: Directory containing *.gff3 files
            use_cache: Use cached NCBI lookups (default: True)
            limit: Limit number of genomes to load (for testing)

        Returns:
            Dict with loading statistics

        Example:
            >>> loader = GenomeDataLoader("microgrow.duckdb")
            >>> stats = loader.load_all_genomes("data/bakta_cmm", limit=5)
            >>> stats["genomes_processed"] == 5
            True
        """
        gff3_dir = Path(gff3_dir)
        gff3_files = sorted(list(gff3_dir.glob("*.gff3")))

        if limit:
            gff3_files = gff3_files[:limit]

        logger.info(f"Found {len(gff3_files)} GFF3 files to process")

        stats = {
            "genomes_processed": 0,
            "genomes_successful": 0,
            "genomes_failed": 0,
            "total_features": 0,
            "ncbi_lookups_successful": 0,
            "ncbi_lookups_failed": 0,
        }

        for i, gff3_path in enumerate(gff3_files, 1):
            logger.info(f"Processing {i}/{len(gff3_files)}: {gff3_path.name}")

            try:
                self.load_single_genome(gff3_path)
                stats["genomes_successful"] += 1
            except Exception as e:
                logger.error(f"Failed to load {gff3_path.name}: {e}")
                stats["genomes_failed"] += 1

            stats["genomes_processed"] += 1

            # Log progress every 5 genomes
            if i % 5 == 0:
                logger.info(f"Progress: {i}/{len(gff3_files)} genomes processed")

        # Save NCBI cache
        self.ncbi.save_cache()

        # Get final cache stats
        cache_stats = self.ncbi.get_cache_stats()
        stats["ncbi_lookups_successful"] = cache_stats["successful"]
        stats["ncbi_lookups_failed"] = cache_stats["failed"]

        # Get total features count
        result = self.conn.execute("SELECT COUNT(*) FROM genome_annotations").fetchone()
        stats["total_features"] = result[0] if result else 0

        logger.info(f"Loading complete: {stats}")

        return stats

    def load_single_genome(self, gff3_path: Path) -> str:
        """
        Load a single GFF3 file.

        Args:
            gff3_path: Path to GFF3 file

        Returns:
            genome_id (SAMN ID)

        Example:
            >>> loader = GenomeDataLoader("microgrow.duckdb")
            >>> genome_id = loader.load_single_genome("SAMN00114986.bakta.gff3")
            >>> genome_id
            'SAMN00114986'
        """
        # Extract SAMN ID from filename
        genome_id = gff3_path.stem.split(".")[0]  # SAMN00114986.bakta.gff3 -> SAMN00114986

        logger.info(f"Loading genome: {genome_id}")

        # Parse GFF3 file
        metadata, features = self.parser.parse_file(gff3_path)

        # Get genome stats
        stats = self.parser.extract_genome_stats(features, metadata)

        # Lookup organism info from NCBI
        ncbi_result = self.ncbi.lookup_biosample(genome_id)

        # Insert genome metadata
        self._insert_genome_metadata(
            genome_id=genome_id,
            metadata=metadata,
            stats=stats,
            ncbi_result=ncbi_result
        )

        # Insert genome annotations (batched)
        self._batch_insert_features(genome_id, features)

        logger.info(f"Loaded {genome_id}: {len(features)} features")

        return genome_id

    def _insert_genome_metadata(
        self,
        genome_id: str,
        metadata: Dict,
        stats: Dict,
        ncbi_result: Dict
    ):
        """
        Insert genome metadata into genome_metadata table.

        Args:
            genome_id: SAMN ID
            metadata: Parsed GFF3 metadata
            stats: Genome statistics
            ncbi_result: NCBI lookup result
        """
        # Prepare organism ID (NCBITaxon format)
        organism_id = None
        if ncbi_result.get("taxid"):
            organism_id = f"NCBITaxon:{ncbi_result['taxid']}"

        # Prepare metadata row
        meta_row = {
            "genome_id": genome_id,
            "organism_id": organism_id,
            "organism_name": ncbi_result.get("organism_name"),
            "biosample_id": genome_id,
            "assembly_size": stats.get("assembly_size"),
            "contig_count": stats.get("contig_count"),
            "gene_count": stats.get("gene_count"),
            "cds_count": stats.get("cds_count"),
            "trna_count": stats.get("trna_count"),
            "rrna_count": stats.get("rrna_count"),
            "ncrna_count": stats.get("ncrna_count"),
            "annotation_tool": metadata.get("annotation_tool", "Bakta"),
            "annotation_version": metadata.get("annotation_version"),
            "annotation_database": metadata.get("database_version"),
            "annotation_date": None,  # Not in GFF3 header
            "metadata_json": None  # Could store extra metadata as JSON
        }

        # Convert to DataFrame for INSERT
        df = pd.DataFrame([meta_row])

        # Insert with INSERT OR REPLACE to handle re-loading
        self.conn.execute("""
            INSERT OR REPLACE INTO genome_metadata (
                genome_id, organism_id, organism_name, biosample_id,
                assembly_size, contig_count, gene_count, cds_count,
                trna_count, rrna_count, ncrna_count,
                annotation_tool, annotation_version, annotation_database,
                annotation_date, metadata_json
            )
            SELECT * FROM df
        """)

    def _batch_insert_features(
        self,
        genome_id: str,
        features: List[Dict],
        batch_size: int = 50000
    ):
        """
        Batch insert features into genome_annotations table.

        Args:
            genome_id: SAMN ID
            features: List of parsed features
            batch_size: Number of rows per batch
        """
        # Convert features to rows
        rows = []
        for feature in features:
            # Join list fields to comma-separated strings
            ec_numbers = ",".join(feature.get("ec_numbers", []))
            go_terms = ",".join(feature.get("go_terms", []))
            kegg_ids = ",".join(feature.get("kegg_ids", []))
            cog_ids = ",".join(feature.get("cog_ids", []))
            cog_categories = ",".join(feature.get("cog_categories", []))

            row = {
                "genome_id": genome_id,
                "feature_id": feature.get("ID"),
                "feature_type": feature.get("type"),
                "contig_id": feature.get("seqid"),
                "start_pos": feature.get("start"),
                "end_pos": feature.get("end"),
                "strand": feature.get("strand"),
                "locus_tag": feature.get("locus_tag"),
                "gene_symbol": feature.get("gene"),
                "product": feature.get("product"),
                "ec_numbers": ec_numbers if ec_numbers else None,
                "go_terms": go_terms if go_terms else None,
                "kegg_ids": kegg_ids if kegg_ids else None,
                "cog_ids": cog_ids if cog_ids else None,
                "cog_categories": cog_categories if cog_categories else None,
                "protein_id": feature.get("protein_id"),
                "dbxref": feature.get("Dbxref"),
                "source": feature.get("source"),
                "score": feature.get("score"),
                "phase": feature.get("phase"),
            }
            rows.append(row)

        # Convert to DataFrame
        df = pd.DataFrame(rows)

        # Batch insert
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i + batch_size]

            self.conn.execute("""
                INSERT OR IGNORE INTO genome_annotations (
                    genome_id, feature_id, feature_type, contig_id,
                    start_pos, end_pos, strand, locus_tag, gene_symbol,
                    product, ec_numbers, go_terms, kegg_ids, cog_ids,
                    cog_categories, protein_id, dbxref, source, score, phase
                )
                SELECT
                    genome_id, feature_id, feature_type, contig_id,
                    start_pos, end_pos, strand, locus_tag, gene_symbol,
                    product, ec_numbers, go_terms, kegg_ids, cog_ids,
                    cog_categories, protein_id, dbxref, source, score, phase
                FROM batch
            """)

            logger.debug(f"Inserted batch {i // batch_size + 1}: {len(batch)} features")

    def validate_loading(self) -> Dict:
        """
        Validate loaded data and return statistics.

        Returns:
            Dict with validation statistics

        Example:
            >>> loader = GenomeDataLoader("microgrow.duckdb")
            >>> stats = loader.validate_loading()
            >>> stats["genomes_loaded"] > 0
            True
        """
        stats = {}

        # Count genomes
        result = self.conn.execute("SELECT COUNT(*) FROM genome_metadata").fetchone()
        stats["genomes_loaded"] = result[0] if result else 0

        # Count features
        result = self.conn.execute("SELECT COUNT(*) FROM genome_annotations").fetchone()
        stats["total_features"] = result[0] if result else 0

        # Count by feature type
        result = self.conn.execute("""
            SELECT feature_type, COUNT(*) as count
            FROM genome_annotations
            GROUP BY feature_type
            ORDER BY count DESC
        """).fetchall()
        stats["features_by_type"] = {row[0]: row[1] for row in result}

        # Annotation coverage (% of CDS with each annotation type)
        result = self.conn.execute("""
            SELECT
                COUNT(*) as total_cds,
                SUM(CASE WHEN ec_numbers IS NOT NULL AND ec_numbers != '' THEN 1 ELSE 0 END) as with_ec,
                SUM(CASE WHEN go_terms IS NOT NULL AND go_terms != '' THEN 1 ELSE 0 END) as with_go,
                SUM(CASE WHEN kegg_ids IS NOT NULL AND kegg_ids != '' THEN 1 ELSE 0 END) as with_kegg,
                SUM(CASE WHEN cog_ids IS NOT NULL AND cog_ids != '' THEN 1 ELSE 0 END) as with_cog
            FROM genome_annotations
            WHERE feature_type = 'CDS'
        """).fetchone()

        if result and result[0] > 0:
            total_cds = result[0]
            stats["annotation_coverage"] = {
                "total_cds": total_cds,
                "ec_coverage": f"{result[1] / total_cds * 100:.1f}%",
                "go_coverage": f"{result[2] / total_cds * 100:.1f}%",
                "kegg_coverage": f"{result[3] / total_cds * 100:.1f}%",
                "cog_coverage": f"{result[4] / total_cds * 100:.1f}%",
            }

        # Organism linkage
        result = self.conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN organism_id IS NOT NULL THEN 1 ELSE 0 END) as with_organism_id
            FROM genome_metadata
        """).fetchone()

        if result and result[0] > 0:
            stats["organism_linkage"] = f"{result[1] / result[0] * 100:.1f}%"

        return stats

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

"""
GFF3 Parser for Bakta genome annotations.

Parses Bakta GFF3 files and extracts structured annotations including
functional annotations (EC numbers, GO terms, KEGG IDs, COG categories).

Author: MicroGrowAgents Team
"""

import logging
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class GFF3Parser:
    """
    Parse Bakta GFF3 files and extract structured annotations.

    Bakta GFF3 format:
    - Standard 9-column GFF3 format
    - Column 9 contains semicolon-separated attributes
    - Dbxref attribute contains comma-separated database cross-references
    - Supports URL encoding (e.g., %20 for space)

    Example:
        >>> parser = GFF3Parser()
        >>> metadata, features = parser.parse_file("SAMN00114986.bakta.gff3")
        >>> len(features)
        4295
        >>> metadata["gff_version"]
        '3'
    """

    def __init__(self):
        """Initialize GFF3Parser."""
        pass

    def parse_file(self, gff3_path: Path) -> Tuple[Dict, List[Dict]]:
        """
        Parse a GFF3 file.

        Args:
            gff3_path: Path to GFF3 file

        Returns:
            Tuple of (metadata_dict, list_of_features)
            - metadata: Dict with gff_version, annotation_tool, database_version, sequence_regions
            - features: List of feature dicts with parsed attributes

        Example:
            >>> parser = GFF3Parser()
            >>> metadata, features = parser.parse_file(Path("test.gff3"))
            >>> metadata["gff_version"]
            '3'
        """
        if not gff3_path.exists():
            raise FileNotFoundError(f"GFF3 file not found: {gff3_path}")

        metadata = {}
        features = []
        header_lines = []
        feature_lines = []

        logger.info(f"Parsing GFF3 file: {gff3_path}")

        # Read file and separate header from features
        with open(gff3_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                if line.startswith("##"):
                    header_lines.append(line)
                elif line.startswith("#"):
                    # Skip non-## comments
                    continue
                else:
                    feature_lines.append(line)

        # Parse header
        metadata = self._parse_header(header_lines)

        # Parse features
        for line in feature_lines:
            try:
                feature = self._parse_feature_line(line)
                if feature:
                    features.append(feature)
            except Exception as e:
                logger.warning(f"Failed to parse line: {line[:100]}... Error: {e}")
                continue

        logger.info(f"Parsed {len(features)} features from {gff3_path.name}")

        return metadata, features

    def _parse_header(self, lines: List[str]) -> Dict:
        """
        Extract metadata from ##-prefixed header lines.

        Args:
            lines: List of header lines starting with ##

        Returns:
            Dict with extracted metadata

        Example:
            >>> parser = GFF3Parser()
            >>> lines = ["##gff-version 3", "# Software: v1.9.4"]
            >>> meta = parser._parse_header(lines)
            >>> meta["gff_version"]
            '3'
        """
        metadata = {
            "gff_version": None,
            "annotation_tool": None,
            "annotation_version": None,
            "database_version": None,
            "sequence_regions": [],
        }

        for line in lines:
            if line.startswith("##gff-version"):
                metadata["gff_version"] = line.split()[-1]

            elif line.startswith("# Software:"):
                # Example: "# Software: v1.9.4"
                parts = line.split(":")
                if len(parts) >= 2:
                    metadata["annotation_version"] = parts[1].strip()
                metadata["annotation_tool"] = "Bakta"

            elif line.startswith("# Database:"):
                # Example: "# Database: v5.1, full"
                parts = line.split(":")
                if len(parts) >= 2:
                    metadata["database_version"] = parts[1].strip()

            elif line.startswith("##sequence-region"):
                # Example: "##sequence-region contig00001 1 123456"
                parts = line.split()
                if len(parts) >= 4:
                    metadata["sequence_regions"].append({
                        "seqid": parts[1],
                        "start": int(parts[2]),
                        "end": int(parts[3])
                    })

        return metadata

    def _parse_feature_line(self, line: str) -> Optional[Dict]:
        """
        Parse a single GFF3 feature line (9 columns).

        GFF3 format:
        1. seqid (contig)
        2. source (Pyrodigal, Bakta, etc.)
        3. type (CDS, tRNA, etc.)
        4. start
        5. end
        6. score
        7. strand (+/-)
        8. phase (0,1,2)
        9. attributes (semicolon-separated)

        Args:
            line: GFF3 feature line

        Returns:
            Dict with parsed feature or None if parsing fails

        Example:
            >>> parser = GFF3Parser()
            >>> line = "contig00001\\tPyrodigal\\tCDS\\t55\\t2037\\t.\\t-\\t0\\tID=GENE_00005;Name=protein"
            >>> feature = parser._parse_feature_line(line)
            >>> feature["type"]
            'CDS'
        """
        parts = line.split("\t")
        if len(parts) != 9:
            logger.warning(f"Invalid GFF3 line (expected 9 columns, got {len(parts)})")
            return None

        # Parse fixed columns
        feature = {
            "seqid": parts[0],
            "source": parts[1],
            "type": parts[2],
            "start": int(parts[3]) if parts[3] != "." else None,
            "end": int(parts[4]) if parts[4] != "." else None,
            "score": float(parts[5]) if parts[5] not in (".", "") else None,
            "strand": parts[6] if parts[6] != "." else None,
            "phase": int(parts[7]) if parts[7] not in (".", "") else None,
        }

        # Parse attributes (column 9)
        attributes = self._parse_attributes(parts[8])
        feature.update(attributes)

        return feature

    def _parse_attributes(self, attr_string: str) -> Dict:
        """
        Parse semicolon-separated attributes from column 9.

        Attributes format: "ID=GENE_00005;Name=protein;Dbxref=COG:COG2202,EC:1.1.1.1"

        Args:
            attr_string: Attribute string from GFF3 column 9

        Returns:
            Dict with parsed attributes including structured Dbxref

        Example:
            >>> parser = GFF3Parser()
            >>> attrs = parser._parse_attributes("ID=GENE_001;Name=test;Dbxref=EC:1.1.1.1,GO:0005575")
            >>> attrs["ID"]
            'GENE_001'
            >>> attrs["ec_numbers"]
            ['1.1.1.1']
        """
        attributes = {
            "ID": None,
            "Name": None,
            "locus_tag": None,
            "product": None,
            "gene": None,
            "Dbxref": None,
            # Structured Dbxref fields
            "ec_numbers": [],
            "go_terms": [],
            "kegg_ids": [],
            "cog_ids": [],
            "cog_categories": [],
            "protein_id": None,
        }

        # Split by semicolon
        pairs = attr_string.split(";")

        for pair in pairs:
            if "=" not in pair:
                continue

            key, value = pair.split("=", 1)
            key = key.strip()
            value = value.strip()

            # URL decode value
            value = urllib.parse.unquote(value)

            # Store basic attributes
            if key in ["ID", "Name", "locus_tag", "product", "gene"]:
                attributes[key] = value

            # Parse Dbxref specially
            elif key == "Dbxref":
                attributes["Dbxref"] = value
                dbxref_parsed = self._parse_dbxref(value)
                attributes.update(dbxref_parsed)

        return attributes

    def _parse_dbxref(self, dbxref_string: str) -> Dict:
        """
        Parse comma-separated Dbxref into structured fields.

        Dbxref format: "COG:COG2202,COG:T,EC:2.3.2.30,GO:0005575,KEGG:K22310,RefSeq:WP_123"

        Args:
            dbxref_string: Comma-separated database cross-references

        Returns:
            Dict with ec_numbers, go_terms, kegg_ids, cog_ids, cog_categories, protein_id

        Example:
            >>> parser = GFF3Parser()
            >>> refs = parser._parse_dbxref("COG:COG2202,EC:2.3.2.30,GO:0005575,KEGG:K22310")
            >>> refs["ec_numbers"]
            ['2.3.2.30']
            >>> refs["go_terms"]
            ['0005575']
            >>> refs["kegg_ids"]
            ['K22310']
            >>> refs["cog_ids"]
            ['COG2202']
        """
        parsed = {
            "ec_numbers": [],
            "go_terms": [],
            "kegg_ids": [],
            "cog_ids": [],
            "cog_categories": [],
            "protein_id": None,
        }

        # Split by comma
        refs = dbxref_string.split(",")

        for ref in refs:
            ref = ref.strip()
            if ":" not in ref:
                continue

            db, identifier = ref.split(":", 1)
            db = db.strip()
            identifier = identifier.strip()

            if db == "EC":
                parsed["ec_numbers"].append(identifier)

            elif db == "GO":
                # Store GO term IDs without GO: prefix
                parsed["go_terms"].append(identifier)

            elif db == "KEGG":
                parsed["kegg_ids"].append(identifier)

            elif db == "COG":
                # Check if it's a COG ID (starts with COG) or category (single letter)
                if identifier.startswith("COG"):
                    parsed["cog_ids"].append(identifier)
                elif len(identifier) == 1:
                    # COG functional category (single letter)
                    parsed["cog_categories"].append(identifier)

            elif db in ["RefSeq", "UniRef", "UniParc"]:
                # Store first protein ID encountered
                if not parsed["protein_id"]:
                    parsed["protein_id"] = identifier

        return parsed

    def extract_genome_stats(self, features: List[Dict], metadata: Dict) -> Dict:
        """
        Calculate genome statistics from features.

        Args:
            features: List of parsed features
            metadata: Metadata dict with sequence regions

        Returns:
            Dict with gene_count, cds_count, trna_count, etc.

        Example:
            >>> parser = GFF3Parser()
            >>> features = [{"type": "CDS"}, {"type": "CDS"}, {"type": "tRNA"}]
            >>> stats = parser.extract_genome_stats(features, {})
            >>> stats["cds_count"]
            2
            >>> stats["trna_count"]
            1
        """
        stats = {
            "gene_count": 0,
            "cds_count": 0,
            "trna_count": 0,
            "rrna_count": 0,
            "ncrna_count": 0,
            "tmrna_count": 0,
            "crispr_count": 0,
            "assembly_size": 0,
            "contig_count": 0,
        }

        # Count feature types
        for feature in features:
            feature_type = feature.get("type", "")

            if feature_type == "CDS":
                stats["cds_count"] += 1
                stats["gene_count"] += 1
            elif feature_type == "tRNA":
                stats["trna_count"] += 1
                stats["gene_count"] += 1
            elif feature_type == "rRNA":
                stats["rrna_count"] += 1
                stats["gene_count"] += 1
            elif feature_type == "ncRNA":
                stats["ncrna_count"] += 1
                stats["gene_count"] += 1
            elif feature_type == "tmRNA":
                stats["tmrna_count"] += 1
                stats["gene_count"] += 1
            elif feature_type == "CRISPR":
                stats["crispr_count"] += 1

        # Calculate assembly size from sequence regions
        if "sequence_regions" in metadata:
            stats["contig_count"] = len(metadata["sequence_regions"])
            stats["assembly_size"] = sum(
                region["end"] - region["start"] + 1
                for region in metadata["sequence_regions"]
            )

        return stats

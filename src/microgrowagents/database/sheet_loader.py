"""
Sheet Data Loader for Extended Information Sheets.

Loads TSV files and publication markdown files from data/sheets_* directories
into DuckDB database for querying.

Author: MicroGrowAgents Team
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)


class SheetDataLoader:
    """
    Load information sheets (TSV + markdown publications) into DuckDB.

    Handles loading of topic-specific data collections from sheets_* directories,
    including TSV tables and publication markdown files.

    Example:
        >>> loader = SheetDataLoader(db_path="data/processed/microgrow.duckdb")
        >>> loader.load_collection("cmm", Path("data/sheets_cmm"))
        >>> stats = loader.validate_loading("cmm")
        >>> stats["tables_loaded"]
        17
    """

    def __init__(self, db_path: Path):
        """
        Initialize Sheet Data Loader.

        Args:
            db_path: Path to DuckDB database
        """
        self.db_path = Path(db_path)
        self.conn = None
        logger.info(f"SheetDataLoader initialized with database: {db_path}")

    def _connect(self):
        """Connect to database."""
        if self.conn is None:
            self.conn = duckdb.connect(str(self.db_path))

    def _close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def load_collection(
        self,
        collection_id: str,
        sheets_dir: Path
    ) -> Dict:
        """
        Load complete sheet collection (TSV + publications).

        Args:
            collection_id: Collection identifier (e.g., 'cmm', 'xyz')
            sheets_dir: Path to sheets directory (e.g., data/sheets_cmm)

        Returns:
            Dict with loading statistics

        Example:
            >>> loader = SheetDataLoader("microgrow.duckdb")
            >>> stats = loader.load_collection("cmm", Path("data/sheets_cmm"))
            >>> stats["success"]
            True
        """
        self._connect()
        sheets_dir = Path(sheets_dir)

        if not sheets_dir.exists():
            return {
                "success": False,
                "error": f"Directory does not exist: {sheets_dir}"
            }

        logger.info(f"Loading collection '{collection_id}' from {sheets_dir}")

        # Find all TSV files
        tsv_files = list(sheets_dir.glob("*.tsv"))
        logger.info(f"Found {len(tsv_files)} TSV files")

        # Load TSV tables
        tables_loaded = 0
        total_rows = 0

        for tsv_path in sorted(tsv_files):
            logger.info(f"  Loading {tsv_path.name}...")
            result = self._load_tsv_table(collection_id, tsv_path)
            if result["success"]:
                tables_loaded += 1
                total_rows += result["row_count"]

        # Load publications if directory exists
        pubs_dir = sheets_dir / "publications"
        publications_loaded = 0

        if pubs_dir.exists():
            logger.info(f"Loading publications from {pubs_dir}...")
            pub_result = self._load_publications(collection_id, pubs_dir)
            publications_loaded = pub_result.get("publications_loaded", 0)

        # Build cross-references
        refs_created = 0
        if publications_loaded > 0:
            logger.info("Building publication cross-references...")
            refs_created = self._build_publication_references(collection_id)

        # Register collection in database
        self._register_collection(
            collection_id=collection_id,
            directory_path=str(sheets_dir),
            table_count=tables_loaded,
            total_rows=total_rows
        )

        logger.info(f"Collection '{collection_id}' loaded successfully")

        return {
            "success": True,
            "collection_id": collection_id,
            "tables_loaded": tables_loaded,
            "total_rows": total_rows,
            "publications_loaded": publications_loaded,
            "references_created": refs_created
        }

    def _register_collection(
        self,
        collection_id: str,
        directory_path: str,
        table_count: int,
        total_rows: int
    ):
        """Register collection metadata in database."""
        self.conn.execute(
            """
            INSERT OR REPLACE INTO sheet_collections (
                collection_id, collection_name, directory_path,
                loaded_at, table_count, total_rows
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                collection_id,
                f"{collection_id.upper()} Extended Data",
                directory_path,
                datetime.now(),
                table_count,
                total_rows
            )
        )

    def _load_tsv_table(self, collection_id: str, tsv_path: Path) -> Dict:
        """
        Load single TSV file into database.

        Args:
            collection_id: Collection ID
            tsv_path: Path to TSV file

        Returns:
            Dict with loading result
        """
        self._connect()
        try:
            # Read TSV
            df = pd.read_csv(tsv_path, sep='\t', dtype=str, keep_default_na=False)

            if len(df) == 0:
                return {"success": True, "row_count": 0}

            # Infer entity type and table name
            entity_type = self._infer_entity_type(tsv_path.name)
            table_name = self._extract_table_name(tsv_path.name)
            table_id = f"{collection_id}_{table_name}"

            # Register table
            self._register_table(
                table_id=table_id,
                collection_id=collection_id,
                table_name=table_name,
                source_file=tsv_path.name,
                row_count=len(df),
                column_count=len(df.columns),
                columns=list(df.columns)
            )

            # Batch insert rows
            batch_size = 1000
            for batch_start in range(0, len(df), batch_size):
                batch_df = df.iloc[batch_start:batch_start + batch_size]
                self._insert_data_batch(
                    table_id=table_id,
                    entity_type=entity_type,
                    batch_df=batch_df,
                    row_offset=batch_start
                )

            logger.info(f"  Loaded {len(df)} rows from {tsv_path.name}")

            return {
                "success": True,
                "table_name": table_name,
                "row_count": len(df),
                "entity_type": entity_type
            }

        except Exception as e:
            logger.error(f"Error loading {tsv_path.name}: {e}")
            return {"success": False, "error": str(e)}

    def _register_table(
        self,
        table_id: str,
        collection_id: str,
        table_name: str,
        source_file: str,
        row_count: int,
        column_count: int,
        columns: List[str]
    ):
        """Register table metadata in database."""
        self.conn.execute(
            """
            INSERT OR REPLACE INTO sheet_tables (
                table_id, collection_id, table_name, source_file,
                row_count, column_count, columns_json, loaded_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                table_id,
                collection_id,
                table_name,
                source_file,
                row_count,
                column_count,
                json.dumps(columns),
                datetime.now()
            )
        )

    def _insert_data_batch(
        self,
        table_id: str,
        entity_type: str,
        batch_df: pd.DataFrame,
        row_offset: int
    ):
        """Insert batch of rows into sheet_data table."""
        for idx, row in batch_df.iterrows():
            row_dict = row.to_dict()

            # Extract entity ID and name
            entity_id, entity_name = self._extract_entity_id_and_name(row_dict, entity_type)

            # Build searchable text from all text columns
            searchable_text = self._build_searchable_text(row_dict)

            # Insert row
            self.conn.execute(
                """
                INSERT INTO sheet_data (
                    table_id, row_id, entity_id, entity_name, entity_type,
                    data_json, searchable_text
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    table_id,
                    row_offset + idx,
                    entity_id,
                    entity_name,
                    entity_type,
                    json.dumps(row_dict),
                    searchable_text
                )
            )

    def _infer_entity_type(self, filename: str) -> str:
        """
        Infer entity type from filename.

        Args:
            filename: TSV filename

        Returns:
            Entity type string
        """
        filename_lower = filename.lower()

        if "chemical" in filename_lower:
            return "chemical"
        elif "gene" in filename_lower or "protein" in filename_lower:
            return "gene"
        elif "strain" in filename_lower:
            return "strain"
        elif "publication" in filename_lower:
            return "publication"
        elif "pathway" in filename_lower:
            return "pathway"
        elif "assay" in filename_lower:
            return "assay"
        elif "biosample" in filename_lower:
            return "biosample"
        elif "medium" in filename_lower or "media" in filename_lower:
            return "medium"
        elif "ingredient" in filename_lower:
            return "ingredient"
        elif "taxon" in filename_lower or "genome" in filename_lower:
            return "taxon"
        else:
            return "unknown"

    def _extract_table_name(self, filename: str) -> str:
        """Extract table name from filename."""
        # Remove prefix like 'BER_CMM_Data_for_AI_' and suffix like '_extended.tsv'
        name = filename.replace(".tsv", "")
        name = re.sub(r"^BER_[A-Z]+_Data_for_AI_", "", name)
        name = re.sub(r"^BER_TEST_", "", name)
        name = name.replace("_extended", "")
        return name

    def _extract_entity_id_and_name(
        self,
        row_dict: Dict,
        entity_type: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract entity ID and name from row data.

        Args:
            row_dict: Row data as dictionary
            entity_type: Entity type

        Returns:
            Tuple of (entity_id, entity_name)
        """
        # Common ID column patterns
        id_columns = [
            f"{entity_type}_id",
            "id",
            "gene or protein id",
            "strain_id",
            "pathway_id",
            "assay_id",
            "URL"
        ]

        # Common name column patterns
        name_columns = [
            f"{entity_type}_name",
            "name",
            "annotation",
            "scientific_name",
            "pathway_name",
            "assay_name",
            "Title"
        ]

        # Find ID
        entity_id = None
        for col in id_columns:
            if col in row_dict and row_dict[col]:
                entity_id = row_dict[col]
                break

        # Find name
        entity_name = None
        for col in name_columns:
            if col in row_dict and row_dict[col]:
                entity_name = row_dict[col]
                break

        return entity_id, entity_name

    def _build_searchable_text(self, row_dict: Dict) -> str:
        """
        Build searchable text from all text columns.

        Args:
            row_dict: Row data

        Returns:
            Concatenated searchable text
        """
        text_parts = []
        for key, value in row_dict.items():
            if value and isinstance(value, str) and len(value.strip()) > 0:
                text_parts.append(value.strip())

        return " | ".join(text_parts)

    def _load_publications(self, collection_id: str, pubs_dir: Path) -> Dict:
        """
        Load all publication markdown files from directory.

        Args:
            collection_id: Collection ID
            pubs_dir: Path to publications directory

        Returns:
            Dict with loading result
        """
        md_files = list(pubs_dir.glob("*.md"))
        logger.info(f"  Found {len(md_files)} publication files")

        publications_loaded = 0
        for md_path in sorted(md_files):
            result = self._load_single_publication(collection_id, md_path)
            if result["success"]:
                publications_loaded += 1

        return {
            "success": True,
            "publications_loaded": publications_loaded
        }

    def _load_single_publication(self, collection_id: str, pub_path: Path) -> Dict:
        """
        Load single publication markdown file.

        Args:
            collection_id: Collection ID
            pub_path: Path to markdown file

        Returns:
            Dict with loading result
        """
        self._connect()
        try:
            # Read file
            full_text = pub_path.read_text(encoding='utf-8')

            # Extract publication ID from filename
            pub_id, pub_type = self._extract_publication_id(pub_path.name)

            # Count words
            word_count = len(full_text.split())

            # Insert into database
            self.conn.execute(
                """
                INSERT INTO sheet_publications (
                    collection_id, file_name, publication_id, publication_type,
                    full_text, word_count, loaded_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    collection_id,
                    pub_path.name,
                    pub_id,
                    pub_type,
                    full_text,
                    word_count,
                    datetime.now()
                )
            )

            return {
                "success": True,
                "publication_id": pub_id,
                "publication_type": pub_type
            }

        except Exception as e:
            logger.error(f"Error loading publication {pub_path.name}: {e}")
            return {"success": False, "error": str(e)}

    def _extract_publication_id(self, filename: str) -> Tuple[str, str]:
        """
        Extract publication ID and type from filename.

        Args:
            filename: Markdown filename

        Returns:
            Tuple of (publication_id, publication_type)

        Examples:
            PMID_24816778.md -> ('pmid:24816778', 'pmid')
            doi_10_1038-nature16174.md -> ('doi:10.1038/nature16174', 'doi')
            PMC6764073.md -> ('pmc:6764073', 'pmc')
        """
        # PMID pattern
        pmid_match = re.match(r'PMID_(\d+)\.md', filename)
        if pmid_match:
            return f"pmid:{pmid_match.group(1)}", "pmid"

        # DOI pattern
        doi_match = re.match(r'doi_(.+)\.md', filename)
        if doi_match:
            # Convert filename format back to DOI format
            # Example: "10_1038-nature16174" -> "10.1038/nature16174"
            doi = doi_match.group(1)
            # Replace underscores with dots, then hyphens with slashes
            doi = doi.replace('_', '.').replace('-', '/')
            return f"doi:{doi}", "doi"

        # PMC pattern
        pmc_match = re.match(r'PMC(\d+)\.md', filename)
        if pmc_match:
            return f"pmc:{pmc_match.group(1)}", "pmc"

        # Default: use filename without extension
        return filename.replace('.md', ''), 'unknown'

    def _build_publication_references(self, collection_id: str) -> int:
        """
        Build cross-references between entities and publications.

        Extracts DOI/PMID from URL columns in sheet_data and matches
        them to publications in sheet_publications.

        Args:
            collection_id: Collection ID

        Returns:
            Number of references created
        """
        # Get all publications for this collection
        pubs = self.conn.execute(
            """
            SELECT id, publication_id, publication_type
            FROM sheet_publications
            WHERE collection_id = ?
            """,
            (collection_id,)
        ).fetchall()

        if not pubs:
            return 0

        # Create lookup maps
        pub_map = {}  # Maps normalized ID to database ID
        for pub_id, pub_identifier, pub_type in pubs:
            # Store by identifier (e.g., 'pmid:24816778')
            pub_map[pub_identifier] = pub_id

        # Get all entities in this collection
        entities = self.conn.execute(
            """
            SELECT sd.entity_id, sd.table_id, sd.data_json
            FROM sheet_data sd
            JOIN sheet_tables st ON sd.table_id = st.table_id
            WHERE st.collection_id = ?
            """,
            (collection_id,)
        ).fetchall()

        refs_created = 0
        for entity_id, table_id, data_json_str in entities:
            data = json.loads(data_json_str)

            # Look for URL/DOI columns
            for col_name, col_value in data.items():
                if not col_value:
                    continue

                # Check if column looks like a URL or DOI reference
                if any(keyword in col_name.lower() for keyword in ['url', 'doi', 'download', 'reference']):
                    # Extract PMID, DOI, or PMC from URL
                    extracted_id = self._extract_pub_id_from_url(col_value)
                    if extracted_id and extracted_id in pub_map:
                        # Create reference
                        self.conn.execute(
                            """
                            INSERT INTO sheet_publication_references (
                                publication_id, table_id, entity_id, reference_column, reference_value
                            )
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (pub_map[extracted_id], table_id, entity_id, col_name, col_value)
                        )
                        refs_created += 1

        logger.info(f"  Created {refs_created} publication references")
        return refs_created

    def _extract_pub_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract publication ID from URL.

        Args:
            url: URL string

        Returns:
            Normalized publication ID or None
        """
        # PMID URLs
        pmid_match = re.search(r'pubmed\.ncbi\.nlm\.nih\.gov/(\d+)', url)
        if pmid_match:
            return f"pmid:{pmid_match.group(1)}"

        # PMC URLs
        pmc_match = re.search(r'pmc\.ncbi\.nlm\.nih\.gov/articles/PMC(\d+)', url)
        if pmc_match:
            return f"pmc:{pmc_match.group(1)}"

        # DOI URLs
        doi_match = re.search(r'doi\.org/(10\.\S+)', url)
        if doi_match:
            return f"doi:{doi_match.group(1)}"

        return None

    def validate_loading(self, collection_id: str) -> Dict:
        """
        Validate loaded data and return statistics.

        Args:
            collection_id: Collection ID to validate

        Returns:
            Dict with validation statistics
        """
        self._connect()

        # Get collection info
        collection = self.conn.execute(
            "SELECT table_count, total_rows FROM sheet_collections WHERE collection_id = ?",
            (collection_id,)
        ).fetchone()

        if not collection:
            return {"success": False, "error": "Collection not found"}

        # Count entities by type
        entity_counts = {}
        entity_types = self.conn.execute(
            """
            SELECT entity_type, COUNT(*) as count
            FROM sheet_data sd
            JOIN sheet_tables st ON sd.table_id = st.table_id
            WHERE st.collection_id = ?
            GROUP BY entity_type
            """,
            (collection_id,)
        ).fetchall()

        for entity_type, count in entity_types:
            entity_counts[entity_type] = count

        # Count publications
        pubs_count = self.conn.execute(
            "SELECT COUNT(*) FROM sheet_publications WHERE collection_id = ?",
            (collection_id,)
        ).fetchone()[0]

        # Count references
        refs_count = self.conn.execute(
            """
            SELECT COUNT(*)
            FROM sheet_publication_references spr
            JOIN sheet_tables st ON spr.table_id = st.table_id
            WHERE st.collection_id = ?
            """,
            (collection_id,)
        ).fetchone()[0]

        return {
            "success": True,
            "tables_loaded": collection[0],
            "total_rows": collection[1],
            "entity_counts": entity_counts,
            "publications_loaded": pubs_count,
            "references_created": refs_count
        }

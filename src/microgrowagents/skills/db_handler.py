"""
Database handler for skills framework.

Provides database validation, auto-initialization, and connection pooling.
"""

import os
from pathlib import Path
from typing import Optional
import duckdb


class DatabaseHandler:
    """
    Handle database validation and initialization for skills.

    Provides:
    - Database validation (check required tables exist)
    - Auto-initialization from data/raw/ if missing
    - Connection pooling

    Examples:
        >>> handler = DatabaseHandler()
        >>> if handler.validate():
        ...     conn = handler.get_connection()
    """

    # Required tables for skills to function
    REQUIRED_TABLES = [
        "media",
        "ingredients",
        "media_ingredients",
        "organisms",
        "chemical_properties",
        "kg_nodes",
        "kg_edges",
    ]

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database handler.

        Args:
            db_path: Path to DuckDB database file. If None, uses default.
        """
        if db_path is None:
            # Default to data/processed/microgrow.duckdb
            db_path = "data/processed/microgrow.duckdb"

        self.db_path = db_path
        self._connection = None

    def validate(self) -> bool:
        """
        Validate database exists and has required tables.

        Returns:
            True if database valid, False otherwise

        Examples:
            >>> handler = DatabaseHandler()
            >>> handler.validate()
            True
        """
        # Check if database file exists
        if not os.path.exists(self.db_path):
            # Try to auto-initialize
            return self._initialize_database()

        # Check if required tables exist
        try:
            conn = self.get_connection()
            tables = conn.execute(
                "SELECT table_name FROM information_schema.tables"
            ).fetchall()
            table_names = {table[0] for table in tables}

            missing_tables = [
                table for table in self.REQUIRED_TABLES
                if table not in table_names
            ]

            if missing_tables:
                # Try to auto-initialize
                return self._initialize_database()

            return True

        except Exception:
            return False

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """
        Get database connection (creates if needed).

        Returns:
            DuckDB connection

        Examples:
            >>> handler = DatabaseHandler()
            >>> conn = handler.get_connection()
            >>> result = conn.execute("SELECT COUNT(*) FROM kg_nodes").fetchone()
        """
        if self._connection is None:
            self._connection = duckdb.connect(self.db_path)

        return self._connection

    def _initialize_database(self) -> bool:
        """
        Auto-initialize database from data/raw/.

        Checks for required data files and loads them into DuckDB.

        Returns:
            True if initialization succeeded, False otherwise
        """
        # Check if data/raw/ directory exists
        data_dir = Path("data/raw")
        if not data_dir.exists():
            return False

        # Check for KG-Microbe files
        kg_nodes_file = data_dir / "merged-kg_nodes.tsv"
        kg_edges_file = data_dir / "merged-kg_edges.tsv"

        if not kg_nodes_file.exists() or not kg_edges_file.exists():
            # Missing KG-Microbe files
            return False

        try:
            # Create database directory if needed
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)

            # Get connection (creates database file)
            conn = self.get_connection()

            # Create schema
            from microgrowagents.database.schema import create_schema
            create_schema(conn)

            # Load KG-Microbe data
            print("Loading KG-Microbe nodes...")
            conn.execute(f"""
                COPY kg_nodes FROM '{kg_nodes_file}'
                (DELIMITER '\t', HEADER TRUE)
            """)

            print("Loading KG-Microbe edges...")
            conn.execute(f"""
                COPY kg_edges FROM '{kg_edges_file}'
                (DELIMITER '\t', HEADER TRUE)
            """)

            # Load media data if available
            media_file = data_dir / "mediadive_media.tsv"
            if media_file.exists():
                print("Loading media data...")
                conn.execute(f"""
                    COPY media FROM '{media_file}'
                    (DELIMITER '\t', HEADER TRUE)
                """)

            # Load ingredient properties if available
            props_file = data_dir / "mp_medium_ingredient_properties.csv"
            if props_file.exists():
                print("Loading ingredient properties...")
                # This requires custom loading logic
                # For now, skip - will be loaded by specific agents

            print("Database initialized successfully!")
            return True

        except Exception as e:
            print(f"Database initialization failed: {e}")
            return False

    def close(self):
        """
        Close database connection.

        Examples:
            >>> handler = DatabaseHandler()
            >>> conn = handler.get_connection()
            >>> handler.close()
        """
        if self._connection:
            self._connection.close()
            self._connection = None

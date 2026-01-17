"""
Initialize Database Utility Skill.

Sets up MicroGrow database from KG-Microbe data files.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from microgrowagents.skills.base_skill import BaseSkill, SkillMetadata, SkillParameter
from microgrowagents.skills.db_handler import DatabaseHandler


class InitializeDatabaseSkill(BaseSkill):
    """
    Initialize MicroGrow database from data files.

    Checks for KG-Microbe data files in data/raw/ and loads them into DuckDB.

    Creates tables:
    - kg_nodes (1.5M nodes)
    - kg_edges (5.1M edges)
    - media, ingredients, organisms
    - chemical_properties, ingredient_effects

    Examples:
        >>> skill = InitializeDatabaseSkill()
        >>> result = skill.run(output_format="markdown")
        >>> "success" in result.lower() or "initialized" in result.lower()
        True
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize skill.

        Args:
            db_path: Path to DuckDB database (optional)
        """
        super().__init__()
        self.db_path = db_path or Path("data/processed/microgrow.duckdb")

    def get_metadata(self) -> SkillMetadata:
        """
        Get skill metadata.

        Returns:
            SkillMetadata with parameters and examples
        """
        return SkillMetadata(
            name="initialize-database",
            description="Initialize MicroGrow database from KG-Microbe data files",
            category="utility",
            parameters=[
                SkillParameter(
                    name="force",
                    type="bool",
                    description="Force reinitialization even if database exists",
                    required=False,
                    default=False,
                ),
            ],
            examples=[
                "initialize-database",
                "initialize-database --force true",
            ],
            requires_database=False,  # This skill creates the database
            requires_internet=False,
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute database initialization.

        Args:
            force: Force reinitialization

        Returns:
            Result dictionary with initialization status
        """
        force = kwargs.get("force", False)

        # Check if database already exists
        if self.db_path.exists() and not force:
            return {
                "success": False,
                "error": f"Database already exists at {self.db_path}. Use force=True to reinitialize.",
            }

        # Check for required data files
        data_dir = Path("data/raw")
        required_files = {
            "kg_nodes": data_dir / "merged-kg_nodes.tsv",
            "kg_edges": data_dir / "merged-kg_edges.tsv",
        }

        missing_files = []
        for name, file_path in required_files.items():
            if not file_path.exists():
                missing_files.append(str(file_path))

        if missing_files:
            return {
                "success": False,
                "error": f"Missing required data files: {', '.join(missing_files)}",
            }

        # Initialize database
        handler = DatabaseHandler(db_path=str(self.db_path))

        try:
            success = handler._initialize_database()

            if not success:
                return {
                    "success": False,
                    "error": "Database initialization failed. Check logs for details.",
                }

            # Get table row counts
            conn = handler.get_connection()
            row_counts = {}

            for table in DatabaseHandler.REQUIRED_TABLES:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    row_counts[table] = count
                except Exception:
                    row_counts[table] = 0

            handler.close()

            # Format results
            return {
                "success": True,
                "data": {
                    "database_path": str(self.db_path),
                    "tables_created": len(row_counts),
                    "row_counts": row_counts,
                },
                "metadata": {
                    "initialization_method": "kg_microbe_tsv",
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Database initialization error: {str(e)}",
            }

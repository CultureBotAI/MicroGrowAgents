"""
Query Database Skill.

Wraps SQLAgent to run SQL queries on the database.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from microgrowagents.skills.base_skill import BaseSkill, SkillMetadata, SkillParameter
from microgrowagents.agents.sql_agent import SQLAgent


class QueryDatabaseSkill(BaseSkill):
    """
    Run SQL queries on the MicroGrow database.

    Uses SQLAgent to query:
    - Media and ingredients
    - Organism growth data
    - Chemical properties
    - KG-Microbe nodes and edges

    Examples:
        >>> skill = QueryDatabaseSkill()
        >>> result = skill.run(
        ...     query="SELECT name FROM media LIMIT 5",
        ...     output_format="markdown"
        ... )
        >>> "media" in result.lower() or "name" in result.lower()
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
        self._agent = None

    def get_metadata(self) -> SkillMetadata:
        """
        Get skill metadata.

        Returns:
            SkillMetadata with parameters and examples
        """
        return SkillMetadata(
            name="query-database",
            description="Run SQL queries on the MicroGrow database",
            category="simple",
            parameters=[
                SkillParameter(
                    name="query",
                    type="str",
                    description="SQL query to execute",
                    required=True,
                ),
                SkillParameter(
                    name="max_rows",
                    type="int",
                    description="Maximum rows to return",
                    required=False,
                    default=100,
                ),
            ],
            examples=[
                "query-database 'SELECT * FROM media LIMIT 5'",
                "query-database 'SELECT name, category FROM kg_nodes WHERE category LIKE \"%Chemical%\" LIMIT 10'",
                "query-database 'SELECT COUNT(*) FROM kg_edges'",
            ],
            requires_database=True,
            requires_internet=False,
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute SQL query.

        Args:
            query: SQL query string
            max_rows: Maximum rows to return

        Returns:
            Result dictionary with query results
        """
        # Get parameters
        query = kwargs.get("query")
        if not query:
            return {
                "success": False,
                "error": "Missing required parameter: query",
            }

        max_rows = kwargs.get("max_rows", 100)

        # Initialize agent if needed
        if self._agent is None:
            self._agent = SQLAgent(db_path=self.db_path)

        # Run query
        try:
            result = self._agent.run(query=query, max_rows=max_rows)

            if not result.get("success", False):
                return result

            # Transform result for skill output
            transformed = self._transform_result(result)
            return transformed

        except Exception as e:
            return {
                "success": False,
                "error": f"Database query failed: {str(e)}",
            }

    def _transform_result(self, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform agent result to skill output format.

        Args:
            agent_result: Result from SQLAgent

        Returns:
            Transformed result with formatted data
        """
        data = agent_result.get("data", {})
        df = data.get("dataframe")

        if df is None or df.empty:
            return {
                "success": True,
                "data": [],
                "metadata": {"row_count": 0},
            }

        # Convert DataFrame to list of dicts
        rows = df.to_dict(orient="records")

        return {
            "success": True,
            "data": rows,
            "metadata": {
                "row_count": len(rows),
                "column_count": len(df.columns),
            },
        }

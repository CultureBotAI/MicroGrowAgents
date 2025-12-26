"""
SQL Agent: Query DuckDB for media/ingredient data.

Capabilities:
- Execute SQL queries on the DuckDB database
- Natural language to SQL (simple pattern matching)
- Prebuilt query templates for common operations
- Result formatting as pandas DataFrame
"""

from typing import Any, Dict, Optional

import duckdb
import pandas as pd

from microgrowagents.agents.base_agent import BaseAgent
from microgrowagents.database.queries import QUERY_TEMPLATES


class SQLAgent(BaseAgent):
    """Agent for querying media/ingredient database."""

    def run(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute SQL query or convert natural language to SQL.

        Args:
            query: SQL query or natural language question
            params: Optional query parameters for parameterized queries
            max_rows: Maximum number of rows to return (default: 100)

        Returns:
            Dictionary with:
            - success: bool
            - data: pandas DataFrame (if successful)
            - sql: The executed SQL query
            - error: Error message (if failed)
            - row_count: Number of rows returned

        Examples:
            >>> agent = SQLAgent()
            >>> result = agent.run("SELECT * FROM media LIMIT 5")
            >>> result = agent.run("ingredients for LB medium")
            >>> result = agent.run("media by organism", params=["NCBITaxon:562"])
        """
        if not self.validate_database():
            return {"success": False, "error": "Database not found"}

        # Get optional parameters
        params = kwargs.get("params", [])
        max_rows = kwargs.get("max_rows", 100)

        # Try template matching first
        sql = self._match_template(query, params) or query

        # Add LIMIT if not present and max_rows specified
        if max_rows and "LIMIT" not in sql.upper():
            sql = f"{sql.rstrip(';')} LIMIT {max_rows}"

        try:
            conn = duckdb.connect(str(self.db_path), read_only=True)
            result_df = conn.execute(sql, params).fetchdf()
            conn.close()

            self.log(f"Query executed successfully: {len(result_df)} rows returned")

            return {
                "success": True,
                "data": result_df,
                "sql": sql,
                "row_count": len(result_df),
            }

        except Exception as e:
            self.log(f"Query failed: {str(e)}", level="ERROR")
            return {"success": False, "error": str(e), "sql": sql}

    def _match_template(self, query: str, params: list) -> Optional[str]:
        """
        Match natural language to SQL template.

        Args:
            query: Natural language query
            params: Query parameters

        Returns:
            SQL query string or None if no match
        """
        lower = query.lower().strip()

        # Pattern matching for common queries
        if "ingredients for" in lower or "ingredients by medium" in lower:
            return QUERY_TEMPLATES["ingredients_by_medium"]

        elif "media for organism" in lower or "media by organism" in lower:
            return QUERY_TEMPLATES["media_by_organism"]

        elif "similar media" in lower:
            return QUERY_TEMPLATES["similar_media"]

        elif "organisms for medium" in lower or "organisms by medium" in lower:
            return QUERY_TEMPLATES["organisms_for_medium"]

        elif "ingredient properties" in lower or "properties of" in lower:
            return QUERY_TEMPLATES["ingredient_properties"]

        elif "ingredient effects" in lower or "effects of" in lower:
            return QUERY_TEMPLATES["ingredient_effects"]

        elif "media by ph" in lower or "ph range" in lower:
            return QUERY_TEMPLATES["media_by_ph_range"]

        elif "search media" in lower:
            return QUERY_TEMPLATES["search_media_by_name"]

        elif "search ingredient" in lower:
            return QUERY_TEMPLATES["search_ingredients_by_name"]

        return None

    def get_media_info(self, media_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a medium.

        Args:
            media_id: Media ID (e.g., "mediadive.medium:123")

        Returns:
            Dictionary with media information or None if not found
        """
        result = self.run(
            "SELECT * FROM media WHERE id = ?",
            params=[media_id],
        )

        if result["success"] and len(result["data"]) > 0:
            return result["data"].iloc[0].to_dict()
        return None

    def get_ingredients_for_media(self, media_id: str) -> pd.DataFrame:
        """
        Get all ingredients for a given medium.

        Args:
            media_id: Media ID

        Returns:
            DataFrame with ingredients and concentrations
        """
        result = self.run(
            QUERY_TEMPLATES["ingredients_by_medium"],
            params=[media_id],
        )

        if result["success"]:
            return result["data"]
        return pd.DataFrame()

    def search_media(self, search_term: str) -> pd.DataFrame:
        """
        Search for media by name.

        Args:
            search_term: Search term (supports wildcards %)

        Returns:
            DataFrame with matching media
        """
        result = self.run(
            QUERY_TEMPLATES["search_media_by_name"],
            params=[f"%{search_term}%"],
        )

        if result["success"]:
            return result["data"]
        return pd.DataFrame()

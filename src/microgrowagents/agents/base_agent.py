"""
Base agent class following kg-microbe Transform pattern.

All agents inherit from BaseAgent and implement run() method.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional


class BaseAgent(ABC):
    """
    Base class for all MicroGrowAgents agents.

    Follows the Transform pattern from kg-microbe for consistency.
    All agents must implement the run() method to execute their tasks.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize base agent.

        Args:
            db_path: Path to DuckDB database. If None, uses default path.
        """
        self.db_path = db_path or Path("data/processed/microgrow.duckdb")
        self.results: Dict[str, Any] = {}

    @abstractmethod
    def run(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute agent task.

        Args:
            query: Query or task description
            **kwargs: Additional arguments specific to agent

        Returns:
            Dictionary with results and metadata
        """
        pass

    def log(self, message: str, level: str = "INFO") -> None:
        """
        Log agent activity.

        Args:
            message: Log message
            level: Log level (INFO, WARNING, ERROR)
        """
        print(f"[{self.__class__.__name__}] [{level}] {message}")

    def validate_database(self) -> bool:
        """
        Check if database exists.

        Returns:
            True if database exists, False otherwise
        """
        if not self.db_path.exists():
            self.log(
                f"Database not found at {self.db_path}. Run 'python run.py load-data' first.",
                level="ERROR",
            )
            return False
        return True

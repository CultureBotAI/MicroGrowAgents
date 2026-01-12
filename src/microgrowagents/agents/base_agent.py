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

    def __init__(
        self,
        db_path: Optional[Path] = None,
        enable_provenance: bool = True
    ):
        """
        Initialize base agent.

        Args:
            db_path: Path to DuckDB database. If None, uses default path.
            enable_provenance: Enable automatic provenance tracking
        """
        self.db_path = db_path or Path("data/processed/microgrow.duckdb")
        self.results: Dict[str, Any] = {}
        self.enable_provenance = enable_provenance
        self._tracker = None

        # Initialize provenance tracker
        if enable_provenance:
            try:
                from microgrowagents.provenance.tracker import get_tracker
                self._tracker = get_tracker(db_path=self.db_path)
            except Exception as e:
                print(f"Warning: Provenance tracking disabled: {e}")
                self.enable_provenance = False

    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Public entry point with provenance tracking.

        Args:
            query: Query or task description
            **kwargs: Additional arguments specific to agent

        Returns:
            Dictionary with results and metadata
        """
        return self._run_with_provenance(query, **kwargs)

    def _run_with_provenance(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Wrapper for run() with automatic provenance tracking.

        Args:
            query: Query or task description
            **kwargs: Additional arguments specific to agent

        Returns:
            Dictionary with results and metadata
        """
        if not self.enable_provenance or not self._tracker:
            return self.run(query, **kwargs)

        parent_session_id = kwargs.pop("_parent_session_id", None)
        session_id = self._tracker.start_session(
            agent_type=self.__class__.__name__,
            query=query,
            kwargs=kwargs,
            parent_session_id=parent_session_id,
        )

        try:
            result = self.run(query, **kwargs)
            self._tracker.end_session(success=True, result=result)
            return result
        except Exception as e:
            self._tracker.end_session(success=False, error=str(e))
            raise

    @abstractmethod
    def run(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute agent task. Implement in subclass.

        Args:
            query: Query or task description
            **kwargs: Additional arguments specific to agent

        Returns:
            Dictionary with results and metadata
        """
        pass

    def log(self, message: str, level: str = "INFO") -> None:
        """
        Log agent activity with provenance tracking.

        Args:
            message: Log message
            level: Log level (INFO, WARNING, ERROR)
        """
        print(f"[{self.__class__.__name__}] [{level}] {message}")

        # Record to provenance if enabled
        if self.enable_provenance and self._tracker:
            self._tracker.record_event(
                "log",
                f"log_{level.lower()}",
                {"message": message, "level": level}
            )

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

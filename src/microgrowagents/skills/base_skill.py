"""
Base class for all MicroGrowAgents skills.

Provides common functionality for database validation, output formatting,
error handling, and evidence citation formatting.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import time
import json


@dataclass
class SkillParameter:
    """
    Parameter definition for a skill.

    Attributes:
        name: Parameter name
        type: Parameter type (str, int, bool, etc.)
        description: Parameter description
        required: Whether parameter is required
        default: Default value if not required
        options: List of valid options (for enum-like params)

    Examples:
        >>> param = SkillParameter(
        ...     name="query",
        ...     type="str",
        ...     description="Ingredient name or formula",
        ...     required=True
        ... )
        >>> param.name
        'query'
    """
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    options: List[str] = field(default_factory=list)


@dataclass
class SkillMetadata:
    """
    Metadata for a skill.

    Attributes:
        name: Skill name (kebab-case for CLI)
        description: Short description
        category: Skill category (simple, workflow, utility)
        parameters: List of parameter definitions
        examples: List of usage examples
        requires_database: Whether skill needs database
        requires_internet: Whether skill needs internet
        version: Skill version

    Examples:
        >>> metadata = SkillMetadata(
        ...     name="predict-concentration",
        ...     description="Predict concentration ranges",
        ...     category="simple",
        ...     parameters=[],
        ...     examples=["predict-concentration glucose"]
        ... )
        >>> metadata.category
        'simple'
    """
    name: str
    description: str
    category: str  # simple, workflow, utility
    parameters: List[SkillParameter]
    examples: List[str]
    requires_database: bool = True
    requires_internet: bool = False
    version: str = "1.0.0"


class BaseSkill(ABC):
    """
    Base class for all skills.

    Provides common functionality:
    - Database validation with auto-initialization
    - Output formatting (markdown + JSON)
    - Error handling with user-friendly messages
    - Evidence citation formatting (DOI/PMID links)

    Subclasses must implement:
    - get_metadata() - Return SkillMetadata
    - execute() - Implement skill logic

    Examples:
        >>> class ExampleSkill(BaseSkill):
        ...     def get_metadata(self) -> SkillMetadata:
        ...         return SkillMetadata(
        ...             name="example",
        ...             description="Example skill",
        ...             category="simple",
        ...             parameters=[],
        ...             examples=[]
        ...         )
        ...     def execute(self, **kwargs) -> Dict[str, Any]:
        ...         return {"success": True, "data": {}}
    """

    def __init__(self):
        """Initialize base skill."""
        self._db_handler = None
        self._start_time = None

    @abstractmethod
    def get_metadata(self) -> SkillMetadata:
        """
        Get skill metadata.

        Returns:
            SkillMetadata with name, description, parameters, etc.
        """
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute skill logic.

        Must return dict with:
        - success: bool
        - data: Any (skill-specific data)
        - metadata: Optional[Dict] (execution metadata)
        - evidence: Optional[List[Dict]] (citations)
        - error: Optional[str] (if success=False)

        Args:
            **kwargs: Skill-specific parameters

        Returns:
            Result dictionary
        """
        pass

    def run(self, output_format: str = "markdown", **kwargs) -> str:
        """
        Main entry point for skill execution.

        Workflow:
        1. Validate database (if required)
        2. Execute skill logic
        3. Format output
        4. Return formatted result

        Args:
            output_format: Output format ("markdown", "json", "both")
            **kwargs: Skill-specific parameters

        Returns:
            Formatted output string

        Examples:
            >>> skill = ExampleSkill()
            >>> result = skill.run(query="glucose")
        """
        self._start_time = time.time()
        metadata = self.get_metadata()

        # Validate database if required
        if metadata.requires_database:
            db_valid = self._validate_database()
            if not db_valid:
                return self._format_error(
                    "Database not initialized. Run 'initialize-database' first."
                )

        # Execute skill logic
        try:
            result = self.execute(**kwargs)
        except Exception as e:
            return self._format_error(str(e))

        # Format output
        if not result.get("success", False):
            return self._format_error(result.get("error", "Unknown error"))

        return self._format_output(result, output_format)

    def _validate_database(self) -> bool:
        """
        Validate database is available.

        Returns:
            True if database valid, False otherwise
        """
        # Import here to avoid circular imports
        from microgrowagents.skills.db_handler import DatabaseHandler

        if self._db_handler is None:
            self._db_handler = DatabaseHandler()

        return self._db_handler.validate()

    def _format_output(self, result: Dict[str, Any], output_format: str) -> str:
        """
        Format skill output.

        Args:
            result: Skill result dictionary
            output_format: Output format ("markdown", "json", "both")

        Returns:
            Formatted output string
        """
        if output_format == "json":
            return self._format_json(result)
        elif output_format == "both":
            markdown = self._format_markdown(result)
            json_output = self._format_json(result)
            return f"{markdown}\n\n---\n\nJSON Output:\n```json\n{json_output}\n```"
        else:  # markdown (default)
            return self._format_markdown(result)

    def _format_markdown(self, result: Dict[str, Any]) -> str:
        """
        Format result as markdown.

        Args:
            result: Skill result dictionary

        Returns:
            Markdown formatted string
        """
        # Import here to avoid circular imports
        from microgrowagents.skills.formatters.markdown import MarkdownFormatter

        formatter = MarkdownFormatter()
        output = formatter.format(result)

        # Add execution metadata
        if self._start_time:
            elapsed = time.time() - self._start_time
            output += f"\n\n*Execution time: {elapsed:.2f}s*"

        return output

    def _format_json(self, result: Dict[str, Any]) -> str:
        """
        Format result as JSON.

        Args:
            result: Skill result dictionary

        Returns:
            JSON formatted string
        """
        # Add execution metadata
        output_dict = result.copy()
        if self._start_time:
            if "metadata" not in output_dict:
                output_dict["metadata"] = {}
            output_dict["metadata"]["execution_time"] = time.time() - self._start_time

        return json.dumps(output_dict, indent=2)

    def _format_error(self, error_message: str) -> str:
        """
        Format error message with helpful context.

        Args:
            error_message: Error message

        Returns:
            Formatted error message
        """
        metadata = self.get_metadata()

        error_output = f"# Error: {metadata.name}\n\n"
        error_output += f"**Error:** {error_message}\n\n"

        # Add helpful context
        if "database" in error_message.lower():
            error_output += "**Troubleshooting:**\n"
            error_output += "- Run `initialize-database` to set up the database\n"
            error_output += "- Ensure data files exist in `data/raw/`\n"
            error_output += "- Check database permissions\n"
        elif "parameter" in error_message.lower() or "argument" in error_message.lower():
            error_output += "**Usage Examples:**\n"
            for example in metadata.examples[:3]:
                error_output += f"- `{example}`\n"

        return error_output

    def _format_citations(self, evidence: List[Dict[str, Any]]) -> str:
        """
        Format evidence citations as markdown links.

        Args:
            evidence: List of evidence dictionaries with DOI/PMID/KG nodes

        Returns:
            Markdown formatted citations

        Examples:
            >>> skill = ExampleSkill()
            >>> evidence = [
            ...     {"doi": "10.1021/acs.jced.8b00201", "confidence": 0.95}
            ... ]
            >>> citations = skill._format_citations(evidence)
        """
        if not evidence:
            return ""

        citations = "\n\n## References\n\n"

        for i, item in enumerate(evidence, 1):
            if "doi" in item and item["doi"]:
                doi = item["doi"]
                if not doi.startswith("http"):
                    doi = f"https://doi.org/{doi}"
                citations += f"{i}. [{doi}]({doi})"

                if "confidence" in item:
                    citations += f" (confidence: {item['confidence']:.2%})"

                citations += "\n"

            elif "pmid" in item and item["pmid"]:
                pmid = item["pmid"]
                url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                citations += f"{i}. [PMID:{pmid}]({url})\n"

            elif "kg_node" in item and item["kg_node"]:
                node_id = item["kg_node"]
                citations += f"{i}. KG Node: `{node_id}`\n"

        return citations

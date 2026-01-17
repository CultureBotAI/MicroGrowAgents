"""
Markdown formatter for skill output.

Formats skill results as markdown tables with DOI citations and metadata.
"""

from typing import Any, Dict, List, Optional


class MarkdownFormatter:
    """
    Format skill results as markdown.

    Provides:
    - Table generation from list of dictionaries
    - DOI/PMID citation formatting
    - Metadata formatting (execution time, data sources)

    Examples:
        >>> formatter = MarkdownFormatter()
        >>> result = {
        ...     "success": True,
        ...     "data": [{"name": "glucose", "concentration": "10 g/L"}]
        ... }
        >>> output = formatter.format(result)
    """

    def format(self, result: Dict[str, Any]) -> str:
        """
        Format skill result as markdown.

        Args:
            result: Skill result dictionary with "data", "metadata", "evidence"

        Returns:
            Markdown formatted string

        Examples:
            >>> formatter = MarkdownFormatter()
            >>> result = {"success": True, "data": {"value": 42}}
            >>> output = formatter.format(result)
        """
        if not result.get("success", False):
            return self._format_error(result)

        output = ""

        # Format main data
        data = result.get("data", {})

        if isinstance(data, list) and len(data) > 0:
            # List of dictionaries -> table
            output += self._format_table(data)
        elif isinstance(data, dict):
            # Single dictionary -> key-value pairs
            output += self._format_dict(data)
        else:
            # Simple value
            output += str(data)

        # Format evidence citations
        evidence = result.get("evidence", [])
        if evidence:
            output += self._format_evidence(evidence)

        # Format metadata
        metadata = result.get("metadata", {})
        if metadata:
            output += self._format_metadata(metadata)

        return output

    def _format_table(self, data: List[Dict[str, Any]]) -> str:
        """
        Format list of dictionaries as markdown table.

        Args:
            data: List of dictionaries with same keys

        Returns:
            Markdown table string

        Examples:
            >>> formatter = MarkdownFormatter()
            >>> data = [
            ...     {"name": "glucose", "conc": "10 g/L"},
            ...     {"name": "NaCl", "conc": "5 g/L"}
            ... ]
            >>> table = formatter._format_table(data)
        """
        if not data:
            return ""

        # Get columns from first row
        columns = list(data[0].keys())

        # Build header
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join(["---"] * len(columns)) + " |"

        # Build rows
        rows = []
        for row in data:
            row_values = [self._format_cell_value(row.get(col, "")) for col in columns]
            rows.append("| " + " | ".join(row_values) + " |")

        return "\n".join([header, separator] + rows) + "\n"

    def _format_dict(self, data: Dict[str, Any]) -> str:
        """
        Format dictionary as key-value pairs.

        Args:
            data: Dictionary to format

        Returns:
            Markdown formatted key-value pairs

        Examples:
            >>> formatter = MarkdownFormatter()
            >>> data = {"name": "glucose", "formula": "C6H12O6"}
            >>> output = formatter._format_dict(data)
        """
        output = ""
        for key, value in data.items():
            # Format key (convert snake_case to Title Case)
            formatted_key = key.replace("_", " ").title()

            # Format value
            if isinstance(value, dict):
                output += f"\n### {formatted_key}\n\n"
                output += self._format_dict(value)
            elif isinstance(value, list):
                output += f"**{formatted_key}:** "
                if len(value) > 0 and isinstance(value[0], dict):
                    output += "\n\n" + self._format_table(value)
                else:
                    output += ", ".join(str(v) for v in value) + "\n\n"
            else:
                output += f"**{formatted_key}:** {value}\n\n"

        return output

    def _format_cell_value(self, value: Any) -> str:
        """
        Format a cell value for markdown table.

        Handles special cases:
        - None → empty string
        - Lists → comma-separated
        - Dicts → JSON representation
        - DOI → markdown link

        Args:
            value: Cell value

        Returns:
            Formatted string
        """
        if value is None:
            return ""

        if isinstance(value, list):
            return ", ".join(str(v) for v in value)

        if isinstance(value, dict):
            # For nested dicts, show compact representation
            return "; ".join(f"{k}: {v}" for k, v in value.items())

        value_str = str(value)

        # Convert DOI to link
        if value_str.startswith("10.") and "/" in value_str:
            return f"[{value_str}](https://doi.org/{value_str})"

        # Handle URLs
        if value_str.startswith("http"):
            # Extract readable text from URL if possible
            return f"[Link]({value_str})"

        return value_str

    def _format_evidence(self, evidence: List[Dict[str, Any]]) -> str:
        """
        Format evidence citations.

        Args:
            evidence: List of evidence dictionaries with DOI/PMID/KG nodes

        Returns:
            Markdown formatted citations

        Examples:
            >>> formatter = MarkdownFormatter()
            >>> evidence = [
            ...     {"doi": "10.1021/acs.jced.8b00201", "confidence": 0.95},
            ...     {"pmid": "12345678"}
            ... ]
            >>> citations = formatter._format_evidence(evidence)
        """
        if not evidence:
            return ""

        output = "\n\n## References\n\n"

        for i, item in enumerate(evidence, 1):
            if "doi" in item and item["doi"]:
                doi = item["doi"]
                # Ensure DOI is a full URL
                if not doi.startswith("http"):
                    doi_url = f"https://doi.org/{doi}"
                else:
                    doi_url = doi
                    doi = doi.split("/")[-1] if "/" in doi else doi

                output += f"{i}. [{doi}]({doi_url})"

                if "confidence" in item and item["confidence"] is not None:
                    output += f" (confidence: {item['confidence']:.1%})"

                if "snippet" in item and item["snippet"]:
                    output += f"\n   > {item['snippet']}"

                output += "\n"

            elif "pmid" in item and item["pmid"]:
                pmid = item["pmid"]
                url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                output += f"{i}. [PMID:{pmid}]({url})\n"

            elif "kg_node" in item and item["kg_node"]:
                node_id = item["kg_node"]
                label = item.get("kg_label", node_id)
                output += f"{i}. KG Node: `{node_id}` ({label})\n"

        return output

    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        Format execution metadata.

        Args:
            metadata: Metadata dictionary (execution_time, data_sources, etc.)

        Returns:
            Markdown formatted metadata

        Examples:
            >>> formatter = MarkdownFormatter()
            >>> metadata = {
            ...     "execution_time": 1.23,
            ...     "data_sources": ["kg_microbe", "mediadive"]
            ... }
            >>> output = formatter._format_metadata(metadata)
        """
        if not metadata:
            return ""

        output = "\n\n---\n\n*Metadata:*\n\n"

        for key, value in metadata.items():
            formatted_key = key.replace("_", " ").title()

            if key == "execution_time":
                output += f"- {formatted_key}: {value:.2f}s\n"
            elif key == "data_sources" and isinstance(value, list):
                output += f"- {formatted_key}: {', '.join(value)}\n"
            else:
                output += f"- {formatted_key}: {value}\n"

        return output

    def _format_error(self, result: Dict[str, Any]) -> str:
        """
        Format error result.

        Args:
            result: Result dictionary with error message

        Returns:
            Formatted error message
        """
        error = result.get("error", "Unknown error")
        return f"**Error:** {error}\n"

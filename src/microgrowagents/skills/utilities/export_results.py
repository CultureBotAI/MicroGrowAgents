"""
Export Results Utility Skill.

Export skill results to CSV or JSON files.
"""

import json
import csv
from typing import Any, Dict, List, Optional
from pathlib import Path

from microgrowagents.skills.base_skill import BaseSkill, SkillMetadata, SkillParameter


class ExportResultsSkill(BaseSkill):
    """
    Export skill results to files.

    Supports:
    - CSV export (for tabular data)
    - JSON export (for all data types)
    - Automatic flattening of nested structures

    Examples:
        >>> skill = ExportResultsSkill()
        >>> data = {"data": [{"name": "glucose", "conc": "10 g/L"}]}
        >>> result = skill.run(
        ...     results=data,
        ...     output_path="results.csv",
        ...     format="csv"
        ... )
        >>> result["success"]
        True
    """

    def __init__(self):
        """Initialize skill."""
        super().__init__()

    def get_metadata(self) -> SkillMetadata:
        """
        Get skill metadata.

        Returns:
            SkillMetadata with parameters and examples
        """
        return SkillMetadata(
            name="export-results",
            description="Export skill results to CSV or JSON file",
            category="utility",
            parameters=[
                SkillParameter(
                    name="results",
                    type="dict",
                    description="Skill results dictionary to export",
                    required=True,
                ),
                SkillParameter(
                    name="output_path",
                    type="str",
                    description="Output file path (extension determines format if format not specified)",
                    required=True,
                ),
                SkillParameter(
                    name="format",
                    type="str",
                    description="Export format: 'csv' or 'json' (auto-detected from path if not specified)",
                    required=False,
                    options=["csv", "json"],
                ),
                SkillParameter(
                    name="flatten",
                    type="bool",
                    description="Flatten nested structures (for CSV export)",
                    required=False,
                    default=True,
                ),
            ],
            examples=[
                "export-results --results <data> --output_path results.csv",
                "export-results --results <data> --output_path results.json",
                "export-results --results <data> --output_path output.csv --format csv --flatten true",
            ],
            requires_database=False,
            requires_internet=False,
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute export.

        Args:
            results: Results dictionary to export
            output_path: Output file path
            format: Export format (csv or json)
            flatten: Flatten nested structures

        Returns:
            Result dictionary with export status
        """
        results = kwargs.get("results")
        if not results:
            return {
                "success": False,
                "error": "Missing required parameter: results",
            }

        output_path = kwargs.get("output_path")
        if not output_path:
            return {
                "success": False,
                "error": "Missing required parameter: output_path",
            }

        # Auto-detect format from extension
        export_format = kwargs.get("format")
        if not export_format:
            output_path_obj = Path(output_path)
            ext = output_path_obj.suffix.lower()
            if ext == ".csv":
                export_format = "csv"
            elif ext == ".json":
                export_format = "json"
            else:
                return {
                    "success": False,
                    "error": f"Cannot auto-detect format from extension '{ext}'. Specify format parameter.",
                }

        flatten = kwargs.get("flatten", True)

        # Extract data from results
        data = results.get("data", results)

        # Export
        try:
            if export_format == "csv":
                success, message = self._export_csv(data, output_path, flatten)
            elif export_format == "json":
                success, message = self._export_json(results, output_path)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported format: {export_format}",
                }

            if not success:
                return {
                    "success": False,
                    "error": message,
                }

            return {
                "success": True,
                "data": {
                    "output_path": output_path,
                    "format": export_format,
                    "message": message,
                },
                "metadata": {
                    "export_format": export_format,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Export failed: {str(e)}",
            }

    def _export_csv(
        self, data: Any, output_path: str, flatten: bool
    ) -> tuple[bool, str]:
        """
        Export to CSV.

        Args:
            data: Data to export
            output_path: Output file path
            flatten: Flatten nested structures

        Returns:
            (success, message) tuple
        """
        # Convert to list of dicts if needed
        if isinstance(data, dict):
            # Single dict -> list with one item
            data = [data]
        elif not isinstance(data, list):
            return False, "CSV export requires list or dict data"

        if not data:
            return False, "No data to export"

        # Flatten if requested
        if flatten:
            data = [self._flatten_dict(row) for row in data]

        # Get field names from first row
        fieldnames = list(data[0].keys())

        # Write CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        return True, f"Exported {len(data)} rows to {output_path}"

    def _export_json(self, data: Any, output_path: str) -> tuple[bool, str]:
        """
        Export to JSON.

        Args:
            data: Data to export
            output_path: Output file path

        Returns:
            (success, message) tuple
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return True, f"Exported to {output_path}"

    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """
        Flatten nested dictionary.

        Args:
            d: Dictionary to flatten
            parent_key: Parent key prefix
            sep: Separator for nested keys

        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k

            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert list to comma-separated string
                if v and isinstance(v[0], dict):
                    # List of dicts -> JSON string
                    items.append((new_key, json.dumps(v)))
                else:
                    # Simple list -> comma-separated
                    items.append((new_key, ', '.join(str(x) for x in v)))
            else:
                items.append((new_key, v))

        return dict(items)

"""
JSON schema validation for skill output.

Ensures skill output conforms to expected structure.
"""

from typing import Any, Dict, List, Optional


class JSONSchemaValidator:
    """
    Validate skill output against JSON schema.

    Ensures output has required fields:
    - success: bool
    - data: Any
    - metadata: Optional[Dict]
    - evidence: Optional[List[Dict]]
    - error: Optional[str]

    Examples:
        >>> validator = JSONSchemaValidator()
        >>> result = {"success": True, "data": {}}
        >>> validator.validate(result)
        True
    """

    REQUIRED_FIELDS = ["success"]
    OPTIONAL_FIELDS = ["data", "metadata", "evidence", "error"]

    def validate(self, result: Dict[str, Any]) -> bool:
        """
        Validate skill output structure.

        Args:
            result: Skill output dictionary

        Returns:
            True if valid, False otherwise

        Examples:
            >>> validator = JSONSchemaValidator()
            >>> result = {"success": True, "data": {"value": 42}}
            >>> validator.validate(result)
            True
        """
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in result:
                return False

        # Validate field types
        if not isinstance(result["success"], bool):
            return False

        # If success=False, error should be present
        if not result["success"] and "error" not in result:
            return False

        # Validate optional fields if present
        if "metadata" in result and not isinstance(result["metadata"], dict):
            return False

        if "evidence" in result and not isinstance(result["evidence"], list):
            return False

        return True

    def get_errors(self, result: Dict[str, Any]) -> List[str]:
        """
        Get list of validation errors.

        Args:
            result: Skill output dictionary

        Returns:
            List of error messages

        Examples:
            >>> validator = JSONSchemaValidator()
            >>> result = {"data": {}}
            >>> errors = validator.get_errors(result)
            >>> "success" in errors[0]
            True
        """
        errors = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in result:
                errors.append(f"Missing required field: {field}")

        if "success" in result and not isinstance(result["success"], bool):
            errors.append("Field 'success' must be boolean")

        if "success" in result and not result["success"] and "error" not in result:
            errors.append("Field 'error' required when success=False")

        if "metadata" in result and not isinstance(result["metadata"], dict):
            errors.append("Field 'metadata' must be dictionary")

        if "evidence" in result and not isinstance(result["evidence"], list):
            errors.append("Field 'evidence' must be list")

        return errors

    def validate_evidence(self, evidence: List[Dict[str, Any]]) -> bool:
        """
        Validate evidence citations structure.

        Each evidence item should have at least one of:
        - doi: str
        - pmid: str
        - kg_node: str

        Args:
            evidence: List of evidence dictionaries

        Returns:
            True if valid, False otherwise

        Examples:
            >>> validator = JSONSchemaValidator()
            >>> evidence = [{"doi": "10.1021/acs.jced.8b00201"}]
            >>> validator.validate_evidence(evidence)
            True
        """
        if not isinstance(evidence, list):
            return False

        for item in evidence:
            if not isinstance(item, dict):
                return False

            # Must have at least one citation field
            has_citation = any(
                key in item and item[key]
                for key in ["doi", "pmid", "kg_node"]
            )

            if not has_citation:
                return False

        return True

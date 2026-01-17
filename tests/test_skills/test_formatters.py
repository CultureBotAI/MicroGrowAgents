"""
Tests for output formatters.
"""

import pytest
from microgrowagents.skills.formatters.markdown import MarkdownFormatter
from microgrowagents.skills.formatters.json_schema import JSONSchemaValidator


class TestMarkdownFormatter:
    """Tests for MarkdownFormatter."""

    def test_format_table(self):
        """Test table formatting."""
        formatter = MarkdownFormatter()
        data = [
            {"name": "glucose", "concentration": "10 g/L"},
            {"name": "NaCl", "concentration": "5 g/L"},
        ]

        table = formatter._format_table(data)

        assert "| name |" in table
        assert "| concentration |" in table
        assert "| glucose |" in table
        assert "| NaCl |" in table
        assert "| --- |" in table  # Markdown separator

    def test_format_dict(self):
        """Test dictionary formatting."""
        formatter = MarkdownFormatter()
        data = {
            "ingredient_name": "glucose",
            "formula": "C6H12O6",
            "molecular_weight": 180.16,
        }

        output = formatter._format_dict(data)

        assert "Ingredient Name" in output
        assert "glucose" in output
        assert "C6H12O6" in output

    def test_format_evidence(self):
        """Test evidence formatting."""
        formatter = MarkdownFormatter()
        evidence = [
            {"doi": "10.1021/test", "confidence": 0.90},
            {"pmid": "12345678"},
        ]

        output = formatter._format_evidence(evidence)

        assert "References" in output
        assert "doi.org/10.1021/test" in output
        assert "pubmed.ncbi.nlm.nih.gov/12345678" in output
        assert "90" in output  # confidence percentage

    def test_format_metadata(self):
        """Test metadata formatting."""
        formatter = MarkdownFormatter()
        metadata = {
            "execution_time": 1.234,
            "data_sources": ["kg_microbe", "mediadive"],
        }

        output = formatter._format_metadata(metadata)

        assert "Metadata" in output
        assert "1.23s" in output
        assert "kg_microbe" in output

    def test_format_cell_value_doi(self):
        """Test DOI cell value formatting."""
        formatter = MarkdownFormatter()
        doi = "10.1021/acs.jced.8b00201"

        formatted = formatter._format_cell_value(doi)

        assert "doi.org" in formatted
        assert doi in formatted
        assert "[" in formatted and "]" in formatted

    def test_format_cell_value_list(self):
        """Test list cell value formatting."""
        formatter = MarkdownFormatter()
        value = ["item1", "item2", "item3"]

        formatted = formatter._format_cell_value(value)

        assert "item1" in formatted
        assert "," in formatted

    def test_format_success_result(self):
        """Test formatting successful result."""
        formatter = MarkdownFormatter()
        result = {
            "success": True,
            "data": [{"name": "glucose", "conc": "10 g/L"}],
        }

        output = formatter.format(result)

        assert "glucose" in output
        assert "10 g/L" in output

    def test_format_error_result(self):
        """Test formatting error result."""
        formatter = MarkdownFormatter()
        result = {
            "success": False,
            "error": "Test error message",
        }

        output = formatter.format(result)

        assert "Error" in output
        assert "Test error message" in output


class TestJSONSchemaValidator:
    """Tests for JSONSchemaValidator."""

    def test_validate_success(self):
        """Test valid result."""
        validator = JSONSchemaValidator()
        result = {
            "success": True,
            "data": {"value": 42},
        }

        assert validator.validate(result) is True

    def test_validate_missing_success(self):
        """Test result missing success field."""
        validator = JSONSchemaValidator()
        result = {"data": {}}

        assert validator.validate(result) is False

    def test_validate_invalid_success_type(self):
        """Test result with invalid success type."""
        validator = JSONSchemaValidator()
        result = {"success": "true"}

        assert validator.validate(result) is False

    def test_validate_error_without_message(self):
        """Test error result without error message."""
        validator = JSONSchemaValidator()
        result = {"success": False}

        assert validator.validate(result) is False

    def test_validate_error_with_message(self):
        """Test error result with error message."""
        validator = JSONSchemaValidator()
        result = {
            "success": False,
            "error": "Test error",
        }

        assert validator.validate(result) is True

    def test_validate_with_metadata(self):
        """Test result with metadata."""
        validator = JSONSchemaValidator()
        result = {
            "success": True,
            "data": {},
            "metadata": {"key": "value"},
        }

        assert validator.validate(result) is True

    def test_validate_invalid_metadata(self):
        """Test result with invalid metadata type."""
        validator = JSONSchemaValidator()
        result = {
            "success": True,
            "metadata": "not a dict",
        }

        assert validator.validate(result) is False

    def test_get_errors(self):
        """Test error message generation."""
        validator = JSONSchemaValidator()
        result = {"data": {}}

        errors = validator.get_errors(result)

        assert len(errors) > 0
        assert any("success" in error for error in errors)

    def test_validate_evidence(self):
        """Test evidence validation."""
        validator = JSONSchemaValidator()
        evidence = [
            {"doi": "10.1234/test"},
            {"pmid": "12345678"},
        ]

        assert validator.validate_evidence(evidence) is True

    def test_validate_evidence_missing_citation(self):
        """Test evidence without citation field."""
        validator = JSONSchemaValidator()
        evidence = [{"confidence": 0.95}]

        assert validator.validate_evidence(evidence) is False

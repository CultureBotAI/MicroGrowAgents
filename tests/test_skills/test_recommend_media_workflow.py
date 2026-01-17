"""
Tests for RecommendMediaWorkflow skill.
"""

import pytest
from pathlib import Path

from microgrowagents.skills.workflows.recommend_media import RecommendMediaWorkflow


class TestRecommendMediaWorkflow:
    """Test RecommendMediaWorkflow skill."""

    @pytest.fixture
    def workflow(self):
        """Create workflow instance for testing."""
        return RecommendMediaWorkflow()

    def test_workflow_initialization(self, workflow):
        """Test workflow initialization."""
        assert workflow is not None
        assert workflow.db_path is not None

    def test_get_metadata(self, workflow):
        """Test metadata retrieval."""
        metadata = workflow.get_metadata()

        assert metadata.name == "recommend-media"
        assert metadata.category == "workflow"
        assert metadata.requires_database is True
        assert metadata.requires_internet is True
        assert len(metadata.parameters) > 0
        assert len(metadata.examples) > 0

    def test_metadata_parameters(self, workflow):
        """Test metadata parameters are correctly defined."""
        metadata = workflow.get_metadata()
        param_names = [p.name for p in metadata.parameters]

        # Check required parameters
        assert "query" in param_names

        # Check optional parameters
        assert "organism" in param_names
        assert "temperature" in param_names
        assert "pH" in param_names
        assert "oxygen" in param_names
        assert "carbon_source" in param_names
        assert "goals" in param_names
        assert "base_medium" in param_names
        assert "include_alternatives" in param_names

    def test_metadata_examples(self, workflow):
        """Test metadata examples are provided."""
        metadata = workflow.get_metadata()
        examples = metadata.examples

        assert len(examples) >= 3
        # All examples should include the skill name
        for example in examples:
            assert "recommend-media" in example

    def test_basic_execution(self, workflow):
        """Test basic workflow execution."""
        result = workflow.execute(
            query="Recommend a minimal medium",
            goals="minimal,defined"
        )

        assert result["success"]
        assert "data" in result
        assert "metadata" in result

    def test_execute_with_organism(self, workflow):
        """Test execution with organism specification."""
        result = workflow.execute(
            query="Medium for E. coli",
            organism="Escherichia coli",
            goals="defined"
        )

        assert result["success"]
        data = result["data"]
        assert "formulation" in data
        assert "rationale" in data
        assert "evidence" in data

    def test_execute_missing_query(self, workflow):
        """Test execution without required query parameter."""
        result = workflow.execute()

        assert not result["success"]
        assert "error" in result
        assert "query" in result["error"].lower()

    def test_execute_with_growth_conditions(self, workflow):
        """Test execution with growth conditions."""
        result = workflow.execute(
            query="Custom medium",
            temperature=37.0,
            pH=7.5,
            oxygen="aerobic",
            carbon_source="glucose"
        )

        assert result["success"]
        data = result["data"]
        formulation = data["formulation"]

        # Check growth conditions are included
        growth_conds = formulation.get("growth_conditions", {})
        assert growth_conds["temperature"] == 37.0
        assert growth_conds["pH"] == 7.5
        assert growth_conds["oxygen"] == "aerobic"
        assert growth_conds["carbon_source"] == "glucose"

    def test_execute_multiple_goals(self, workflow):
        """Test execution with multiple formulation goals."""
        result = workflow.execute(
            query="Multi-goal medium",
            goals="defined,cost_effective,high_yield"
        )

        assert result["success"]
        data = result["data"]
        formulation = data["formulation"]

        goals = formulation.get("goals", [])
        assert len(goals) >= 2

    def test_execute_with_alternatives(self, workflow):
        """Test execution with alternative ingredients."""
        result = workflow.execute(
            query="Medium with alternatives",
            goals="defined",
            include_alternatives=True
        )

        assert result["success"]
        data = result["data"]
        assert "alternatives" in data

    def test_execute_without_alternatives(self, workflow):
        """Test execution without alternative ingredients."""
        result = workflow.execute(
            query="Medium without alternatives",
            goals="defined",
            include_alternatives=False
        )

        assert result["success"]
        data = result["data"]
        alternatives = data.get("alternatives", {})
        assert alternatives == {}

    def test_workflow_data_structure(self, workflow):
        """Test workflow returns expected data structure."""
        result = workflow.execute(
            query="Test medium",
            goals="defined"
        )

        assert result["success"]
        data = result["data"]

        # Check all expected keys
        assert "formulation" in data
        assert "rationale" in data
        assert "essential_roles" in data
        assert "alternatives" in data
        assert "evidence" in data

        # Check formulation structure
        formulation = data["formulation"]
        assert "name" in formulation
        assert "ingredients" in formulation
        assert "properties" in formulation

        # Check evidence structure
        evidence = data["evidence"]
        assert "kg_microbe" in evidence
        assert "literature" in evidence
        assert "compatibility" in evidence

    def test_workflow_metadata_structure(self, workflow):
        """Test workflow metadata structure."""
        result = workflow.execute(
            query="Test medium",
            organism="Escherichia coli",
            goals="defined"
        )

        assert result["success"]
        metadata = result["metadata"]

        # Check metadata keys
        assert "workflow" in metadata
        assert metadata["workflow"] == "recommend_media"
        assert "agents_used" in metadata
        assert "confidence" in metadata

        # Check agents used list
        agents_used = metadata["agents_used"]
        assert isinstance(agents_used, list)
        assert "MediaFormulationAgent" in agents_used

    def test_run_method_markdown_format(self, workflow):
        """Test run method with markdown output."""
        result = workflow.run(
            query="Test medium",
            goals="defined",
            output_format="markdown"
        )

        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain markdown headers
        assert "#" in result

    def test_run_method_json_format(self, workflow):
        """Test run method with JSON output."""
        result = workflow.run(
            query="Test medium",
            goals="defined",
            output_format="json"
        )

        assert isinstance(result, dict)
        assert "success" in result

    def test_run_method_both_format(self, workflow):
        """Test run method with both output formats."""
        result = workflow.run(
            query="Test medium",
            goals="defined",
            output_format="both"
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        markdown_output, json_output = result

        assert isinstance(markdown_output, str)
        assert isinstance(json_output, dict)

    def test_format_markdown(self, workflow):
        """Test markdown formatting."""
        # First execute
        result = workflow.execute(
            query="Test medium",
            organism="Escherichia coli",
            goals="defined"
        )

        # Then format
        markdown = workflow.format_markdown(result)

        assert isinstance(markdown, str)
        assert len(markdown) > 0

        # Check for expected markdown sections
        assert "# " in markdown  # Headers
        assert "## " in markdown  # Subheaders
        assert "Formulation" in markdown or "formulation" in markdown
        assert "Rationale" in markdown or "rationale" in markdown

    def test_format_markdown_with_organism(self, workflow):
        """Test markdown formatting includes organism info."""
        result = workflow.execute(
            query="E. coli medium",
            organism="Escherichia coli",
            goals="defined"
        )

        markdown = workflow.format_markdown(result)

        assert "Escherichia coli" in markdown or "E. coli" in markdown

    def test_format_markdown_with_tables(self, workflow):
        """Test markdown formatting includes tables."""
        result = workflow.execute(
            query="Test medium",
            goals="defined"
        )

        markdown = workflow.format_markdown(result)

        # Should have table formatting
        assert "|" in markdown  # Table delimiter
        assert "Ingredient" in markdown or "ingredient" in markdown

    def test_format_markdown_error_handling(self, workflow):
        """Test markdown formatting handles errors."""
        error_result = {
            "success": False,
            "error": "Test error message"
        }

        markdown = workflow.format_markdown(error_result)

        assert isinstance(markdown, str)
        assert "Error" in markdown
        assert "Test error message" in markdown

    def test_format_json(self, workflow):
        """Test JSON formatting."""
        result = workflow.execute(
            query="Test medium",
            goals="defined"
        )

        json_output = workflow.format_json(result)

        assert isinstance(json_output, dict)
        assert json_output == result  # Should be passthrough

    def test_anaerobic_conditions(self, workflow):
        """Test anaerobic medium recommendation."""
        result = workflow.execute(
            query="Anaerobic medium",
            oxygen="anaerobic",
            goals="defined"
        )

        assert result["success"]
        data = result["data"]

        # Check for reducing agent role
        essential_roles = data.get("essential_roles", {})
        role_names = list(essential_roles.keys())
        assert "Reducing Agent" in role_names

    def test_aerobic_conditions(self, workflow):
        """Test aerobic medium recommendation."""
        result = workflow.execute(
            query="Aerobic medium",
            oxygen="aerobic",
            goals="defined"
        )

        assert result["success"]
        data = result["data"]
        formulation = data["formulation"]

        assert formulation["growth_conditions"]["oxygen"] == "aerobic"

    def test_minimal_goal(self, workflow):
        """Test minimal medium goal."""
        result = workflow.execute(
            query="Minimal medium",
            goals="minimal"
        )

        assert result["success"]
        data = result["data"]
        formulation = data["formulation"]

        assert "minimal" in formulation["goals"]

    def test_complex_goal(self, workflow):
        """Test complex medium goal."""
        result = workflow.execute(
            query="Complex medium",
            goals="complex"
        )

        assert result["success"]
        data = result["data"]
        formulation = data["formulation"]

        assert "complex" in formulation["goals"]

    def test_high_yield_goal(self, workflow):
        """Test high-yield medium goal."""
        result = workflow.execute(
            query="High-yield medium",
            goals="high_yield"
        )

        assert result["success"]
        data = result["data"]
        formulation = data["formulation"]

        assert "high_yield" in formulation["goals"]

    def test_cost_effective_goal(self, workflow):
        """Test cost-effective medium goal."""
        result = workflow.execute(
            query="Cost-effective medium",
            goals="cost_effective"
        )

        assert result["success"]
        data = result["data"]
        formulation = data["formulation"]

        assert "cost_effective" in formulation["goals"]

    def test_selective_goal(self, workflow):
        """Test selective medium goal."""
        result = workflow.execute(
            query="Selective medium",
            goals="selective"
        )

        assert result["success"]
        data = result["data"]
        formulation = data["formulation"]

        assert "selective" in formulation["goals"]

    def test_custom_base_medium(self, workflow):
        """Test custom base medium specification."""
        result = workflow.execute(
            query="Custom medium",
            base_medium="LB",
            goals="defined"
        )

        assert result["success"]
        metadata = result["metadata"]
        assert metadata.get("base_medium") == "LB"

    def test_confidence_levels(self, workflow):
        """Test confidence level reporting."""
        result = workflow.execute(
            query="Test medium",
            organism="Escherichia coli",
            goals="defined"
        )

        assert result["success"]
        metadata = result["metadata"]

        confidence = metadata.get("confidence")
        assert confidence in ["low", "medium", "high"]

    def test_evidence_sources(self, workflow):
        """Test evidence sources are included."""
        result = workflow.execute(
            query="Test medium",
            organism="Escherichia coli",
            goals="defined"
        )

        assert result["success"]
        data = result["data"]
        evidence = data["evidence"]

        # Should have all evidence types
        assert "kg_microbe" in evidence
        assert "literature" in evidence
        assert "compatibility" in evidence

    def test_temperature_range(self, workflow):
        """Test different temperature values."""
        # Low temperature
        result_low = workflow.execute(
            query="Low temp medium",
            temperature=15.0,
            goals="defined"
        )

        # High temperature
        result_high = workflow.execute(
            query="High temp medium",
            temperature=65.0,
            goals="defined"
        )

        assert result_low["success"]
        assert result_high["success"]

    def test_ph_range(self, workflow):
        """Test different pH values."""
        # Acidic
        result_acid = workflow.execute(
            query="Acidic medium",
            pH=5.0,
            goals="defined"
        )

        # Alkaline
        result_alk = workflow.execute(
            query="Alkaline medium",
            pH=9.0,
            goals="defined"
        )

        assert result_acid["success"]
        assert result_alk["success"]

    def test_common_organisms(self, workflow):
        """Test recommendations for common model organisms."""
        organisms = [
            "Escherichia coli",
            "Bacillus subtilis",
            "Saccharomyces cerevisiae"
        ]

        for organism in organisms:
            result = workflow.execute(
                query=f"Medium for {organism}",
                organism=organism,
                goals="defined"
            )

            assert result["success"], f"Failed for {organism}"
            assert organism in str(result["data"])

    def test_methanotroph_recommendation(self, workflow):
        """Test methanotroph medium recommendation."""
        result = workflow.execute(
            query="Medium for methanotrophic bacteria",
            organism="Methylococcus capsulatus",
            carbon_source="methane",
            goals="defined"
        )

        assert result["success"]
        data = result["data"]
        formulation = data["formulation"]

        # Should mention methane
        assert "methane" in str(formulation).lower()

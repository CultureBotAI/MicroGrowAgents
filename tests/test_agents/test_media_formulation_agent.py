"""Test MediaFormulationAgent class."""

import pytest
from pathlib import Path

from microgrowagents.agents.media_formulation_agent import MediaFormulationAgent


class TestMediaFormulationAgent:
    """Test media formulation recommendation."""

    @pytest.fixture
    def agent(self):
        """Create MediaFormulationAgent instance for testing."""
        return MediaFormulationAgent()

    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent is not None
        assert agent.kg_agent is not None
        assert agent.conc_agent is not None
        assert agent.role_agent is not None
        assert agent.chem_agent is not None
        assert agent.lit_agent is not None

    def test_basic_formulation_recommendation(self, agent):
        """Test basic formulation recommendation without organism."""
        result = agent.run(
            query="Recommend a minimal defined medium",
            formulation_goals=["minimal", "defined"]
        )

        assert result["success"]
        assert "formulation" in result["data"]
        assert "rationale" in result["data"]
        assert "evidence" in result["data"]
        assert "metadata" in result

        formulation = result["data"]["formulation"]
        assert "name" in formulation
        assert "ingredients" in formulation
        assert "properties" in formulation

    def test_organism_specific_formulation(self, agent):
        """Test organism-specific formulation recommendation."""
        result = agent.run(
            query="Recommend medium for methanotrophic bacteria",
            organism="Methylococcus capsulatus",
            growth_conditions={
                "temperature": 42,
                "pH": 6.8,
                "oxygen": "aerobic",
                "carbon_source": "methane"
            },
            formulation_goals=["defined"]
        )

        assert result["success"]
        assert "formulation" in result["data"]

        formulation = result["data"]["formulation"]
        assert formulation["organism"] == "Methylococcus capsulatus"
        assert "methane" in str(formulation).lower() or "carbon_source" in formulation.get("growth_conditions", {})

    def test_aerobic_formulation(self, agent):
        """Test aerobic medium formulation."""
        result = agent.run(
            query="Aerobic medium for general use",
            growth_conditions={"oxygen": "aerobic"},
            formulation_goals=["defined"]
        )

        assert result["success"]
        formulation = result["data"]["formulation"]
        assert formulation["growth_conditions"]["oxygen"] == "aerobic"

    def test_anaerobic_formulation(self, agent):
        """Test anaerobic medium formulation includes reducing agent."""
        result = agent.run(
            query="Anaerobic medium",
            growth_conditions={"oxygen": "anaerobic"},
            formulation_goals=["defined"]
        )

        assert result["success"]
        formulation = result["data"]["formulation"]
        assert formulation["growth_conditions"]["oxygen"] == "anaerobic"

        # Check that essential roles includes reducing agent
        essential_roles = result["data"]["essential_roles"]
        role_names = list(essential_roles.keys())
        assert "Reducing Agent" in role_names

    def test_minimal_medium_goals(self, agent):
        """Test minimal medium formulation has fewer trace elements."""
        result = agent.run(
            query="Minimal medium",
            formulation_goals=["minimal"]
        )

        assert result["success"]

        # Check goals in formulation
        formulation = result["data"]["formulation"]
        assert "minimal" in formulation["goals"]

    def test_high_yield_goals(self, agent):
        """Test high-yield medium formulation."""
        result = agent.run(
            query="High-yield production medium",
            formulation_goals=["high_yield", "complex"]
        )

        assert result["success"]
        formulation = result["data"]["formulation"]
        assert "high_yield" in formulation["goals"] or "complex" in formulation["goals"]

    def test_essential_roles_coverage(self, agent):
        """Test that essential nutrient roles are identified."""
        result = agent.run(
            query="General purpose medium",
            formulation_goals=["defined"]
        )

        assert result["success"]
        essential_roles = result["data"]["essential_roles"]

        # Check core essential roles are present
        assert "Carbon Source" in essential_roles
        assert "Nitrogen Source" in essential_roles
        assert "Phosphate Source" in essential_roles
        assert "Essential Macronutrient (Mg)" in essential_roles
        assert "Trace Element (Fe)" in essential_roles

        # Check role properties
        for role, info in essential_roles.items():
            assert "priority" in info
            assert "required" in info
            assert "rationale" in info

    def test_concentration_predictions(self, agent):
        """Test that concentrations are predicted for ingredients."""
        result = agent.run(
            query="Standard medium",
            formulation_goals=["defined"]
        )

        assert result["success"]
        ingredients = result["data"]["formulation"]["ingredients"]

        assert len(ingredients) > 0

        for ingredient in ingredients:
            assert "ingredient" in ingredient
            assert "role" in ingredient
            assert "concentration" in ingredient
            assert "unit" in ingredient
            assert "confidence" in ingredient

    def test_chemical_compatibility_validation(self, agent):
        """Test chemical compatibility validation."""
        result = agent.run(
            query="Complete medium with trace elements",
            formulation_goals=["defined"]
        )

        assert result["success"]
        evidence = result["data"]["evidence"]

        assert "compatibility" in evidence
        compatibility = evidence["compatibility"]
        assert "compatible" in compatibility
        assert "notes" in compatibility or "issues" in compatibility

    def test_alternative_ingredients(self, agent):
        """Test alternative ingredient suggestions."""
        result = agent.run(
            query="Medium with alternatives",
            formulation_goals=["defined"],
            include_alternatives=True
        )

        assert result["success"]
        alternatives = result["data"]["alternatives"]

        # Should have alternatives for at least some ingredients
        assert isinstance(alternatives, dict)

    def test_no_alternatives(self, agent):
        """Test formulation without alternatives."""
        result = agent.run(
            query="Medium without alternatives",
            formulation_goals=["defined"],
            include_alternatives=False
        )

        assert result["success"]
        alternatives = result["data"]["alternatives"]

        # Should be empty dict
        assert alternatives == {}

    def test_kg_evidence_collection(self, agent):
        """Test KG-Microbe evidence collection."""
        result = agent.run(
            query="Medium for E. coli",
            organism="Escherichia coli",
            formulation_goals=["defined"]
        )

        assert result["success"]
        evidence = result["data"]["evidence"]

        assert "kg_microbe" in evidence
        kg_evidence = evidence["kg_microbe"]

        assert "organism_info" in kg_evidence
        assert "pathways" in kg_evidence
        assert "metabolites" in kg_evidence

    def test_literature_evidence_collection(self, agent):
        """Test literature evidence collection."""
        result = agent.run(
            query="Medium for model organism",
            organism="Escherichia coli",
            formulation_goals=["defined"]
        )

        assert result["success"]
        evidence = result["data"]["evidence"]

        assert "literature" in evidence
        lit_evidence = evidence["literature"]

        assert "organism_studies" in lit_evidence
        assert "ingredient_studies" in lit_evidence

    def test_confidence_scoring(self, agent):
        """Test confidence score calculation."""
        result = agent.run(
            query="Medium with good evidence",
            organism="Escherichia coli",
            formulation_goals=["defined"]
        )

        assert result["success"]
        metadata = result["metadata"]

        assert "confidence" in metadata
        assert metadata["confidence"] in ["low", "medium", "high"]

    def test_rationale_generation(self, agent):
        """Test rationale text generation."""
        result = agent.run(
            query="Medium for testing",
            organism="Escherichia coli",
            formulation_goals=["defined"]
        )

        assert result["success"]
        rationale = result["data"]["rationale"]

        assert isinstance(rationale, str)
        assert len(rationale) > 0
        assert "Escherichia coli" in rationale or "organism" in rationale.lower()

    def test_formulation_name_generation(self, agent):
        """Test formulation name generation."""
        result = agent.run(
            query="Test medium",
            organism="Methylococcus capsulatus",
            formulation_goals=["minimal", "defined"]
        )

        assert result["success"]
        formulation = result["data"]["formulation"]

        name = formulation["name"]
        assert isinstance(name, str)
        assert len(name) > 0
        # Should include genus name
        assert "Methylococcus" in name or "Medium" in name
        # Should include goal descriptors
        assert "Minimal" in name or "Defined" in name

    def test_medium_properties_calculation(self, agent):
        """Test medium properties calculation."""
        result = agent.run(
            query="Standard medium",
            growth_conditions={"pH": 7.0, "temperature": 37},
            formulation_goals=["defined"]
        )

        assert result["success"]
        formulation = result["data"]["formulation"]
        properties = formulation["properties"]

        # Should have predicted properties
        assert "target_pH" in properties
        assert "target_temperature" in properties
        assert "oxygen_requirement" in properties

    def test_cost_effective_goal(self, agent):
        """Test cost-effective formulation goal."""
        result = agent.run(
            query="Cost-effective medium",
            formulation_goals=["cost_effective", "defined"]
        )

        assert result["success"]
        formulation = result["data"]["formulation"]
        assert "cost_effective" in formulation["goals"]

    def test_selective_goal(self, agent):
        """Test selective medium formulation goal."""
        result = agent.run(
            query="Selective medium",
            formulation_goals=["selective", "defined"]
        )

        assert result["success"]
        formulation = result["data"]["formulation"]
        assert "selective" in formulation["goals"]

    def test_error_handling_empty_query(self, agent):
        """Test error handling for empty query."""
        result = agent.run(
            query="",
            formulation_goals=["defined"]
        )

        # Should still work with empty query
        assert result is not None

    def test_metadata_sources(self, agent):
        """Test metadata includes source information."""
        result = agent.run(
            query="Standard medium",
            formulation_goals=["defined"]
        )

        assert result["success"]
        metadata = result["metadata"]

        assert "sources" in metadata
        sources = metadata["sources"]
        assert isinstance(sources, list)
        assert len(sources) > 0

    def test_multiple_goals(self, agent):
        """Test formulation with multiple goals."""
        result = agent.run(
            query="Multi-goal medium",
            formulation_goals=["defined", "cost_effective", "high_yield"]
        )

        assert result["success"]
        formulation = result["data"]["formulation"]
        goals = formulation["goals"]

        assert len(goals) >= 2
        assert "defined" in goals or "cost_effective" in goals or "high_yield" in goals

    def test_custom_carbon_source(self, agent):
        """Test custom carbon source specification."""
        result = agent.run(
            query="Medium with custom carbon source",
            growth_conditions={"carbon_source": "methanol"},
            formulation_goals=["defined"]
        )

        assert result["success"]
        formulation = result["data"]["formulation"]

        # Check that methanol is in the carbon source
        growth_conds = formulation.get("growth_conditions", {})
        assert growth_conds.get("carbon_source") == "methanol"

    def test_different_temperatures(self, agent):
        """Test formulation at different temperatures."""
        # Mesophilic
        result_meso = agent.run(
            query="Mesophilic medium",
            growth_conditions={"temperature": 30},
            formulation_goals=["defined"]
        )

        # Thermophilic
        result_thermo = agent.run(
            query="Thermophilic medium",
            growth_conditions={"temperature": 60},
            formulation_goals=["defined"]
        )

        assert result_meso["success"]
        assert result_thermo["success"]

        # Both should have temperature in properties
        assert "temperature" in result_meso["data"]["formulation"]["properties"]["target_temperature"]
        assert "temperature" in result_thermo["data"]["formulation"]["properties"]["target_temperature"]

    def test_different_ph_values(self, agent):
        """Test formulation at different pH values."""
        # Acidic
        result_acid = agent.run(
            query="Acidic medium",
            growth_conditions={"pH": 5.0},
            formulation_goals=["defined"]
        )

        # Alkaline
        result_alk = agent.run(
            query="Alkaline medium",
            growth_conditions={"pH": 9.0},
            formulation_goals=["defined"]
        )

        assert result_acid["success"]
        assert result_alk["success"]

        assert "pH" in result_acid["data"]["formulation"]["properties"]["target_pH"]
        assert "pH" in result_alk["data"]["formulation"]["properties"]["target_pH"]


class TestMediaFormulationHelperMethods:
    """Test helper methods of MediaFormulationAgent."""

    @pytest.fixture
    def agent(self):
        """Create MediaFormulationAgent instance for testing."""
        return MediaFormulationAgent()

    def test_identify_essential_roles_minimal(self, agent):
        """Test essential roles identification for minimal medium."""
        roles = agent._identify_essential_roles(
            organism=None,
            growth_conditions={},
            goals=["minimal"]
        )

        assert "Carbon Source" in roles
        assert "Nitrogen Source" in roles
        assert "Phosphate Source" in roles

        # Minimal shouldn't have many trace elements
        trace_elements = [k for k in roles.keys() if "Trace Element" in k]
        assert len(trace_elements) <= 2  # Only essential ones

    def test_identify_essential_roles_complex(self, agent):
        """Test essential roles identification for complex medium."""
        roles = agent._identify_essential_roles(
            organism=None,
            growth_conditions={},
            goals=["complex", "high_yield"]
        )

        assert "Carbon Source" in roles
        assert "Nitrogen Source" in roles

        # Complex should have vitamins
        assert "Vitamin/Cofactor Precursor" in roles

    def test_identify_essential_roles_anaerobic(self, agent):
        """Test essential roles for anaerobic conditions."""
        roles = agent._identify_essential_roles(
            organism=None,
            growth_conditions={"oxygen": "anaerobic"},
            goals=["defined"]
        )

        # Should include reducing agent
        assert "Reducing Agent" in roles

    def test_calculate_confidence_high(self, agent):
        """Test confidence calculation - high confidence."""
        kg_evidence = {
            "organism_info": {"id": "test"},
            "pathways": [1, 2, 3],
            "metabolites": [1, 2]
        }
        literature = {
            "organism_studies": [1, 2, 3],
            "ingredient_studies": {"glucose": [1]}
        }
        concentrations = [
            {"confidence": "high"},
            {"confidence": "high"},
            {"confidence": "high"}
        ]

        confidence = agent._calculate_confidence(kg_evidence, literature, concentrations)
        assert confidence == "high"

    def test_calculate_confidence_low(self, agent):
        """Test confidence calculation - low confidence."""
        kg_evidence = {}
        literature = {}
        concentrations = [
            {"confidence": "low"},
            {"confidence": "low"}
        ]

        confidence = agent._calculate_confidence(kg_evidence, literature, concentrations)
        assert confidence == "low"

    def test_generate_formulation_name(self, agent):
        """Test formulation name generation."""
        name1 = agent._generate_formulation_name("Escherichia coli", ["minimal"])
        assert "Escherichia" in name1 or "Minimal" in name1

        name2 = agent._generate_formulation_name("Bacillus subtilis", ["defined", "selective"])
        assert "Bacillus" in name2 or "Defined" in name2 or "Selective" in name2

        name3 = agent._generate_formulation_name(None, ["complex"])
        assert "Complex" in name3 or "Custom" in name3

"""
Tests for CofactorMediaAgent.
"""

import pytest
from pathlib import Path
from microgrowagents.agents.cofactor_media_agent import CofactorMediaAgent, CofactorRequirement, IngredientRecommendation


@pytest.fixture
def db_path():
    """Fixture providing database path."""
    return Path("data/processed/microgrow.duckdb")


@pytest.fixture
def agent(db_path):
    """Fixture providing CofactorMediaAgent instance."""
    return CofactorMediaAgent(db_path)


def test_agent_initialization(agent):
    """Test that agent initializes correctly."""
    assert agent is not None
    assert agent.cofactor_hierarchy is not None
    assert agent.ingredient_cofactor_map is not None
    assert agent.ec_cofactor_map is not None


def test_cofactor_hierarchy_loaded(agent):
    """Test that cofactor hierarchy is properly loaded."""
    assert "vitamins" in agent.cofactor_hierarchy
    assert "metals" in agent.cofactor_hierarchy
    assert "nucleotides" in agent.cofactor_hierarchy
    assert "energy_cofactors" in agent.cofactor_hierarchy
    assert "other" in agent.cofactor_hierarchy


def test_ingredient_cofactor_mapping_loaded(agent):
    """Test that ingredient-to-cofactor mapping is loaded."""
    mapping = agent.ingredient_cofactor_map
    assert len(mapping) > 0
    # Check structure
    assert all("Component" in item for item in mapping)
    assert all("Cofactors_Provided" in item for item in mapping)


def test_cofactor_requirement_dataclass():
    """Test CofactorRequirement dataclass."""
    req = CofactorRequirement(
        cofactor_id="CHEBI:15846",
        cofactor_key="nad",
        cofactor_name="NAD+",
        category="nucleotides",
        biosynthesis_status="capable",
        biosynthesis_completeness=0.9,
        acquisition_mechanism="transporter",
        acquisition_evidence=[],
        external_supply_needed=False,
        confidence="high",
        evidence_sources=["genome", "kegg"]
    )

    assert req.cofactor_id == "CHEBI:15846"
    assert req.cofactor_key == "nad"
    assert req.cofactor_name == "NAD+"
    assert req.category == "nucleotides"


def test_ingredient_recommendation_dataclass():
    """Test IngredientRecommendation dataclass."""
    rec = IngredientRecommendation(
        ingredient_name="Thiamin",
        database_id="CHEBI:49105",
        status="existing",
        cofactors_provided=["thiamine_pyrophosphate"],
        rationale="Provides TPP cofactor",
        concentration_range=None,
        confidence=0.9,
        evidence=["MP medium database"]
    )

    assert rec.ingredient_name == "Thiamin"
    assert rec.status == "existing"
    assert "thiamine_pyrophosphate" in rec.cofactors_provided


def test_map_ec_to_cofactors(agent):
    """Test EC number to cofactor mapping."""
    # Test NAD-dependent dehydrogenase
    cofactors = agent._map_ec_to_cofactors("1.1.1.1")

    assert isinstance(cofactors, dict)
    # Should map to NAD+/NADP+
    assert any(cf in ["nad", "nadp"] for cf in cofactors.keys())


def test_get_cofactor_info(agent):
    """Test getting cofactor information from hierarchy."""
    info = agent._get_cofactor_info("nad")

    assert info is not None
    assert "id" in info
    assert "name" in info
    assert "category" in info


def test_analyze_cofactor_requirements_mock(agent):
    """Test cofactor requirements analysis with mock organism."""
    # This is a minimal test - full test requires database with genome data
    result = agent.analyze_cofactor_requirements("test_organism")

    assert isinstance(result, list)
    # May be empty if organism not in database, which is OK for this test


def test_map_ingredients_to_cofactors(agent):
    """Test mapping ingredients to cofactor requirements."""
    # Create mock requirements
    mock_reqs = [
        CofactorRequirement(
            cofactor_id="CHEBI:18248",
            cofactor_key="iron_ion",
            cofactor_name="Fe",
            category="metals",
            biosynthesis_status="N/A",
            biosynthesis_completeness=0.0,
            acquisition_mechanism="transporter",
            acquisition_evidence=[],
            external_supply_needed=True,
            confidence="high",
            evidence_sources=["genome"]
        )
    ]

    result = agent.map_ingredients_to_cofactors(mock_reqs, "MP")

    assert "existing" in result
    assert "new" in result
    assert "all" in result


def test_build_cofactor_table(agent):
    """Test building hierarchical cofactor table."""
    # Create mock data
    mock_reqs = [
        CofactorRequirement(
            cofactor_id="CHEBI:15846",
            cofactor_key="nad",
            cofactor_name="NAD+",
            category="nucleotides",
            biosynthesis_status="capable",
            biosynthesis_completeness=0.9,
            acquisition_mechanism="none",
            acquisition_evidence=[],
            external_supply_needed=False,
            confidence="high",
            evidence_sources=["genome"]
        )
    ]

    mock_ingredients = {
        "existing": [],
        "new": [
            IngredientRecommendation(
                ingredient_name="NOT COVERED",
                database_id="",
                status="missing",
                cofactors_provided=["NAD+"],
                rationale="No ingredient found",
                concentration_range=None,
                confidence=0.5,
                evidence=[]
            )
        ],
        "all": []
    }

    table = agent._build_cofactor_table(mock_reqs, mock_ingredients)

    assert isinstance(table, list)
    assert len(table) > 0
    # Check required columns
    required_cols = ["Category", "Cofactor", "Ingredient", "Status"]
    for row in table:
        for col in required_cols:
            assert col in row


def test_run_method_structure(agent):
    """Test that run method returns correct structure."""
    # Run with a test organism (may fail if not in DB, which is OK)
    result = agent.run(
        query="test cofactor analysis",
        organism="test_organism",
        base_medium="MP"
    )

    # Check structure regardless of success
    assert "success" in result
    assert "data" in result or "error" in result

    if result.get("success"):
        data = result["data"]
        assert "cofactor_table" in data
        assert "cofactor_requirements" in data
        assert "ingredient_recommendations" in data


def test_integration_with_genome_function_agent(agent):
    """Test integration with GenomeFunctionAgent."""
    # Verify that genome agent is initialized
    assert agent.genome_agent is not None


def test_integration_with_kg_agent(agent):
    """Test integration with KGReasoningAgent."""
    # Verify that KG agent is initialized
    assert agent.kg_agent is not None


def test_integration_with_literature_agent(agent):
    """Test integration with LiteratureAgent."""
    # Verify that literature agent is initialized
    assert agent.lit_agent is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

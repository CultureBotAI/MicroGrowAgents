"""
Comprehensive tests for genome function integration.

Tests genome data loading, GenomeFunctionAgent, and integrations with:
- MediaFormulationAgent
- GenMediaConcAgent
- KGReasoningAgent

Run with: pytest tests/test_genome_integration.py -v
"""

import pytest
from pathlib import Path

from microgrowagents.agents.genome_function_agent import GenomeFunctionAgent
from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent


@pytest.fixture
def db_path():
    """Database path fixture."""
    return Path("data/processed/microgrow.duckdb")


@pytest.fixture
def genome_agent(db_path):
    """GenomeFunctionAgent fixture."""
    return GenomeFunctionAgent(db_path)


@pytest.fixture
def kg_agent(db_path):
    """KGReasoningAgent fixture."""
    return KGReasoningAgent(db_path)


class TestGenomeDataLoading:
    """Test genome data loading and database tables."""

    def test_genome_tables_exist(self, db_path):
        """Test that genome tables were created."""
        import duckdb
        conn = duckdb.connect(str(db_path), read_only=True)

        # Check genome_metadata table
        result = conn.execute("""
            SELECT COUNT(*) FROM genome_metadata
        """).fetchone()

        assert result[0] > 0, "genome_metadata table should have rows"

        # Check genome_annotations table
        result = conn.execute("""
            SELECT COUNT(*) FROM genome_annotations
        """).fetchone()

        assert result[0] > 0, "genome_annotations table should have rows"

        conn.close()

    def test_genome_count(self, db_path):
        """Test that all 57 genomes were loaded."""
        import duckdb
        conn = duckdb.connect(str(db_path), read_only=True)

        result = conn.execute("""
            SELECT COUNT(*) FROM genome_metadata
        """).fetchone()

        assert result[0] == 57, f"Expected 57 genomes, got {result[0]}"

        conn.close()

    def test_annotation_coverage(self, db_path):
        """Test annotation coverage statistics."""
        import duckdb
        conn = duckdb.connect(str(db_path), read_only=True)

        result = conn.execute("""
            SELECT
                COUNT(*) as total_cds,
                SUM(CASE WHEN ec_numbers IS NOT NULL AND ec_numbers != '' THEN 1 ELSE 0 END) as with_ec,
                SUM(CASE WHEN go_terms IS NOT NULL AND go_terms != '' THEN 1 ELSE 0 END) as with_go,
                SUM(CASE WHEN kegg_ids IS NOT NULL AND kegg_ids != '' THEN 1 ELSE 0 END) as with_kegg
            FROM genome_annotations
            WHERE feature_type = 'CDS'
        """).fetchone()

        total, with_ec, with_go, with_kegg = result

        assert total > 600000, f"Expected >600k CDS features, got {total}"
        assert with_ec / total > 0.1, f"EC coverage too low: {with_ec/total:.1%}"
        assert with_go / total > 0.1, f"GO coverage too low: {with_go/total:.1%}"

        conn.close()


class TestGenomeFunctionAgent:
    """Test GenomeFunctionAgent core functionality."""

    def test_find_enzymes_by_ec_wildcard(self, genome_agent):
        """Test finding enzymes with EC wildcard pattern."""
        result = genome_agent.find_enzymes(
            query="find oxidoreductases",
            organism="SAMN00114986",
            ec_number="1.1.*"
        )

        assert result["success"] is True
        assert result["data"]["count"] > 0
        assert isinstance(result["data"]["enzymes"], list)

    def test_find_enzymes_by_product(self, genome_agent):
        """Test finding enzymes by product description."""
        result = genome_agent.find_enzymes(
            query="find dehydrogenase",
            product="dehydrogenase"
        )

        assert result["success"] is True
        assert result["data"]["count"] > 0

    def test_detect_auxotrophies(self, genome_agent):
        """Test auxotrophy detection."""
        result = genome_agent.detect_auxotrophies(
            query="detect auxotrophies",
            organism="SAMN00114986"
        )

        assert result["success"] is True
        assert "auxotrophies" in result["data"]
        assert "summary" in result["data"]
        assert result["data"]["summary"]["total_pathways_checked"] > 0

    def test_check_pathway_completeness(self, genome_agent):
        """Test pathway completeness check."""
        result = genome_agent.check_pathway_completeness(
            query="check pathway",
            organism="SAMN00114986",
            pathway_id="ko00270"
        )

        assert result["success"] is True
        assert "completeness" in result["data"]
        assert 0 <= result["data"]["completeness"] <= 1.0

    def test_find_cofactor_requirements(self, genome_agent):
        """Test cofactor requirement analysis."""
        result = genome_agent.find_cofactor_requirements(
            query="find cofactors",
            organism="SAMN00114986"
        )

        assert result["success"] is True
        assert "cofactors" in result["data"]

    def test_find_transporters(self, genome_agent):
        """Test transporter gene search."""
        result = genome_agent.find_transporters(
            query="find glucose transporters",
            organism="SAMN00114986",
            substrate="glucose"
        )

        assert result["success"] is True
        assert "transporters" in result["data"]


class TestKGReasoningIntegration:
    """Test KGReasoningAgent genome query integration."""

    def test_genome_enzymes_query(self, kg_agent):
        """Test genome_enzymes query type."""
        result = kg_agent.run("genome_enzymes SAMN00114986 1.1.*")

        assert result["success"] is True
        assert result["query_type"] == "genome_enzymes"
        assert "enzymes" in result["data"]

    def test_genome_auxotrophies_query(self, kg_agent):
        """Test genome_auxotrophies query type."""
        result = kg_agent.run("genome_auxotrophies SAMN00114986")

        assert result["success"] is True
        assert result["query_type"] == "genome_auxotrophies"
        assert "auxotrophies" in result["data"]

    def test_genome_transporters_query(self, kg_agent):
        """Test genome_transporters query type."""
        result = kg_agent.run("genome_transporters SAMN00114986 glucose")

        assert result["success"] is True
        assert result["query_type"] == "genome_transporters"
        assert "transporters" in result["data"]


class TestMediaFormulationIntegration:
    """Test MediaFormulationAgent genome integration."""

    def test_formulation_with_organism(self, db_path):
        """Test media formulation with organism-specific genome analysis."""
        from microgrowagents.agents.media_formulation_agent import MediaFormulationAgent

        agent = MediaFormulationAgent(db_path)

        # This tests that genome agent is initialized and called
        # Full integration test would require organism in database
        assert hasattr(agent, 'genome_agent')
        assert agent.genome_agent is not None


class TestGenMediaConcIntegration:
    """Test GenMediaConcAgent transporter integration."""

    def test_conc_agent_has_genome_agent(self, db_path):
        """Test that GenMediaConcAgent has genome agent."""
        from microgrowagents.agents.gen_media_conc_agent import GenMediaConcAgent

        agent = GenMediaConcAgent(db_path)

        assert hasattr(agent, 'genome_agent')
        assert agent.genome_agent is not None

    def test_transporter_refinement_method(self, db_path):
        """Test transporter refinement method exists."""
        from microgrowagents.agents.gen_media_conc_agent import GenMediaConcAgent

        agent = GenMediaConcAgent(db_path)

        assert hasattr(agent, '_refine_concentration_with_transporters')


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_genome_to_media_workflow(self, db_path):
        """Test complete workflow: genome analysis → media formulation."""
        from microgrowagents.agents.genome_function_agent import GenomeFunctionAgent
        from microgrowagents.agents.media_formulation_agent import MediaFormulationAgent

        # Step 1: Analyze genome
        genome_agent = GenomeFunctionAgent(db_path)
        aux_result = genome_agent.detect_auxotrophies(
            query="detect auxotrophies",
            organism="SAMN00114986"
        )

        assert aux_result["success"] is True

        # Step 2: Use in media formulation
        media_agent = MediaFormulationAgent(db_path)

        # Verify genome agent is integrated
        assert media_agent.genome_agent is not None

    def test_all_agents_initialized(self, db_path):
        """Test that all agents can be initialized with genome support."""
        from microgrowagents.agents.genome_function_agent import GenomeFunctionAgent
        from microgrowagents.agents.media_formulation_agent import MediaFormulationAgent
        from microgrowagents.agents.gen_media_conc_agent import GenMediaConcAgent
        from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent

        # All agents should initialize without errors
        genome_agent = GenomeFunctionAgent(db_path)
        media_agent = MediaFormulationAgent(db_path)
        conc_agent = GenMediaConcAgent(db_path)
        kg_agent = KGReasoningAgent(db_path)

        assert genome_agent is not None
        assert media_agent is not None
        assert conc_agent is not None
        assert kg_agent is not None

        # Media agent should have genome agent
        assert hasattr(media_agent, 'genome_agent')

        # Conc agent should have genome agent
        assert hasattr(conc_agent, 'genome_agent')

        # KG agent should have genome agent
        assert hasattr(kg_agent, 'genome_agent')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

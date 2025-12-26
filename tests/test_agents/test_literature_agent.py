"""Test LiteratureAgent class."""

import pytest
from unittest.mock import patch, Mock

from microgrowagents.agents.literature_agent import LiteratureAgent


@pytest.fixture
def agent():
    """Create LiteratureAgent instance."""
    return LiteratureAgent()


def test_literature_agent_init(agent):
    """Test LiteratureAgent initialization."""
    assert agent.PUBMED_BASE_URL == "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


@patch("microgrowagents.agents.literature_agent.requests.get")
def test_pubmed_search(mock_get, agent):
    """Test PubMed search functionality."""
    # Mock search response
    search_response = Mock()
    search_response.json.return_value = {
        "esearchresult": {"idlist": ["12345678", "87654321"]}
    }
    search_response.raise_for_status.return_value = None

    # Mock fetch response
    fetch_response = Mock()
    fetch_response.json.return_value = {
        "result": {
            "12345678": {
                "title": "Test Article 1",
                "authors": [{"name": "Smith J"}],
                "fulljournalname": "Test Journal",
                "pubdate": "2024",
                "elocationid": "doi:10.1234/test",
            },
            "87654321": {
                "title": "Test Article 2",
                "authors": [{"name": "Jones A"}],
                "fulljournalname": "Science",
                "pubdate": "2023",
                "elocationid": "",
            },
        }
    }
    fetch_response.raise_for_status.return_value = None

    # Mock abstract response
    abstract_response = Mock()
    abstract_response.raise_for_status.return_value = None
    abstract_response.text = "<xml></xml>"

    mock_get.side_effect = [search_response, fetch_response, abstract_response]

    # Test search
    results = agent._pubmed_search("test query", max_results=5)

    assert len(results) == 2
    assert results[0]["pmid"] == "12345678"
    assert results[0]["title"] == "Test Article 1"
    assert results[0]["source"] == "PubMed"
    assert "pubmed.ncbi.nlm.nih.gov" in results[0]["url"]


def test_parse_authors(agent):
    """Test author parsing."""
    authors_data = [
        {"name": "Smith J"},
        {"name": "Jones A"},
        {"name": "Brown B"},
        {"name": "Green G"},
    ]

    result = agent._parse_authors(authors_data)
    assert result == "Smith J, Jones A, Brown B, et al."

    # Test with fewer authors
    result = agent._parse_authors(authors_data[:2])
    assert result == "Smith J, Jones A"

    # Test empty list
    result = agent._parse_authors([])
    assert result == ""


@patch("microgrowagents.agents.literature_agent.requests.get")
def test_run_method(mock_get, agent):
    """Test the main run method."""
    # Mock responses
    search_response = Mock()
    search_response.json.return_value = {"esearchresult": {"idlist": []}}
    search_response.raise_for_status.return_value = None

    mock_get.return_value = search_response

    result = agent.run("test query", max_results=5, search_type="pubmed")

    assert result["success"] is True
    assert "results" in result
    assert "pubmed" in result["results"]
    assert result["query"] == "test query"


def test_search_for_organism(agent):
    """Test organism-specific search."""
    with patch.object(agent, "run") as mock_run:
        mock_run.return_value = {"success": True, "results": {}}

        agent.search_for_organism("Escherichia coli")

        # Check that run was called with appropriate query
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "Escherichia coli" in call_args[0][0]
        assert "growth medium" in call_args[0][0]


def test_search_for_ingredient(agent):
    """Test ingredient-specific search."""
    with patch.object(agent, "run") as mock_run:
        mock_run.return_value = {"success": True, "results": {}}

        agent.search_for_ingredient("glucose")

        # Check that run was called with appropriate query
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "glucose" in call_args[0][0]
        assert "concentration" in call_args[0][0]

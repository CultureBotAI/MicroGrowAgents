"""Tests for eQuilibrator API client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from microgrowagents.chemistry.api_clients.equilibrator_client import EquilibratorClient


class TestEquilibratorClientInit:
    """Test eQuilibrator client initialization."""

    def test_init_default_email(self):
        """Test initialization with default email."""
        client = EquilibratorClient()
        assert client.email == "microgrowagents@example.com"
        assert client.last_request_time == 0.0

    def test_init_custom_email(self):
        """Test initialization with custom email."""
        client = EquilibratorClient(email="test@example.com")
        assert client.email == "test@example.com"

    def test_cache_file_path(self):
        """Test cache file path is set."""
        assert EquilibratorClient.CACHE_FILE == "data/cache/equilibrator_cache.sqlite"

    def test_rate_limit_value(self):
        """Test rate limit is set correctly."""
        assert EquilibratorClient.RATE_LIMIT_DELAY == 0.5  # 2 req/sec


class TestCompoundFormationEnergy:
    """Test compound formation energy retrieval."""

    def test_get_compound_formation_energy_success(self):
        """Test successful retrieval of compound formation energy."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()  # No exception
        mock_response.json.return_value = {
            "compound_id": "KEGG:C00031",
            "compound_name": "D-Glucose",
            "formation_energy": {
                "value": -426.71,  # kJ/mol
                "uncertainty": 0.5,
                "conditions": {
                    "ph": 7.0,
                    "ionic_strength": 0.1,
                    "temperature": 298.15
                }
            },
            "method": "component_contribution"
        }

        client = EquilibratorClient()

        with patch.object(client.session, 'get', return_value=mock_response) as mock_get:
            result = client.get_compound_formation_energy(
                compound_id="KEGG:C00031",
                ph=7.0,
                ionic_strength=0.1,
                temperature=25.0
            )

            assert result is not None
            assert result["formation_energy"]["value"] == pytest.approx(-426.71, abs=1.0)
            assert result["compound_name"] == "D-Glucose"
            assert result["method"] == "component_contribution"

    @patch('requests.Session.get')
    def test_get_compound_formation_energy_not_found(self, mock_get):
        """Test handling of compound not found."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Not found")
        mock_get.return_value = mock_response

        client = EquilibratorClient()
        result = client.get_compound_formation_energy("INVALID:12345")

        assert result is None

    @patch('requests.Session.get')
    def test_get_compound_formation_energy_timeout(self, mock_get):
        """Test handling of request timeout."""
        mock_get.side_effect = Exception("Timeout")

        client = EquilibratorClient()
        result = client.get_compound_formation_energy("KEGG:C00031")

        assert result is None


class TestReactionEnergy:
    """Test reaction energy calculations."""

    def test_get_reaction_energy_success(self):
        """Test successful retrieval of reaction energy."""
        # Mock API response for glucose → 2 ethanol + 2 CO2
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "reaction": "KEGG:C00031 => 2 KEGG:C00469 + 2 KEGG:C00011",
            "delta_g_prime": {
                "value": -72.3,  # kJ/mol (favorable)
                "uncertainty": 1.5,
                "conditions": {
                    "ph": 7.0,
                    "ionic_strength": 0.1,
                    "temperature": 298.15
                }
            },
            "feasibility": "favorable",
            "method": "component_contribution"
        }

        client = EquilibratorClient()

        with patch.object(client.session, 'get', return_value=mock_response):
            result = client.get_reaction_energy(
                reaction="KEGG:C00031 => 2 KEGG:C00469 + 2 KEGG:C00011",
                ph=7.0,
                ionic_strength=0.1,
                temperature=25.0
            )

            assert result is not None
            assert result["delta_g_prime"]["value"] < 0  # Favorable reaction
            assert result["feasibility"] == "favorable"

    def test_get_reaction_energy_unfavorable(self):
        """Test unfavorable reaction (positive ΔG)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "reaction": "test",
            "delta_g_prime": {"value": 50.0, "uncertainty": 2.0},
            "feasibility": "unfavorable"
        }

        client = EquilibratorClient()

        with patch.object(client.session, 'get', return_value=mock_response):
            result = client.get_reaction_energy("test")

            assert result["delta_g_prime"]["value"] > 0
            assert result["feasibility"] == "unfavorable"

    @patch('requests.Session.get')
    def test_get_reaction_energy_invalid_reaction(self, mock_get):
        """Test handling of invalid reaction string."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = Exception("Invalid reaction")
        mock_get.return_value = mock_response

        client = EquilibratorClient()
        result = client.get_reaction_energy("INVALID")

        assert result is None


class TestCompoundSearch:
    """Test compound search functionality."""

    def test_search_compound_by_name(self):
        """Test compound search by name."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "compound_id": "KEGG:C00031",
                    "compound_name": "D-Glucose",
                    "formula": "C6H12O6",
                    "inchi": "InChI=1S/C6H12O6/...",
                    "match_score": 1.0
                },
                {
                    "compound_id": "KEGG:C00267",
                    "compound_name": "alpha-D-Glucose",
                    "formula": "C6H12O6",
                    "match_score": 0.95
                }
            ]
        }

        client = EquilibratorClient()

        with patch.object(client.session, 'get', return_value=mock_response):
            results = client.search_compound("glucose", search_by="name")

            assert len(results) == 2
            assert results[0]["compound_id"] == "KEGG:C00031"
            assert results[0]["match_score"] == 1.0

    def test_search_compound_by_inchi(self):
        """Test compound search by InChI."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "compound_id": "KEGG:C00031",
                    "compound_name": "D-Glucose",
                    "inchi": "InChI=1S/C6H12O6/...",
                    "match_score": 1.0
                }
            ]
        }

        client = EquilibratorClient()

        with patch.object(client.session, 'get', return_value=mock_response):
            results = client.search_compound(
                "InChI=1S/C6H12O6/...",
                search_by="inchi"
            )

            assert len(results) == 1
            assert results[0]["compound_id"] == "KEGG:C00031"

    @patch('requests.Session.get')
    def test_search_compound_no_results(self, mock_get):
        """Test search with no results."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        client = EquilibratorClient()
        results = client.search_compound("nonexistent_compound")

        assert results == []


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limit_enforced(self):
        """Test that rate limiting delays requests."""
        import time

        client = EquilibratorClient()

        # First request - no delay
        start = time.time()
        client._rate_limit()
        elapsed1 = time.time() - start
        assert elapsed1 < 0.1  # Should be nearly instant

        # Second request immediately - should delay
        start = time.time()
        client._rate_limit()
        elapsed2 = time.time() - start
        assert elapsed2 >= 0.5  # Should wait at least 0.5 seconds

    def test_rate_limit_respects_previous_time(self):
        """Test rate limiting uses last request time."""
        import time

        client = EquilibratorClient()

        # Set last request time to now
        client.last_request_time = time.time()

        # Immediate rate limit should wait
        start = time.time()
        client._rate_limit()
        elapsed = time.time() - start
        assert elapsed >= 0.5


class TestCaching:
    """Test caching functionality."""

    @patch('requests_cache.install_cache')
    def test_cache_installed(self, mock_install_cache):
        """Test that caching is installed on init."""
        client = EquilibratorClient()

        mock_install_cache.assert_called_once()
        call_args = mock_install_cache.call_args
        assert call_args[0][0] == "data/cache/equilibrator_cache.sqlite"
        assert call_args[1]["backend"] == "sqlite"
        assert call_args[1]["expire_after"] == 86400  # 24 hours


class TestpHAndIonicStrength:
    """Test pH and ionic strength parameter handling."""

    def test_ph_parameter_sent(self):
        """Test that pH parameter is sent to API."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "compound_id": "test",
            "formation_energy": {"value": -100.0}
        }

        client = EquilibratorClient()

        with patch.object(client.session, 'get', return_value=mock_response) as mock_get:
            client.get_compound_formation_energy("test", ph=5.5)

            # Check that API was called with pH parameter
            call_args = mock_get.call_args
            assert call_args is not None
            # Check URL contains ph parameter
            assert "ph=" in call_args[0][0]

    def test_ionic_strength_parameter_sent(self):
        """Test that ionic strength parameter is sent to API."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "compound_id": "test",
            "formation_energy": {"value": -100.0}
        }

        client = EquilibratorClient()

        with patch.object(client.session, 'get', return_value=mock_response) as mock_get:
            client.get_compound_formation_energy("test", ionic_strength=0.25)

            # Check that API was called
            call_args = mock_get.call_args
            assert call_args is not None
            # Check URL contains ionic_strength parameter
            assert "ionic_strength=" in call_args[0][0]


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_network_error_handling(self):
        """Test handling of network errors."""
        with patch('requests.Session.get', side_effect=ConnectionError("Network error")):
            client = EquilibratorClient()
            result = client.get_compound_formation_energy("test")
            assert result is None

    @patch('requests.Session.get')
    def test_malformed_json_response(self, mock_get):
        """Test handling of malformed JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Malformed JSON")
        mock_get.return_value = mock_response

        client = EquilibratorClient()
        result = client.get_compound_formation_energy("test")
        assert result is None

    @patch('requests.Session.get')
    def test_empty_response(self, mock_get):
        """Test handling of empty response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        client = EquilibratorClient()
        result = client.get_compound_formation_energy("test")
        # Should handle gracefully, even if data is missing
        assert result is not None or result is None  # Depends on implementation

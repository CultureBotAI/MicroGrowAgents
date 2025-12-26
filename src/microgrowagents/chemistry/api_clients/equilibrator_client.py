"""
eQuilibrator API client for biochemical thermodynamics data.

eQuilibrator (https://equilibrator.weizmann.ac.il/) provides biochemical
thermodynamic data using the Component Contribution method. This client
accesses formation energies and reaction energies for metabolic compounds
and reactions.

API Documentation: https://equilibrator.readthedocs.io/
Component Contribution: Noor et al., 2013, PLoS Comput Biol

Usage Policy:
- Rate limit to 2 requests per second (0.5s delay)
- Use aggressive caching (24 hours) as thermodynamic data is stable
- Provide email in User-Agent for contact
"""

import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urlencode

import requests
import requests_cache


class EquilibratorClient:
    """
    Client for eQuilibrator biochemical thermodynamics API.

    Features:
    - Compound formation energy (ΔGf°) retrieval
    - Reaction energy (ΔG'°) calculation
    - pH and ionic strength corrections
    - Compound search by name/InChI/KEGG ID
    - Automatic rate limiting (2 req/sec)
    - Response caching (24 hours)

    Examples:
        >>> client = EquilibratorClient(email="user@example.com")
        >>> # Get formation energy for glucose
        >>> result = client.get_compound_formation_energy(
        ...     compound_id="KEGG:C00031",
        ...     ph=7.0
        ... )  # doctest: +SKIP
    """

    BASE_URL = "https://api.equilibrator.weizmann.ac.il/v1"
    RATE_LIMIT_DELAY = 0.5  # 500ms between requests (2 req/sec max)
    CACHE_FILE = "data/cache/equilibrator_cache.sqlite"

    def __init__(self, email: str = "microgrowagents@example.com"):
        """
        Initialize eQuilibrator client.

        Args:
            email: Contact email for User-Agent header
        """
        self.email = email
        self.last_request_time = 0.0

        # Setup caching (24 hour expiration - thermodynamic data is stable)
        requests_cache.install_cache(
            self.CACHE_FILE,
            backend="sqlite",
            expire_after=86400,  # 24 hours
        )

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"MicroGrowAgents/1.0 ({self.email})",
            "Accept": "application/json"
        })

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    def get_compound_formation_energy(
        self,
        compound_id: str,
        ph: float = 7.0,
        ionic_strength: float = 0.1,
        temperature: float = 25.0
    ) -> Optional[Dict[str, Any]]:
        """
        Get standard formation energy (ΔGf'°) for a compound.

        The formation energy is adjusted for pH, ionic strength, and temperature
        using the Component Contribution method.

        Args:
            compound_id: Compound identifier (KEGG:C00031, InChI, etc.)
            ph: pH value (default: 7.0, biochemical standard state)
            ionic_strength: Ionic strength in M (default: 0.1)
            temperature: Temperature in °C (default: 25.0)

        Returns:
            Dictionary with keys:
                - compound_id: Compound identifier
                - compound_name: Common name
                - formation_energy: Dict with value (kJ/mol), uncertainty, conditions
                - method: Calculation method
            or None if not found/error

        Examples:
            >>> client = EquilibratorClient()
            >>> result = client.get_compound_formation_energy(
            ...     "KEGG:C00031",
            ...     ph=7.0
            ... )  # doctest: +SKIP
            >>> result["compound_name"]  # doctest: +SKIP
            'D-Glucose'
        """
        self._rate_limit()

        # Convert temperature to Kelvin
        temp_kelvin = temperature + 273.15

        # Build query parameters
        params = {
            "ph": ph,
            "ionic_strength": ionic_strength,
            "temperature": temp_kelvin
        }

        # Construct URL
        # Note: This is a simplified implementation
        # Real eQuilibrator API may have different endpoint structure
        url = f"{self.BASE_URL}/compounds/{quote_plus(compound_id)}/formation_energy"
        url_with_params = f"{url}?{urlencode(params)}"

        try:
            response = self.session.get(url_with_params, timeout=15)
            response.raise_for_status()
            data = response.json()

            return data

        except requests.exceptions.HTTPError as e:
            # Handle 404, 400, etc.
            return None
        except requests.exceptions.Timeout:
            return None
        except requests.exceptions.ConnectionError:
            return None
        except ValueError:
            # JSON decode error
            return None
        except Exception as e:
            # Catch-all for unexpected errors
            return None

    def get_reaction_energy(
        self,
        reaction: str,
        ph: float = 7.0,
        ionic_strength: float = 0.1,
        temperature: float = 25.0
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate reaction energy (ΔG'°) for a biochemical reaction.

        The reaction energy is calculated using formation energies of reactants
        and products, adjusted for pH, ionic strength, and temperature.

        Args:
            reaction: Reaction string (e.g., "KEGG:C00031 => 2 KEGG:C00469 + 2 KEGG:C00011")
            ph: pH value (default: 7.0)
            ionic_strength: Ionic strength in M (default: 0.1)
            temperature: Temperature in °C (default: 25.0)

        Returns:
            Dictionary with keys:
                - reaction: Reaction string
                - delta_g_prime: Dict with value (kJ/mol), uncertainty, conditions
                - feasibility: "favorable" (ΔG < 0) or "unfavorable" (ΔG > 0)
                - method: Calculation method
            or None if error

        Examples:
            >>> client = EquilibratorClient()
            >>> # Glucose fermentation to ethanol
            >>> result = client.get_reaction_energy(
            ...     "KEGG:C00031 => 2 KEGG:C00469 + 2 KEGG:C00011",
            ...     ph=7.0
            ... )  # doctest: +SKIP
            >>> result["feasibility"]  # doctest: +SKIP
            'favorable'
        """
        self._rate_limit()

        # Convert temperature to Kelvin
        temp_kelvin = temperature + 273.15

        # Build query parameters
        params = {
            "ph": ph,
            "ionic_strength": ionic_strength,
            "temperature": temp_kelvin,
            "reaction": reaction
        }

        # Construct URL
        url = f"{self.BASE_URL}/reactions/energy"
        url_with_params = f"{url}?{urlencode(params)}"

        try:
            response = self.session.get(url_with_params, timeout=15)
            response.raise_for_status()
            data = response.json()

            return data

        except requests.exceptions.HTTPError as e:
            return None
        except requests.exceptions.Timeout:
            return None
        except requests.exceptions.ConnectionError:
            return None
        except ValueError:
            return None
        except Exception as e:
            return None

    def search_compound(
        self,
        query: str,
        search_by: str = "name"
    ) -> List[Dict[str, Any]]:
        """
        Search for compounds by name, InChI, or KEGG ID.

        Args:
            query: Search query string
            search_by: Search field - "name", "inchi", or "kegg_id" (default: "name")

        Returns:
            List of matching compounds with keys:
                - compound_id: Compound identifier
                - compound_name: Common name
                - formula: Molecular formula
                - inchi: InChI string (if available)
                - match_score: Match quality (0.0 to 1.0)

        Examples:
            >>> client = EquilibratorClient()
            >>> results = client.search_compound("glucose")  # doctest: +SKIP
            >>> len(results) > 0  # doctest: +SKIP
            True
        """
        self._rate_limit()

        # Build query parameters
        params = {
            "query": query,
            "search_by": search_by
        }

        url = f"{self.BASE_URL}/compounds/search"
        url_with_params = f"{url}?{urlencode(params)}"

        try:
            response = self.session.get(url_with_params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Extract results list
            results = data.get("results", [])
            return results

        except requests.exceptions.HTTPError:
            return []
        except requests.exceptions.Timeout:
            return []
        except requests.exceptions.ConnectionError:
            return []
        except ValueError:
            return []
        except Exception:
            return []

    def get_compound_details(
        self,
        compound_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a compound.

        Args:
            compound_id: Compound identifier (KEGG, InChI, etc.)

        Returns:
            Dictionary with compound details or None if not found

        Examples:
            >>> client = EquilibratorClient()
            >>> details = client.get_compound_details("KEGG:C00031")  # doctest: +SKIP
            >>> details["compound_name"]  # doctest: +SKIP
            'D-Glucose'
        """
        self._rate_limit()

        url = f"{self.BASE_URL}/compounds/{quote_plus(compound_id)}"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            return data

        except Exception:
            return None

    def batch_formation_energy(
        self,
        compound_ids: List[str],
        ph: float = 7.0,
        ionic_strength: float = 0.1,
        temperature: float = 25.0
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Batch retrieval of formation energies for multiple compounds.

        Args:
            compound_ids: List of compound identifiers
            ph: pH value
            ionic_strength: Ionic strength in M
            temperature: Temperature in °C

        Returns:
            Dictionary mapping compound_id → formation energy result
            (or None if not found)

        Examples:
            >>> client = EquilibratorClient()
            >>> results = client.batch_formation_energy([
            ...     "KEGG:C00031",  # glucose
            ...     "KEGG:C00469"   # ethanol
            ... ])  # doctest: +SKIP
        """
        results = {}

        for compound_id in compound_ids:
            results[compound_id] = self.get_compound_formation_energy(
                compound_id,
                ph=ph,
                ionic_strength=ionic_strength,
                temperature=temperature
            )
            # Rate limiting is handled in get_compound_formation_energy

        return results

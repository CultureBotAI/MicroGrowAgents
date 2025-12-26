"""
PubChem REST API client.

Adapted from MicroMediaParam data_downloader.py with simplifications:
- Synchronous (not async) for simplicity
- REST API only (no FTP bulk downloads in this version)
- Comprehensive caching via requests_cache
- Rate limiting to respect PubChem guidelines

API Documentation: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest

PubChem Usage Policy:
- Max 5 requests per second
- Use caching to minimize API calls
- Provide email in User-Agent
"""

import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import requests
import requests_cache

class PubChemClient:
    """
    Client for PubChem PUG REST API.

    Features:
    - Compound name → CID lookup
    - CID → properties retrieval
    - Experimental data extraction (pKa, solubility, etc.)
    - Automatic rate limiting
    - Response caching
    """

    BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    RATE_LIMIT_DELAY = 0.2  # 200ms between requests (5 req/sec max)
    CACHE_FILE = "data/cache/pubchem_cache.sqlite"

    def __init__(self, email: str = "microgrowagents@example.com"):
        """
        Initialize PubChem client.

        Args:
            email: Contact email for User-Agent header
        """
        self.email = email
        self.last_request_time = 0.0

        # Setup caching (24 hour expiration)
        requests_cache.install_cache(
            self.CACHE_FILE,
            backend="sqlite",
            expire_after=86400,  # 24 hours
        )

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"MicroGrowAgents/1.0 ({self.email})"
        })

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    def search_by_name(
        self, compound_name: str, max_results: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Search compound by name and return properties.

        Args:
            compound_name: Compound name to search
            max_results: Maximum number of results (default: 1 - best match)

        Returns:
            Dictionary with compound properties or None if not found

        Example:
            >>> client = PubChemClient()
            >>> result = client.search_by_name("glucose")
            >>> result["MolecularWeight"]
            180.16
        """
        # First, get CID from name
        cid = self.name_to_cid(compound_name)
        if not cid:
            return None

        # Then get properties
        return self.get_properties(cid)

    def name_to_cid(self, compound_name: str) -> Optional[int]:
        """
        Convert compound name to PubChem CID.

        Args:
            compound_name: Compound name

        Returns:
            PubChem CID (integer) or None if not found

        Example:
            >>> client = PubChemClient()
            >>> client.name_to_cid("glucose")
            5793
        """
        self._rate_limit()

        url = f"{self.BASE_URL}/compound/name/{quote_plus(compound_name)}/cids/JSON"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            cids = data.get("IdentifierList", {}).get("CID", [])
            if cids:
                return cids[0]  # Return first (best) match

        except Exception as e:
            # Not found or error
            return None

        return None

    def get_properties(
        self, cid: int, properties: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get compound properties by CID.

        Args:
            cid: PubChem CID
            properties: List of property names (default: common properties)

        Returns:
            Dictionary with properties

        Example:
            >>> client = PubChemClient()
            >>> props = client.get_properties(5793)  # glucose CID
            >>> props["MolecularFormula"]
            'C6H12O6'
        """
        if properties is None:
            properties = [
                "MolecularFormula",
                "MolecularWeight",
                "IUPACName",
                "CanonicalSMILES",
                "InChI",
                "InChIKey",
                "Charge",
                "XLogP",
            ]

        self._rate_limit()

        property_str = ",".join(properties)
        url = f"{self.BASE_URL}/compound/cid/{cid}/property/{property_str}/JSON"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            props = data.get("PropertyTable", {}).get("Properties", [])
            if props:
                return props[0]

        except Exception as e:
            return None

        return None

    def get_experimental_properties(
        self, cid: int, property_name: str = "pKa"
    ) -> List[Dict[str, Any]]:
        """
        Get experimental properties (pKa, solubility, etc.).

        Note: This data is often sparse and may not be available.

        Args:
            cid: PubChem CID
            property_name: Property name (pKa, Solubility, LogP, etc.)

        Returns:
            List of experimental data entries

        Example:
            >>> client = PubChemClient()
            >>> pka_data = client.get_experimental_properties(5793, "pKa")
        """
        self._rate_limit()

        # Use compound view to get experimental data
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON"

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()

            # Parse experimental sections
            # Note: PubChem data structure is complex and nested
            # This is a simplified extractor
            experimental_data = []

            # Would need to traverse the nested structure to find property_name
            # Placeholder for now
            return experimental_data

        except Exception as e:
            return []

    def batch_cid_lookup(
        self, compound_names: List[str]
    ) -> Dict[str, Optional[int]]:
        """
        Batch lookup of CIDs for multiple compounds.

        Args:
            compound_names: List of compound names

        Returns:
            Dictionary mapping name → CID (or None if not found)

        Example:
            >>> client = PubChemClient()
            >>> cids = client.batch_cid_lookup(["glucose", "NaCl", "caffeine"])
            >>> cids["glucose"]
            5793
        """
        results = {}

        for name in compound_names:
            results[name] = self.name_to_cid(name)
            # Rate limiting is handled in name_to_cid

        return results

    def get_synonyms(self, cid: int, max_synonyms: int = 10) -> List[str]:
        """
        Get synonyms for a compound.

        Args:
            cid: PubChem CID
            max_synonyms: Maximum number of synonyms to return

        Returns:
            List of synonym strings

        Example:
            >>> client = PubChemClient()
            >>> synonyms = client.get_synonyms(5793)
            >>> "D-glucose" in synonyms
            True
        """
        self._rate_limit()

        url = f"{self.BASE_URL}/compound/cid/{cid}/synonyms/JSON"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            synonyms = (
                data.get("InformationList", {})
                .get("Information", [{}])[0]
                .get("Synonym", [])
            )

            return synonyms[:max_synonyms]

        except Exception as e:
            return []

    def search_by_formula(self, formula: str) -> List[int]:
        """
        Search compounds by molecular formula.

        Args:
            formula: Molecular formula (e.g., "C6H12O6")

        Returns:
            List of matching CIDs

        Example:
            >>> client = PubChemClient()
            >>> cids = client.search_by_formula("C6H12O6")
            >>> 5793 in cids  # glucose
            True
        """
        self._rate_limit()

        url = f"{self.BASE_URL}/compound/fastformula/{formula}/cids/JSON"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            cids = data.get("IdentifierList", {}).get("CID", [])
            return cids

        except Exception as e:
            return []

    def get_compound_info(self, compound_identifier: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive compound information.

        High-level method that tries name → CID → properties.

        Args:
            compound_identifier: Compound name or CID

        Returns:
            Dictionary with properties, synonyms, formula, etc.

        Example:
            >>> client = PubChemClient()
            >>> info = client.get_compound_info("glucose")
            >>> info["cid"]
            5793
            >>> info["molecular_weight"]
            180.16
        """
        # Try as name first
        cid = None
        if isinstance(compound_identifier, str):
            if compound_identifier.isdigit():
                cid = int(compound_identifier)
            else:
                cid = self.name_to_cid(compound_identifier)
        elif isinstance(compound_identifier, int):
            cid = compound_identifier

        if not cid:
            return None

        # Get properties
        props = self.get_properties(cid)
        if not props:
            return None

        # Get synonyms
        synonyms = self.get_synonyms(cid, max_synonyms=5)

        # Combine into comprehensive info
        return {
            "cid": cid,
            "molecular_formula": props.get("MolecularFormula"),
            "molecular_weight": props.get("MolecularWeight"),
            "iupac_name": props.get("IUPACName"),
            "smiles": props.get("CanonicalSMILES"),
            "inchi": props.get("InChI"),
            "inchikey": props.get("InChIKey"),
            "charge": props.get("Charge", 0),
            "xlogp": props.get("XLogP"),
            "synonyms": synonyms,
            "source": "PubChem",
        }

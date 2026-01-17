"""
NCBI Lookup Service for BioSample organism information.

Maps SAMN BioSample IDs to organism names and NCBITaxon IDs using NCBI E-utilities.

Author: MicroGrowAgents Team
"""

import json
import logging
import ssl
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger(__name__)


class NCBILookupService:
    """
    Query NCBI for organism information from BioSample IDs.

    Uses NCBI E-utilities API with rate limiting and caching.
    Rate limit: 3 requests/second (without API key).

    Example:
        >>> service = NCBILookupService()
        >>> result = service.lookup_biosample("SAMN00114986")
        >>> result["organism_name"]
        'Escherichia coli'
        >>> result["taxid"]
        '562'
    """

    def __init__(self, cache_file: Optional[Path] = None, rate_limit: float = 0.34):
        """
        Initialize NCBI Lookup Service.

        Args:
            cache_file: Path to cache file (default: data/processed/biosample_cache.json)
            rate_limit: Seconds between requests (default: 0.34 = ~3 req/sec)
        """
        if cache_file is None:
            cache_file = Path("data/processed/biosample_cache.json")

        self.cache_file = cache_file
        self.rate_limit = rate_limit
        self.cache = {}
        self.last_request_time = 0

        # NCBI E-utilities base URLs
        self.esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

        # SSL context for handling certificate issues
        self.ssl_context = ssl._create_unverified_context()

        # Load cache if exists
        self._load_cache()

    def _load_cache(self):
        """Load cached results from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} cached BioSample lookups")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                self.cache = {}

    def save_cache(self):
        """Save cached results to file."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f, indent=2)
            logger.info(f"Saved {len(self.cache)} BioSample lookups to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def _rate_limit_wait(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()

    def lookup_biosample(self, samn_id: str) -> Dict:
        """
        Query NCBI BioSample for organism info.

        Args:
            samn_id: BioSample ID (e.g., "SAMN00114986")

        Returns:
            Dict with organism_name, taxid, strain, error
            {
                'organism_name': 'Escherichia coli K-12',
                'taxid': '83333',
                'strain': 'K-12',
                'error': None
            }

        Example:
            >>> service = NCBILookupService()
            >>> result = service.lookup_biosample("SAMN00114986")
            >>> result["organism_name"] is not None
            True
        """
        # Check cache first
        if samn_id in self.cache:
            logger.debug(f"Cache hit for {samn_id}")
            return self.cache[samn_id]

        logger.info(f"Querying NCBI for {samn_id}")

        result = {
            "organism_name": None,
            "taxid": None,
            "strain": None,
            "error": None
        }

        try:
            # Step 1: Search BioSample database for SAMN ID
            self._rate_limit_wait()
            biosample_uid = self._esearch_biosample(samn_id)

            if not biosample_uid:
                result["error"] = "BioSample ID not found in NCBI"
                self.cache[samn_id] = result
                return result

            # Step 2: Fetch BioSample record
            self._rate_limit_wait()
            biosample_data = self._efetch_biosample(biosample_uid)

            if not biosample_data:
                result["error"] = "Failed to fetch BioSample record"
                self.cache[samn_id] = result
                return result

            # Step 3: Parse organism info from XML
            result = self._parse_biosample_xml(biosample_data)

            # Cache successful result
            self.cache[samn_id] = result

        except Exception as e:
            logger.error(f"Error looking up {samn_id}: {e}")
            result["error"] = str(e)
            self.cache[samn_id] = result

        return result

    def _esearch_biosample(self, samn_id: str) -> Optional[str]:
        """
        Search BioSample database for SAMN ID.

        Args:
            samn_id: BioSample ID

        Returns:
            BioSample UID (integer as string) or None
        """
        url = f"{self.esearch_url}?db=biosample&term={quote(samn_id)}&retmode=json"

        try:
            with urlopen(url, timeout=10, context=self.ssl_context) as response:
                data = json.loads(response.read().decode())

            uid_list = data.get("esearchresult", {}).get("idlist", [])
            if uid_list:
                return uid_list[0]

        except (URLError, HTTPError, json.JSONDecodeError) as e:
            logger.error(f"ESearch failed for {samn_id}: {e}")

        return None

    def _efetch_biosample(self, uid: str) -> Optional[str]:
        """
        Fetch BioSample record XML.

        Args:
            uid: BioSample UID

        Returns:
            XML string or None
        """
        url = f"{self.efetch_url}?db=biosample&id={uid}&retmode=xml"

        try:
            with urlopen(url, timeout=10, context=self.ssl_context) as response:
                return response.read().decode()

        except (URLError, HTTPError) as e:
            logger.error(f"EFetch failed for UID {uid}: {e}")

        return None

    def _parse_biosample_xml(self, xml_data: str) -> Dict:
        """
        Parse BioSample XML to extract organism info.

        Args:
            xml_data: BioSample XML response

        Returns:
            Dict with organism_name, taxid, strain
        """
        result = {
            "organism_name": None,
            "taxid": None,
            "strain": None,
            "error": None
        }

        try:
            root = ET.fromstring(xml_data)

            # Find BioSample element
            biosample = root.find(".//BioSample")
            if biosample is None:
                result["error"] = "No BioSample element found in XML"
                return result

            # Extract organism name
            organism = biosample.find(".//Organism")
            if organism is not None:
                organism_name = organism.find("OrganismName")
                if organism_name is not None:
                    result["organism_name"] = organism_name.text

                # Extract taxonomy ID
                tax_id_elem = organism.get("taxonomy_id")
                if tax_id_elem:
                    result["taxid"] = tax_id_elem

            # Extract strain from attributes
            attributes = biosample.find(".//Attributes")
            if attributes is not None:
                for attr in attributes.findall("Attribute"):
                    attr_name = attr.get("attribute_name", "").lower()
                    if attr_name in ["strain", "isolate", "culture collection"]:
                        result["strain"] = attr.text
                        break

        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            result["error"] = f"XML parsing error: {e}"

        return result

    def lookup_batch(self, samn_ids: List[str], save_interval: int = 10) -> Dict[str, Dict]:
        """
        Batch lookup with rate limiting and periodic cache saving.

        Args:
            samn_ids: List of BioSample IDs
            save_interval: Save cache every N lookups

        Returns:
            Dict mapping SAMN ID to result dict

        Example:
            >>> service = NCBILookupService()
            >>> ids = ["SAMN00114986", "SAMN00766392"]
            >>> results = service.lookup_batch(ids)
            >>> len(results)
            2
        """
        results = {}

        for i, samn_id in enumerate(samn_ids):
            results[samn_id] = self.lookup_biosample(samn_id)

            # Save cache periodically
            if (i + 1) % save_interval == 0:
                self.save_cache()
                logger.info(f"Progress: {i + 1}/{len(samn_ids)} BioSamples processed")

        # Final save
        self.save_cache()

        return results

    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dict with total_cached, successful, failed
        """
        successful = sum(1 for v in self.cache.values() if v.get("error") is None)
        failed = len(self.cache) - successful

        return {
            "total_cached": len(self.cache),
            "successful": successful,
            "failed": failed,
            "cache_file": str(self.cache_file)
        }

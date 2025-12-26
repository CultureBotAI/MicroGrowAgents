"""
ChEBI fuzzy matcher client.

Adapted from MicroMediaParam chebi_fuzzy_matcher.py with enhancements:
- Simplified interface for agent integration
- Uses local ChEBI OWL file (no API calls needed)
- Fast fuzzy string matching using fuzzywuzzy
- Two-tier matching: exact → fuzzy
- Comprehensive compound normalization

ChEBI OWL file can be downloaded from:
https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.owl
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional

from fuzzywuzzy import fuzz, process


class ChEBIClient:
    """
    Client for ChEBI compound matching using local OWL file.

    Features:
    - Exact and fuzzy compound name matching
    - Comprehensive normalization (hydrates, prefixes)
    - Synonym support (exact and related)
    - Fast in-memory lookups (no API rate limits)

    Examples:
        >>> client = ChEBIClient(Path("chebi.owl"))
        >>> results = client.match_compounds(["glucose", "NaCl"])
        >>> results["glucose"]["chebi_id"]
        'CHEBI:17234'
        >>> results["glucose"]["confidence"]
        1.0
    """

    # RDF/OWL namespaces
    NAMESPACES = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "owl": "http://www.w3.org/2002/07/owl#",
        "obo": "http://purl.obolibrary.org/obo/",
        "oboInOwl": "http://www.geneontology.org/formats/oboInOwl#",
    }

    # Hydration patterns to remove (from MicroMediaParam)
    HYDRATION_PATTERNS = [
        r"\s*[x×]\s*\d*\s*h2o\s*$",  # x H2O, × H2O
        r"\s*[·•]\s*\d*\s*h2o\s*$",  # · H2O, • H2O
        r"\s*\.\s*\d*\s*h2o\s*$",  # . H2O
        r"\s*\*\s*\d*\s*h2o\s*$",  # * H2O
        r"\s+\d*\s*h2o\s*$",  # Space H2O
        r"\s*\(\d*\s*h2o\)\s*$",  # (H2O), (2H2O)
        r"\s*\bmonohydrate\b\s*$",  # monohydrate
        r"\s*\bdihydrate\b\s*$",  # dihydrate
        r"\s*\btrihydrate\b\s*$",  # trihydrate
        r"\s*\btetrahydrate\b\s*$",  # tetrahydrate
        r"\s*\bpentahydrate\b\s*$",  # pentahydrate
        r"\s*\bhexahydrate\b\s*$",  # hexahydrate
        r"\s*\bheptahydrate\b\s*$",  # heptahydrate
        r"\s*\boctahydrate\b\s*$",  # octahydrate
        r"\s*\bnonahydrate\b\s*$",  # nonahydrate
        r"\s*\bdecahydrate\b\s*$",  # decahydrate
        r"\s*\bhydrate\b\s*$",  # generic hydrate
    ]

    # Chemical prefix conversions
    PREFIX_CONVERSIONS = {
        r"\bNa\s": "sodium ",
        r"\bNa-": "sodium ",
        r"\bNa2-": "disodium ",
        r"\bNH4-": "ammonium ",
        r"\bNH4\s": "ammonium ",
    }

    def __init__(self, owl_file: Path):
        """
        Initialize ChEBI client with OWL file.

        Args:
            owl_file: Path to ChEBI OWL file

        Raises:
            FileNotFoundError: If OWL file not found

        Examples:
            >>> client = ChEBIClient(Path("data/chebi.owl"))
        """
        self.owl_file = Path(owl_file)

        if not self.owl_file.exists():
            raise FileNotFoundError(f"ChEBI OWL file not found: {self.owl_file}")

        # Dictionary of {lowercase_name: {id, name, type, synonym?}}
        self.chebi_terms: Dict[str, Dict[str, str]] = {}

        # Load ChEBI data
        self._load_chebi_owl_data()

    def _load_chebi_owl_data(self) -> None:
        """
        Load ChEBI OWL file and build searchable index.

        Parses OWL XML and extracts:
        - Primary labels (rdfs:label)
        - Exact synonyms (oboInOwl:hasExactSynonym)
        - Related synonyms (oboInOwl:hasRelatedSynonym)

        Populates self.chebi_terms dictionary.
        """
        tree = ET.parse(self.owl_file)
        root = tree.getroot()

        # Find all owl:Class elements
        for owl_class in root.findall(".//owl:Class", self.NAMESPACES):
            # Get ChEBI ID from rdf:about attribute
            about = owl_class.get(f"{{{self.NAMESPACES['rdf']}}}about")
            if not about or "CHEBI_" not in about:
                continue

            # Convert CHEBI_12345 to CHEBI:12345
            chebi_id = about.split("/")[-1].replace("CHEBI_", "CHEBI:")

            # Get primary label
            label_elem = owl_class.find("rdfs:label", self.NAMESPACES)
            if label_elem is not None and label_elem.text:
                primary_label = label_elem.text.strip()
                self.chebi_terms[primary_label.lower()] = {
                    "id": chebi_id,
                    "name": primary_label,
                    "type": "primary",
                }

            # Get exact synonyms
            for syn_elem in owl_class.findall(
                "oboInOwl:hasExactSynonym", self.NAMESPACES
            ):
                if syn_elem.text:
                    synonym = syn_elem.text.strip()
                    self.chebi_terms[synonym.lower()] = {
                        "id": chebi_id,
                        "name": primary_label if label_elem is not None else synonym,
                        "type": "exact_synonym",
                        "synonym": synonym,
                    }

            # Get related synonyms
            for syn_elem in owl_class.findall(
                "oboInOwl:hasRelatedSynonym", self.NAMESPACES
            ):
                if syn_elem.text:
                    synonym = syn_elem.text.strip()
                    self.chebi_terms[synonym.lower()] = {
                        "id": chebi_id,
                        "name": primary_label if label_elem is not None else synonym,
                        "type": "related_synonym",
                        "synonym": synonym,
                    }

    def normalize_compound_name(self, name: str) -> str:
        """
        Normalize compound name for matching.

        Normalization steps:
        1. Remove hydration notations (·2H2O, monohydrate, etc.)
        2. Convert chemical prefixes (Na → sodium, NH4 → ammonium)
        3. Lowercase
        4. Normalize whitespace

        Args:
            name: Compound name

        Returns:
            Normalized name

        Examples:
            >>> client = ChEBIClient(owl_file)
            >>> client.normalize_compound_name("CaCl2·2H2O")
            'calcium chloride'
            >>> client.normalize_compound_name("Na-phosphate")
            'sodium phosphate'
        """
        normalized = name.strip()

        # Remove hydration patterns
        for pattern in self.HYDRATION_PATTERNS:
            normalized = re.sub(pattern, "", normalized, flags=re.IGNORECASE)

        # Convert chemical prefixes
        for pattern, replacement in self.PREFIX_CONVERSIONS.items():
            normalized = re.sub(pattern, replacement, normalized)

        # Lowercase and normalize whitespace
        normalized = normalized.lower()
        normalized = " ".join(normalized.split())

        return normalized

    def find_exact_matches(self, compounds: List[str]) -> Dict[str, Dict]:
        """
        Find exact matches for compound names.

        Args:
            compounds: List of compound names

        Returns:
            Dictionary mapping compound name → match info with:
            - chebi_id: ChEBI identifier
            - chebi_name: Primary ChEBI name
            - confidence: 1.0 for exact matches
            - match_type: "exact"
            - matched_term: Term that matched

        Examples:
            >>> results = client.find_exact_matches(["glucose", "NaCl"])
            >>> results["glucose"]["chebi_id"]
            'CHEBI:17234'
        """
        results = {}

        for compound in compounds:
            normalized = self.normalize_compound_name(compound)

            if normalized in self.chebi_terms:
                term_data = self.chebi_terms[normalized]
                results[compound] = {
                    "chebi_id": term_data["id"],
                    "chebi_name": term_data["name"],
                    "confidence": 1.0,
                    "match_type": "exact",
                    "matched_term": normalized,
                }

        return results

    def find_fuzzy_matches(
        self, compounds: List[str], min_confidence: float = 0.8, max_results: int = 3
    ) -> Dict[str, List[Dict]]:
        """
        Find fuzzy matches for compound names.

        Uses token sort ratio algorithm (fuzzywuzzy) which:
        - Tokenizes strings
        - Sorts tokens
        - Compares (handles word reordering)

        Args:
            compounds: List of compound names
            min_confidence: Minimum confidence threshold (0-1)
            max_results: Maximum matches per compound

        Returns:
            Dictionary mapping compound name → list of match dicts with:
            - chebi_id: ChEBI identifier
            - chebi_name: Primary ChEBI name
            - confidence: Confidence score (0-1)
            - match_type: "fuzzy"
            - matched_term: Term that matched

        Examples:
            >>> results = client.find_fuzzy_matches(["glukose"], min_confidence=0.7)
            >>> results["glukose"][0]["chebi_name"]
            'glucose'
        """
        results = {}

        # Get all searchable terms
        all_terms = list(self.chebi_terms.keys())

        for compound in compounds:
            normalized = self.normalize_compound_name(compound)

            # Use fuzzywuzzy to find best matches
            matches = process.extract(
                normalized,
                all_terms,
                scorer=fuzz.token_sort_ratio,
                limit=max_results,
            )

            # Filter by confidence and format results
            compound_matches = []
            for matched_term, score in matches:
                # Convert score from 0-100 to 0-1
                confidence = score / 100.0

                if confidence >= min_confidence:
                    term_data = self.chebi_terms[matched_term]
                    compound_matches.append(
                        {
                            "chebi_id": term_data["id"],
                            "chebi_name": term_data["name"],
                            "confidence": round(confidence, 3),
                            "match_type": "fuzzy",
                            "matched_term": matched_term,
                        }
                    )

            if compound_matches:
                results[compound] = compound_matches

        return results

    def match_compounds(
        self, compounds: List[str], min_fuzzy_confidence: float = 0.8
    ) -> Dict[str, Dict]:
        """
        Match compounds using exact → fuzzy strategy.

        Workflow:
        1. Deduplicate input compounds
        2. Try exact matches first
        3. Apply fuzzy matching to unmatched compounds
        4. Return single best match per compound

        Args:
            compounds: List of compound names
            min_fuzzy_confidence: Confidence threshold for fuzzy matching

        Returns:
            Dictionary mapping compound name → best match info

        Examples:
            >>> results = client.match_compounds(["glucose", "glukose"])
            >>> results["glucose"]["match_type"]
            'exact'
            >>> results["glukose"]["match_type"]
            'fuzzy'
        """
        if not compounds:
            return {}

        # Deduplicate compounds
        unique_compounds = list(set(compounds))

        # Step 1: Exact matches
        exact_results = self.find_exact_matches(unique_compounds)

        # Step 2: Fuzzy matches for unmatched compounds
        unmatched = [c for c in unique_compounds if c not in exact_results]

        fuzzy_results = {}
        if unmatched:
            fuzzy_matches = self.find_fuzzy_matches(
                unmatched, min_confidence=min_fuzzy_confidence
            )

            # Select best match for each compound
            for compound, matches in fuzzy_matches.items():
                if matches:
                    # Take highest confidence match
                    fuzzy_results[compound] = matches[0]

        # Combine results
        all_results = {**exact_results, **fuzzy_results}

        return all_results

    def get_compound_info(self, compound_name: str) -> Optional[Dict]:
        """
        Get ChEBI information for a single compound.

        Convenience method that tries matching and returns best result.

        Args:
            compound_name: Compound name

        Returns:
            Match info dict or None if no match found

        Examples:
            >>> info = client.get_compound_info("glucose")
            >>> info["chebi_id"]
            'CHEBI:17234'
        """
        results = self.match_compounds([compound_name])
        return results.get(compound_name)

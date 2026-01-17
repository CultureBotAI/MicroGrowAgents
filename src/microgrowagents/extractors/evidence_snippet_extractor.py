"""Evidence Snippet Extractor.

Extracts relevant 200-character snippets from scientific text that support
property values and mention organisms.
"""

from dataclasses import dataclass
from typing import List, Optional
import re


@dataclass
class EvidenceSnippet:
    """
    Evidence snippet extracted from text.

    Attributes:
        snippet: The extracted text (max 200 chars)
        confidence: Confidence score (0.0-1.0)
        contains_value: Whether snippet contains the property value
        contains_organism: Whether snippet contains organism name
        source_type: Type of source ("pdf" or "abstract")
    """
    snippet: str
    confidence: float
    contains_value: bool
    contains_organism: bool
    source_type: str = "pdf"


class EvidenceSnippetExtractor:
    """
    Extract evidence snippets from scientific text.

    Finds relevant passages that:
    1. Contain the property value
    2. Mention the organism
    3. Provide supporting context

    Examples:
        >>> extractor = EvidenceSnippetExtractor()
        >>> snippet = extractor.extract(
        ...     text="Growth of E. coli at 0.1 mM phosphate was observed.",
        ...     property_value="0.1 mM",
        ...     organism="E. coli"
        ... )
        >>> snippet.contains_value and snippet.contains_organism
        True
        >>> len(snippet.snippet) <= 200
        True
    """

    MAX_LENGTH = 200
    ELLIPSIS = "..."

    def __init__(self):
        """Initialize evidence snippet extractor."""
        pass

    def extract(
        self,
        text: str,
        property_value: str,
        organism: Optional[str] = None,
        property_name: Optional[str] = None
    ) -> EvidenceSnippet:
        """
        Extract evidence snippet from text.

        Args:
            text: Full markdown text to search
            property_value: Property value to find (e.g., "0.1 mM", "pH 7.0")
            organism: Organism name to include (optional)
            property_name: Property name for context (e.g., "Lower Bound")

        Returns:
            EvidenceSnippet with extracted text

        Examples:
            >>> extractor = EvidenceSnippetExtractor()
            >>> snippet = extractor.extract(
            ...     "E. coli requires 0.1 mM phosphate for growth",
            ...     "0.1 mM",
            ...     "E. coli"
            ... )
            >>> snippet.contains_value
            True
        """
        # Find sentences containing the property value
        value_sentences = self._find_sentences_with_value(text, property_value)

        if not value_sentences:
            # No sentences with value found - return context around property name
            return self._extract_contextual_snippet(text, property_name or "")

        # Find sentence that contains both value and organism (preferred)
        if organism:
            best_sentence = self._find_best_sentence_with_organism(
                value_sentences, organism
            )
            if best_sentence:
                snippet_text = self._truncate_snippet(best_sentence, property_value, organism)
                return EvidenceSnippet(
                    snippet=snippet_text,
                    confidence=0.95,
                    contains_value=True,
                    contains_organism=True
                )

        # Fallback: use first sentence with value
        best_sentence = value_sentences[0]
        snippet_text = self._truncate_snippet(best_sentence, property_value, organism)

        return EvidenceSnippet(
            snippet=snippet_text,
            confidence=0.8 if organism else 0.6,
            contains_value=True,
            contains_organism=bool(organism and organism in snippet_text)
        )

    def _find_sentences_with_value(self, text: str, value: str) -> List[str]:
        """
        Find sentences containing the property value.

        Args:
            text: Text to search
            value: Value to find

        Returns:
            List of sentences containing the value

        Examples:
            >>> extractor = EvidenceSnippetExtractor()
            >>> sentences = extractor._find_sentences_with_value(
            ...     "First sentence. Second with 0.1 mM. Third sentence.",
            ...     "0.1 mM"
            ... )
            >>> len(sentences) > 0
            True
        """
        # Split text into sentences
        # Use negative lookbehind to avoid splitting on abbreviations like "E. coli"
        # Pattern: period/!/?  followed by space, but NOT preceded by single capital letter
        sentence_pattern = r'(?<![A-Z])[.!?]\s+'
        sentences = re.split(sentence_pattern, text)

        # Find sentences containing the value
        matching_sentences = []
        for sentence in sentences:
            if value in sentence:
                # Clean up sentence
                sentence = sentence.strip()
                if sentence:
                    matching_sentences.append(sentence)

        return matching_sentences

    def _find_best_sentence_with_organism(
        self,
        sentences: List[str],
        organism: str
    ) -> Optional[str]:
        """
        Find best sentence that contains both value and organism.

        Args:
            sentences: List of candidate sentences
            organism: Organism name to find

        Returns:
            Best matching sentence or None

        Examples:
            >>> extractor = EvidenceSnippetExtractor()
            >>> sentences = ["E. coli grows at 0.1 mM", "Other sentence"]
            >>> result = extractor._find_best_sentence_with_organism(sentences, "E. coli")
            >>> result is not None
            True
        """
        # Look for sentences containing organism name
        for sentence in sentences:
            if organism in sentence:
                return sentence

            # Try abbreviated forms (e.g., "E. coli" if organism is "Escherichia coli")
            abbreviated = self._get_abbreviation(organism)
            if abbreviated and abbreviated in sentence:
                return sentence

        return None

    def _get_abbreviation(self, organism: str) -> Optional[str]:
        """
        Get abbreviation of organism name.

        Args:
            organism: Full organism name (e.g., "Escherichia coli")

        Returns:
            Abbreviated form (e.g., "E. coli") or None

        Examples:
            >>> extractor = EvidenceSnippetExtractor()
            >>> extractor._get_abbreviation("Escherichia coli")
            'E. coli'
            >>> extractor._get_abbreviation("E. coli")
            'E. coli'
        """
        parts = organism.split()
        if len(parts) >= 2:
            # Return first letter of genus + species
            return f"{parts[0][0]}. {parts[1]}"
        return None

    def _truncate_snippet(
        self,
        text: str,
        value: str,
        organism: Optional[str] = None
    ) -> str:
        """
        Truncate snippet to max 200 characters while preserving key elements.

        Strategy:
        1. If text <= 200 chars, return as-is
        2. Otherwise, keep text centered around value and organism

        Args:
            text: Text to truncate
            value: Property value (must be preserved)
            organism: Organism name (should be preserved if possible)

        Returns:
            Truncated text with ellipsis if needed

        Examples:
            >>> extractor = EvidenceSnippetExtractor()
            >>> result = extractor._truncate_snippet(
            ...     "A very long sentence " * 20,
            ...     "0.1 mM"
            ... )
            >>> len(result) <= 200
            True
        """
        if len(text) <= self.MAX_LENGTH:
            return text

        # Find position of value
        value_pos = text.find(value)
        if value_pos == -1:
            # Value not in text (shouldn't happen), truncate from start
            return f"{text[:self.MAX_LENGTH-3]}{self.ELLIPSIS}"

        # Calculate how much space we have
        available_space = self.MAX_LENGTH - len(self.ELLIPSIS) * 2  # Account for ellipsis on both ends

        # Try to center around value, but also consider organism position
        half_space = available_space // 2

        # Calculate start and end positions centered on value (value is most important)
        start = max(0, value_pos - half_space)
        end = min(len(text), value_pos + len(value) + half_space)

        # If organism specified, try to include it without losing the value
        if organism:
            organism_pos = text.find(organism)
            if organism_pos != -1 and organism_pos < value_pos:
                # Organism appears before value - try to include it
                # But ensure we still have the value by not going too far back
                desired_start = organism_pos
                if value_pos + len(value) - desired_start <= available_space:
                    # We can fit both organism and value
                    start = desired_start
                    end = start + available_space

        # Extract snippet
        snippet = text[start:end]

        # Add ellipsis if truncated
        if start > 0:
            snippet = f"{self.ELLIPSIS}{snippet}"
        if end < len(text):
            snippet = f"{snippet}{self.ELLIPSIS}"

        # Ensure length constraint
        if len(snippet) > self.MAX_LENGTH:
            snippet = snippet[:self.MAX_LENGTH-3] + self.ELLIPSIS

        return snippet

    def _extract_contextual_snippet(
        self,
        text: str,
        property_name: str
    ) -> EvidenceSnippet:
        """
        Extract contextual snippet when property value not found.

        Looks for property name mentions or related keywords.

        Args:
            text: Text to search
            property_name: Property name (e.g., "Lower Bound", "Toxicity")

        Returns:
            EvidenceSnippet with contextual information

        Examples:
            >>> extractor = EvidenceSnippetExtractor()
            >>> snippet = extractor._extract_contextual_snippet(
            ...     "The toxicity threshold was determined experimentally.",
            ...     "Toxicity"
            ... )
            >>> len(snippet.snippet) <= 200
            True
        """
        # Look for property-related keywords
        keywords = self._get_property_keywords(property_name)

        for keyword in keywords:
            if keyword.lower() in text.lower():
                # Find sentence with keyword
                sentences = self._find_sentences_with_value(text, keyword)
                if sentences:
                    snippet_text = self._truncate_snippet(sentences[0], keyword)
                    return EvidenceSnippet(
                        snippet=snippet_text,
                        confidence=0.5,  # Lower confidence for contextual match
                        contains_value=False,
                        contains_organism=False
                    )

        # No match found - return first 200 chars of abstract
        abstract_start = text[:self.MAX_LENGTH]
        return EvidenceSnippet(
            snippet=abstract_start,
            confidence=0.3,
            contains_value=False,
            contains_organism=False
        )

    def _get_property_keywords(self, property_name: str) -> List[str]:
        """
        Get keywords related to property name.

        Args:
            property_name: Property name

        Returns:
            List of related keywords

        Examples:
            >>> extractor = EvidenceSnippetExtractor()
            >>> keywords = extractor._get_property_keywords("Toxicity")
            >>> "toxic" in keywords
            True
        """
        keyword_map = {
            "toxicity": ["toxic", "toxicity", "inhibit", "lethal", "LD50", "EC50"],
            "lower bound": ["minimum", "lower bound", "threshold", "required"],
            "upper bound": ["maximum", "upper bound", "toxic", "inhibit"],
            "solubility": ["soluble", "solubility", "dissolve"],
            "ph effect": ["pH", "acid", "alkaline"],
            "pka": ["pKa", "dissociation"],
            "light sensitivity": ["light", "photodegradation", "photosensitive"],
            "autoclave stability": ["autoclave", "heat", "stability"],
            "metabolic role": ["metabolic", "pathway", "enzyme"],
        }

        # Get keywords for property (case-insensitive match)
        for key, keywords in keyword_map.items():
            if key in property_name.lower():
                return keywords

        # Default keywords
        return [property_name]

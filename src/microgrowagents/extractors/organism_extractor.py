"""Organism Extractor for Evidence.

Extracts organism names from scientific text using hybrid approach:
- Regex patterns for clear, structured organism mentions
- Claude Code integration for complex context-dependent extraction
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
import re

from microgrowagents.services.taxonomy_validator import TaxonomyValidator


@dataclass
class OrganismExtractionResult:
    """
    Result of organism extraction.

    Attributes:
        organisms: List of organism names found (empty if none)
        confidence: Confidence score (0.0-1.0)
        method: Extraction method used ("regex", "claude_code", "hybrid")
        context: Text context where organisms were found
    """
    organisms: List[str]
    confidence: float
    method: str
    context: str = ""

    def get_primary_organism(self) -> Optional[str]:
        """Get the first/primary organism or None."""
        return self.organisms[0] if self.organisms else None

    def get_all_organisms_string(self) -> str:
        """Get comma-separated list of all organisms."""
        return ", ".join(self.organisms) if self.organisms else ""


class OrganismExtractor:
    """
    Extract organism names from scientific text.

    Uses hybrid approach:
    1. Regex patterns for common formats (fast, high confidence)
    2. Claude Code for complex cases (slower, context-aware)

    Examples:
        >>> extractor = OrganismExtractor()
        >>> result = extractor.extract("Growth of Escherichia coli at 37°C")
        >>> "Escherichia coli" in result.organisms
        True
        >>> result.confidence > 0.8
        True
    """

    # Comprehensive blacklist of false positive patterns
    ORGANISM_BLACKLIST = {
        # Common sentence fragments
        "All of", "As a", "As shown", "As described", "After purification",
        "A prerequisite", "And in", "At the", "The first", "The second",
        "The third", "In this", "In addition", "In contrast", "For example",
        "These results", "This study", "Figure shows", "Table shows",

        # Method/procedure terms
        "Available online", "Buffer capacity", "Cell growth", "Dose dependency",
        "Protein expression", "After purification",

        # Publication metadata
        "Journal of", "Division of", "Department of", "Institute of",
        "Received in", "Available online",

        # Chemistry/buffer terms
        "Buffers for", "Hill reaction", "Phosphate has", "Properties of",
        "Representation of", "Similar functions", "The density", "The same",
        "These buffers", "These densities", "These two", "Water at",

        # Generic phrases
        "We describe", "We monitored", "We studied", "Increasing the", "Engineering and",

        # Short fragments (likely false positives)
        "Ten are", "Two of", "I and", "We studied E",
    }

    # Known biological organism indicators (genus names)
    KNOWN_GENERA = {
        "Escherichia", "Bacillus", "Salmonella", "Pseudomonas",
        "Staphylococcus", "Streptococcus", "Lactobacillus",
        "Clostridium", "Enterobacter", "Klebsiella", "Listeria",
        "Mycobacterium", "Vibrio", "Shigella", "Yersinia",
        "Campylobacter", "Helicobacter", "Legionella",
        "Methylobacterium", "Methylacidiphilum", "Gemmatimonas",
        "Methanococcus", "Methanobacterium", "Sulfolobus",
    }

    def __init__(self, use_taxonomy_validation: bool = True):
        """Initialize organism extractor with regex patterns.

        Args:
            use_taxonomy_validation: If True, validate against GTDB+LPSN databases (default: True)
        """
        # Regex patterns for organism names
        self.patterns = self._build_patterns()

        # Taxonomy validator (GTDB + LPSN)
        self.taxonomy_validator = None
        if use_taxonomy_validation:
            try:
                self.taxonomy_validator = TaxonomyValidator()
                print(f"[OrganismExtractor] Taxonomy validation enabled")
            except Exception as e:
                print(f"[OrganismExtractor] Warning: Could not load taxonomy validator: {e}")
                print(f"[OrganismExtractor] Falling back to heuristic validation")

    def _build_patterns(self) -> List[re.Pattern]:
        """
        Build regex patterns for organism name extraction.

        Returns:
            List of compiled regex patterns
        """
        patterns = []

        # Pattern 1: Full scientific name (Genus species)
        # Examples: Escherichia coli, Bacillus subtilis
        patterns.append(
            re.compile(r'\b([A-Z][a-z]+\s+[a-z]+)\b')
        )

        # Pattern 2: Abbreviated genus + species
        # Examples: E. coli, B. subtilis
        patterns.append(
            re.compile(r'\b([A-Z]\.?\s+[a-z]+)\b')
        )

        # Pattern 3: Scientific name with strain
        # Examples: E. coli K-12, Salmonella enterica LT2
        patterns.append(
            re.compile(r'\b([A-Z][a-z]+\s+[a-z]+\s+[A-Z0-9\-]+)\b')
        )

        # Pattern 4: Abbreviated with strain
        # Examples: E. coli K-12, S. enterica LT2
        patterns.append(
            re.compile(r'\b([A-Z]\.?\s+[a-z]+\s+[A-Z0-9\-]+)\b')
        )

        # Pattern 5: Full genus + species + subspecies
        # Examples: Salmonella enterica serovar Typhimurium
        patterns.append(
            re.compile(r'\b([A-Z][a-z]+\s+[a-z]+\s+serovar\s+[A-Z][a-z]+)\b')
        )

        return patterns

    def extract_with_regex(self, text: str, max_results: int = 10) -> OrganismExtractionResult:
        """
        Extract organisms using regex patterns.

        Args:
            text: Text to search for organisms
            max_results: Maximum number of unique organisms to extract

        Returns:
            OrganismExtractionResult with extracted organisms

        Examples:
            >>> extractor = OrganismExtractor()
            >>> result = extractor.extract_with_regex("E. coli and B. subtilis were tested")
            >>> len(result.organisms) >= 2
            True
        """
        organisms_found = set()
        context_snippets = []

        for pattern in self.patterns:
            matches = pattern.finditer(text)
            for match in matches:
                organism = match.group(1)

                # Normalize whitespace in organism name
                organism_normalized = ' '.join(organism.split())

                # Filter out false positives (common non-organism patterns)
                if self._is_valid_organism(organism_normalized):
                    organisms_found.add(organism_normalized)

                    # Extract context (±50 chars around match)
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end]
                    context_snippets.append(context)

                if len(organisms_found) >= max_results:
                    break

        # Sort organisms by frequency of mention (most common first)
        organisms_list = sorted(list(organisms_found))

        return OrganismExtractionResult(
            organisms=organisms_list,
            confidence=0.9 if organisms_list else 0.0,
            method="regex",
            context="; ".join(context_snippets[:3])  # First 3 contexts
        )

    def _is_valid_organism(self, text: str) -> bool:
        """
        Validate if extracted text is likely an organism name.

        Uses taxonomy database validation (GTDB+LPSN) when available,
        otherwise falls back to heuristic validation.

        Args:
            text: Potential organism name

        Returns:
            True if valid, False if likely false positive

        Examples:
            >>> extractor = OrganismExtractor(use_taxonomy_validation=False)
            >>> extractor._is_valid_organism("Escherichia coli")
            True
            >>> extractor._is_valid_organism("The first")
            False
            >>> extractor._is_valid_organism("All of")
            False
        """
        # Use taxonomy validation if available
        if self.taxonomy_validator:
            result = self.taxonomy_validator.validate(text)
            # Accept if validated with reasonable confidence
            return result.is_valid and result.confidence >= 0.7

        # Fall back to heuristic validation
        return self._heuristic_validation(text)

    def _heuristic_validation(self, text: str) -> bool:
        """Heuristic-based organism validation (fallback when taxonomy DB unavailable).

        Args:
            text: Potential organism name

        Returns:
            True if passes heuristic checks
        """
        # Check blacklist (case-sensitive)
        if text in self.ORGANISM_BLACKLIST:
            return False

        # Check case-insensitive blacklist matches
        if any(text.lower() == blacklisted.lower() for blacklisted in self.ORGANISM_BLACKLIST):
            return False

        # Must not be too short (< 5 chars likely fragment)
        if len(text) < 5:
            return False

        # Must not be too long (> 60 chars likely sentence fragment)
        if len(text) > 60:
            return False

        # Must have at least one lowercase letter (species name)
        if not any(c.islower() for c in text):
            return False

        # Split into words
        words = text.split()

        # Must have at least 2 words (Genus species)
        if len(words) < 2:
            return False

        # First word should be capitalized (Genus)
        if not words[0][0].isupper():
            return False

        # Normalize whitespace - replace multiple spaces/newlines with single space
        text = ' '.join(text.split())
        words = text.split()

        # Re-check word count after normalization
        if len(words) < 2:
            return False

        # Filter out common English words that shouldn't be genus names
        genus = words[0].rstrip('.,;:')  # Remove punctuation

        # Reject single-letter genus unless it's a known abbreviation
        # Known: E (Escherichia), B (Bacillus), S (Salmonella), P (Pseudomonas)
        if len(genus) == 1 and genus not in {"E", "B", "S", "P"}:
            return False

        common_genus_false_positives = {
            # Common English words
            "We", "The", "These", "This", "All", "Some", "Many", "Most",
            "Each", "Both", "Other", "Another", "Such", "Any", "Several",
            "Few", "One", "Two", "Three", "First", "Second", "Third",
            "After", "Before", "During", "When", "Where", "While", "As",
            "At", "By", "For", "From", "In", "Of", "On", "To", "With",
            "Similar", "Available", "Increasing", "Received", "Water",
            "Buffers", "Buffer", "Cell", "Cells", "Protein", "Proteins",
            "Journal", "Division", "Department", "Institute", "University",
            # Common sentence starters
            "They", "There", "Thus", "Moreover", "Much", "Great", "Since",
            "Function", "Twelve", "Four", "No", "If", "Because", "Consequently",
            "Presumably", "Obviously", "Whereas", "Adjacent", "Our", "It",
            "A", "Simple", "Various", "Was", "Had", "Has", "Have", "Were",
            # Publication metadata (HIGH FALSE POSITIVE RATE)
            "Mailing", "Published", "Present", "Supplemental", "Corresponding",
            "Author", "Authors", "Communication", "Biology", "Control",
            "Updated", "Light", "Key", "Specialty", "Work", "Recent",
            # Technical/biological terms (not organisms)
            "Dissociation", "Isothermal", "Specific", "Stock", "Batch",
            "Operating", "Continuous", "Maximum", "Standard", "Important",
            "Trace", "Synthetic", "Completed", "Properties", "Agreement",
            "Chromate", "Molybdate", "Selenate", "Radiometer", "Erlenmeyer",
            "Methanogenic", "Biochemical", "Biotechnological", "Antimicrobial",
            "Gene", "Bacterial", "Biofilm", "Transformation", "Wild",
            "Type", "Strain", "Mutants", "Encoding", "Despite", "Upon",
            "Bacteria", "Formation", "Expression", "Growth", "Activity",
            "Commercial", "Canada", "Maximal", "Reduced", "Electron",
            # Molecular biology terms
            "Fur", "Heavy", "Taken", "Representative", "Dietary", "Infectious",
            "Transition", "Intracellular", "Supplementary", "Femtomolar",
            "Metalloregulatory", "Homeostasis", "Regulation", "Represses",
            # Chemistry/methods
            "Reagent", "Analytical", "Culture", "Media", "Density", "Temperature",
            "Measurement", "Measurements", "Values", "Errors", "Loading",
            "Ostwald", "Tables", "Among", "Chemically", "Pure", "Determinations",
            "Contribution", "Never", "Viscometer", "Obtained",
            # Author names and institutions
            "Smith", "Whalley", "Smoothed", "Estimated", "Complexes", "Studies",
            "Total", "Early", "Brien", "Cai", "Gardner", "Latham", "Sahdev",
            "Venters", "Colleran", "Lens", "Patidar", "Steckel", "Wirtz",
            "Indian", "Centro", "Facultad", "Laboratorio", "Universidad",
            "Institut", "Germany", "Rehman", "Johns",
            # More false positives from full extraction
            "Abbreviations", "Complex", "Dr", "Phaseolus", "Sodium", "Ultraviolet",
            "Warburg", "Assay", "Comparative", "Data", "Further", "Inhibition",
            "More", "Null", "Set", "Sulfur", "Volatile", "Fresh", "Glacial",
            "Recrystallization", "Tricine", "Bicine", "Absorbance", "Actinic",
            "Almost", "Spinaciu", "Condensate", "Equilibrium", "Ethylbenzene",
            "Internal", "Isobaric", "Vapor", "Propylbenzene", "Cottrell",
            "Liquid", "Azarova", "Abiotic", "Bertani", "Laboratoire",
            "Microbiologie", "Slight", "Iron", "Using", "Alkalin", "Argon",
            "Capillary", "Corrective", "Differential", "Heating", "Surface",
            "Their", "Vertical", "Alkali", "Metal", "Molalities", "Neither",
            "Nineteen", "Runs", "Attention", "Far", "Special", "Analysis",
            "Showed", "Isopiestic", "Ratios", "Activity", "Coefficients",
            "Bell", "Binodal", "Cartesian", "Coordinates", "Diammonium",
            "Citrate", "Hydrogen", "Samples", "Having", "Silicone", "Rubber",
            "Ternary", "Lines", "Tie", "Actually", "Ample", "Azeotropic",
            "Compositions", "Gives", "Laar", "Equations", "Relating", "Only",
            "Previous", "Still", "Thorough", "Mixing", "Very", "Low",
            "Zinc", "Serves", "Manduca", "Sexta", "Photuris", "Material",
            "Information", "Emission", "Application", "Although", "Relevant",
            "Genotype", "Transformed", "Bands", "Corresponding", "Linear",
            "Least", "Smaller", "Decreases", "Also", "Note", "Rates",
            "Canada", "Fellowship", "Funding", "Fold", "Levels", "Acid",
            "Stress", "Although", "Properties", "Salts", "Such", "Words",
            "Active", "Against", "Peptides", "Dye", "Leakage", "Novel",
            "Antimicrobials", "Same", "Buffers", "Having", "Binding",
            "Over", "Time", "Motion", "Brownian", "He", "Treated", "Membranes",
            "Absorb", "Observed", "Section", "Yasir", "Controls", "Broth",
            "Address", "Additions", "May", "Liter", "Pour",
        }
        if genus in common_genus_false_positives:
            return False

        # Second word should be lowercase (species) or uppercase (strain)
        # But not all uppercase (likely acronym)
        if words[1].isupper() and len(words[1]) > 3:
            return False

        # Check if first word contains newlines (PDF artifact)
        if '\n' in words[0]:
            return False

        # Bonus: Check if genus is in known genera list (increases confidence but not required)
        # genus already defined above
        is_known_genus = genus in self.KNOWN_GENERA

        # Filter out common English words that match pattern
        common_words = {
            "Thus where", "Similar functions", "These densities",
            "Assays with", "Received in", "Tare b",
        }
        if text in common_words:
            return False

        # If it passes all checks, validate species name
        species = words[1] if len(words) > 1 else ""

        # Species should not be a common English word
        common_species_false_positives = {
            "was", "are", "is", "the", "and", "or", "of", "in", "to",
            "for", "with", "on", "at", "by", "from", "as", "has", "have",
            # Additional common English words seen in false positives
            "formed", "water", "tends", "more", "should", "above", "few",
            "new", "types", "other", "join", "values", "standard", "et",
            "initial", "examples", "producing", "reducing", "degradation",
            "involving", "methanogenic", "temperature", "composition",
            "author", "michael",
            # More false positives from pilot test
            "formal", "most", "constants", "we", "physical", "also", "all",
            "preliminary", "automatic", "solution", "compressibilities",
            "conditions", "volume", "impressive", "forms", "assay", "flasks",
            "flask", "only", "sugar", "function", "alkyl", "enters", "error",
            "addition", "density", "substrate", "metals", "issues", "toxicity",
            "among", "represents", "below",
            # More false positives from second pilot test
            "used", "formaticn", "decomposi", "melting", "vur", "ions",
            "spectra", "vessels", "prepared", "being", "cannot", "when",
            "where", "must", "were", "details", "assessment", "analysis",
            "investigations", "due", "than", "hypothesis", "no", "metabolism",
            "suspended",
        }
        if species.lower() in common_species_false_positives:
            return False

        # If genus is known, accept (high confidence)
        if is_known_genus:
            return True

        # Otherwise, accept if it passes basic checks
        # (allowing for novel organisms not in our list)
        return True

    def extract_from_title(self, text: str) -> OrganismExtractionResult:
        """
        Extract organism specifically from title or abstract section.

        Args:
            text: Title or abstract text

        Returns:
            OrganismExtractionResult with lower confidence (title-only mention)

        Examples:
            >>> extractor = OrganismExtractor()
            >>> result = extractor.extract_from_title("# Phosphate transport in E. coli")
            >>> len(result.organisms) > 0
            True
        """
        result = self.extract_with_regex(text, max_results=3)

        # Lower confidence if only found in title
        if result.organisms:
            return OrganismExtractionResult(
                organisms=result.organisms,
                confidence=0.7,  # Lower confidence for title-only
                method="regex_title",
                context=result.context
            )

        return result

    def extract_with_context(
        self,
        markdown_text: str,
        property_name: str,
        property_value: str
    ) -> OrganismExtractionResult:
        """
        Extract organism with context awareness.

        This method is a placeholder for Claude Code integration.
        In the actual implementation, this would use Claude Code to:
        1. Understand the experimental context
        2. Identify which organism the property applies to
        3. Handle multiple organisms in comparative studies

        Args:
            markdown_text: Full markdown content
            property_name: Property being extracted (e.g., "Lower Bound")
            property_value: Property value from CSV (e.g., "0.1 mM")

        Returns:
            OrganismExtractionResult with context-aware extraction

        Note:
            This method will be enhanced with Claude Code integration
            to handle complex cases that regex cannot solve.
        """
        # For now, use regex as fallback
        # TODO: Integrate Claude Code here for context-aware extraction
        return self.extract_with_regex(markdown_text)

    def extract(
        self,
        text: str,
        method: str = "hybrid",
        property_name: Optional[str] = None,
        property_value: Optional[str] = None
    ) -> OrganismExtractionResult:
        """
        Extract organisms using specified method.

        Args:
            text: Text to search
            method: Extraction method ("regex", "claude_code", "hybrid")
            property_name: Optional property name for context
            property_value: Optional property value for context

        Returns:
            OrganismExtractionResult

        Examples:
            >>> extractor = OrganismExtractor()
            >>> result = extractor.extract("E. coli grows at 0.1 mM phosphate")
            >>> len(result.organisms) > 0
            True
        """
        if method == "regex":
            return self.extract_with_regex(text)

        elif method == "claude_code":
            # Use context-aware extraction
            return self.extract_with_context(text, property_name or "", property_value or "")

        elif method == "hybrid":
            # Try regex first (fast)
            regex_result = self.extract_with_regex(text)

            # If high confidence, use regex result
            if regex_result.confidence >= 0.9 and regex_result.organisms:
                return regex_result

            # Otherwise, use context-aware extraction
            return self.extract_with_context(text, property_name or "", property_value or "")

        else:
            raise ValueError(f"Unknown extraction method: {method}")

    def infer_organism_from_context(self, markdown_text: str) -> OrganismExtractionResult:
        """
        Infer organism when not explicitly mentioned with property.

        Strategy:
        1. Check title and abstract for primary organism
        2. Check methods section for organism
        3. If single organism mentioned throughout, use it
        4. If multiple organisms, return "unknown" (manual review needed)

        Args:
            markdown_text: Full markdown content

        Returns:
            OrganismExtractionResult with inferred organism

        Examples:
            >>> extractor = OrganismExtractor()
            >>> text = "# Study of E. coli\\n\\nMethods: Cells were grown..."
            >>> result = extractor.infer_organism_from_context(text)
            >>> result.confidence < 0.9  # Lower confidence for inference
            True
        """
        # Extract title/abstract section (first 500 chars)
        title_section = markdown_text[:500]
        title_result = self.extract_from_title(title_section)

        # If single organism in title, likely applies to whole paper
        if len(title_result.organisms) == 1:
            return OrganismExtractionResult(
                organisms=title_result.organisms,
                confidence=0.75,  # Medium confidence for inference
                method="inferred_from_title",
                context="Organism mentioned in title/abstract"
            )

        # Extract from full text
        full_result = self.extract_with_regex(markdown_text, max_results=5)

        # If only one organism mentioned in entire paper
        if len(full_result.organisms) == 1:
            return OrganismExtractionResult(
                organisms=full_result.organisms,
                confidence=0.8,
                method="inferred_from_context",
                context="Single organism mentioned throughout paper"
            )

        # Multiple organisms or unclear - return empty (prefer empty over "unknown")
        return OrganismExtractionResult(
            organisms=[],
            confidence=0.0,
            method="inference_failed",
            context="Multiple organisms or unclear context"
        )

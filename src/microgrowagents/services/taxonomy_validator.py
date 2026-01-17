"""Taxonomy Validator using GTDB database.

Validates organism names against GTDB (Genome Taxonomy Database) release 226.
Provides scientifically validated organism name checking.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Set, Dict, Optional, Tuple
import re


@dataclass
class TaxonomyValidationResult:
    """Result of taxonomy validation.

    Attributes:
        is_valid: Whether the organism name is valid
        matched_name: The canonical name from GTDB (if found)
        genus: Genus name
        species: Species epithet (without genus)
        confidence: Confidence score (1.0 for exact match, 0.8 for fuzzy)
    """
    is_valid: bool
    matched_name: Optional[str] = None
    genus: Optional[str] = None
    species: Optional[str] = None
    confidence: float = 0.0


class TaxonomyValidator:
    """Validate organism names against GTDB taxonomy database.

    Uses GTDB release 226 for bacteria and archaea.
    Supports:
    - Full scientific names (Escherichia coli)
    - Abbreviated names (E. coli)
    - Strain designations (E. coli K-12)

    Examples:
        >>> validator = TaxonomyValidator()
        >>> result = validator.validate("Escherichia coli")
        >>> result.is_valid
        True
        >>> result.matched_name
        'Escherichia coli'
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize taxonomy validator.

        Args:
            data_dir: Directory containing GTDB taxonomy files.
                     Defaults to data/taxonomy in project root.
        """
        if data_dir is None:
            # Default to project data/taxonomy directory
            project_root = Path(__file__).parent.parent.parent.parent
            data_dir = project_root / "data" / "taxonomy"

        self.data_dir = Path(data_dir)

        # Storage for taxonomy data
        self.valid_species: Set[str] = set()  # Full species names
        self.valid_genera: Set[str] = set()   # Genus names only
        self.genus_to_species: Dict[str, Set[str]] = {}  # Genus → species epithets

        # Abbreviation mappings (genus → abbreviation)
        self.genus_abbreviations: Dict[str, str] = {}

        # Load taxonomy data
        self._load_taxonomy()

    def _load_taxonomy(self) -> None:
        """Load GTDB and LPSN taxonomy data."""
        # Load GTDB data (bacteria + archaea)
        bac_file = self.data_dir / "bac120_taxonomy_r226.tsv"
        ar_file = self.data_dir / "ar53_taxonomy_r226.tsv"

        if bac_file.exists() and ar_file.exists():
            # Load bacterial taxonomy
            self._parse_gtdb_file(bac_file)

            # Load archaeal taxonomy
            self._parse_gtdb_file(ar_file)

            print(f"[TaxonomyValidator] Loaded GTDB: {len(self.valid_species)} species, {len(self.valid_genera)} genera")
        else:
            print(f"[TaxonomyValidator] Warning: GTDB files not found, skipping")

        # Load LPSN data (authoritative prokaryotic nomenclature)
        lpsn_file = self.data_dir / "lpsn_gss_2026-01-08.csv"
        if lpsn_file.exists():
            species_before = len(self.valid_species)
            genera_before = len(self.valid_genera)
            self._parse_lpsn_file(lpsn_file)
            species_added = len(self.valid_species) - species_before
            genera_added = len(self.valid_genera) - genera_before
            print(f"[TaxonomyValidator] Loaded LPSN: +{species_added} species, +{genera_added} genera")
        else:
            print(f"[TaxonomyValidator] Warning: LPSN file not found, skipping")

        # Load NCBI Taxonomy (comprehensive coverage including eukaryotes)
        ncbi_nodes_file = self.data_dir / "ncbitaxon_nodes.tsv"
        if ncbi_nodes_file.exists():
            species_before = len(self.valid_species)
            genera_before = len(self.valid_genera)
            self._parse_ncbi_taxonomy(ncbi_nodes_file)
            species_added = len(self.valid_species) - species_before
            genera_added = len(self.valid_genera) - genera_before
            print(f"[TaxonomyValidator] Loaded NCBI: +{species_added} species, +{genera_added} genera")
        else:
            print(f"[TaxonomyValidator] Warning: NCBI taxonomy file not found, skipping")

        print(f"[TaxonomyValidator] Total: {len(self.valid_species)} species, {len(self.valid_genera)} genera")

    def _parse_gtdb_file(self, filepath: Path) -> None:
        """Parse GTDB taxonomy TSV file.

        Format: accession\ttaxonomy_string
        Taxonomy string: d__Domain;p__Phylum;c__Class;o__Order;f__Family;g__Genus;s__Species
        """
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = line.split('\t')
                if len(parts) < 2:
                    continue

                taxonomy_string = parts[1]

                # Extract genus and species
                genus, species = self._extract_genus_species(taxonomy_string)

                if genus:
                    self.valid_genera.add(genus)

                    # Store genus abbreviation (first letter + ".")
                    abbrev = f"{genus[0]}."
                    self.genus_abbreviations[genus] = abbrev

                if species:
                    self.valid_species.add(species)

                    # Map genus to species epithet
                    if genus:
                        species_epithet = species.replace(f"{genus} ", "")
                        if genus not in self.genus_to_species:
                            self.genus_to_species[genus] = set()
                        self.genus_to_species[genus].add(species_epithet)

    def _parse_lpsn_file(self, filepath: Path) -> None:
        """Parse LPSN taxonomy CSV file.

        Format: genus_name,sp_epithet,subsp_epithet,reference,status,...
        """
        import csv

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                genus_name = row.get('genus_name', '').strip()
                sp_epithet = row.get('sp_epithet', '').strip()

                # Skip if no genus name
                if not genus_name:
                    continue

                # Add genus
                self.valid_genera.add(genus_name)

                # Add genus abbreviation
                if genus_name:
                    abbrev = f"{genus_name[0]}."
                    self.genus_abbreviations[genus_name] = abbrev

                # If species epithet present, add full species name
                if sp_epithet:
                    full_species = f"{genus_name} {sp_epithet}"
                    self.valid_species.add(full_species)

                    # Map genus to species epithet
                    if genus_name not in self.genus_to_species:
                        self.genus_to_species[genus_name] = set()
                    self.genus_to_species[genus_name].add(sp_epithet)

    def _parse_ncbi_taxonomy(self, filepath: Path) -> None:
        """Parse NCBI Taxonomy nodes file from KG-Microbe.

        Format: TSV with columns including 'id', 'category', 'name', 'synonym'
        Example: NCBITaxon:562	biolink:OrganismTaxon	Escherichia coli	...
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            # Skip header line
            header = f.readline()

            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = line.split('\t')
                if len(parts) < 3:
                    continue

                # Column 2 is the organism name
                organism_name = parts[2].strip()

                if not organism_name or organism_name == 'root':
                    continue

                # Check if it's a binomial name (Genus species) or just genus
                name_parts = organism_name.split()

                if len(name_parts) >= 2:
                    # Binomial name (Genus species) or longer
                    genus = name_parts[0]

                    # Skip if genus isn't capitalized (not a proper organism name)
                    if not genus[0].isupper():
                        continue

                    # Add genus
                    self.valid_genera.add(genus)

                    # Add genus abbreviation
                    abbrev = f"{genus[0]}."
                    self.genus_abbreviations[genus] = abbrev

                    # Add full species name
                    self.valid_species.add(organism_name)

                    # Map genus to species epithet(s)
                    if len(name_parts) >= 2:
                        species_epithet = ' '.join(name_parts[1:])
                        if genus not in self.genus_to_species:
                            self.genus_to_species[genus] = set()
                        self.genus_to_species[genus].add(species_epithet)

                elif len(name_parts) == 1:
                    # Single word - likely a genus name
                    genus = name_parts[0]
                    if genus[0].isupper():
                        self.valid_genera.add(genus)
                        abbrev = f"{genus[0]}."
                        self.genus_abbreviations[genus] = abbrev

    def _extract_genus_species(self, taxonomy_string: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract genus and species from GTDB taxonomy string.

        Args:
            taxonomy_string: GTDB format like "d__Bacteria;...;g__Escherichia;s__Escherichia coli"

        Returns:
            Tuple of (genus, full_species_name)
        """
        parts = taxonomy_string.split(';')

        genus = None
        species = None

        for part in parts:
            if part.startswith('g__'):
                genus = part[3:].strip()
            elif part.startswith('s__'):
                species = part[3:].strip()

        # Only return if both genus and species are present and species is not generic
        if genus and species and species != 's__':
            # GTDB species format: "Genus species"
            return (genus, species)

        return (None, None)

    def validate(self, organism_name: str) -> TaxonomyValidationResult:
        """Validate an organism name against GTDB taxonomy.

        Args:
            organism_name: Organism name to validate (e.g., "Escherichia coli", "E. coli")

        Returns:
            TaxonomyValidationResult with validation outcome

        Examples:
            >>> validator = TaxonomyValidator()
            >>> validator.validate("Escherichia coli").is_valid
            True
            >>> validator.validate("E. coli").is_valid
            True
            >>> validator.validate("Fake bacterium").is_valid
            False
        """
        # Normalize whitespace
        organism_name = ' '.join(organism_name.split())

        # Try exact match first
        if organism_name in self.valid_species:
            genus = organism_name.split()[0]
            species_epithet = ' '.join(organism_name.split()[1:])
            return TaxonomyValidationResult(
                is_valid=True,
                matched_name=organism_name,
                genus=genus,
                species=species_epithet,
                confidence=1.0
            )

        # Try abbreviated name (e.g., "E. coli")
        if '.' in organism_name:
            expanded = self._expand_abbreviation(organism_name)
            if expanded and expanded in self.valid_species:
                genus = expanded.split()[0]
                species_epithet = ' '.join(expanded.split()[1:])
                return TaxonomyValidationResult(
                    is_valid=True,
                    matched_name=expanded,
                    genus=genus,
                    species=species_epithet,
                    confidence=0.9
                )

        # Try removing strain designation (e.g., "E. coli K-12" → "E. coli")
        base_name = self._remove_strain_designation(organism_name)
        if base_name != organism_name:
            # Recursively validate without strain
            result = self.validate(base_name)
            if result.is_valid:
                # Lower confidence for strain-containing names
                result.confidence *= 0.95
                return result

        # Not found in taxonomy
        return TaxonomyValidationResult(
            is_valid=False,
            confidence=0.0
        )

    def _expand_abbreviation(self, abbreviated_name: str) -> Optional[str]:
        """Expand abbreviated organism name.

        Args:
            abbreviated_name: e.g., "E. coli", "P. aeruginosa"

        Returns:
            Full name if expansion found, None otherwise

        Examples:
            >>> validator = TaxonomyValidator()
            >>> validator._expand_abbreviation("E. coli")
            'Escherichia coli'
        """
        parts = abbreviated_name.split()
        if len(parts) < 2:
            return None

        abbrev = parts[0]  # e.g., "E."
        species_epithet = ' '.join(parts[1:])  # e.g., "coli" or "coli K-12"

        # Find all genera matching this abbreviation and check which one has a valid species
        # This handles cases like "B." which could be Bacillus, Burkholderia, Bacteroides, etc.
        candidates = []
        for genus, genus_abbrev in self.genus_abbreviations.items():
            if genus_abbrev == abbrev:
                full_name = f"{genus} {species_epithet}"
                # Check if this full name exists in our species database
                if full_name in self.valid_species:
                    return full_name
                # Also store as candidate in case we need to check with strain removal
                candidates.append((genus, full_name))

        # If no exact match found, try removing strain designations from candidates
        for genus, full_name in candidates:
            base_name = self._remove_strain_designation(full_name)
            if base_name in self.valid_species:
                return base_name

        return None

    def _remove_strain_designation(self, organism_name: str) -> str:
        """Remove strain designation from organism name.

        Args:
            organism_name: e.g., "Escherichia coli K-12", "E. coli BL21"

        Returns:
            Base name without strain (e.g., "Escherichia coli", "E. coli")

        Examples:
            >>> validator = TaxonomyValidator()
            >>> validator._remove_strain_designation("E. coli K-12")
            'E. coli'
            >>> validator._remove_strain_designation("Salmonella enterica serovar Typhimurium")
            'Salmonella enterica'
        """
        # Split into words to safely remove strain designations
        parts = organism_name.split()

        # Need at least genus + species
        if len(parts) < 2:
            return organism_name

        # Check if there's a strain designation after the first 2 words
        if len(parts) > 2:
            # Common strain designation keywords
            strain_keywords = {'strain', 'serovar', 'subsp', 'subsp.', 'subspecies', 'var', 'var.'}

            # If third word is a strain keyword, remove it and everything after
            if parts[2].lower().rstrip('.') in strain_keywords:
                return ' '.join(parts[:2])

            # If third+ word looks like a strain ID (all caps, mixed alphanumeric, etc.)
            third_word = parts[2]
            if (re.match(r'^[A-Z][A-Z0-9\-]+$', third_word) or  # K-12, BL21, PAO1
                re.match(r'^[A-Z]{2,}\d+$', third_word) or      # ATCC13032
                re.match(r'^\w+\d+$', third_word)):              # MG1655
                return ' '.join(parts[:2])

        return organism_name

    def is_valid_genus(self, genus_name: str) -> bool:
        """Check if genus name is valid.

        Args:
            genus_name: Genus name to check

        Returns:
            True if genus is in GTDB
        """
        return genus_name in self.valid_genera

    def get_species_for_genus(self, genus_name: str) -> Set[str]:
        """Get all known species epithets for a genus.

        Args:
            genus_name: Genus name

        Returns:
            Set of species epithets (without genus)
        """
        return self.genus_to_species.get(genus_name, set())

    def suggest_corrections(self, organism_name: str, max_suggestions: int = 5) -> list[str]:
        """Suggest possible corrections for invalid organism names.

        Args:
            organism_name: Invalid organism name
            max_suggestions: Maximum number of suggestions

        Returns:
            List of suggested valid names
        """
        suggestions = []

        # Try partial matching on genus
        parts = organism_name.split()
        if len(parts) >= 2:
            genus_candidate = parts[0]
            species_candidate = parts[1].lower()

            # Find similar genera
            for genus in self.valid_genera:
                if genus.lower().startswith(genus_candidate.lower()[:3]):
                    # Check if any species match
                    species_epithets = self.get_species_for_genus(genus)
                    for epithet in species_epithets:
                        if epithet.lower().startswith(species_candidate[:3]):
                            full_name = f"{genus} {epithet}"
                            if full_name not in suggestions:
                                suggestions.append(full_name)
                            if len(suggestions) >= max_suggestions:
                                return suggestions

        return suggestions


if __name__ == "__main__":
    # Test the validator
    validator = TaxonomyValidator()

    test_names = [
        "Escherichia coli",
        "E. coli",
        "E. coli K-12",
        "Bacillus subtilis",
        "Pseudomonas aeruginosa",
        "P. aeruginosa PAO1",
        "Salmonella enterica serovar Typhimurium",
        "Fake bacterium",  # Invalid
        "Mailing address",  # Invalid
    ]

    for name in test_names:
        result = validator.validate(name)
        print(f"{name:45s} → Valid: {result.is_valid:5} | "
              f"Match: {result.matched_name or 'N/A':30s} | "
              f"Conf: {result.confidence:.2f}")

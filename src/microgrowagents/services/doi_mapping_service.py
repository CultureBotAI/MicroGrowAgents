"""DOI to Markdown File Mapping Service.

Maps DOI URLs to their corresponding markdown files in data/pdfs/ or data/abstracts/.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple
import re


class DOIMappingService:
    """
    Service for resolving DOI URLs to markdown file paths.

    Handles multiple filename conventions:
    - Full URL format: https___doi.org_10.1021_bi00866a011.md
    - Short format: 10.1021_bi00866a011.md
    - Abstract format: 10.1021_bi00866a011.md (in abstracts directory)

    Examples:
        >>> mapper = DOIMappingService()
        >>> path, source = mapper.resolve_markdown("https://doi.org/10.1021/bi00866a011")
        >>> path.exists()
        True
        >>> source in ["pdf", "abstract"]
        True
    """

    def __init__(
        self,
        pdf_dir: Optional[Path] = None,
        abstract_dir: Optional[Path] = None
    ):
        """
        Initialize DOI mapping service.

        Args:
            pdf_dir: Directory containing PDF markdown files (default: data/pdfs)
            abstract_dir: Directory containing abstract markdown files (default: data/abstracts)
        """
        self.pdf_dir = pdf_dir or Path("data/pdfs")
        self.abstract_dir = abstract_dir or Path("data/abstracts")

        # Cache for resolved mappings
        self._cache: Dict[str, Tuple[Optional[Path], Optional[str]]] = {}

        # Build initial cache from filesystem
        self._build_cache()

    def _build_cache(self) -> None:
        """
        Build cache of all available markdown files.

        Scans pdf_dir and abstract_dir to create a lookup dictionary.
        """
        # Scan PDF directory
        if self.pdf_dir.exists():
            for md_file in self.pdf_dir.glob("*.md"):
                # Extract DOI from filename
                doi = self._extract_doi_from_filename(md_file.name)
                if doi:
                    self._cache[doi] = (md_file, "pdf")

        # Scan abstract directory (don't override if PDF exists)
        if self.abstract_dir.exists():
            for md_file in self.abstract_dir.glob("*.md"):
                doi = self._extract_doi_from_filename(md_file.name)
                if doi and doi not in self._cache:
                    self._cache[doi] = (md_file, "abstract")

    def _extract_doi_from_filename(self, filename: str) -> Optional[str]:
        """
        Extract DOI from markdown filename.

        Args:
            filename: Markdown filename (e.g., "10.1021_bi00866a011.md")

        Returns:
            Normalized DOI or None if not a valid DOI filename

        Examples:
            >>> mapper = DOIMappingService()
            >>> mapper._extract_doi_from_filename("10.1021_bi00866a011.md")
            '10.1021/bi00866a011'
            >>> mapper._extract_doi_from_filename("https___doi.org_10.1021_bi00866a011.md")
            '10.1021/bi00866a011'
        """
        # Remove .md extension
        name = filename.replace(".md", "")

        # Handle full URL format: https___doi.org_10.1021_bi00866a011
        if name.startswith("https___doi.org_"):
            name = name.replace("https___doi.org_", "")
        elif name.startswith("http___doi.org_"):
            name = name.replace("http___doi.org_", "")

        # Convert underscores back to slashes (but keep underscores in DOI suffix)
        # DOI format: 10.XXXX/suffix where suffix may have underscores
        # Split on first underscore after the prefix
        parts = name.split("_", 1)
        if len(parts) == 2 and parts[0].startswith("10."):
            # Replace remaining underscores with slashes/dots as needed
            # Most DOIs use / after the prefix, but suffixes vary
            doi = f"{parts[0]}/{parts[1]}"
            # Normalize special characters that may have been escaped
            doi = doi.replace("_", "/")  # Simple case: all underscores are slashes
            return doi

        return None

    def normalize_doi(self, doi: str) -> str:
        """
        Normalize DOI URL to standard format.

        Removes https://doi.org/ prefix and standardizes format.

        Args:
            doi: DOI URL or DOI string

        Returns:
            Normalized DOI (e.g., "10.1021/bi00866a011")

        Examples:
            >>> mapper = DOIMappingService()
            >>> mapper.normalize_doi("https://doi.org/10.1021/bi00866a011")
            '10.1021/bi00866a011'
            >>> mapper.normalize_doi("10.1021/bi00866a011")
            '10.1021/bi00866a011'
        """
        # Remove URL prefix
        normalized = doi.replace("https://doi.org/", "")
        normalized = normalized.replace("http://doi.org/", "")
        normalized = normalized.strip()

        return normalized

    def doi_to_filename(self, doi: str) -> str:
        """
        Convert DOI to markdown filename format.

        Args:
            doi: Normalized DOI (e.g., "10.1021/bi00866a011")

        Returns:
            Filename format (e.g., "10.1021_bi00866a011.md")

        Examples:
            >>> mapper = DOIMappingService()
            >>> mapper.doi_to_filename("10.1021/bi00866a011")
            '10.1021_bi00866a011.md'
        """
        # Replace slashes with underscores
        safe_doi = doi.replace("/", "_")
        return f"{safe_doi}.md"

    def resolve_markdown(self, doi: str) -> Tuple[Optional[Path], Optional[str]]:
        """
        Resolve DOI to markdown file path.

        Tries multiple filename patterns in order of preference:
        1. Full PDF markdown (more context)
        2. Abstract markdown (fallback)
        3. None (DOI not available)

        Args:
            doi: DOI URL or DOI string

        Returns:
            Tuple of (file_path, source_type) where source_type is "pdf", "abstract", or None

        Examples:
            >>> mapper = DOIMappingService()
            >>> path, source = mapper.resolve_markdown("https://doi.org/10.1021/bi00866a011")
            >>> source in [None, "pdf", "abstract"]
            True
        """
        # Normalize DOI
        normalized = self.normalize_doi(doi)

        # Check cache first
        if normalized in self._cache:
            return self._cache[normalized]

        # Try to resolve from filesystem
        safe_doi = normalized.replace("/", "_")

        # Try 1: PDF with https prefix
        path = self.pdf_dir / f"https___doi.org_{safe_doi}.md"
        if path.exists():
            self._cache[normalized] = (path, "pdf")
            return (path, "pdf")

        # Try 2: PDF without prefix
        path = self.pdf_dir / f"{safe_doi}.md"
        if path.exists():
            self._cache[normalized] = (path, "pdf")
            return (path, "pdf")

        # Try 3: Abstract
        path = self.abstract_dir / f"{safe_doi}.md"
        if path.exists():
            self._cache[normalized] = (path, "abstract")
            return (path, "abstract")

        # Not found
        self._cache[normalized] = (None, None)
        return (None, None)

    def get_available_dois(self) -> Dict[str, Tuple[Path, str]]:
        """
        Get all available DOIs and their file paths.

        Returns:
            Dictionary mapping DOI → (file_path, source_type)

        Examples:
            >>> mapper = DOIMappingService()
            >>> dois = mapper.get_available_dois()
            >>> len(dois) > 0
            True
        """
        return {doi: (path, source) for doi, (path, source) in self._cache.items() if path is not None}

    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about available markdown files.

        Returns:
            Dictionary with counts of pdf, abstract, and total files

        Examples:
            >>> mapper = DOIMappingService()
            >>> stats = mapper.get_statistics()
            >>> 'total' in stats and 'pdf' in stats and 'abstract' in stats
            True
        """
        available = self.get_available_dois()

        pdf_count = sum(1 for _, source in available.values() if source == "pdf")
        abstract_count = sum(1 for _, source in available.values() if source == "abstract")

        return {
            "total": len(available),
            "pdf": pdf_count,
            "abstract": abstract_count,
            "missing": len([doi for doi, (path, _) in self._cache.items() if path is None])
        }

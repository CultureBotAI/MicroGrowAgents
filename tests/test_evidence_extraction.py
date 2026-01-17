"""Unit tests for evidence extraction components."""

import pytest
from pathlib import Path

from microgrowagents.services.doi_mapping_service import DOIMappingService
from microgrowagents.extractors.organism_extractor import OrganismExtractor
from microgrowagents.extractors.evidence_snippet_extractor import EvidenceSnippetExtractor


class TestDOIMappingService:
    """Tests for DOI mapping service."""

    def test_normalize_doi(self):
        """Test DOI normalization."""
        mapper = DOIMappingService(
            pdf_dir=Path("data/pdfs"),
            abstract_dir=Path("data/abstracts")
        )

        # Test with full URL
        assert mapper.normalize_doi("https://doi.org/10.1021/bi00866a011") == "10.1021/bi00866a011"

        # Test with http
        assert mapper.normalize_doi("http://doi.org/10.1021/bi00866a011") == "10.1021/bi00866a011"

        # Test already normalized
        assert mapper.normalize_doi("10.1021/bi00866a011") == "10.1021/bi00866a011"

    def test_doi_to_filename(self):
        """Test DOI to filename conversion."""
        mapper = DOIMappingService(
            pdf_dir=Path("data/pdfs"),
            abstract_dir=Path("data/abstracts")
        )

        result = mapper.doi_to_filename("10.1021/bi00866a011")
        assert result == "10.1021_bi00866a011.md"

    def test_get_statistics(self):
        """Test statistics calculation."""
        mapper = DOIMappingService(
            pdf_dir=Path("data/pdfs"),
            abstract_dir=Path("data/abstracts")
        )

        stats = mapper.get_statistics()

        assert "total" in stats
        assert "pdf" in stats
        assert "abstract" in stats
        assert isinstance(stats["total"], int)
        assert stats["total"] >= 0


class TestOrganismExtractor:
    """Tests for organism extractor."""

    def test_extract_scientific_name(self):
        """Test extraction of full scientific name."""
        extractor = OrganismExtractor()

        text = "Growth of Escherichia coli at 37°C was measured."
        result = extractor.extract_with_regex(text)

        assert len(result.organisms) > 0
        assert "Escherichia coli" in result.organisms
        assert result.confidence > 0.8

    def test_extract_abbreviated_name(self):
        """Test extraction of abbreviated organism name."""
        extractor = OrganismExtractor()

        text = "E. coli and B. subtilis were tested."
        result = extractor.extract_with_regex(text)

        assert len(result.organisms) >= 2
        # Should find at least the abbreviated forms
        assert result.confidence > 0.0

    def test_extract_with_strain(self):
        """Test extraction of organism with strain."""
        extractor = OrganismExtractor()

        text = "E. coli K-12 was used as the model organism."
        result = extractor.extract_with_regex(text)

        assert len(result.organisms) > 0
        assert result.confidence > 0.8

    def test_is_valid_organism(self):
        """Test organism validation."""
        extractor = OrganismExtractor()

        # Valid organisms
        assert extractor._is_valid_organism("Escherichia coli")
        assert extractor._is_valid_organism("E. coli")
        assert extractor._is_valid_organism("Bacillus subtilis")

        # Invalid (false positives)
        assert not extractor._is_valid_organism("The first")
        assert not extractor._is_valid_organism("In this")
        assert not extractor._is_valid_organism("AB")  # Too short

    def test_extract_from_title(self):
        """Test title extraction with lower confidence."""
        extractor = OrganismExtractor()

        title = "# Phosphate transport in E. coli"
        result = extractor.extract_from_title(title)

        if result.organisms:
            assert result.confidence == 0.7  # Lower confidence for title-only

    def test_infer_organism_single_mention(self):
        """Test organism inference from context."""
        extractor = OrganismExtractor()

        text = """
        # Study of E. coli Growth

        Abstract: We studied E. coli under various conditions.

        Methods: E. coli was grown at 37°C...
        """

        result = extractor.infer_organism_from_context(text)

        # Should find E. coli since it's mentioned throughout
        assert len(result.organisms) > 0
        assert result.confidence > 0.7


class TestEvidenceSnippetExtractor:
    """Tests for evidence snippet extractor."""

    def test_extract_with_value_and_organism(self):
        """Test snippet extraction with both value and organism."""
        extractor = EvidenceSnippetExtractor()

        text = "Growth of E. coli at 0.1 mM phosphate was observed in minimal medium."
        result = extractor.extract(
            text=text,
            property_value="0.1 mM",
            organism="E. coli"
        )

        assert result.contains_value
        assert result.contains_organism
        assert "0.1 mM" in result.snippet
        assert "E. coli" in result.snippet
        assert len(result.snippet) <= 200

    def test_extract_with_value_only(self):
        """Test snippet extraction with value but no organism."""
        extractor = EvidenceSnippetExtractor()

        text = "The solubility at 25°C was determined to be 100 mM in aqueous solution."
        result = extractor.extract(
            text=text,
            property_value="100 mM"
        )

        assert result.contains_value
        assert "100 mM" in result.snippet
        assert len(result.snippet) <= 200

    def test_truncate_long_snippet(self):
        """Test truncation of long snippets."""
        extractor = EvidenceSnippetExtractor()

        long_text = "This is a very long sentence about the growth of E. coli at various concentrations. " * 20
        long_text += " The concentration of 0.1 mM was found to be optimal. " + "More text. " * 50

        result = extractor._truncate_snippet(long_text, "0.1 mM", "E. coli")

        assert len(result) <= 200
        assert "0.1 mM" in result  # Value preserved
        assert "..." in result  # Ellipsis added

    def test_get_abbreviation(self):
        """Test organism name abbreviation."""
        extractor = EvidenceSnippetExtractor()

        assert extractor._get_abbreviation("Escherichia coli") == "E. coli"
        assert extractor._get_abbreviation("Bacillus subtilis") == "B. subtilis"
        assert extractor._get_abbreviation("E. coli") == "E. coli"

    def test_find_sentences_with_value(self):
        """Test finding sentences containing value."""
        extractor = EvidenceSnippetExtractor()

        text = "First sentence. Second sentence has 0.1 mM phosphate. Third sentence."
        sentences = extractor._find_sentences_with_value(text, "0.1 mM")

        assert len(sentences) > 0
        assert any("0.1 mM" in s for s in sentences)

    def test_get_property_keywords(self):
        """Test property keyword mapping."""
        extractor = EvidenceSnippetExtractor()

        toxicity_keywords = extractor._get_property_keywords("Toxicity")
        assert "toxic" in toxicity_keywords
        assert "toxicity" in toxicity_keywords

        solubility_keywords = extractor._get_property_keywords("Solubility")
        assert "soluble" in solubility_keywords


class TestIntegration:
    """Integration tests for complete workflow."""

    def test_doi_mapper_with_real_files(self):
        """Test DOI mapping with actual markdown files."""
        mapper = DOIMappingService(
            pdf_dir=Path("data/pdfs"),
            abstract_dir=Path("data/abstracts")
        )

        stats = mapper.get_statistics()

        # Should have some files
        assert stats["total"] > 0
        print(f"\nFound {stats['total']} markdown files:")
        print(f"  PDFs: {stats['pdf']}")
        print(f"  Abstracts: {stats['abstract']}")

    def test_extract_organism_from_real_markdown(self):
        """Test organism extraction from a real markdown file."""
        mapper = DOIMappingService()

        # Get first available DOI
        available_dois = mapper.get_available_dois()
        if not available_dois:
            pytest.skip("No markdown files available")

        # Test with first available DOI
        doi, (markdown_path, source) = list(available_dois.items())[0]

        # Load markdown
        with open(markdown_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract organisms
        extractor = OrganismExtractor()
        result = extractor.extract_with_regex(content[:5000])  # First 5000 chars

        print(f"\nExtracted from {source} ({doi}):")
        print(f"  Organisms found: {len(result.organisms)}")
        if result.organisms:
            print(f"  Examples: {result.organisms[:3]}")


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

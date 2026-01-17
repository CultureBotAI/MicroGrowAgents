"""Tests for CSV All-DOIs Enrichment Agent."""

import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from microgrowagents.agents.csv_all_dois_enrichment_agent import CSVAllDOIsEnrichmentAgent


class TestCSVDOIExtraction:
    """Test DOI extraction from CSV."""

    @pytest.fixture
    def sample_csv_data(self, tmp_path):
        """Create a sample CSV with DOI columns."""
        csv_content = """Component,Lower Bound Citation (DOI),Upper Bound Citation (DOI),Toxicity Citation (DOI)
PIPES,https://doi.org/10.1021/bi00866a011,https://doi.org/10.1021/bi00866a011,https://doi.org/10.1021/bi00866a011
MgCl2,https://doi.org/10.1371/journal.pone.0023307,https://doi.org/10.1371/journal.pone.0023307,https://doi.org/10.1684/mrh.2014.0362
FeSO4,https://doi.org/10.1016/S0168-6445(03)00055-X,https://doi.org/10.1016/j.biortech.2004.11.001,https://doi.org/10.1016/j.chemosphere.2005.04.016
"""
        csv_path = tmp_path / "test_ingredients.csv"
        csv_path.write_text(csv_content)
        return csv_path

    @pytest.fixture
    def agent(self, sample_csv_data):
        """Create agent with sample CSV."""
        return CSVAllDOIsEnrichmentAgent(
            csv_path=sample_csv_data, email="test@example.com"
        )

    def test_extract_all_dois_from_csv(self, agent):
        """Test extraction of all unique DOIs from CSV."""
        dois = agent.extract_all_dois()

        # Should have 6 unique DOIs from 3 rows x 3 columns (some duplicates)
        assert len(dois) >= 5
        assert "https://doi.org/10.1021/bi00866a011" in dois
        assert "https://doi.org/10.1371/journal.pone.0023307" in dois

    def test_extract_dois_by_column(self, agent):
        """Test extraction of DOIs grouped by column."""
        dois_by_column = agent.extract_dois_by_column()

        assert "Lower Bound Citation (DOI)" in dois_by_column
        assert "Upper Bound Citation (DOI)" in dois_by_column
        assert "Toxicity Citation (DOI)" in dois_by_column

        # Check that DOIs are extracted correctly
        assert len(dois_by_column["Lower Bound Citation (DOI)"]) >= 3

    def test_doi_column_detection(self, agent):
        """Test detection of DOI columns."""
        doi_columns = agent.get_doi_columns()

        assert len(doi_columns) == 3
        assert "Lower Bound Citation (DOI)" in doi_columns
        assert "Component" not in doi_columns  # Non-DOI column


class TestBulkPDFDownload:
    """Test bulk PDF downloading."""

    @pytest.fixture
    def agent(self, tmp_path):
        """Create agent with mock CSV."""
        csv_content = """Component,Toxicity Citation (DOI)
PIPES,https://doi.org/10.1021/bi00866a011
"""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text(csv_content)

        return CSVAllDOIsEnrichmentAgent(
            csv_path=csv_path, email="test@example.com", pdf_cache_dir=tmp_path
        )

    def test_download_single_doi_success(self, agent):
        """Test successful PDF download for a single DOI."""
        with patch.object(
            agent.pdf_extractor, "_get_pdf_url_from_publisher"
        ) as mock_publisher:
            mock_publisher.return_value = "https://example.com/paper.pdf"

            with patch("requests.get") as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.content = b"%PDF-1.4 fake pdf content"
                mock_response.headers = {"content-type": "application/pdf"}
                mock_get.return_value = mock_response

                result = agent.download_doi_pdf("https://doi.org/10.1021/test")

                assert result["success"] is True
                assert result["source"] is not None

    def test_download_single_doi_failure(self, agent):
        """Test failed PDF download."""
        with patch.object(
            agent.pdf_extractor, "_get_pdf_url_from_publisher"
        ) as mock_publisher:
            mock_publisher.return_value = None

            with patch.object(
                agent.pdf_extractor, "_get_pdf_url_from_pmc"
            ) as mock_pmc:
                mock_pmc.return_value = None

                with patch.object(
                    agent.pdf_extractor, "_get_pdf_url_from_unpaywall"
                ) as mock_unpaywall:
                    mock_unpaywall.return_value = None

                    with patch.object(
                        agent.pdf_extractor, "_get_pdf_url_from_semantic_scholar"
                    ) as mock_semantic:
                        mock_semantic.return_value = None

                        with patch.object(
                            agent.pdf_extractor, "_get_pdf_url_from_web_search"
                        ) as mock_web:
                            mock_web.return_value = None

                            result = agent.download_doi_pdf(
                                "https://doi.org/10.1021/blocked"
                            )

                            assert result["success"] is False
                            assert "error" in result

    def test_bulk_download_with_cache(self, agent, tmp_path):
        """Test bulk download respects cache."""
        doi = "https://doi.org/10.1021/test"
        # DOI safe format: replace both / and . with _
        doi_safe = "10_1021_test"
        pdf_path = tmp_path / f"{doi_safe}.pdf"

        # Create a fake cached PDF
        pdf_path.write_bytes(b"%PDF-1.4 cached")

        result = agent.download_doi_pdf(doi)

        # Should use cache, not download
        assert result["success"] is True
        assert result["source"] == "cache"

    def test_process_all_dois_dry_run(self, agent):
        """Test dry run mode - no actual downloads."""
        result = agent.run(dry_run=True)

        assert result["success"] is True
        assert result["stats"]["total_dois"] >= 1
        assert result["stats"]["pdfs_downloaded"] == 0  # Dry run

    def test_process_all_dois_limit(self, agent):
        """Test limiting number of downloads."""
        with patch.object(agent, "download_doi_pdf") as mock_download:
            mock_download.return_value = {"success": True, "source": "test"}

            result = agent.run(limit=2, dry_run=False)

            # Should only process up to 2 DOIs
            assert mock_download.call_count <= 2


class TestReporting:
    """Test report generation."""

    @pytest.fixture
    def agent_with_results(self, tmp_path):
        """Create agent with mock results."""
        csv_content = """Component,Toxicity Citation (DOI),pH Effect DOI
PIPES,https://doi.org/10.1021/bi00866a011,https://doi.org/10.1128/jb.119.3.736-747.1974
MgCl2,https://doi.org/10.1371/journal.pone.0023307,
"""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text(csv_content)

        return CSVAllDOIsEnrichmentAgent(
            csv_path=csv_path, email="test@example.com"
        )

    def test_generate_summary_statistics(self, agent_with_results):
        """Test summary statistics generation."""
        # Mock some results
        results = [
            {
                "doi": "https://doi.org/10.1021/test1",
                "success": True,
                "source": "publisher",
            },
            {
                "doi": "https://doi.org/10.1021/test2",
                "success": False,
                "error": "403 Forbidden",
            },
            {
                "doi": "https://doi.org/10.1021/test3",
                "success": True,
                "source": "cache",
            },
        ]

        stats = agent_with_results.generate_statistics(results)

        assert stats["total"] == 3
        assert stats["successful"] == 2
        assert stats["failed"] == 1
        assert stats["sources"]["publisher"] == 1
        assert stats["sources"]["cache"] == 1

    def test_generate_markdown_report(self, agent_with_results, tmp_path):
        """Test markdown report generation."""
        results = [
            {
                "doi": "https://doi.org/10.1021/test1",
                "success": True,
                "source": "publisher",
            }
        ]

        report_path = tmp_path / "report.md"
        agent_with_results.generate_report(results, report_path)

        assert report_path.exists()
        content = report_path.read_text()
        assert "PDF Download Report" in content
        assert "10.1021/test1" in content


class TestDOIPatternMatching:
    """Test DOI pattern matching and extraction."""

    def test_extract_dois_from_text(self):
        """Test DOI extraction from various text formats."""
        agent = CSVAllDOIsEnrichmentAgent(csv_path=Path("dummy.csv"))

        # Single DOI
        text1 = "https://doi.org/10.1021/bi00866a011"
        dois1 = agent.extract_dois_from_text(text1)
        assert len(dois1) == 1
        assert dois1[0] == "https://doi.org/10.1021/bi00866a011"

        # Multiple DOIs separated by semicolons
        text2 = "https://doi.org/10.1021/test1; https://doi.org/10.1128/test2"
        dois2 = agent.extract_dois_from_text(text2)
        assert len(dois2) == 2

        # Empty text
        text3 = ""
        dois3 = agent.extract_dois_from_text(text3)
        assert len(dois3) == 0

    def test_normalize_doi(self):
        """Test DOI normalization."""
        agent = CSVAllDOIsEnrichmentAgent(csv_path=Path("dummy.csv"))

        # HTTP to HTTPS
        doi1 = "http://doi.org/10.1021/test"
        normalized1 = agent.normalize_doi(doi1)
        assert normalized1 == "https://doi.org/10.1021/test"

        # Already HTTPS
        doi2 = "https://doi.org/10.1021/test"
        normalized2 = agent.normalize_doi(doi2)
        assert normalized2 == "https://doi.org/10.1021/test"

        # DOI without URL
        doi3 = "10.1021/test"
        normalized3 = agent.normalize_doi(doi3)
        assert normalized3 == "https://doi.org/10.1021/test"

"""
PDF Evidence Extractor.

Downloads PDFs from DOIs and extracts relevant evidence snippets.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
import re
import tempfile
import os


class PDFEvidenceExtractor:
    """
    Extract evidence snippets from scientific PDFs.

    Workflow:
    1. Download PDF from DOI (via Unpaywall API)
    2. Extract text from PDF
    3. Search for relevant passages mentioning:
       - Organism names
       - Concentration values
       - Toxicity data
    """

    def __init__(self, email: str = "your@email.com", use_fallback_pdf: bool = True):
        """
        Initialize PDF extractor.

        Args:
            email: Email for Unpaywall API (required for polite usage)
            use_fallback_pdf: Whether to use fallback PDF sources (default: True)
        """
        self.email = email
        self.unpaywall_base = "https://api.unpaywall.org/v2"
        self.cache_dir = Path(tempfile.gettempdir()) / "microgrow_pdfs"
        self.cache_dir.mkdir(exist_ok=True)

        # Fallback PDF source configuration
        self.use_fallback_pdf = use_fallback_pdf
        self.fallback_pdf_urls = self._get_fallback_pdf_urls()

    def _get_fallback_pdf_urls(self) -> List[str]:
        """
        Get list of fallback PDF source URLs.

        Can be configured via FALLBACK_PDF_MIRRORS environment variable (comma-separated).
        Defaults to a curated list of commonly working mirrors.

        Returns:
            List of fallback PDF base URLs

        Examples:
            >>> extractor = PDFEvidenceExtractor()
            >>> urls = extractor._get_fallback_pdf_urls()
            >>> len(urls) > 0
            True
            >>> all(isinstance(url, str) for url in urls)
            True
        """
        # Check environment variable first (similar to Aurelian's DOI_FULL_TEXT_URLS)
        env_mirrors = os.getenv("FALLBACK_PDF_MIRRORS", "")
        if env_mirrors:
            return [url.strip() for url in env_mirrors.split(",") if url.strip()]

        # Default fallback mirrors (these change frequently, but these are commonly stable)
        return [
            "https://sci-hub.se",
            "https://sci-hub.st",
            "https://sci-hub.ru",
            "https://sci-hub.ren",
        ]

    def extract_from_doi(
        self,
        doi: str,
        ingredient_id: str,
        concentration_low: Optional[float] = None,
        concentration_high: Optional[float] = None,
        toxicity_value: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Download PDF and extract evidence snippets.

        Tries multiple sources in cascading order:
        1. Direct publisher website (ASM, PLOS, Frontiers, MDPI, Nature, etc.)
        2. PubMed Central (PMC)
        3. Unpaywall API
        4. Semantic Scholar
        5. Web search (arXiv, bioRxiv, Europe PMC, Sci-Hub, Google Scholar)

        Args:
            doi: DOI of paper
            ingredient_id: ChEBI ID
            concentration_low: Lower concentration bound
            concentration_high: Upper concentration bound
            toxicity_value: Toxicity threshold

        Returns:
            Dictionary with snippets

        Examples:
            >>> extractor = PDFEvidenceExtractor()
            >>> result = extractor.extract_from_doi("10.1128/AEM.02738-08", "CHEBI:17790")
            >>> "success" in result
            True
        """
        # Step 1: Try to get PDF URL from multiple sources (cascade)
        pdf_url = None
        source = None

        # Try 1: Direct publisher website
        print(f"Trying direct publisher access for {doi}...")
        pdf_url = self._get_pdf_url_from_publisher(doi)
        if pdf_url:
            source = "publisher"
            print(f"✓ Found PDF via publisher")

        # Try 2: PubMed Central (PMC)
        if not pdf_url:
            print(f"Trying PubMed Central for {doi}...")
            pdf_url = self._get_pdf_url_from_pmc(doi)
            if pdf_url:
                source = "pmc"
                print(f"✓ Found PDF via PubMed Central")

        # Try 3: Unpaywall API
        if not pdf_url:
            print(f"Trying Unpaywall API for {doi}...")
            pdf_url = self._get_pdf_url_from_unpaywall(doi)
            if pdf_url:
                source = "unpaywall"
                print(f"✓ Found PDF via Unpaywall")

        # Try 4: Semantic Scholar
        if not pdf_url:
            print(f"Trying Semantic Scholar for {doi}...")
            pdf_url = self._get_pdf_url_from_semantic_scholar(doi)
            if pdf_url:
                source = "semantic_scholar"
                print(f"✓ Found PDF via Semantic Scholar")

        # Try 5: Web search as last resort
        if not pdf_url:
            print(f"Trying web search for {doi}...")
            pdf_url = self._get_pdf_url_from_web_search(doi)
            if pdf_url:
                source = "web_search"
                print(f"✓ Found PDF via web search")

        if not pdf_url:
            return {
                "success": False,
                "error": "PDF not available via any source",
                "snippets": {},
            }

        # Step 2: Download PDF
        pdf_path = self._download_pdf(pdf_url, doi)

        if not pdf_path:
            return {
                "success": False,
                "error": "Failed to download PDF",
                "snippets": {},
            }

        # Step 3: Extract text from PDF
        text = self._extract_text_from_pdf(pdf_path)

        if not text:
            return {
                "success": False,
                "error": "Failed to extract text from PDF",
                "snippets": {},
            }

        # Step 4: Extract relevant snippets
        snippets = self._extract_snippets(
            text=text,
            ingredient_id=ingredient_id,
            concentration_low=concentration_low,
            concentration_high=concentration_high,
            toxicity_value=toxicity_value,
        )

        return {
            "success": True,
            "snippets": snippets,
            "pdf_path": str(pdf_path),
            "source": source,
        }

    def _get_pdf_url_from_publisher(self, doi: str) -> Optional[str]:
        """
        Try to get PDF directly from publisher website.

        Args:
            doi: DOI of paper

        Returns:
            PDF URL or None
        """
        # Try direct DOI resolution with .pdf extension
        publisher_patterns = [
            f"https://doi.org/{doi}.pdf",  # Some publishers support this
            f"https://doi.org/{doi}/pdf",  # Alternative pattern
        ]

        # Publisher-specific patterns
        if "asm.org" in doi or "ASM" in doi or doi.startswith("10.1128"):
            # American Society for Microbiology
            publisher_patterns.append(f"https://journals.asm.org/doi/pdf/{doi}")
            publisher_patterns.append(f"https://journals.asm.org/doi/pdfdirect/{doi}")

        elif "plos" in doi.lower() or doi.startswith("10.1371"):
            # PLOS journals
            publisher_patterns.append(f"https://journals.plos.org/plosone/article/file?id={doi}&type=printable")

        elif "frontiersin" in doi.lower() or doi.startswith("10.3389"):
            # Frontiers journals
            publisher_patterns.append(f"https://www.frontiersin.org/articles/{doi}/pdf")

        elif "mdpi" in doi.lower() or doi.startswith("10.3390"):
            # MDPI journals
            publisher_patterns.append(f"https://www.mdpi.com/{doi}/pdf")

        elif "nature" in doi.lower() or doi.startswith("10.1038"):
            # Nature journals
            publisher_patterns.append(f"https://www.nature.com/articles/{doi}.pdf")

        elif "science" in doi.lower() or doi.startswith("10.1126"):
            # Science journals
            publisher_patterns.append(f"https://www.science.org/doi/pdf/{doi}")

        elif "elsevier" in doi.lower() or doi.startswith("10.1016"):
            # Elsevier journals
            publisher_patterns.append(f"https://www.sciencedirect.com/science/article/pii/{doi}/pdfft")

        # Try each pattern
        for url in publisher_patterns:
            try:
                response = requests.head(url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    content_type = response.headers.get("Content-Type", "")
                    if "pdf" in content_type.lower():
                        return url
            except Exception:
                continue

        return None

    def _get_pdf_url_from_pmc(self, doi: str) -> Optional[str]:
        """
        Get PDF URL from PubMed Central (PMC).

        Args:
            doi: DOI of paper

        Returns:
            PDF URL or None
        """
        try:
            # Step 1: Search for PMC ID using DOI
            search_url = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
            params = {
                "ids": doi,
                "format": "json",
                "tool": "microgrow_agents",
                "email": self.email,
            }

            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Check if we got a PMC ID
            if "records" in data and len(data["records"]) > 0:
                record = data["records"][0]
                pmcid = record.get("pmcid")

                if pmcid:
                    # Step 2: Construct PDF URL from PMC ID
                    # PMC PDFs are available at: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC[ID]/pdf/
                    pmc_number = pmcid.replace("PMC", "")
                    pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_number}/pdf/"

                    # Verify it exists
                    head_response = requests.head(pdf_url, timeout=5, allow_redirects=True)
                    if head_response.status_code == 200:
                        return pdf_url

            return None

        except Exception as e:
            # PMC not available is common, don't print error
            return None

    def _get_pdf_url_from_semantic_scholar(self, doi: str) -> Optional[str]:
        """
        Get PDF URL from Semantic Scholar API.

        Args:
            doi: DOI of paper

        Returns:
            PDF URL or None
        """
        try:
            url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
            params = {"fields": "openAccessPdf"}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("openAccessPdf") and data["openAccessPdf"].get("url"):
                return data["openAccessPdf"]["url"]

            return None

        except Exception as e:
            print(f"Semantic Scholar API error for {doi}: {e}")
            return None

    def _get_pdf_url_from_web_search(self, doi: str) -> Optional[str]:
        """
        Search the web for PDF URL using multiple strategies.

        Tries repositories in this order:
        1. Open preprint servers (arXiv, bioRxiv, Europe PMC)
        2. Fallback PDF mirrors (if use_fallback_pdf=True)
        3. Google Scholar

        Args:
            doi: DOI of paper

        Returns:
            PDF URL or None
        """
        # Strategy 1: Try open preprint servers first
        open_repositories = [
            f"https://arxiv.org/pdf/{doi}.pdf",  # arXiv
            f"https://www.biorxiv.org/content/{doi}v1.full.pdf",  # bioRxiv
            f"https://europepmc.org/articles/PMC{doi.split('/')[-1]}?pdf=render",  # Europe PMC
        ]

        for repo_url in open_repositories:
            try:
                response = requests.head(repo_url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    content_type = response.headers.get("Content-Type", "")
                    if "pdf" in content_type.lower():
                        return repo_url
            except Exception:
                continue

        # Strategy 2: Try fallback PDF mirrors (if enabled)
        if self.use_fallback_pdf:
            for fallback_base in self.fallback_pdf_urls:
                fallback_url = f"{fallback_base}/{doi}"
                try:
                    print(f"  Trying fallback PDF mirror: {fallback_base}...")
                    # Some mirrors don't respond well to HEAD requests, use GET
                    response = requests.get(fallback_url, timeout=10, allow_redirects=True)
                    if response.status_code == 200:
                        # Mirror returns HTML page with embedded PDF
                        pdf_url = self._extract_pdf_from_fallback_html(response.text)
                        if pdf_url:
                            print(f"  ✓ Found PDF via fallback: {pdf_url}")
                            return pdf_url
                        else:
                            print(f"  ✗ Fallback page loaded but no PDF found")
                    else:
                        print(f"  ✗ Fallback returned status {response.status_code}")
                except Exception as e:
                    print(f"  ✗ Fallback error: {e}")
                    continue

        # Strategy 3: Use Google Scholar search (parse HTML for PDF links)
        try:
            return self._search_google_scholar(doi)
        except Exception:
            pass

        return None

    def _extract_pdf_from_fallback_html(self, html: str) -> Optional[str]:
        """
        Extract actual PDF URL from fallback PDF source HTML page.

        Fallback sources embed PDFs in various ways:
        - <object type="application/pdf" data="/storage/.../file.pdf">
        - <a href="/download/.../file.pdf">
        - <embed src="...pdf">
        - <iframe src="...pdf">

        Args:
            html: HTML content from fallback PDF source page

        Returns:
            PDF URL or None
        """
        try:
            # Determine base URL from first configured mirror
            base_url = self.fallback_pdf_urls[0] if self.fallback_pdf_urls else "https://sci-hub.se"

            # Strategy 1: Look for <object type="application/pdf" data="...">
            object_pattern = r'<object[^>]+type\s*=\s*["\']application/pdf["\'][^>]+data\s*=\s*["\']([^"\'#]+)'
            matches = re.findall(object_pattern, html, re.IGNORECASE)
            if matches:
                pdf_path = matches[0]
                if not pdf_path.startswith('http'):
                    if pdf_path.startswith('//'):
                        pdf_url = 'https:' + pdf_path
                    else:
                        pdf_url = base_url + pdf_path
                else:
                    pdf_url = pdf_path
                return pdf_url

            # Strategy 2: Look for download links <a href="/download/...pdf">
            download_pattern = r'<a[^>]+href\s*=\s*["\']([^"\']+\.pdf[^"\']*)["\']'
            matches = re.findall(download_pattern, html, re.IGNORECASE)
            if matches:
                pdf_path = matches[0]
                if not pdf_path.startswith('http'):
                    if pdf_path.startswith('//'):
                        pdf_url = 'https:' + pdf_path
                    else:
                        pdf_url = base_url + pdf_path
                else:
                    pdf_url = pdf_path
                return pdf_url

            # Strategy 3: Look for embed/iframe tags
            embed_patterns = [
                r'<embed[^>]+src=["\']([^"\']+\.pdf[^"\']*)["\']',
                r'<iframe[^>]+src=["\']([^"\']+\.pdf[^"\']*)["\']',
            ]

            for pattern in embed_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                if matches:
                    pdf_path = matches[0]
                    if not pdf_path.startswith('http'):
                        if pdf_path.startswith('//'):
                            pdf_url = 'https:' + pdf_path
                        else:
                            pdf_url = base_url + pdf_path
                    else:
                        pdf_url = pdf_path
                    return pdf_url

            # Strategy 4: Look for direct PDF URLs in the HTML
            pdf_pattern = r'(https?://[^\s"\'<>]+\.pdf)'
            matches = re.findall(pdf_pattern, html)
            if matches:
                return matches[0]

            return None

        except Exception as e:
            print(f"    Error extracting PDF from fallback HTML: {e}")
            return None

    def _search_google_scholar(self, doi: str) -> Optional[str]:
        """
        Search Google Scholar for PDF link.

        Args:
            doi: DOI of paper

        Returns:
            PDF URL or None
        """
        try:
            # Google Scholar search URL
            search_url = f"https://scholar.google.com/scholar?q={doi}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            }

            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse HTML for PDF links
            import re
            pdf_pattern = r'href="([^"]+\.pdf)"'
            matches = re.findall(pdf_pattern, response.text)

            if matches:
                # Return first PDF link
                pdf_url = matches[0]
                if not pdf_url.startswith("http"):
                    pdf_url = "https://scholar.google.com" + pdf_url
                return pdf_url

            return None

        except Exception:
            return None

    def _get_pdf_url_from_unpaywall(self, doi: str) -> Optional[str]:
        """
        Get PDF URL from Unpaywall API.

        Args:
            doi: DOI of paper

        Returns:
            PDF URL or None
        """
        url = f"{self.unpaywall_base}/{doi}?email={self.email}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Try to get best open access PDF
            if data.get("best_oa_location") and data["best_oa_location"].get("url_for_pdf"):
                return data["best_oa_location"]["url_for_pdf"]

            # Try other OA locations
            if data.get("oa_locations"):
                for location in data["oa_locations"]:
                    if location.get("url_for_pdf"):
                        return location["url_for_pdf"]

            return None

        except requests.HTTPError as e:
            # Don't print errors for expected failures (422 = invalid email or not found)
            if e.response.status_code != 422:
                print(f"Unpaywall HTTP error for {doi}: {e}")
            return None
        except Exception as e:
            # Only print unexpected errors
            print(f"Unpaywall error for {doi}: {e}")
            return None

    def _download_pdf(self, pdf_url: str, doi: str) -> Optional[Path]:
        """
        Download PDF to cache directory.

        Args:
            pdf_url: URL to PDF
            doi: DOI (for filename)

        Returns:
            Path to downloaded PDF or None
        """
        # Create safe filename from DOI
        safe_doi = doi.replace("/", "_").replace(":", "_")
        pdf_path = self.cache_dir / f"{safe_doi}.pdf"

        # Check if already cached
        if pdf_path.exists():
            print(f"Using cached PDF: {pdf_path}")
            return pdf_path

        # Headers to avoid 403 errors
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/pdf,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            print(f"Downloading PDF from {pdf_url}...")
            response = requests.get(pdf_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()

            with open(pdf_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"Downloaded PDF: {pdf_path}")
            return pdf_path

        except requests.HTTPError as e:
            if e.response.status_code == 403:
                print(f"Download blocked (403 Forbidden) - may need institutional access")
            else:
                print(f"Download HTTP error: {e}")
            return None
        except Exception as e:
            print(f"Download error: {e}")
            return None

    def _extract_text_from_pdf(self, pdf_path: Path) -> Optional[str]:
        """
        Extract text from PDF file.

        Args:
            pdf_path: Path to PDF

        Returns:
            Extracted text or None
        """
        try:
            import PyPDF2

            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text_parts = []

                for page in reader.pages:
                    text_parts.append(page.extract_text())

                return "\n".join(text_parts)

        except ImportError:
            print("PyPDF2 not installed. Install with: pip install PyPDF2")
            return None
        except Exception as e:
            print(f"PDF extraction error: {e}")
            return None

    def _extract_snippets(
        self,
        text: str,
        ingredient_id: str,
        concentration_low: Optional[float],
        concentration_high: Optional[float],
        toxicity_value: Optional[float],
    ) -> Dict[str, str]:
        """
        Extract relevant snippets from PDF text.

        Args:
            text: Full PDF text
            ingredient_id: ChEBI ID
            concentration_low: Lower concentration
            concentration_high: Upper concentration
            toxicity_value: Toxicity threshold

        Returns:
            Dictionary with extracted snippets
        """
        snippets = {}

        # Split into sentences
        sentences = re.split(r"[.!?]\s+", text)

        # Extract organism mentions
        organisms = self._extract_organisms(sentences)
        if organisms:
            snippets["organism"] = ", ".join(organisms[:3])  # Top 3 organisms

        # Extract concentration-related snippets
        if concentration_low or concentration_high:
            conc_snippet = self._find_concentration_snippet(
                sentences, concentration_low, concentration_high
            )
            if conc_snippet:
                snippets["concentration_snippet"] = conc_snippet

        # Extract toxicity-related snippets
        if toxicity_value:
            tox_snippet = self._find_toxicity_snippet(sentences, toxicity_value)
            if tox_snippet:
                snippets["toxicity_snippet"] = tox_snippet

        return snippets

    def _extract_organisms(self, sentences: List[str]) -> List[str]:
        """
        Extract organism names from sentences.

        Args:
            sentences: List of sentences

        Returns:
            List of organism names
        """
        organisms = set()

        # Common microbial organism patterns
        patterns = [
            r"([A-Z][a-z]+ [a-z]+)",  # Genus species (e.g., Escherichia coli)
            r"E\.\s*coli",
            r"B\.\s*subtilis",
            r"P\.\s*aeruginosa",
            r"S\.\s*cerevisiae",
        ]

        for sentence in sentences[:100]:  # Check first 100 sentences
            for pattern in patterns:
                matches = re.findall(pattern, sentence)
                for match in matches:
                    # Filter out common non-organism phrases
                    if not any(
                        word in match.lower()
                        for word in ["figure", "table", "supplementary", "method"]
                    ):
                        organisms.add(match)

        return list(organisms)

    def _find_concentration_snippet(
        self,
        sentences: List[str],
        concentration_low: Optional[float],
        concentration_high: Optional[float],
    ) -> Optional[str]:
        """
        Find sentence mentioning concentration range.

        Args:
            sentences: List of sentences
            concentration_low: Lower bound
            concentration_high: Upper bound

        Returns:
            Snippet or None
        """
        # Search for concentration mentions
        conc_pattern = r"\d+\.?\d*\s*(mM|µM|mg/L|g/L)"

        for sentence in sentences:
            if re.search(conc_pattern, sentence):
                # Check if values are close to our range
                if concentration_low:
                    low_str = str(int(concentration_low))
                    if low_str in sentence:
                        return sentence[:200]  # Truncate if too long

                if concentration_high:
                    high_str = str(int(concentration_high))
                    if high_str in sentence:
                        return sentence[:200]

        return None

    def _find_toxicity_snippet(
        self, sentences: List[str], toxicity_value: float
    ) -> Optional[str]:
        """
        Find sentence mentioning toxicity.

        Args:
            sentences: List of sentences
            toxicity_value: Toxicity threshold

        Returns:
            Snippet or None
        """
        tox_keywords = ["toxic", "inhibit", "lethal", "LD50", "EC50", "MIC"]

        for sentence in sentences:
            if any(kw in sentence.lower() for kw in tox_keywords):
                # Check if toxicity value is mentioned
                tox_str = str(int(toxicity_value))
                if tox_str in sentence:
                    return sentence[:200]

        return None

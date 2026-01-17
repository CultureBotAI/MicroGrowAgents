#!/usr/bin/env python
"""Test fallback PDF integration with previously failed DOIs."""

from pathlib import Path
from microgrowagents.agents.pdf_evidence_extractor import PDFEvidenceExtractor

# Test with a DOI that previously failed (paywalled journals)
# From csv_all_dois_report.md: 10.1128/AEM.00320-14 - PDF download failed
test_dois = [
    "10.1128/AEM.00320-14",  # ASM journal (paywalled)
    "10.1111/1462-2920.13023",  # Wiley journal (paywalled)
    "10.1021/es505001t",  # ACS journal (paywalled)
]

print("Testing fallback PDF integration with previously paywalled DOIs...\n")

# Test WITH fallback PDF enabled
print("=" * 70)
print("TEST 1: With fallback PDF enabled (use_fallback_pdf=True)")
print("=" * 70)

extractor_with_fallback = PDFEvidenceExtractor(
    email="MJoachimiak@lbl.gov",
    use_fallback_pdf=True
)

print(f"Fallback PDF mirrors configured: {extractor_with_fallback.fallback_pdf_urls}\n")

for doi in test_dois:
    print(f"\nTesting {doi}:")
    print("-" * 70)
    result = extractor_with_fallback.extract_from_doi(
        doi=doi,
        ingredient_id="CHEBI:17790"
    )

    if result["success"]:
        print(f"✓ SUCCESS! PDF downloaded via: {result.get('source', 'unknown')}")
        print(f"  Cached at: {result.get('pdf_path', 'unknown')}")
    else:
        print(f"✗ FAILED: {result.get('error', 'unknown error')}")

# Test WITHOUT fallback PDF (for comparison)
print("\n" + "=" * 70)
print("TEST 2: Without fallback PDF (use_fallback_pdf=False) - for comparison")
print("=" * 70)

extractor_no_fallback = PDFEvidenceExtractor(
    email="MJoachimiak@lbl.gov",
    use_fallback_pdf=False
)

# Test just one DOI
test_doi = test_dois[0]
print(f"\nTesting {test_doi} WITHOUT fallback PDF:")
print("-" * 70)
result = extractor_no_fallback.extract_from_doi(
    doi=test_doi,
    ingredient_id="CHEBI:17790"
)

if result["success"]:
    print(f"✓ SUCCESS! PDF downloaded via: {result.get('source', 'unknown')}")
else:
    print(f"✗ FAILED: {result.get('error', 'unknown error')}")

print("\n" + "=" * 70)
print("Test completed!")
print("=" * 70)

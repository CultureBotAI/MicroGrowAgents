#!/usr/bin/env python
"""
Re-run enrichment on previously failed DOIs with fallback PDF sources enabled.

This script loads the results from the initial enrichment run and retries
all failed DOIs with fallback PDF sources enabled to measure the improvement.
"""

import json
from pathlib import Path
from microgrowagents.agents.pdf_evidence_extractor import PDFEvidenceExtractor

# Load previous results
results_file = Path("csv_all_dois_results.json")
if not results_file.exists():
    print(f"Error: {results_file} not found!")
    print("Please run the full enrichment first.")
    exit(1)

with open(results_file) as f:
    previous_results = json.load(f)

# Extract failed DOIs from the results list
failed_dois = []
for result in previous_results.get("results", []):
    if not result.get("success", False):
        # Normalize DOI (remove https://doi.org/ prefix if present)
        doi = result["doi"]
        if doi.startswith("https://doi.org/"):
            doi = doi.replace("https://doi.org/", "")
        failed_dois.append(doi)

print(f"Fallback PDF Recovery Attempt")
print("=" * 70)
print(f"Total previously failed DOIs: {len(failed_dois)}")
print(f"Testing with fallback PDF sources enabled...\n")

# Initialize extractor with fallback PDF enabled
extractor = PDFEvidenceExtractor(
    email="MJoachimiak@lbl.gov",
    use_fallback_pdf=True
)

# Track results
recovered = []
still_failed = []

# Test a sample first (10 DOIs) to avoid long runtime
sample_size = min(20, len(failed_dois))
print(f"Testing sample of {sample_size} failed DOIs:\n")

for i, doi in enumerate(failed_dois[:sample_size], 1):
    print(f"[{i}/{sample_size}] Testing {doi}...")

    result = extractor.extract_from_doi(
        doi=doi,
        ingredient_id="CHEBI:17790"
    )

    if result["success"]:
        recovered.append(doi)
        source = result.get("source", "unknown")
        print(f"  ✓ RECOVERED via {source}!")
    else:
        still_failed.append(doi)
        error = result.get("error", "unknown")
        print(f"  ✗ Still failed: {error}")
    print()

# Summary
print("=" * 70)
print("RESULTS SUMMARY")
print("=" * 70)
print(f"Sample size tested: {sample_size}")
print(f"Recovered with fallback PDF: {len(recovered)} ({len(recovered)/sample_size*100:.1f}%)")
print(f"Still failed: {len(still_failed)} ({len(still_failed)/sample_size*100:.1f}%)")

if recovered:
    print(f"\nRecovered DOIs:")
    for doi in recovered:
        print(f"  - {doi}")

print(f"\nProjected total recovery from all {len(failed_dois)} failed DOIs:")
print(f"  ~{int(len(recovered)/sample_size * len(failed_dois))} additional PDFs")

print(f"\n" + "=" * 70)
print("To run full recovery, increase sample_size or remove the [:sample_size] limit")
print("=" * 70)

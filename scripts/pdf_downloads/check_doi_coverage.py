#!/usr/bin/env python3
"""
Check DOI coverage: which DOIs have PDFs, which have abstracts, which have neither.
Create markdown link files for DOIs without PDFs.
"""

import json
from pathlib import Path
from typing import Dict, List, Set


def get_doi_from_filename(filename: str) -> str:
    """Extract DOI from PDF filename."""
    # Remove .pdf extension
    name = filename.replace('.pdf', '').replace('.md', '')

    # Handle both formats:
    # 1. 10.1016_S0969-2126(96)00095-0
    # 2. https___doi.org_10.1016_S0969-2126(96)00095-0

    if name.startswith('https___doi.org_'):
        name = name.replace('https___doi.org_', '')

    # Convert underscores back to slashes for DOI
    # First underscore is the separator between prefix and suffix
    parts = name.split('_', 1)
    if len(parts) == 2:
        doi = f"{parts[0]}/{parts[1]}"
        # Restore special characters
        doi = doi.replace('_', '/')
        return f"https://doi.org/{doi}"
    else:
        return f"https://doi.org/{name}"


def normalize_doi(doi: str) -> str:
    """Normalize DOI to standard format."""
    doi = doi.strip()
    if not doi.startswith('http'):
        doi = f"https://doi.org/{doi}"
    return doi.lower().replace('http://doi.org/', 'https://doi.org/')


def main():
    """Check DOI coverage."""

    # Read all DOIs
    all_dois_file = Path('data/results/all_doi_links.txt')
    all_dois = []

    with open(all_dois_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('https://doi.org/'):
                all_dois.append(normalize_doi(line))

    print(f"Total DOIs: {len(all_dois)}")

    # Find all PDFs
    pdf_dir = Path('data/pdfs')
    pdf_files = list(pdf_dir.glob('*.pdf'))

    # Extract DOIs from PDF filenames
    dois_with_pdfs = set()
    for pdf_file in pdf_files:
        try:
            doi = get_doi_from_filename(pdf_file.name)
            doi = normalize_doi(doi)
            dois_with_pdfs.add(doi)
        except:
            print(f"Warning: Could not parse DOI from {pdf_file.name}")

    print(f"DOIs with PDFs: {len(dois_with_pdfs)}")

    # Find DOIs without PDFs
    dois_without_pdfs = set()
    for doi in all_dois:
        if doi not in dois_with_pdfs:
            dois_without_pdfs.add(doi)

    print(f"DOIs without PDFs: {len(dois_without_pdfs)}")

    # Check which DOIs have abstracts
    abstract_dir = Path('data/abstracts')
    abstract_files = list(abstract_dir.glob('*.json')) if abstract_dir.exists() else []

    dois_with_abstracts = set()
    for abstract_file in abstract_files:
        try:
            with open(abstract_file, 'r') as f:
                data = json.load(f)
                doi = normalize_doi(data.get('doi', ''))
                dois_with_abstracts.add(doi)
        except:
            pass

    print(f"DOIs with abstracts: {len(dois_with_abstracts)}")

    # Categorize DOIs
    dois_with_pdf_only = dois_with_pdfs - dois_with_abstracts
    dois_with_abstract_only = dois_with_abstracts - dois_with_pdfs
    dois_with_both = dois_with_pdfs & dois_with_abstracts
    dois_with_neither = dois_without_pdfs - dois_with_abstracts

    print()
    print("="*70)
    print("COVERAGE BREAKDOWN")
    print("="*70)
    print(f"DOIs with PDF only: {len(dois_with_pdf_only)}")
    print(f"DOIs with abstract only: {len(dois_with_abstract_only)}")
    print(f"DOIs with both PDF and abstract: {len(dois_with_both)}")
    print(f"DOIs with NEITHER PDF nor abstract: {len(dois_with_neither)}")
    print()
    print(f"Total coverage (PDF or abstract): {len(dois_with_pdfs | dois_with_abstracts)}/{len(all_dois)} ({len(dois_with_pdfs | dois_with_abstracts)/len(all_dois)*100:.1f}%)")

    # Save detailed results
    results = {
        'total_dois': len(all_dois),
        'dois_with_pdfs': len(dois_with_pdfs),
        'dois_with_abstracts': len(dois_with_abstracts),
        'coverage': {
            'pdf_only': len(dois_with_pdf_only),
            'abstract_only': len(dois_with_abstract_only),
            'both': len(dois_with_both),
            'neither': len(dois_with_neither)
        },
        'dois_without_pdfs': sorted(list(dois_without_pdfs)),
        'dois_with_neither': sorted(list(dois_with_neither))
    }

    results_file = Path('data/results/doi_coverage_analysis.json')
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"✓ Results saved to {results_file}")

    # Create markdown link files for DOIs without PDFs
    if dois_without_pdfs:
        print()
        print("="*70)
        print("CREATING MARKDOWN LINK FILES")
        print("="*70)

        links_dir = Path('data/doi_links')
        links_dir.mkdir(exist_ok=True)

        # Create individual link files
        for doi in sorted(dois_without_pdfs):
            doi_clean = doi.replace('https://doi.org/', '')
            safe_name = doi_clean.replace('/', '_')

            has_abstract = doi in dois_with_abstracts

            md_content = f"""# DOI Link: {doi_clean}

**Status:** {'Abstract available' if has_abstract else 'No PDF or abstract'}

## Links

- **DOI:** [{doi}]({doi})
- **Abstract:** {'Available in data/abstracts/' if has_abstract else 'Not available'}

## Actions Needed

- [ ] Download PDF if available
- [ ] {'✓' if has_abstract else '[ ]'} Download abstract
- [ ] Extract evidence
- [ ] Fill organism context columns

## Notes

This DOI does not have a PDF file downloaded. Please obtain the PDF or use the abstract for evidence extraction.
"""

            md_file = links_dir / f"{safe_name}.md"
            with open(md_file, 'w') as f:
                f.write(md_content)

        print(f"✓ Created {len(dois_without_pdfs)} markdown link files in {links_dir}")

        # Create summary file
        summary_md = f"""# DOIs Without PDFs - Summary

**Total:** {len(dois_without_pdfs)} DOIs

## Coverage

- With abstracts: {len(dois_with_abstract_only)} ({len(dois_with_abstract_only)/len(dois_without_pdfs)*100:.1f}%)
- Without abstracts: {len(dois_with_neither)} ({len(dois_with_neither)/len(dois_without_pdfs)*100:.1f}%)

## DOIs Without PDFs (but with abstracts)

"""

        for doi in sorted(dois_with_abstract_only):
            doi_clean = doi.replace('https://doi.org/', '')
            summary_md += f"- [{doi_clean}]({doi}) ✓ Abstract available\n"

        summary_md += f"\n## DOIs Without PDFs or Abstracts ({len(dois_with_neither)})\n\n"

        for doi in sorted(dois_with_neither):
            doi_clean = doi.replace('https://doi.org/', '')
            summary_md += f"- [{doi_clean}]({doi}) ⚠️ **Needs abstract download**\n"

        summary_file = links_dir / 'README.md'
        with open(summary_file, 'w') as f:
            f.write(summary_md)

        print(f"✓ Created summary file: {summary_file}")

        # Save list of DOIs needing abstracts
        if dois_with_neither:
            needs_abstract_file = Path('data/results/dois_needing_abstracts.txt')
            with open(needs_abstract_file, 'w') as f:
                f.write("# DOIs that need abstracts downloaded\n")
                f.write(f"# Total: {len(dois_with_neither)}\n\n")
                for doi in sorted(dois_with_neither):
                    f.write(f"{doi}\n")

            print(f"✓ Created list of DOIs needing abstracts: {needs_abstract_file}")
            print(f"  {len(dois_with_neither)} DOIs need abstract downloads")


if __name__ == '__main__':
    main()

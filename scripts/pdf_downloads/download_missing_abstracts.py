#!/usr/bin/env python3
"""
Download abstracts for DOIs that have neither PDFs nor abstracts.
"""

import json
import os
import requests
import time
from pathlib import Path


def get_abstract_from_crossref(doi: str, email: str = "microgrow@example.com") -> dict:
    """
    Get abstract from CrossRef API.

    Args:
        doi: DOI URL or string
        email: Email for polite API usage

    Returns:
        Dict with abstract data
    """
    result = {
        'doi': doi,
        'success': False,
        'abstract': None,
        'title': None,
        'authors': [],
        'journal': None,
        'year': None,
        'error': None
    }

    try:
        # Clean DOI
        doi_clean = doi.replace('https://doi.org/', '').replace('http://doi.org/', '')

        # Query CrossRef API
        url = f"https://api.crossref.org/works/{doi_clean}"
        headers = {
            'User-Agent': f'MicroGrowAgents/1.0 (mailto:{email})',
            'Accept': 'application/json'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            result['error'] = f'CrossRef API returned {response.status_code}'
            return result

        data = response.json()
        message = data.get('message', {})

        # Extract metadata
        result['title'] = message.get('title', [''])[0]
        result['journal'] = message.get('container-title', [''])[0]

        # Extract year
        published = message.get('published-print') or message.get('published-online') or message.get('created')
        if published and 'date-parts' in published:
            date_parts = published['date-parts'][0]
            if date_parts:
                result['year'] = date_parts[0]

        # Extract authors
        authors = message.get('author', [])
        result['authors'] = [
            f"{author.get('given', '')} {author.get('family', '')}".strip()
            for author in authors[:5]  # First 5 authors
        ]

        # Extract abstract
        abstract = message.get('abstract', '')
        if abstract:
            # Clean HTML tags if present
            import re
            abstract = re.sub(r'<[^>]+>', '', abstract)
            result['abstract'] = abstract.strip()
            result['success'] = True
        else:
            result['error'] = 'No abstract in CrossRef data'

    except Exception as e:
        result['error'] = str(e)

    return result


def main():
    """Download abstracts for DOIs without PDFs or abstracts."""

    # Read list of DOIs needing abstracts
    dois_file = Path('data/results/dois_needing_abstracts.txt')

    if not dois_file.exists():
        print(f"Error: {dois_file} not found")
        print("Run check_doi_coverage.py first")
        return

    dois = []
    with open(dois_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                dois.append(line)

    print(f"Downloading abstracts for {len(dois)} DOIs")
    print("="*70)

    abstracts_dir = Path('data/abstracts')
    abstracts_dir.mkdir(exist_ok=True)

    results = []
    success_count = 0
    failed_count = 0

    for i, doi in enumerate(dois, 1):
        doi_clean = doi.replace('https://doi.org/', '')
        print(f"\n[{i}/{len(dois)}] {doi_clean}")

        # Check if abstract already exists
        safe_name = doi_clean.replace('/', '_')
        abstract_file = abstracts_dir / f"{safe_name}.json"

        if abstract_file.exists():
            print(f"  ✓ Abstract already exists")
            success_count += 1
            continue

        # Try to get abstract
        print(f"  Fetching from CrossRef...")
        time.sleep(0.5)  # Be polite to API

        result = get_abstract_from_crossref(doi)

        if result['success']:
            # Save abstract
            with open(abstract_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"  ✓ Downloaded abstract")
            print(f"    Title: {result['title'][:60]}...")
            success_count += 1
        else:
            print(f"  ✗ Failed: {result['error']}")
            failed_count += 1

        results.append(result)

    # Summary
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total DOIs: {len(dois)}")
    print(f"  Successfully downloaded: {success_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Success rate: {success_count/len(dois)*100:.1f}%")

    if failed_count > 0:
        print()
        print("Failed DOIs:")
        for r in results:
            if not r['success']:
                doi_clean = r['doi'].replace('https://doi.org/', '')
                print(f"  - {doi_clean}: {r['error']}")

    # Save results
    results_file = Path('data/results/missing_abstracts_download.json')
    with open(results_file, 'w') as f:
        json.dump({
            'total': len(dois),
            'success': success_count,
            'failed': failed_count,
            'results': results
        }, f, indent=2)

    print()
    print(f"✓ Results saved to {results_file}")
    print(f"✓ Abstracts saved to {abstracts_dir}")


if __name__ == '__main__':
    main()

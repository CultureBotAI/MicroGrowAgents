#!/usr/bin/env python3
"""
Convert PDFs to Markdown using MarkItDown.

This script uses the same PDF to markdown extraction method as the bridge2ai/data-sheets-schema
project, which uses the MarkItDown library.

Based on: /Users/marcin/Documents/VIMSS/ontology/bridge2ai/data-sheets-schema/aurelian/src/aurelian/utils/doi_fetcher.py
"""

import json
from pathlib import Path
from typing import Dict, List
from markitdown import MarkItDown
import time


def convert_pdf_to_markdown(pdf_path: Path, md: MarkItDown) -> Dict:
    """
    Convert a single PDF to markdown using MarkItDown.

    Args:
        pdf_path: Path to PDF file
        md: MarkItDown instance

    Returns:
        Dict with conversion results
    """
    result = {
        'pdf_file': str(pdf_path),
        'success': False,
        'md_file': None,
        'error': None,
        'size_pdf': 0,
        'size_md': 0
    }

    try:
        # Get PDF size
        result['size_pdf'] = pdf_path.stat().st_size

        # Convert PDF to markdown
        print(f"  Converting {pdf_path.name}...")
        conversion = md.convert(str(pdf_path))

        # Get markdown content
        md_content = conversion.text_content

        if not md_content or len(md_content.strip()) == 0:
            result['error'] = 'Empty markdown content'
            return result

        # Save markdown file
        md_path = pdf_path.with_suffix('.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        result['success'] = True
        result['md_file'] = str(md_path)
        result['size_md'] = md_path.stat().st_size
        result['lines'] = len(md_content.splitlines())

        print(f"  ✓ Saved to {md_path.name}")
        print(f"    PDF: {result['size_pdf']:,} bytes → MD: {result['size_md']:,} bytes ({result['lines']} lines)")

    except Exception as e:
        result['error'] = str(e)
        print(f"  ✗ Error: {e}")

    return result


def convert_all_pdfs(pdf_dir: Path, pattern: str = "*.pdf") -> Dict:
    """
    Convert all PDFs in a directory to markdown.

    Args:
        pdf_dir: Directory containing PDFs
        pattern: Glob pattern for PDF files

    Returns:
        Dict with summary results
    """
    # Initialize MarkItDown
    md = MarkItDown()

    # Find all PDFs
    pdf_files = sorted(pdf_dir.glob(pattern))

    print(f"Found {len(pdf_files)} PDF files in {pdf_dir}")
    print("="*70)

    results = []
    success_count = 0
    failed_count = 0

    for pdf_path in pdf_files:
        result = convert_pdf_to_markdown(pdf_path, md)
        results.append(result)

        if result['success']:
            success_count += 1
        else:
            failed_count += 1

        # Small delay to avoid overwhelming the system
        time.sleep(0.1)

    return {
        'total': len(pdf_files),
        'success': success_count,
        'failed': failed_count,
        'results': results
    }


def main():
    """Main conversion script."""

    # Setup paths
    pdf_dir = Path('data/pdfs')

    if not pdf_dir.exists():
        print(f"Error: PDF directory not found: {pdf_dir}")
        return

    print("PDF to Markdown Conversion")
    print("Using MarkItDown library (same as bridge2ai/data-sheets-schema)")
    print("="*70)
    print()

    # Convert all PDFs
    summary = convert_all_pdfs(pdf_dir)

    # Print summary
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total PDFs: {summary['total']}")
    print(f"  Successfully converted: {summary['success']}")
    print(f"  Failed: {summary['failed']}")

    if summary['failed'] > 0:
        print()
        print("Failed conversions:")
        for r in summary['results']:
            if not r['success']:
                print(f"  - {Path(r['pdf_file']).name}: {r['error']}")

    # Calculate total sizes
    total_pdf_size = sum(r.get('size_pdf', 0) for r in summary['results'] if r['success'])
    total_md_size = sum(r.get('size_md', 0) for r in summary['results'] if r['success'])
    total_lines = sum(r.get('lines', 0) for r in summary['results'] if r['success'])

    print()
    print(f"Total PDF size: {total_pdf_size:,} bytes ({total_pdf_size / 1024 / 1024:.1f} MB)")
    print(f"Total MD size: {total_md_size:,} bytes ({total_md_size / 1024 / 1024:.1f} MB)")
    print(f"Total lines: {total_lines:,}")
    print(f"Compression ratio: {total_pdf_size / total_md_size:.1f}x" if total_md_size > 0 else "N/A")

    # Save results
    results_file = Path('data/results/pdf_to_markdown_conversion.json')
    with open(results_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print()
    print(f"✓ Results saved to {results_file}")
    print(f"✓ Markdown files saved in {pdf_dir}")


if __name__ == '__main__':
    main()

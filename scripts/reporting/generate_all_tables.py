#!/usr/bin/env python3
"""Generate all statistical tables from evidence extraction results.

This script generates comprehensive tables showing:
- Organism statistics
- Coverage metrics
- Confidence distributions
- Property extraction status
- DOI citation coverage
- Evidence snippet quality
- Taxonomy database coverage
- Organism diversity by domain
- File source distribution
- Ingredient processing status
"""

import pandas as pd
import json
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple


def load_data() -> Tuple[pd.DataFrame, Dict]:
    """Load CSV and extraction results."""
    csv_path = Path("data/raw/mp_medium_ingredient_properties.csv")
    json_path = Path("/tmp/extraction_results.json")

    df = pd.read_csv(csv_path)

    # Load extraction results if available
    extraction_results = {}
    if json_path.exists():
        with open(json_path, 'r') as f:
            try:
                extraction_results = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load extraction results: {e}")

    return df, extraction_results


def generate_organism_statistics_table(df: pd.DataFrame, results: Dict) -> str:
    """Generate organism statistics table."""
    if 'organism_statistics' in results:
        stats = results['organism_statistics']

        table = "## Organism Statistics\n\n"
        table += "| Metric | Count |\n"
        table += "|--------|-------|\n"
        table += f"| **Unique organisms** | {stats.get('unique_organisms', 0)} |\n"

        if 'most_common_organisms' in stats:
            table += f"| **Total mentions** | {sum(count for _, count in stats['most_common_organisms'])} |\n"
            table += f"| **Most common** | {stats['most_common_organisms'][0][0]} ({stats['most_common_organisms'][0][1]} mentions) |\n"

        table += "\n### Top 20 Most Common Organisms\n\n"
        table += "| Rank | Organism | Mentions |\n"
        table += "|------|----------|----------|\n"

        for i, (org, count) in enumerate(stats.get('most_common_organisms', [])[:20], 1):
            table += f"| {i} | {org} | {count} |\n"

        return table

    return "## Organism Statistics\n\n*No extraction results available*\n"


def generate_coverage_statistics_table(df: pd.DataFrame, results: Dict) -> str:
    """Generate coverage statistics table."""
    org_cols = [c for c in df.columns if 'Organism' in c and 'Model' not in c]
    evidence_cols = [c for c in df.columns if 'Evidence Snippet' in c]

    table = "## Coverage Statistics\n\n"
    table += "| Metric | Value | Percentage |\n"
    table += "|--------|-------|------------|\n"

    # Organism coverage
    total_org_cells = len(df) * len(org_cols)
    filled_org_cells = sum(df[col].notna().sum() for col in org_cols)
    org_pct = (filled_org_cells / total_org_cells * 100) if total_org_cells > 0 else 0
    table += f"| **Organism columns populated** | {filled_org_cells}/{total_org_cells} | {org_pct:.1f}% |\n"

    # Evidence coverage
    total_ev_cells = len(df) * len(evidence_cols)
    filled_ev_cells = sum(df[col].notna().sum() for col in evidence_cols)
    ev_pct = (filled_ev_cells / total_ev_cells * 100) if total_ev_cells > 0 else 0
    table += f"| **Evidence snippet columns populated** | {filled_ev_cells}/{total_ev_cells} | {ev_pct:.1f}% |\n"

    # Extraction results
    if 'summary' in results:
        summary = results['summary']
        table += f"| **Properties attempted** | {summary.get('total_properties_attempted', 0)} | - |\n"
        table += f"| **Successful extractions** | {summary.get('successful_extractions', 0)} | {summary.get('coverage_percentage', 0):.1f}% |\n"
        table += f"| **Failed extractions** | {summary.get('failed_extractions', 0)} | - |\n"

    return table


def generate_confidence_distribution_table(results: Dict) -> str:
    """Generate confidence distribution table."""
    if 'confidence_distribution' not in results:
        return "## Confidence Distribution\n\n*No extraction results available*\n"

    conf_dist = results['confidence_distribution']

    table = "## Confidence Distribution\n\n"
    table += "| Confidence Level | Count | Percentage |\n"
    table += "|-----------------|-------|------------|\n"

    total = sum(conf_dist.values())
    for level, count in conf_dist.items():
        pct = (count / total * 100) if total > 0 else 0
        table += f"| {level} | {count} | {pct:.1f}% |\n"

    return table


def generate_property_extraction_status_table(df: pd.DataFrame) -> str:
    """Generate property extraction status table."""
    org_cols = [c for c in df.columns if 'Organism' in c and 'Model' not in c]

    table = "## Property Extraction Status\n\n"
    table += "| Property | Filled | Total | Percentage |\n"
    table += "|----------|--------|-------|------------|\n"

    for col in org_cols:
        filled = df[col].notna().sum()
        total = len(df)
        pct = (filled / total * 100) if total > 0 else 0
        prop_name = col.replace(' Citation Organism', '').replace(' Organism', '')
        table += f"| {prop_name} | {filled} | {total} | {pct:.1f}% |\n"

    return table


def generate_doi_citation_coverage_table(df: pd.DataFrame) -> str:
    """Generate DOI citation coverage table."""
    doi_cols = [c for c in df.columns if 'DOI' in c or 'Citation' in c and 'Organism' not in c and 'Evidence' not in c]

    table = "## DOI Citation Coverage\n\n"
    table += "| Property | DOIs Present | Total | Percentage |\n"
    table += "|----------|--------------|-------|------------|\n"

    for col in doi_cols:
        if col in df.columns:
            filled = df[col].notna().sum()
            total = len(df)
            pct = (filled / total * 100) if total > 0 else 0
            prop_name = col.replace(' Citation (DOI)', '').replace(' Citation', '').replace(' (DOI)', '')
            table += f"| {prop_name} | {filled} | {total} | {pct:.1f}% |\n"

    return table


def generate_evidence_snippet_quality_table(df: pd.DataFrame) -> str:
    """Generate evidence snippet quality metrics."""
    evidence_cols = [c for c in df.columns if 'Evidence Snippet' in c]

    table = "## Evidence Snippet Quality\n\n"
    table += "| Property | Snippets | Avg Length | Has Organism | Has Value |\n"
    table += "|----------|----------|------------|--------------|----------|\n"

    for col in evidence_cols:
        if col in df.columns:
            snippets = df[col].dropna()
            if len(snippets) > 0:
                avg_len = snippets.str.len().mean()
                prop_name = col.replace(' Evidence Snippet', '')

                # Check for organism mentions (simplified)
                org_col = f"{prop_name} Citation Organism"
                if org_col not in df.columns:
                    org_col = f"{prop_name} Organism"

                has_org = 0
                if org_col in df.columns:
                    # Count snippets where corresponding organism exists
                    has_org = ((df[col].notna()) & (df[org_col].notna())).sum()

                has_org_pct = (has_org / len(snippets) * 100) if len(snippets) > 0 else 0

                table += f"| {prop_name} | {len(snippets)} | {avg_len:.0f} chars | {has_org_pct:.0f}% | - |\n"

    return table


def generate_taxonomy_database_coverage_table() -> str:
    """Generate taxonomy database coverage table."""
    table = "## Taxonomy Database Coverage\n\n"
    table += "| Database | Species | Genera | Domain Coverage |\n"
    table += "|----------|---------|--------|------------------|\n"
    table += "| **GTDB Release 226** | 143,614 | 29,405 | Bacteria + Archaea |\n"
    table += "| **LPSN** | +13,055 | +1,097 | Additional prokaryotes |\n"
    table += "| **NCBI Taxonomy** | +707,694 | +18,516 | All microorganisms |\n"
    table += "| **TOTAL** | **864,363** | **49,018** | **Comprehensive** |\n"

    return table


def generate_organism_diversity_table(results: Dict) -> str:
    """Generate organism diversity by domain table."""
    if 'organism_statistics' not in results or 'organism_list' not in results['organism_statistics']:
        return "## Organism Diversity by Domain\n\n*No extraction results available*\n"

    organisms = results['organism_statistics']['organism_list']

    # Classify by domain (simplified heuristics)
    bacteria = []
    archaea = []
    fungi = []
    protozoa = []

    # Known patterns
    fungi_genera = ['Saccharomyces', 'Aspergillus', 'Fusarium', 'Rhizoctonia',
                   'Trichoderma', 'Cunninghamella', 'Candida', 'Penicillium']
    archaea_genera = ['Methanobacterium', 'Methanococcus', 'Methanopyrus',
                     'Methanothermus', 'Pyrococcus', 'Sulfolobus', 'Thermococcus']
    protozoa_genera = ['Tetrahymena', 'Paramecium', 'Plasmodium', 'Toxoplasma']

    for org in organisms:
        genus = org.split()[0].replace('.', '')

        if genus in fungi_genera or any(f in org for f in fungi_genera):
            fungi.append(org)
        elif genus in archaea_genera or any(a in org for a in archaea_genera):
            archaea.append(org)
        elif genus in protozoa_genera or any(p in org for p in protozoa_genera):
            protozoa.append(org)
        else:
            bacteria.append(org)

    table = "## Organism Diversity by Domain\n\n"
    table += "| Domain | Count | Percentage | Examples |\n"
    table += "|--------|-------|------------|----------|\n"

    total = len(organisms)
    table += f"| **Bacteria** | {len(bacteria)} | {len(bacteria)/total*100:.1f}% | {', '.join(bacteria[:3])} |\n"
    table += f"| **Archaea** | {len(archaea)} | {len(archaea)/total*100:.1f}% | {', '.join(archaea[:3])} |\n"
    table += f"| **Fungi** | {len(fungi)} | {len(fungi)/total*100:.1f}% | {', '.join(fungi[:3])} |\n"
    table += f"| **Protozoa** | {len(protozoa)} | {len(protozoa)/total*100:.1f}% | {', '.join(protozoa[:3])} |\n"
    table += f"| **TOTAL** | **{total}** | **100%** | - |\n"

    return table


def generate_file_source_distribution_table() -> str:
    """Generate file source distribution table."""
    import subprocess

    pdf_count = int(subprocess.check_output("find data/pdfs -name '*.pdf' | wc -l", shell=True).decode().strip())
    pdf_md_count = int(subprocess.check_output("find data/pdfs -name '*.md' | wc -l", shell=True).decode().strip())
    abstract_count = int(subprocess.check_output("find data/abstracts -name '*.md' 2>/dev/null | wc -l", shell=True).decode().strip())

    total_md = pdf_md_count + abstract_count

    table = "## File Source Distribution\n\n"
    table += "| Source Type | Count | Percentage | Quality |\n"
    table += "|-------------|-------|------------|----------|\n"
    table += f"| **Full PDFs** | {pdf_count} | {pdf_count/total_md*100:.1f}% | High (full text) |\n"
    table += f"| **PDF Markdowns** | {pdf_md_count} | {pdf_md_count/total_md*100:.1f}% | High (converted) |\n"
    table += f"| **Abstract-only** | {abstract_count} | {abstract_count/total_md*100:.1f}% | Medium (limited) |\n"
    table += f"| **Total Markdowns** | **{total_md}** | **100%** | - |\n"

    return table


def generate_ingredient_processing_status_table(df: pd.DataFrame) -> str:
    """Generate ingredient processing status table."""
    table = "## Ingredient Processing Status\n\n"
    table += "| Ingredient | Properties Extracted | Evidence Snippets | Organisms Found |\n"
    table += "|------------|---------------------|-------------------|------------------|\n"

    org_cols = [c for c in df.columns if 'Organism' in c and 'Model' not in c]
    evidence_cols = [c for c in df.columns if 'Evidence Snippet' in c]

    for idx, row in df.iterrows():
        ingredient = row.get('Ingredient', f'Ingredient_{idx}')

        # Count filled organism columns
        orgs_filled = sum(1 for col in org_cols if pd.notna(row.get(col)))

        # Count filled evidence columns
        evidence_filled = sum(1 for col in evidence_cols if pd.notna(row.get(col)))

        # Get unique organisms
        organisms = set()
        for col in org_cols:
            if pd.notna(row.get(col)):
                orgs = str(row[col]).split(', ')
                organisms.update(orgs)

        table += f"| {ingredient} | {orgs_filled}/{len(org_cols)} | {evidence_filled}/{len(evidence_cols)} | {len(organisms)} |\n"

    return table


def main():
    """Generate all tables."""
    print("Loading data...")
    df, results = load_data()

    print("Generating tables...")

    tables = {
        "1_organism_statistics": generate_organism_statistics_table(df, results),
        "2_coverage_statistics": generate_coverage_statistics_table(df, results),
        "3_confidence_distribution": generate_confidence_distribution_table(results),
        "4_property_extraction_status": generate_property_extraction_status_table(df),
        "5_doi_citation_coverage": generate_doi_citation_coverage_table(df),
        "6_evidence_snippet_quality": generate_evidence_snippet_quality_table(df),
        "7_taxonomy_database_coverage": generate_taxonomy_database_coverage_table(),
        "8_organism_diversity": generate_organism_diversity_table(results),
        "9_file_source_distribution": generate_file_source_distribution_table(),
        "10_ingredient_processing_status": generate_ingredient_processing_status_table(df)
    }

    # Write all tables to a single comprehensive report
    output_path = Path("notes/COMPREHENSIVE_TABLES_REPORT.md")

    with open(output_path, 'w') as f:
        f.write("# Comprehensive Statistical Tables Report\n\n")
        f.write(f"**Generated:** 2026-01-08 (with NCBI Taxonomy Integration)\n\n")
        f.write("**Data Source:** Evidence extraction with GTDB + LPSN + NCBI validation\n\n")
        f.write("---\n\n")

        for name, table in tables.items():
            f.write(table)
            f.write("\n\n")
            f.write("---\n\n")

    print(f"\n✓ All tables generated: {output_path}")
    print(f"✓ Total tables: {len(tables)}")

    # Also print tables to console
    for name, table in tables.items():
        print(f"\n{table}")


if __name__ == "__main__":
    main()

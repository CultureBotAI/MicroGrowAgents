#!/usr/bin/env python
"""
Run CSV enrichment on the cleaned dataset (invalid DOIs removed).

This script processes the cleaned MP medium ingredient properties CSV,
downloading PDFs for all remaining valid DOIs.
"""

from pathlib import Path

from microgrowagents.agents.csv_all_dois_enrichment_agent import (
    CSVAllDOIsEnrichmentAgent,
)


def main():
    """Run enrichment on cleaned CSV."""
    csv_path = Path("data/processed/mp_medium_ingredient_properties_cleaned.csv")
    email = "MJoachimiak@lbl.gov"

    print("Running enrichment on cleaned CSV (invalid DOIs removed)")
    print(f"CSV: {csv_path}")
    print(f"Email: {email}")
    print()

    # Create agent
    agent = CSVAllDOIsEnrichmentAgent(
        csv_path=csv_path,
        email=email,
        use_fallback_pdf=True,
    )

    # Run enrichment (no limit, process all DOIs)
    result = agent.run(limit=None, dry_run=False)

    # Generate report
    report_path = Path("enrichment_cleaned_csv_report.md")
    agent.generate_report(result["results"], report_path)

    print("\n" + "=" * 70)
    print("Enrichment complete!")
    print("=" * 70)
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()

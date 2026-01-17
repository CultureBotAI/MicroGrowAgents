"""CLI script to download all PDFs from CSV DOI columns.

This script processes all 146 unique DOIs from all 20 DOI citation columns
in the MP medium ingredient properties CSV file.
"""

import json
import sys
from pathlib import Path

from microgrowagents.agents.csv_all_dois_enrichment_agent import (
    CSVAllDOIsEnrichmentAgent,
)


def main():
    """Run the CSV all-DOIs enrichment agent."""
    print("\n" + "=" * 70)
    print("CSV All-DOIs PDF Downloader")
    print("=" * 70)

    # Configuration
    csv_path = Path("data/raw/mp_medium_ingredient_properties.csv")
    email = "MJoachimiak@lbl.gov"
    pdf_cache_dir = Path("data/pdfs")

    if not csv_path.exists():
        print(f"\n❌ Error: CSV file not found at {csv_path}")
        sys.exit(1)

    # Auto-select full download (option 5)
    print("\nAuto-selecting: Full download (all DOIs)")
    dry_run = False
    limit = None  # All DOIs

    # Create agent
    print(f"\nInitializing agent...")
    print(f"  CSV: {csv_path}")
    print(f"  Email: {email}")
    print(f"  PDF cache: {pdf_cache_dir}")

    agent = CSVAllDOIsEnrichmentAgent(
        csv_path=csv_path, email=email, pdf_cache_dir=pdf_cache_dir
    )

    # Run agent
    result = agent.run(limit=limit, dry_run=dry_run)

    # Save results
    if not dry_run and result["results"]:
        results_file = Path("csv_all_dois_results.json")
        with open(results_file, "w") as f:
            # Convert Path objects to strings for JSON serialization
            serializable_results = []
            for r in result["results"]:
                r_copy = r.copy()
                if "pdf_path" in r_copy:
                    r_copy["pdf_path"] = str(r_copy["pdf_path"])
                serializable_results.append(r_copy)

            json.dump(
                {
                    "success": result["success"],
                    "stats": result["stats"],
                    "results": serializable_results,
                },
                f,
                indent=2,
            )
        print(f"\n✓ Results saved to: {results_file}")

        # Generate markdown report
        report_file = Path("csv_all_dois_report.md")
        agent.generate_report(result["results"], report_file)

    print("\n✓ Done!")


if __name__ == "__main__":
    main()

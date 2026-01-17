"""
Script to enrich ingredient_effects table with parsed and literature-derived data.
"""

from pathlib import Path
from microgrowagents.agents.ingredient_effects_enrichment_agent import (
    IngredientEffectsEnrichmentAgent,
)
import json


def main():
    """Run enrichment on ingredient_effects table."""
    db_path = Path("data/processed/microgrow.duckdb")

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return

    # Initialize agent with your email for Unpaywall
    email = input("Enter your email for Unpaywall API (or press Enter to skip PDF download): ")
    if not email:
        email = "noreply@example.com"

    agent = IngredientEffectsEnrichmentAgent(db_path=db_path, email=email)

    print("\n" + "=" * 80)
    print("Ingredient Effects Enrichment")
    print("=" * 80)
    print("\nOptions:")
    print("1. Dry run (parse only, no PDF download, no database updates)")
    print("2. Parse + PDF download (dry run, no database updates)")
    print("3. Full enrichment (parse + PDF + database updates)")
    print("4. Parse only and update database (no PDF download)")

    choice = input("\nSelect option (1-4): ")

    limit = int(input("How many records to process? (default: 3): ") or "3")

    if choice == "1":
        # Dry run - parse only
        print("\n=== DRY RUN: Parse only ===")
        result = agent.run(limit=limit, dry_run=True)

    elif choice == "2":
        # Parse + PDF download (dry run)
        print("\n=== DRY RUN: Parse + PDF download ===")
        result = agent.run(limit=limit, dry_run=True)

    elif choice == "3":
        # Full enrichment
        confirm = input(
            "\nThis will update the database. Continue? (yes/no): "
        )
        if confirm.lower() != "yes":
            print("Cancelled.")
            return

        print("\n=== FULL ENRICHMENT ===")
        result = agent.run(limit=limit, dry_run=False)

    elif choice == "4":
        # Parse only and update
        confirm = input(
            "\nThis will update the database (parse only, no PDF). Continue? (yes/no): "
        )
        if confirm.lower() != "yes":
            print("Cancelled.")
            return

        print("\n=== PARSE AND UPDATE ===")
        result = agent.run(limit=limit, dry_run=False)

    else:
        print("Invalid choice.")
        return

    # Display results
    print("\n" + "=" * 80)
    print("Results")
    print("=" * 80)
    print(f"Success: {result['success']}")
    print(f"\nStatistics:")
    for key, value in result['stats'].items():
        print(f"  {key}: {value}")

    print(f"\n=== Enriched Records ({len(result['enriched_records'])}) ===")
    for record in result["enriched_records"]:
        print(f"\nRecord ID: {record['id']}")
        print(f"  Cellular Role: {record['cellular_role']}")
        print(f"  Toxicity: {record['toxicity_value']} {record['toxicity_unit']}")
        print(f"  Species-specific: {record['toxicity_species_specific']}")
        print(f"  Toxicity Effects: {record['toxicity_cellular_effects']}")
        if record.get("evidence_organism"):
            print(f"  Organism: {record['evidence_organism']}")
        if record.get("evidence_snippet"):
            print(f"  Evidence Snippet: {record['evidence_snippet'][:100]}...")
        if record.get("toxicity_evidence_snippet"):
            print(f"  Toxicity Snippet: {record['toxicity_evidence_snippet'][:100]}...")

    # Save to file
    output_file = Path("enrichment_results.json")
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nFull results saved to: {output_file}")

    agent.close()


if __name__ == "__main__":
    main()

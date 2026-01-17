"""
Migrate existing database to add new evidence and toxicity columns.

This script adds the following columns to ingredient_effects table:
- evidence_organism: Organism(s) relevant to evidence
- evidence_snippet: Supporting text from paper
- cellular_role: Cellular role/function
- cellular_requirements: Specific cellular requirements
- toxicity_value: Minimal concentration eliciting toxicity
- toxicity_unit: Unit for toxicity value
- toxicity_species_specific: Whether toxicity is species-specific
- toxicity_cellular_effects: Cellular effects at toxic levels
- toxicity_evidence: DOI/citation for toxicity
- toxicity_evidence_snippet: Supporting text for toxicity
"""

import duckdb
from pathlib import Path


def migrate_database(db_path: Path) -> None:
    """
    Add new columns to ingredient_effects table.

    Args:
        db_path: Path to DuckDB database file
    """
    print(f"Migrating database: {db_path}")

    conn = duckdb.connect(str(db_path))

    # Check current structure
    print("\n=== Current ingredient_effects structure ===")
    result = conn.execute("PRAGMA table_info(ingredient_effects)").fetchall()
    current_columns = {row[1] for row in result}
    print(f"Current columns: {', '.join(sorted(current_columns))}")

    # Define new columns to add
    new_columns = {
        "evidence_organism": "VARCHAR",
        "evidence_snippet": "TEXT",
        "cellular_role": "VARCHAR",
        "cellular_requirements": "TEXT",
        "toxicity_value": "DOUBLE",
        "toxicity_unit": "VARCHAR",
        "toxicity_species_specific": "BOOLEAN",
        "toxicity_cellular_effects": "TEXT",
        "toxicity_evidence": "TEXT",
        "toxicity_evidence_snippet": "TEXT",
    }

    # Add each new column if it doesn't exist
    print("\n=== Adding new columns ===")
    for col_name, col_type in new_columns.items():
        if col_name not in current_columns:
            print(f"Adding column: {col_name} ({col_type})")
            conn.execute(f"ALTER TABLE ingredient_effects ADD COLUMN {col_name} {col_type}")
        else:
            print(f"Column already exists: {col_name}")

    # Verify new structure
    print("\n=== New ingredient_effects structure ===")
    result = conn.execute("PRAGMA table_info(ingredient_effects)").fetchall()
    for row in result:
        print(f"  {row[1]:<35} {row[2]:<15}")

    # Check row count
    count = conn.execute("SELECT COUNT(*) FROM ingredient_effects").fetchone()[0]
    print(f"\nTotal rows in ingredient_effects: {count}")

    conn.close()
    print("\n✓ Migration completed successfully!")


if __name__ == "__main__":
    db_path = Path("data/processed/microgrow.duckdb")

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Please ensure the database exists before running migration.")
        exit(1)

    # Backup recommendation
    print("=" * 60)
    print("RECOMMENDATION: Create a backup before migration")
    print(f"  cp {db_path} {db_path}.backup")
    print("=" * 60)

    response = input("\nProceed with migration? (yes/no): ")
    if response.lower() in ["yes", "y"]:
        migrate_database(db_path)
    else:
        print("Migration cancelled.")

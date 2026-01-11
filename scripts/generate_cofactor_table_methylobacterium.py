"""
Generate cofactor table for Methylobacterium using CofactorMediaAgent.

This script generates a comprehensive cofactor analysis table showing:
- Required cofactors identified from genome annotations
- Whether they're covered by existing MP medium ingredients
- Recommendations for missing cofactors
"""

import pandas as pd
from pathlib import Path
from microgrowagents.agents import CofactorMediaAgent


def format_cofactor_table(table_data):
    """Format cofactor table for display."""
    if not table_data:
        return None

    df = pd.DataFrame(table_data)

    # Sort by category and cofactor
    category_order = ["vitamins", "metals", "nucleotides", "energy_cofactors", "other"]
    df["Category"] = pd.Categorical(df["Category"], categories=category_order, ordered=True)
    df = df.sort_values(["Category", "Cofactor", "Status"])

    return df


def generate_cofactor_table(organism_name, genome_id=None):
    """
    Generate cofactor table for specified organism.

    Args:
        organism_name: Name of organism (e.g., "Methylobacterium radiotolerans")
        genome_id: Optional SAMN genome ID
    """
    print(f"Analyzing cofactor requirements for: {organism_name}")
    print("=" * 80)

    # Initialize agent
    db_path = Path("data/processed/microgrow.duckdb")
    agent = CofactorMediaAgent(db_path)

    # Use genome_id if provided, otherwise organism_name
    query_organism = genome_id if genome_id else organism_name

    # Run cofactor analysis
    print(f"\n1. Running CofactorMediaAgent for {query_organism}...")
    result = agent.run(
        query=f"Analyze cofactor requirements for {organism_name}",
        organism=query_organism,
        base_medium="MP"
    )

    if not result.get("success"):
        print(f"Error: {result.get('error')}")
        return None

    # Extract results
    data = result["data"]
    cofactor_table = data.get("cofactor_table", [])
    cofactor_requirements = data.get("cofactor_requirements", [])
    existing_coverage = data.get("existing_coverage", [])
    new_recommendations = data.get("new_recommendations", [])

    print(f"✓ Analysis complete")
    print(f"  - {len(cofactor_requirements)} cofactors identified")
    print(f"  - {len(existing_coverage)} covered by MP medium")
    print(f"  - {len(new_recommendations)} gaps identified")

    # Format table
    df = format_cofactor_table(cofactor_table)

    if df is not None:
        print(f"\n2. Cofactor Table ({len(df)} rows):")
        print("=" * 80)

        # Display by category
        for category in df["Category"].unique():
            cat_df = df[df["Category"] == category]
            print(f"\n{category.upper().replace('_', ' ')}")
            print("-" * 80)

            # Show table
            display_cols = ["Cofactor", "Ingredient", "Status", "Rationale"]
            print(cat_df[display_cols].to_string(index=False))

        # Save to CSV
        output_path = Path("outputs/cofactor_analysis")
        output_path.mkdir(parents=True, exist_ok=True)

        csv_file = output_path / f"cofactor_table_{organism_name.replace(' ', '_')}.csv"
        df.to_csv(csv_file, index=False)
        print(f"\n3. Saved to: {csv_file}")

        # Print summary statistics
        print(f"\n4. Summary Statistics:")
        print("=" * 80)
        print(f"Total cofactors analyzed: {len(df)}")
        print(f"Existing in MP medium: {len(df[df['Status'] == 'existing'])}")
        print(f"Missing from MP medium: {len(df[df['Status'] == 'missing'])}")

        # Group by category
        print("\nBy Category:")
        category_stats = df.groupby("Category")["Status"].value_counts().unstack(fill_value=0)
        print(category_stats.to_string())

        return df
    else:
        print("No cofactor table generated")
        return None


def main():
    """Main function."""
    # Try Methylobacterium radiotolerans (available in database)
    print("COFACTOR ANALYSIS FOR METHYLOBACTERIUM")
    print("=" * 80)
    print("\nNote: Using Methylobacterium radiotolerans as a representative")
    print("methylotroph (M. extorquens AM-1 genome not in current database)")
    print()

    df = generate_cofactor_table(
        organism_name="Methylobacterium radiotolerans",
        genome_id="SAMN08769567"
    )

    if df is not None:
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        print("\nThe cofactor table shows:")
        print("  - 'existing': Cofactor provided by ingredient already in MP medium")
        print("  - 'missing': Cofactor not covered by MP medium (gap identified)")
        print("\nFor M. extorquens AM-1 specifically:")
        print("  - Similar cofactor requirements expected (both methylotrophs)")
        print("  - Would need lanthanides (Nd, Pr) for XoxF-type methanol dehydrogenase")
        print("  - PQQ cofactor essential for methanol oxidation")


if __name__ == "__main__":
    main()

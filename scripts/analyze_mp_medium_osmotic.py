#!/usr/bin/env python
"""
Quick integration script: MP Medium with Osmotic Properties

Combines sensitivity analysis with the newly implemented osmotic property
calculations for MP medium.

Usage:
    python scripts/analyze_mp_medium_osmotic.py
    python scripts/analyze_mp_medium_osmotic.py --output-json results.json
    python scripts/analyze_mp_medium_osmotic.py --plot --plot-output mp_osmotic.png
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from microgrowagents.agents.gen_media_conc_agent import GenMediaConcAgent
from microgrowagents.chemistry.osmotic_properties import (
    calculate_osmolarity,
    calculate_water_activity
)


def analyze_mp_medium_osmotic(
    db_path: str = "data/microgrowdb.db",
    output_json: str = None,
    plot: bool = False,
    plot_output: str = None
):
    """
    Analyze MP medium with osmotic properties.

    Args:
        db_path: Path to database
        output_json: Optional JSON output path
        plot: Whether to generate plots
        plot_output: Plot output path
    """
    print("=" * 80)
    print("MP Medium Analysis with Osmotic Properties")
    print("=" * 80)
    print()

    # Step 1: Get MP medium concentrations
    print("Step 1: Retrieving MP medium ingredient concentrations...")
    agent = GenMediaConcAgent(db_path=db_path)
    result = agent.run("MP medium", mode="medium")

    if not result["success"]:
        print(f"Error: {result.get('message', 'Failed to retrieve MP medium')}")
        return

    ingredients_data = result["data"]
    print(f"✓ Found {len(ingredients_data)} ingredients")
    print()

    # Step 2: Prepare ingredients for osmotic calculations
    print("Step 2: Preparing ingredients for osmotic calculations...")
    ingredients = []
    for ing in ingredients_data:
        ingredient = {
            "name": ing["name"],
            "concentration": ing["concentration_mM"],
            "molecular_weight": ing.get("molecular_weight", 0),
            "formula": ing.get("formula", ""),
            "charge": ing.get("charge", 0),
            "grams_per_liter": ing["concentration_g_per_L"]
        }
        ingredients.append(ingredient)
        print(f"  - {ing['name']}: {ing['concentration_mM']:.2f} mM ({ing['concentration_g_per_L']:.2f} g/L)")

    print()

    # Step 3: Calculate osmotic properties
    print("Step 3: Calculating osmotic properties...")
    print()

    # Osmolarity
    osm_result = calculate_osmolarity(ingredients, temperature=25.0)
    print("Osmolarity Results:")
    print(f"  Osmolarity: {osm_result['osmolarity']:.1f} mOsm/L")
    print(f"  Osmolality: {osm_result['osmolality']:.1f} mOsm/kg")
    print(f"  Confidence: {osm_result['confidence']:.2f}")
    print()

    print("  Van't Hoff Factors:")
    for name, factor in osm_result["van_hoff_factors"].items():
        print(f"    {name}: {factor:.2f}")
    print()

    if osm_result["warnings"]:
        print("  Warnings:")
        for warning in osm_result["warnings"]:
            print(f"    ⚠ {warning}")
        print()

    # Water activity
    print("Water Activity Results:")
    aw_result = calculate_water_activity(ingredients, temperature=25.0, method="raoult")
    print(f"  Water Activity (aw): {aw_result['water_activity']:.4f}")
    print(f"  Growth Category: {aw_result['growth_category']}")
    print(f"  Method: {aw_result['method']}")
    print(f"  Confidence: {aw_result['confidence']:.2f}")
    print()

    if aw_result["warnings"]:
        print("  Warnings:")
        for warning in aw_result["warnings"]:
            print(f"    ⚠ {warning}")
        print()

    # Step 4: Interpret results
    print("=" * 80)
    print("Interpretation:")
    print("=" * 80)
    print()

    # Osmolarity interpretation
    osmolarity = osm_result['osmolarity']
    print(f"Osmolarity ({osmolarity:.1f} mOsm/L):")
    if osmolarity < 200:
        print("  → Hypotonic (low osmotic pressure)")
    elif osmolarity < 400:
        print("  → Isotonic (typical for most bacteria)")
    else:
        print("  → Hypertonic (high osmotic pressure)")
    print()

    # Water activity interpretation
    aw = aw_result['water_activity']
    print(f"Water Activity ({aw:.4f}):")
    if aw > 0.98:
        print("  → Suitable for most bacteria and fungi")
    elif aw > 0.93:
        print("  → Suitable for halotolerant bacteria")
    elif aw > 0.75:
        print("  → Suitable for halophilic bacteria and xerophilic fungi")
    else:
        print("  → Extreme environment (limited microbial growth)")
    print()

    # Step 5: Save results
    if output_json:
        print(f"Saving results to {output_json}...")
        output_data = {
            "medium": "MP medium",
            "ingredients": ingredients_data,
            "osmotic_properties": {
                "osmolarity_mOsm_L": osm_result["osmolarity"],
                "osmolality_mOsm_kg": osm_result["osmolality"],
                "van_hoff_factors": osm_result["van_hoff_factors"],
                "water_activity": aw_result["water_activity"],
                "growth_category": aw_result["growth_category"],
                "method": aw_result["method"],
                "confidence": {
                    "osmolarity": osm_result["confidence"],
                    "water_activity": aw_result["confidence"]
                },
                "warnings": osm_result["warnings"] + aw_result["warnings"]
            }
        }

        with open(output_json, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"✓ Saved to {output_json}")
        print()

    # Step 6: Generate plots (optional)
    if plot:
        print("Generating visualization plots...")
        try:
            import matplotlib.pyplot as plt
            import numpy as np

            fig, axes = plt.subplots(2, 2, figsize=(14, 10))

            # Plot 1: Ingredient concentrations (mM)
            ax = axes[0, 0]
            names = [ing["name"] for ing in ingredients_data[:10]]  # Top 10
            concs = [ing["concentration_mM"] for ing in ingredients_data[:10]]
            colors = ['skyblue' if c < 50 else 'salmon' for c in concs]
            ax.barh(names, concs, color=colors, edgecolor='black')
            ax.set_xlabel('Concentration (mM)', fontweight='bold')
            ax.set_title('MP Medium Ingredient Concentrations', fontweight='bold')
            ax.grid(axis='x', alpha=0.3)

            # Plot 2: Van't Hoff factors
            ax = axes[0, 1]
            vhf_names = list(osm_result["van_hoff_factors"].keys())[:10]
            vhf_values = [osm_result["van_hoff_factors"][n] for n in vhf_names]
            colors = ['green' if v > 1.5 else 'orange' if v > 1.1 else 'blue' for v in vhf_values]
            ax.barh(vhf_names, vhf_values, color=colors, edgecolor='black', alpha=0.7)
            ax.axvline(x=1.0, color='red', linestyle='--', label='Non-dissociating')
            ax.set_xlabel("Van't Hoff Factor", fontweight='bold')
            ax.set_title("Dissociation Factors", fontweight='bold')
            ax.legend()
            ax.grid(axis='x', alpha=0.3)

            # Plot 3: Osmotic pressure gauge
            ax = axes[1, 0]
            osmolarity = osm_result['osmolarity']
            categories = ['Hypotonic\n(<200)', 'Isotonic\n(200-400)', 'Hypertonic\n(>400)']
            ranges = [200, 400, 600]
            colors_gauge = ['lightblue', 'lightgreen', 'lightcoral']

            # Horizontal gauge
            y_pos = 0
            x_start = 0
            for i, (cat, r, c) in enumerate(zip(categories, ranges, colors_gauge)):
                width = r - x_start
                ax.barh(y_pos, width, left=x_start, height=0.5, color=c, edgecolor='black')
                ax.text(x_start + width/2, y_pos, cat, ha='center', va='center', fontsize=9)
                x_start = r

            # Mark current value
            ax.plot([osmolarity, osmolarity], [y_pos - 0.3, y_pos + 0.3], 'r-', linewidth=3)
            ax.plot(osmolarity, y_pos, 'ro', markersize=10)
            ax.text(osmolarity, y_pos + 0.6, f'{osmolarity:.0f} mOsm/L', ha='center', fontsize=10, fontweight='bold')

            ax.set_xlim(0, 600)
            ax.set_ylim(-0.5, 0.5)
            ax.set_yticks([])
            ax.set_xlabel('Osmolarity (mOsm/L)', fontweight='bold')
            ax.set_title('Osmotic Pressure Classification', fontweight='bold')

            # Plot 4: Water activity gauge
            ax = axes[1, 1]
            aw = aw_result['water_activity']
            categories_aw = ['Halophiles\n(<0.90)', 'Halotolerant\n(0.90-0.98)', 'Most Bacteria\n(>0.98)']
            ranges_aw = [0.90, 0.98, 1.00]
            colors_aw = ['lightcoral', 'lightyellow', 'lightgreen']

            # Horizontal gauge
            y_pos = 0
            x_start = 0.75
            for i, (cat, r, c) in enumerate(zip(categories_aw, ranges_aw, colors_aw)):
                width = r - x_start
                ax.barh(y_pos, width, left=x_start, height=0.5, color=c, edgecolor='black')
                ax.text(x_start + width/2, y_pos, cat, ha='center', va='center', fontsize=9)
                x_start = r

            # Mark current value
            ax.plot([aw, aw], [y_pos - 0.3, y_pos + 0.3], 'r-', linewidth=3)
            ax.plot(aw, y_pos, 'ro', markersize=10)
            ax.text(aw, y_pos + 0.6, f'{aw:.4f}', ha='center', fontsize=10, fontweight='bold')

            ax.set_xlim(0.75, 1.00)
            ax.set_ylim(-0.5, 0.5)
            ax.set_yticks([])
            ax.set_xlabel('Water Activity (aw)', fontweight='bold')
            ax.set_title('Water Activity Classification', fontweight='bold')

            plt.suptitle('MP Medium Osmotic Properties Analysis', fontsize=16, fontweight='bold')
            plt.tight_layout()

            output_path = plot_output or "mp_medium_osmotic.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Saved plot to {output_path}")
            print()

        except ImportError as e:
            print(f"⚠ Could not generate plots: {e}")
            print("  Install matplotlib to enable plotting")
            print()

    print("=" * 80)
    print("Analysis Complete!")
    print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze MP medium with osmotic properties"
    )
    parser.add_argument(
        "--db-path",
        default="data/microgrowdb.db",
        help="Path to database (default: data/microgrowdb.db)"
    )
    parser.add_argument(
        "--output-json",
        help="Save results to JSON file"
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate visualization plots"
    )
    parser.add_argument(
        "--plot-output",
        help="Plot output path (default: mp_medium_osmotic.png)"
    )

    args = parser.parse_args()

    analyze_mp_medium_osmotic(
        db_path=args.db_path,
        output_json=args.output_json,
        plot=args.plot,
        plot_output=args.plot_output
    )


if __name__ == "__main__":
    main()

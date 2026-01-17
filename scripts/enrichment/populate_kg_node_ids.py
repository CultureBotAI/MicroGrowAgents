#!/usr/bin/env python3
"""Populate KG-Microbe node IDs and labels for alternative ingredients.

Matches alternative ingredient names to KG-Microbe nodes and populates
the DOI Citation, KG Node ID, and KG Node Label columns.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Optional, Tuple
import re


class KGNodeMatcher:
    """Match ingredient names to KG-Microbe nodes."""

    def __init__(self, kg_nodes_path: Path):
        """
        Initialize KG node matcher.

        Args:
            kg_nodes_path: Path to KG-Microbe merged-kg_nodes.tsv
        """
        self.kg_nodes_path = kg_nodes_path
        self.nodes_df = None
        self.name_to_node = {}
        self._load_kg_nodes()

    def _load_kg_nodes(self):
        """Load KG-Microbe nodes and build name index."""
        print(f"Loading KG-Microbe nodes from {self.kg_nodes_path}...")

        # Read TSV
        self.nodes_df = pd.read_csv(
            self.kg_nodes_path,
            sep='\t',
            usecols=['id', 'name', 'category', 'synonym', 'xref']
        )

        # Filter to chemical entities
        self.nodes_df = self.nodes_df[
            self.nodes_df['category'].str.contains('ChemicalEntity|ChemicalSubstance', na=False)
        ]

        print(f"Loaded {len(self.nodes_df)} chemical entity nodes")

        # Build name index (lowercase for matching)
        for _, row in self.nodes_df.iterrows():
            node_id = row['id']
            name = str(row['name']).lower()

            # Index by primary name
            self.name_to_node[name] = (node_id, row['name'])

            # Index by synonyms if available
            if pd.notna(row['synonym']):
                synonyms = str(row['synonym']).split('|')
                for syn in synonyms:
                    syn_clean = syn.strip().lower()
                    if syn_clean and syn_clean not in self.name_to_node:
                        self.name_to_node[syn_clean] = (node_id, row['name'])

        print(f"Built index with {len(self.name_to_node)} names/synonyms")

    def match_ingredient(self, ingredient_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Match ingredient name to KG node.

        Args:
            ingredient_name: Ingredient name to match

        Returns:
            Tuple of (node_id, node_label) or (None, None) if no match
        """
        # Try exact match (case-insensitive)
        name_lower = ingredient_name.lower().strip()

        # Direct match
        if name_lower in self.name_to_node:
            return self.name_to_node[name_lower]

        # Try without suffixes like "chloride", "sulfate", etc.
        name_base = re.sub(r'\s+(chloride|sulfate|acetate|citrate|nitrate).*$', '', name_lower)
        if name_base != name_lower and name_base in self.name_to_node:
            return self.name_to_node[name_base]

        # Try common variations
        variations = [
            name_lower.replace('-', ' '),
            name_lower.replace(' ', '-'),
            name_lower.replace('(iii)', '').strip(),
            name_lower.replace('(ii)', '').strip(),
            name_lower.replace(' hexahydrate', ''),
            name_lower.replace(' dihydrate', ''),
            name_lower.replace(' monohydrate', ''),
        ]

        for variant in variations:
            if variant in self.name_to_node:
                return self.name_to_node[variant]

        # Try partial matches for common compounds
        if 'glucose' in name_lower:
            return self._search_by_keyword('glucose')
        elif 'glycerol' in name_lower:
            return self._search_by_keyword('glycerol')
        elif 'acetate' in name_lower:
            return self._search_by_keyword('acetate')

        return None, None

    def _search_by_keyword(self, keyword: str) -> Tuple[Optional[str], Optional[str]]:
        """Search for node by keyword."""
        keyword_lower = keyword.lower()
        for name, (node_id, label) in self.name_to_node.items():
            if keyword_lower == name:  # Exact keyword match
                return node_id, label
        return None, None


def populate_kg_node_ids(
    input_csv: Path,
    output_csv: Path,
    kg_nodes_path: Path,
    backup: bool = True
):
    """
    Populate KG node IDs and labels for alternative ingredients.

    Args:
        input_csv: Path to alternate_ingredients_table.csv
        output_csv: Path to output CSV
        kg_nodes_path: Path to KG-Microbe merged-kg_nodes.tsv
        backup: Create backup of input file
    """
    print("\n" + "="*70)
    print("POPULATE KG NODE IDs FOR ALTERNATIVE INGREDIENTS")
    print("="*70 + "\n")

    # Load alternative ingredients
    df = pd.read_csv(input_csv)
    print(f"Loaded {len(df)} alternative ingredient mappings")
    print(f"Columns: {list(df.columns)}")

    # Add KG columns if they don't exist
    if 'KG Node ID' not in df.columns:
        df['KG Node ID'] = ''
    if 'KG Node Label' not in df.columns:
        df['KG Node Label'] = ''
    if 'DOI Citation' not in df.columns:
        df['DOI Citation'] = ''

    # Initialize matcher
    matcher = KGNodeMatcher(kg_nodes_path)

    # Match each alternative ingredient
    print("\nMatching alternative ingredients to KG nodes...")
    matched_count = 0

    for idx, row in df.iterrows():
        alt_ingredient = row['Alternate Ingredient']

        # Try to match
        node_id, node_label = matcher.match_ingredient(alt_ingredient)

        if node_id:
            df.at[idx, 'KG Node ID'] = node_id
            df.at[idx, 'KG Node Label'] = node_label
            matched_count += 1
            print(f"  ✓ {alt_ingredient} → {node_id} ({node_label})")
        else:
            print(f"  ✗ {alt_ingredient} → No match")

    # Reorder columns
    column_order = [
        'Ingredient',
        'Alternate Ingredient',
        'Rationale',
        'Alternate Role',
        'DOI Citation',
        'KG Node ID',
        'KG Node Label'
    ]
    df = df[column_order]

    # Backup original
    if backup:
        backup_path = input_csv.parent / f"{input_csv.stem}_before_kg_population.csv"
        if input_csv.exists():
            import shutil
            shutil.copy(input_csv, backup_path)
            print(f"\nCreated backup: {backup_path}")

    # Save
    df.to_csv(output_csv, index=False)

    print("\n" + "="*70)
    print("POPULATION COMPLETE")
    print("="*70)
    print(f"\nMatched: {matched_count}/{len(df)} ({matched_count/len(df)*100:.1f}%)")
    print(f"Output: {output_csv}")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Populate KG node IDs for alternative ingredients"
    )
    parser.add_argument(
        "--input",
        default="data/processed/alternate_ingredients_table.csv",
        help="Input CSV file"
    )
    parser.add_argument(
        "--output",
        default="data/processed/alternate_ingredients_table.csv",
        help="Output CSV file (overwrites input by default)"
    )
    parser.add_argument(
        "--kg-nodes",
        default="data/raw/kg_microbe_core/merged-kg_nodes.tsv",
        help="Path to KG-Microbe nodes TSV"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Don't create backup of input file"
    )

    args = parser.parse_args()

    populate_kg_node_ids(
        input_csv=Path(args.input),
        output_csv=Path(args.output),
        kg_nodes_path=Path(args.kg_nodes),
        backup=not args.no_backup
    )


if __name__ == "__main__":
    main()

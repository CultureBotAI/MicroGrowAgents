"""Evidence Extraction Orchestrator.

Main coordinator for extracting organism context and evidence snippets from markdown files
and populating the CSV with extracted data.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import json
import shutil

import pandas as pd

from microgrowagents.agents.base_agent import BaseAgent
from microgrowagents.services.doi_mapping_service import DOIMappingService
from microgrowagents.extractors.organism_extractor import OrganismExtractor
from microgrowagents.extractors.evidence_snippet_extractor import EvidenceSnippetExtractor


class EvidenceExtractionOrchestrator(BaseAgent):
    """
    Orchestrate evidence extraction from markdown files to CSV.

    Extracts:
    1. Organism names for 21 organism context columns
    2. Evidence snippets for 25 property columns

    Features:
    - Dry-run mode (validation only)
    - Incremental saves (every 5 ingredients)
    - Resume capability
    - Comprehensive logging

    Examples:
        >>> orchestrator = EvidenceExtractionOrchestrator(
        ...     csv_path=Path("data/raw/mp_medium_ingredient_properties.csv")
        ... )
        >>> result = orchestrator.run(dry_run=True, sample_size=1)
        >>> result["success"]
        True
    """

    # Property columns that have DOI citations (must match CSV column names exactly)
    PROPERTY_COLUMNS = [
        "Solubility",
        "Lower Bound",
        "Upper Bound",
        "Toxicity",  # Fixed: was "Limit of Toxicity"
        "pH Effect",
        "pKa",
        "Oxidation Stability",  # Fixed: was "Oxidation State Stability"
        "Light Sensitivity",
        "Autoclave Stability",
        "Stock Concentration",
        "Precipitation Partners",
        "Antagonistic Ions",
        "Chelator Sensitivity",
        "Redox Contribution",
        "Metabolic Role",
        "Essential/Conditional",
        "Uptake Transporter",
        "Regulatory Effects",
        "Gram Differential",  # Fixed: was "Gram+/Gram- Differential"
        "Aerobe/Anaerobe",  # Fixed: was "Aerobe/Anaerobe Differential"
        "Optimal Conc.",  # Fixed: was "Optimal Conc. Model Organisms"
    ]

    def __init__(
        self,
        csv_path: Path,
        pdf_dir: Optional[Path] = None,
        abstract_dir: Optional[Path] = None,
        db_path: Optional[Path] = None
    ):
        """
        Initialize evidence extraction orchestrator.

        Args:
            csv_path: Path to MP medium ingredient properties CSV
            pdf_dir: Directory with PDF markdown files (default: data/pdfs)
            abstract_dir: Directory with abstract markdown files (default: data/abstracts)
            db_path: Path to DuckDB database (optional)
        """
        super().__init__(db_path)
        self.csv_path = Path(csv_path)

        # Initialize services
        self.doi_mapper = DOIMappingService(
            pdf_dir=pdf_dir or Path("data/pdfs"),
            abstract_dir=abstract_dir or Path("data/abstracts")
        )
        self.organism_extractor = OrganismExtractor()
        self.evidence_extractor = EvidenceSnippetExtractor()

        # Cache for markdown files (avoid re-reading)
        self._markdown_cache: Dict[str, str] = {}

        # Extraction log
        self.extraction_log: List[Dict[str, Any]] = []

    def run(
        self,
        query: str = "",
        dry_run: bool = True,
        sample_size: Optional[int] = None,
        start_ingredient: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute evidence extraction.

        Args:
            query: Unused (for BaseAgent compatibility)
            dry_run: If True, don't modify CSV (default: True)
            sample_size: Process only N ingredients (for testing)
            start_ingredient: Resume from specific ingredient

        Returns:
            Dictionary with extraction results and statistics

        Examples:
            >>> orchestrator = EvidenceExtractionOrchestrator(
            ...     csv_path=Path("data/raw/mp_medium_ingredient_properties.csv")
            ... )
            >>> result = orchestrator.run(dry_run=True, sample_size=1)
            >>> "ingredients_processed" in result
            True
        """
        self.log("Starting evidence extraction...")
        self.log(f"Dry run: {dry_run}")
        self.log(f"Sample size: {sample_size if sample_size else 'all'}")

        # Load CSV
        try:
            df = pd.read_csv(self.csv_path)
        except Exception as e:
            self.log(f"Failed to load CSV: {e}", level="ERROR")
            return {"success": False, "error": str(e)}

        self.log(f"Loaded CSV with {len(df)} ingredients")

        # Determine processing order
        processing_order = self._determine_processing_order(df, start_ingredient)

        if sample_size:
            processing_order = processing_order[:sample_size]
            self.log(f"Processing {len(processing_order)} ingredients (sample)")

        # Process each ingredient
        results = []
        for idx, (ing_idx, ingredient_row) in enumerate(processing_order):
            self.log(f"\n{'='*70}")
            self.log(f"Processing ingredient {idx+1}/{len(processing_order)}: {ingredient_row['Component']}")
            self.log(f"{'='*70}")

            ingredient_results = self._process_ingredient(df, ing_idx, ingredient_row)
            results.append(ingredient_results)

            # Incremental save (every 5 ingredients)
            if not dry_run and (idx + 1) % 5 == 0:
                self.log(f"Incremental save after {idx+1} ingredients...")
                self._save_progress(df, results)

        # Generate validation report
        report = self._generate_report(results)

        # Update CSV if not dry run
        if not dry_run:
            self.log("\nUpdating CSV with extracted data...")
            self._update_csv(df, results)
        else:
            self.log("\nDry run complete - CSV not modified")

        return {
            "success": True,
            "ingredients_processed": len(results),
            "total_extractions": sum(r["extractions_count"] for r in results),
            "report": report,
            "dry_run": dry_run
        }

    def _determine_processing_order(
        self,
        df: pd.DataFrame,
        start_ingredient: Optional[str] = None
    ) -> List[Tuple[int, pd.Series]]:
        """
        Determine processing order for ingredients.

        Args:
            df: DataFrame with ingredients
            start_ingredient: Optional ingredient to start from

        Returns:
            List of (index, row) tuples in processing order
        """
        rows = []

        for idx, row in df.iterrows():
            if start_ingredient and row["Component"] != start_ingredient and not rows:
                continue  # Skip until we find start ingredient

            rows.append((idx, row))

        return rows

    def _process_ingredient(
        self,
        df: pd.DataFrame,
        ing_idx: int,
        ingredient_row: pd.Series
    ) -> Dict[str, Any]:
        """
        Process all properties for a single ingredient.

        Args:
            df: Full DataFrame
            ing_idx: Index of ingredient row
            ingredient_row: Ingredient row data

        Returns:
            Dictionary with extraction results for this ingredient
        """
        results = {
            "ingredient": ingredient_row["Component"],
            "ingredient_index": ing_idx,
            "extractions": [],
            "errors": []
        }

        # Process each property
        for property_name in self.PROPERTY_COLUMNS:
            doi_col = self._get_doi_column(property_name)
            org_col = self._get_organism_column(property_name)
            evidence_col = self._get_evidence_column(property_name)

            # Skip if columns don't exist
            if doi_col not in df.columns or org_col not in df.columns:
                continue

            doi = ingredient_row.get(doi_col, "")

            if pd.isna(doi) or str(doi).strip() == "":
                continue  # Skip empty DOIs

            # Extract organism and evidence
            extraction = self._extract_for_property(
                doi=str(doi),
                property_name=property_name,
                property_value=str(ingredient_row.get(property_name, "")),
                ingredient_name=ingredient_row["Component"]
            )

            if extraction:
                results["extractions"].append({
                    "property": property_name,
                    "doi": doi,
                    "organism_column": org_col,
                    "evidence_column": evidence_col,
                    **extraction
                })
            else:
                results["errors"].append({
                    "property": property_name,
                    "doi": doi,
                    "error": "extraction_failed"
                })

        results["extractions_count"] = len(results["extractions"])
        results["errors_count"] = len(results["errors"])

        return results

    def _extract_for_property(
        self,
        doi: str,
        property_name: str,
        property_value: str,
        ingredient_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract organism and evidence for a specific property.

        Args:
            doi: DOI URL
            property_name: Property name (e.g., "Lower Bound")
            property_value: Property value from CSV
            ingredient_name: Ingredient name

        Returns:
            Dictionary with extracted organism and evidence, or None if failed
        """
        # Resolve markdown file
        markdown_path, source_type = self.doi_mapper.resolve_markdown(doi)

        if not markdown_path:
            self.log(f"  Markdown not found for DOI: {doi}", level="WARNING")
            return None

        # Load markdown content (with caching)
        markdown_text = self._load_markdown(markdown_path)

        if not markdown_text:
            self.log(f"  Failed to read markdown: {markdown_path}", level="WARNING")
            return None

        self.log(f"  Processing {property_name} ({source_type})...")

        # Extract organism
        organism_result = self.organism_extractor.extract(
            text=markdown_text,
            method="hybrid",
            property_name=property_name,
            property_value=property_value
        )

        organism = organism_result.get_all_organisms_string()

        # If no organism found, try inference
        if not organism:
            inference_result = self.organism_extractor.infer_organism_from_context(markdown_text)
            organism = inference_result.get_all_organisms_string()
            organism_result = inference_result

        # Extract evidence snippet
        evidence_result = self.evidence_extractor.extract(
            text=markdown_text,
            property_value=property_value,
            organism=organism or None,
            property_name=property_name
        )

        self.log(f"    Organism: {organism or '(none)'}")
        self.log(f"    Evidence: {evidence_result.snippet[:80]}...")
        self.log(f"    Confidence: {organism_result.confidence:.2f}")

        return {
            "organism": organism,
            "organism_confidence": organism_result.confidence,
            "organism_method": organism_result.method,
            "evidence": evidence_result.snippet,
            "evidence_confidence": evidence_result.confidence,
            "markdown_path": str(markdown_path),
            "markdown_source": source_type
        }

    def _load_markdown(self, markdown_path: Path) -> Optional[str]:
        """
        Load markdown file content with caching.

        Args:
            markdown_path: Path to markdown file

        Returns:
            Markdown content or None if failed
        """
        path_str = str(markdown_path)

        if path_str in self._markdown_cache:
            return self._markdown_cache[path_str]

        try:
            with open(markdown_path, "r", encoding="utf-8") as f:
                content = f.read()
                self._markdown_cache[path_str] = content
                return content
        except Exception as e:
            self.log(f"Error reading {markdown_path}: {e}", level="ERROR")
            return None

    def _get_doi_column(self, property_name: str) -> str:
        """Get DOI column name for property."""
        # Pattern for "basic" properties that have value columns: "{Property} Citation (DOI)"
        # Pattern for "model organism" property: "{Property} DOI"
        if property_name in ["Solubility", "Lower Bound", "Upper Bound", "Toxicity"]:
            return f"{property_name} Citation (DOI)"
        elif property_name == "Optimal Conc.":
            return "Optimal Conc. DOI"
        else:
            # Other properties use "{Property} DOI" pattern
            return f"{property_name} DOI"

    def _get_organism_column(self, property_name: str) -> str:
        """Get organism column name for property."""
        # Pattern for "basic" properties: "{Property} Citation Organism"
        # Pattern for others: "{Property} Organism"
        if property_name in ["Solubility", "Lower Bound", "Upper Bound", "Toxicity"]:
            return f"{property_name} Citation Organism"
        else:
            return f"{property_name} Organism"

    def _get_evidence_column(self, property_name: str) -> str:
        """Get evidence snippet column name for property."""
        # All follow same pattern: "{Property} Evidence Snippet"
        return f"{property_name} Evidence Snippet"

    def _update_csv(self, df: pd.DataFrame, results: List[Dict[str, Any]]) -> None:
        """
        Update CSV with extracted data.

        Args:
            df: DataFrame to update
            results: Extraction results
        """
        # Create backup
        backup_path = self.csv_path.parent / f"{self.csv_path.stem}_backup_evidence_{datetime.now():%Y%m%d_%H%M%S}.csv"
        shutil.copy(self.csv_path, backup_path)
        self.log(f"Created backup: {backup_path}")

        # Update DataFrame
        for result in results:
            ing_idx = result["ingredient_index"]
            for extraction in result["extractions"]:
                org_col = extraction["organism_column"]
                evidence_col = extraction["evidence_column"]

                # Update organism column
                if org_col in df.columns:
                    df.at[ing_idx, org_col] = extraction["organism"]

                # Update evidence column (if exists)
                if evidence_col in df.columns:
                    df.at[ing_idx, evidence_col] = extraction["evidence"]

        # Save updated CSV
        df.to_csv(self.csv_path, index=False)
        self.log(f"Updated CSV: {self.csv_path}")

    def _save_progress(self, df: pd.DataFrame, results: List[Dict[str, Any]]) -> None:
        """Save incremental progress."""
        self._update_csv(df, results)
        self.log("Progress saved")

    def _generate_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate validation report.

        Args:
            results: Extraction results

        Returns:
            Dictionary with statistics and validation info
        """
        total_extractions = sum(r["extractions_count"] for r in results)
        successful = sum(1 for r in results for e in r["extractions"] if e.get("organism"))
        failed = total_extractions - successful

        # Organism statistics
        all_organisms = set()
        organism_counts = {}
        for r in results:
            for e in r["extractions"]:
                org = e.get("organism", "")
                if org:
                    organisms = [o.strip() for o in org.split(",")]
                    for organism in organisms:
                        all_organisms.add(organism)
                        organism_counts[organism] = organism_counts.get(organism, 0) + 1

        # Most common organisms
        sorted_organisms = sorted(organism_counts.items(), key=lambda x: x[1], reverse=True)

        # Confidence distribution
        confidences = [e["organism_confidence"] for r in results for e in r["extractions"]]
        high_conf = sum(1 for c in confidences if c >= 0.9)
        med_conf = sum(1 for c in confidences if 0.7 <= c < 0.9)
        low_conf = sum(1 for c in confidences if c < 0.7)

        return {
            "summary": {
                "ingredients_processed": len(results),
                "total_properties_attempted": total_extractions,
                "successful_extractions": successful,
                "failed_extractions": failed,
                "coverage_percentage": (successful / total_extractions * 100) if total_extractions > 0 else 0
            },
            "organism_statistics": {
                "unique_organisms": len(all_organisms),
                "most_common_organisms": sorted_organisms[:10],
                "organism_list": list(all_organisms)
            },
            "confidence_distribution": {
                "high (≥0.9)": high_conf,
                "medium (0.7-0.9)": med_conf,
                "low (<0.7)": low_conf
            }
        }


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract evidence from markdown files")
    parser.add_argument("--csv", required=True, help="Path to CSV file")
    parser.add_argument("--dry-run", action="store_true", help="Don't modify CSV")
    parser.add_argument("--no-dry-run", action="store_true", help="Modify CSV (disables dry-run)")
    parser.add_argument("--sample", type=int, help="Process only N ingredients")
    parser.add_argument("--ingredient", help="Start from specific ingredient")

    args = parser.parse_args()

    orchestrator = EvidenceExtractionOrchestrator(csv_path=Path(args.csv))

    dry_run = not args.no_dry_run  # Default is dry-run unless --no-dry-run specified

    result = orchestrator.run(
        dry_run=dry_run,
        sample_size=args.sample,
        start_ingredient=args.ingredient
    )

    print("\n" + "="*70)
    print("EXTRACTION COMPLETE")
    print("="*70)
    print(json.dumps(result["report"], indent=2))

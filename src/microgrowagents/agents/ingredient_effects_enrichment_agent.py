"""
Ingredient Effects Enrichment Agent.

This agent enriches ingredient_effects table by:
1. Parsing effect_description to extract structured data
2. Downloading PDFs from DOIs
3. Extracting evidence snippets
4. Populating evidence_organism, evidence_snippet, cellular_role, toxicity fields
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import re
import duckdb

from microgrowagents.agents.base_agent import BaseAgent
from microgrowagents.agents.pdf_evidence_extractor import PDFEvidenceExtractor


class IngredientEffectsEnrichmentAgent(BaseAgent):
    """
    Agent to enrich ingredient_effects table with parsed and literature-derived data.

    Workflow:
    1. Parse effect_description to extract role, pH, toxicity
    2. Download PDF from DOI
    3. Search PDF for relevant snippets supporting concentration/toxicity values
    4. Update database with enriched fields
    """

    def __init__(self, db_path: Optional[Path] = None, email: str = "your@email.com"):
        """
        Initialize enrichment agent.

        Args:
            db_path: Path to DuckDB database
            email: Email for Unpaywall API access
        """
        super().__init__(db_path)
        self.conn = duckdb.connect(str(self.db_path))
        self.pdf_extractor = PDFEvidenceExtractor(email=email)

    def run(
        self,
        ingredient_id: Optional[str] = None,
        limit: Optional[int] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Run enrichment on ingredient_effects records.

        Args:
            ingredient_id: Process specific ingredient (None for all)
            limit: Maximum records to process
            dry_run: If True, don't update database

        Returns:
            Result dictionary with enrichment statistics

        Examples:
            >>> agent = IngredientEffectsEnrichmentAgent()
            >>> result = agent.run(limit=5, dry_run=True)
            >>> result["success"]
            True
        """
        self.log("Starting ingredient effects enrichment...")

        # Fetch records to process
        query = """
            SELECT id, ingredient_id, effect_description, evidence, source,
                   concentration_low, concentration_high, unit
            FROM ingredient_effects
            WHERE effect_description IS NOT NULL
        """
        if ingredient_id:
            query += f" AND ingredient_id = '{ingredient_id}'"
        if limit:
            query += f" LIMIT {limit}"

        records = self.conn.execute(query).fetchdf()

        if records.empty:
            return {
                "success": False,
                "error": "No records found to process",
            }

        self.log(f"Processing {len(records)} records...")

        enriched_records = []
        stats = {
            "total": len(records),
            "parsed": 0,
            "pdfs_downloaded": 0,
            "snippets_extracted": 0,
            "updated": 0,
            "errors": 0,
        }

        for idx, row in records.iterrows():
            try:
                self.log(f"Processing {row['ingredient_id']} (ID: {row['id']})...")

                # Step 1: Parse effect_description
                parsed = self._parse_effect_description(row["effect_description"])
                stats["parsed"] += 1

                # Step 2: Download PDF and extract snippets
                doi = self._extract_doi(row["evidence"])
                snippets = {}

                if doi:
                    pdf_result = self._download_and_extract_snippets(
                        doi=doi,
                        ingredient_id=row["ingredient_id"],
                        concentration_low=row["concentration_low"],
                        concentration_high=row["concentration_high"],
                        toxicity_value=parsed.get("toxicity_value"),
                    )

                    if pdf_result["success"]:
                        snippets = pdf_result["snippets"]
                        stats["pdfs_downloaded"] += 1
                        if snippets:
                            stats["snippets_extracted"] += 1

                # Step 3: Combine parsed + extracted data
                enriched = {
                    "id": row["id"],
                    "cellular_role": parsed.get("role"),
                    "cellular_requirements": None,  # Could be extracted from role
                    "evidence_organism": snippets.get("organism"),
                    "evidence_snippet": snippets.get("concentration_snippet"),
                    "toxicity_value": parsed.get("toxicity_value"),
                    "toxicity_unit": parsed.get("toxicity_unit"),
                    "toxicity_species_specific": parsed.get("toxicity_species_specific"),
                    "toxicity_cellular_effects": parsed.get("toxicity_effects"),
                    "toxicity_evidence": row["evidence"],
                    "toxicity_evidence_snippet": snippets.get("toxicity_snippet"),
                }

                enriched_records.append(enriched)

                # Step 4: Update database (if not dry run)
                if not dry_run:
                    self._update_record(enriched)
                    stats["updated"] += 1

            except Exception as e:
                self.log(f"Error processing {row['ingredient_id']}: {e}")
                stats["errors"] += 1

        return {
            "success": True,
            "stats": stats,
            "enriched_records": enriched_records,
            "dry_run": dry_run,
        }

    def _parse_effect_description(self, description: str) -> Dict[str, Any]:
        """
        Parse effect_description to extract structured data.

        Format: "Role: ...; pH: ...; Toxicity: ..."

        Args:
            description: Effect description text

        Returns:
            Dictionary with parsed fields

        Examples:
            >>> agent = IngredientEffectsEnrichmentAgent()
            >>> result = agent._parse_effect_description(
            ...     "Role: Primary N source; pH: Acidic; Toxicity: >500 mM (osmotic effects)"
            ... )
            >>> result["role"]
            'Primary N source'
        """
        parsed = {}

        # Extract Role
        role_match = re.search(r"Role:\s*([^;]+)", description)
        if role_match:
            parsed["role"] = role_match.group(1).strip()

        # Extract Toxicity
        tox_match = re.search(
            r"Toxicity:\s*([<>≤≥]?\s*\d+\.?\d*)\s*(mM|µM|mg/L|g/L)?\s*(\([^)]+\))?",
            description,
        )

        if tox_match:
            tox_str = tox_match.group(1).strip()
            # Remove inequality symbols to get minimal value
            tox_value_str = re.sub(r"[<>≤≥]", "", tox_str).strip()

            try:
                parsed["toxicity_value"] = float(tox_value_str)
            except ValueError:
                parsed["toxicity_value"] = None

            parsed["toxicity_unit"] = tox_match.group(2) if tox_match.group(2) else None

            # Extract effects from parentheses
            if tox_match.group(3):
                effects = tox_match.group(3).strip("()")
                parsed["toxicity_effects"] = effects

                # Check if species-specific
                species_keywords = [
                    "species-dependent",
                    "species-specific",
                    "E. coli",
                    "species",
                ]
                parsed["toxicity_species_specific"] = any(
                    kw in effects for kw in species_keywords
                )
            else:
                parsed["toxicity_effects"] = None
                parsed["toxicity_species_specific"] = False

        return parsed

    def _extract_doi(self, evidence: str) -> Optional[str]:
        """
        Extract DOI from evidence field.

        Args:
            evidence: Evidence string (URL or DOI)

        Returns:
            DOI string or None

        Examples:
            >>> agent = IngredientEffectsEnrichmentAgent()
            >>> agent._extract_doi("https://doi.org/10.1128/AEM.02738-08")
            '10.1128/AEM.02738-08'
        """
        if not evidence:
            return None

        # Match DOI pattern
        doi_match = re.search(r"10\.\d{4,}/[^\s]+", evidence)
        if doi_match:
            return doi_match.group(0)

        return None

    def _download_and_extract_snippets(
        self,
        doi: str,
        ingredient_id: str,
        concentration_low: Optional[float],
        concentration_high: Optional[float],
        toxicity_value: Optional[float],
    ) -> Dict[str, Any]:
        """
        Download PDF and extract relevant snippets.

        Args:
            doi: DOI of paper
            ingredient_id: ChEBI ID
            concentration_low: Lower concentration bound
            concentration_high: Upper concentration bound
            toxicity_value: Toxicity threshold

        Returns:
            Dictionary with success flag and snippets

        Examples:
            >>> agent = IngredientEffectsEnrichmentAgent()
            >>> result = agent._download_and_extract_snippets(
            ...     "10.1128/AEM.02738-08", "CHEBI:17790", 1.0, 500.0, 2000.0
            ... )
            >>> "success" in result
            True
        """
        return self.pdf_extractor.extract_from_doi(
            doi=doi,
            ingredient_id=ingredient_id,
            concentration_low=concentration_low,
            concentration_high=concentration_high,
            toxicity_value=toxicity_value,
        )

    def _update_record(self, enriched: Dict[str, Any]) -> None:
        """
        Update database record with enriched data.

        Args:
            enriched: Dictionary with enriched fields
        """
        update_query = """
            UPDATE ingredient_effects
            SET
                cellular_role = ?,
                cellular_requirements = ?,
                evidence_organism = ?,
                evidence_snippet = ?,
                toxicity_value = ?,
                toxicity_unit = ?,
                toxicity_species_specific = ?,
                toxicity_cellular_effects = ?,
                toxicity_evidence = ?,
                toxicity_evidence_snippet = ?
            WHERE id = ?
        """

        self.conn.execute(
            update_query,
            [
                enriched["cellular_role"],
                enriched["cellular_requirements"],
                enriched["evidence_organism"],
                enriched["evidence_snippet"],
                enriched["toxicity_value"],
                enriched["toxicity_unit"],
                enriched["toxicity_species_specific"],
                enriched["toxicity_cellular_effects"],
                enriched["toxicity_evidence"],
                enriched["toxicity_evidence_snippet"],
                enriched["id"],
            ],
        )

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()

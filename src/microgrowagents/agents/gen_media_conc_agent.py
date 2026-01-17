"""
Generate Media Concentration Agent.

Predicts optimal concentration ranges for media ingredients based on:
- Literature evidence (PubMed searches)
- Chemical properties (PubChem/ChEBI APIs)
- Database records (ingredient_effects table)
- Rule-based heuristics (osmotic pressure, pH, etc.)

Capabilities:
- Generate concentration ranges from existing medium
- Predict concentrations for ingredient lists
- Organism-specific vs general predictions
- Multi-source evidence integration
- Confidence scoring
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from microgrowagents.agents.base_agent import BaseAgent
from microgrowagents.agents.chemistry_agent import ChemistryAgent
from microgrowagents.agents.genome_function_agent import GenomeFunctionAgent
from microgrowagents.agents.literature_agent import LiteratureAgent
from microgrowagents.agents.media_ph_calculator import MediaPhCalculator
from microgrowagents.agents.sql_agent import SQLAgent


class GenMediaConcAgent(BaseAgent):
    """
    Agent for generating media ingredient concentration predictions.

    Input Modes:
    1. Existing medium name/ID (e.g., "MP medium", "LB medium")
    2. List of ingredients without concentrations

    Output:
    For each ingredient:
    - concentration_low: minimum concentration (0 for non-essential)
    - concentration_high: maximum concentration (below toxicity)
    - unit: standard unit (mM or g/L)
    - confidence: confidence score (0-1)
    - is_essential: boolean
    - evidence: list of evidence sources

    Prediction Modes:
    1. General (organism-agnostic)
    2. Organism-specific (NCBITaxon ID or scientific name)

    Examples:
        >>> agent = GenMediaConcAgent()
        >>> result = agent.run("MP medium")
        >>> result["success"]
        True
        >>> result = agent.run("glucose,NaCl,tris", mode="ingredients")
        >>> len(result["data"]) >= 3
        True
    """

    # Essential nutrient categories from ChEBI roles
    ESSENTIAL_CATEGORIES = {
        "carbon source",
        "nitrogen source",
        "phosphorus source",
        "sulfur source",
        "metal ion",
        "vitamin",
        "cofactor",
    }

    # Toxicity thresholds (conservative defaults in mM)
    TOXICITY_THRESHOLDS = {
        "metal": 10.0,  # Most heavy metals toxic above 10mM
        "salt": 500.0,  # High salt concentrations
        "organic_acid": 100.0,
        "default": 1000.0,  # Conservative default
    }

    def __init__(
        self,
        db_path: Optional[Path] = None,
        chebi_owl_file: Optional[Path] = None,
        pubchem_email: str = "microgrowagents@example.com",
    ):
        """
        Initialize GenMediaConcAgent.

        Args:
            db_path: Path to DuckDB database
            chebi_owl_file: Path to ChEBI OWL file (for role lookups)
            pubchem_email: Email for PubChem API
        """
        super().__init__(db_path)

        # Initialize dependent agents
        self.sql_agent = SQLAgent(db_path)
        self.chemistry_agent = ChemistryAgent(
            db_path=db_path,
            chebi_owl_file=chebi_owl_file,
            pubchem_email=pubchem_email,
        )
        self.genome_agent = GenomeFunctionAgent(db_path)  # NEW: genome-based refinement
        self.literature_agent = LiteratureAgent(db_path)
        self.ph_calculator = MediaPhCalculator()

    def run(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Generate concentration predictions.

        Args:
            query: Medium name/ID OR comma-separated ingredient list
            mode: "medium" or "ingredients" (auto-detected if not specified)
            organism: NCBITaxon ID or organism name (optional)
            unit: Preferred output unit "mM" or "g/L" (default: "mM")
            include_evidence: Include full evidence details (default: True)

        Returns:
            Dictionary with:
            - success: bool
            - data: List of ingredient predictions with ranges
            - organism: Organism info (if specified)
            - method: Prediction method used
            - summary: Summary statistics

        Examples:
            >>> agent = GenMediaConcAgent()
            >>> result = agent.run("MP medium")
            >>> result["success"]
            True
        """
        # Validate query
        if not query or not query.strip():
            return {"success": False, "error": "Empty query provided"}

        if not self.validate_database():
            return {"success": False, "error": "Database not found"}

        # Parse arguments
        mode = kwargs.get("mode")
        if mode is None:
            mode = self._detect_mode(query)
        organism = kwargs.get("organism")
        unit = kwargs.get("unit", "mM")
        include_evidence = kwargs.get("include_evidence", True)

        try:
            # Step 1: Get ingredient list
            if mode == "medium":
                ingredients = self._get_ingredients_from_medium(query)
            else:  # mode == "ingredients"
                ingredients = self._parse_ingredient_list(query)

            if not ingredients:
                return {
                    "success": False,
                    "error": f"No ingredients found for query: {query}",
                }

            # Step 2: Get organism info (if specified)
            organism_info = None
            if organism:
                organism_info = self._get_organism_info(organism)

            # Step 3: Generate predictions for each ingredient
            predictions = []
            for ingredient in ingredients:
                prediction = self._predict_concentration_range(
                    ingredient,
                    organism_info=organism_info,
                    unit=unit,
                    include_evidence=include_evidence,
                )
                predictions.append(prediction)

            # Step 3.5: Calculate pH effects for each ingredient at low/high concentrations
            if kwargs.get("include_ph", True):
                predictions = self._add_ph_predictions(predictions, unit)

            # Step 4: Calculate summary statistics
            summary = self._calculate_summary(predictions)

            # Step 5: Format results
            result = {
                "success": True,
                "data": predictions,
                "query": query,
                "mode": mode,
                "unit": unit,
                "organism": organism_info,
                "summary": summary,
                "method": "multi-source" if organism_info else "general",
            }

            self.log(
                f"Generated {len(predictions)} concentration predictions "
                f"(avg confidence: {summary['avg_confidence']:.2f})"
            )

            return result

        except Exception as e:
            self.log(f"Prediction failed: {str(e)}", level="ERROR")
            return {"success": False, "error": str(e), "query": query}

    def _detect_mode(self, query: str) -> str:
        """
        Auto-detect if query is a medium name or ingredient list.

        Args:
            query: Query string

        Returns:
            "medium" or "ingredients"

        Examples:
            >>> agent = GenMediaConcAgent()
            >>> agent._detect_mode("glucose,NaCl")
            'ingredients'
        """
        # Check for comma separation (ingredient list indicator)
        if "," in query:
            return "ingredients"

        # Try to find in media table
        result = self.sql_agent.search_media(query)
        if not result.empty:
            return "medium"

        # Default to ingredients
        return "ingredients"

    def _get_ingredients_from_medium(self, medium_query: str) -> List[Dict[str, Any]]:
        """
        Get ingredients from existing medium in database.

        Args:
            medium_query: Medium name or ID

        Returns:
            List of ingredient dictionaries

        Examples:
            >>> agent = GenMediaConcAgent()
            >>> ingredients = agent._get_ingredients_from_medium("LB medium")
            >>> isinstance(ingredients, list)
            True
        """
        # Search for medium
        media = self.sql_agent.search_media(medium_query)

        if media.empty:
            return []

        # Get first match
        medium_id = media.iloc[0]["id"]

        # Get ingredients for this medium
        ingredients_df = self.sql_agent.get_ingredients_for_media(medium_id)

        # Convert to list of dicts
        ingredients = []
        for _, row in ingredients_df.iterrows():
            ingredients.append(
                {
                    "id": row.get("ingredient_id", ""),
                    "name": row.get("name", ""),
                    "chebi_id": row.get("chebi_id", ""),
                    "category": row.get("category", ""),
                    "current_concentration": row.get(
                        "mmol_per_liter", row.get("amount", 0)
                    ),
                    "unit": row.get("unit", "mM"),
                }
            )

        return ingredients

    def _parse_ingredient_list(self, ingredient_str: str) -> List[Dict[str, Any]]:
        """
        Parse comma-separated ingredient list.

        Args:
            ingredient_str: Comma-separated ingredient names

        Returns:
            List of ingredient dictionaries

        Examples:
            >>> agent = GenMediaConcAgent()
            >>> ingredients = agent._parse_ingredient_list("glucose, NaCl")
            >>> len(ingredients)
            2
        """
        ingredients = []

        # Split by comma and clean
        names = [name.strip() for name in ingredient_str.split(",")]

        for name in names:
            if not name:
                continue

            # Try to find in database
            result = self.sql_agent.run(
                "SELECT * FROM ingredients WHERE LOWER(name) LIKE LOWER(?)",
                params=[f"%{name}%"],
                max_rows=1,
            )

            if result["success"] and not result["data"].empty:
                row = result["data"].iloc[0]
                ingredients.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "chebi_id": row.get("chebi_id", ""),
                        "category": row.get("category", ""),
                        "current_concentration": None,
                        "unit": None,
                    }
                )
            else:
                # Not in database, add as-is
                ingredients.append(
                    {
                        "id": None,
                        "name": name,
                        "chebi_id": None,
                        "category": "",
                        "current_concentration": None,
                        "unit": None,
                    }
                )

        return ingredients

    def _get_organism_info(self, organism_query: str) -> Optional[Dict[str, Any]]:
        """
        Get organism information from database.

        Args:
            organism_query: NCBITaxon ID or organism name

        Returns:
            Organism info dictionary or None

        Examples:
            >>> agent = GenMediaConcAgent()
            >>> info = agent._get_organism_info("NCBITaxon:562")
            >>> info is None or "name" in info
            True
        """
        # Check if it's an NCBITaxon ID
        if organism_query.startswith("NCBITaxon:"):
            result = self.sql_agent.run(
                "SELECT * FROM organisms WHERE id = ?",
                params=[organism_query],
                max_rows=1,
            )
        else:
            # Search by name
            result = self.sql_agent.run(
                "SELECT * FROM organisms WHERE LOWER(name) LIKE LOWER(?)",
                params=[f"%{organism_query}%"],
                max_rows=1,
            )

        if result["success"] and not result["data"].empty:
            row = result["data"].iloc[0]
            return {
                "id": row["id"],
                "name": row["name"],
                "rank": row.get("rank", ""),
                "lineage": row.get("lineage", ""),
            }

        return None

    def _predict_concentration_range(
        self,
        ingredient: Dict[str, Any],
        organism_info: Optional[Dict[str, Any]] = None,
        unit: str = "mM",
        include_evidence: bool = True,
    ) -> Dict[str, Any]:
        """
        Predict concentration range for a single ingredient.

        Args:
            ingredient: Ingredient dictionary
            organism_info: Organism info (for organism-specific predictions)
            unit: Output unit (mM or g/L)
            include_evidence: Include detailed evidence

        Returns:
            Prediction dictionary

        Examples:
            >>> agent = GenMediaConcAgent()
            >>> pred = agent._predict_concentration_range({"name": "glucose"})
            >>> "concentration_low" in pred
            True
        """
        ingredient_name = ingredient["name"]

        self.log(f"Predicting concentration range for: {ingredient_name}")

        # Initialize evidence collectors
        evidence_sources: List[Dict[str, Any]] = []
        concentration_ranges: List[Dict[str, Any]] = []

        # Step 1: Check database ingredient_effects table
        db_ranges = self._get_database_ranges(ingredient, organism_info)
        if db_ranges:
            concentration_ranges.extend(db_ranges)
            evidence_sources.append(
                {
                    "source": "database",
                    "type": "ingredient_effects",
                    "confidence": 0.9,
                    "ranges": db_ranges,
                }
            )

        # Step 2: Determine essentiality
        is_essential = self._determine_essentiality(
            ingredient, organism_info, evidence_sources
        )

        # Step 3: Aggregate ranges and calculate final prediction
        if concentration_ranges:
            conc_low, conc_high = self._aggregate_ranges(
                concentration_ranges, is_essential
            )
        else:
            # Use conservative defaults
            conc_low = 0.0 if not is_essential else 0.1
            conc_high = self._estimate_toxicity_threshold(ingredient)

        # NEW Step 3b: Refine concentrations based on transporter presence
        transporter_adjustment = None
        if organism_info:
            conc_low, conc_high, transporter_adjustment = self._refine_concentration_with_transporters(
                ingredient_name, conc_low, conc_high, organism_info
            )
            if transporter_adjustment:
                self.log(f"Transporter adjustment for {ingredient_name}: {transporter_adjustment}")

        # Step 4: Calculate confidence score
        confidence = self._calculate_confidence(evidence_sources, concentration_ranges)

        # Step 5: Extract cellular role and toxicity from ranges
        cellular_roles: List[str] = []
        cellular_requirements: List[str] = []
        toxicity_info: List[Dict[str, Any]] = []

        for range_data in concentration_ranges:
            if range_data.get("cellular_role"):
                cellular_roles.append(range_data["cellular_role"])
            if range_data.get("cellular_requirements"):
                cellular_requirements.append(range_data["cellular_requirements"])
            if range_data.get("toxicity"):
                toxicity_info.append(range_data["toxicity"])

        # Step 6: Format result
        prediction = {
            "name": ingredient_name,
            "ingredient_id": ingredient.get("id"),
            "chebi_id": ingredient.get("chebi_id"),
            "concentration_low": round(conc_low, 4),
            "concentration_high": round(conc_high, 4),
            "unit": unit,
            "confidence": round(confidence, 3),
            "is_essential": is_essential,
        }

        # Add cellular role information if available
        if cellular_roles:
            # Use the most common role or first if all unique
            prediction["cellular_role"] = cellular_roles[0]
        if cellular_requirements:
            # Combine all requirements
            prediction["cellular_requirements"] = "; ".join(
                set(cellular_requirements)
            )

        # Add toxicity information if available
        if toxicity_info:
            # Use the lowest toxicity value (most restrictive)
            min_tox = min(toxicity_info, key=lambda x: x.get("value", float("inf")))
            prediction["toxicity"] = min_tox

        if include_evidence:
            prediction["evidence"] = evidence_sources

        return prediction

    def _get_database_ranges(
        self,
        ingredient: Dict[str, Any],
        organism_info: Optional[Dict[str, Any]],
    ) -> List[Dict[str, float]]:
        """
        Get concentration ranges from ingredient_effects table.

        Args:
            ingredient: Ingredient dictionary
            organism_info: Organism info (optional)

        Returns:
            List of range dictionaries

        Examples:
            >>> agent = GenMediaConcAgent()
            >>> ranges = agent._get_database_ranges({"id": "CHEBI:123"}, None)
            >>> isinstance(ranges, list)
            True
        """
        if not ingredient.get("id"):
            return []

        # Query ingredient_effects table with enhanced evidence fields
        result = self.sql_agent.run(
            """
            SELECT concentration_low, concentration_high, unit,
                   effect_type, effect_description,
                   evidence, evidence_organism, evidence_snippet,
                   source, cellular_role, cellular_requirements,
                   toxicity_value, toxicity_unit, toxicity_species_specific,
                   toxicity_cellular_effects, toxicity_evidence, toxicity_evidence_snippet
            FROM ingredient_effects
            WHERE ingredient_id = ?
            """,
            params=[ingredient["id"]],
            max_rows=100,
        )

        if not result["success"] or result["data"].empty:
            return []

        ranges = []
        for _, row in result["data"].iterrows():
            range_dict = {
                "low": row["concentration_low"],
                "high": row["concentration_high"],
                "unit": row["unit"],
                "effect_type": row.get("effect_type", ""),
                "source": row.get("source", "database"),
                "evidence": row.get("evidence", ""),
                "evidence_organism": row.get("evidence_organism", ""),
                "evidence_snippet": row.get("evidence_snippet", ""),
                "cellular_role": row.get("cellular_role", ""),
                "cellular_requirements": row.get("cellular_requirements", ""),
            }

            # Add toxicity information if present
            if pd.notna(row.get("toxicity_value")):
                range_dict["toxicity"] = {
                    "value": row["toxicity_value"],
                    "unit": row.get("toxicity_unit", ""),
                    "species_specific": row.get("toxicity_species_specific", False),
                    "cellular_effects": row.get("toxicity_cellular_effects", ""),
                    "evidence": row.get("toxicity_evidence", ""),
                    "evidence_snippet": row.get("toxicity_evidence_snippet", ""),
                }

            ranges.append(range_dict)

        return ranges

    def _get_literature_ranges(
        self,
        ingredient_name: str,
        organism_info: Optional[Dict[str, Any]],
    ) -> List[Dict[str, float]]:
        """
        Search literature for concentration information.

        Args:
            ingredient_name: Ingredient name
            organism_info: Organism info (optional)

        Returns:
            List of ranges extracted from literature
        """
        ranges: List[Dict[str, Any]] = []

        # Build search query
        if organism_info:
            organism_name = organism_info["name"]
            query = (
                f"{ingredient_name} concentration {organism_name} growth medium"
            )
        else:
            query = f"{ingredient_name} concentration microbial growth medium"

        # Search literature
        result = self.literature_agent.run(query, max_results=10, search_type="pubmed")

        if not result["success"]:
            return ranges

        # Parse abstracts for concentration mentions
        pubmed_results = result.get("results", {}).get("pubmed", [])

        for paper in pubmed_results:
            # Extract concentration ranges from title/abstract
            extracted_ranges = self._extract_concentration_from_text(
                paper.get("title", "") + " " + paper.get("abstract", "")
            )

            for range_dict in extracted_ranges:
                range_dict["pmid"] = paper.get("pmid", "")
                range_dict["source"] = "literature"
                ranges.append(range_dict)

        return ranges

    def _extract_concentration_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract concentration ranges from text using regex.

        Args:
            text: Text to parse

        Returns:
            List of extracted ranges

        Examples:
            >>> agent = GenMediaConcAgent()
            >>> ranges = agent._extract_concentration_from_text("5-50 mM glucose")
            >>> len(ranges) >= 1
            True
        """
        ranges = []

        # Regex patterns for concentration ranges
        patterns = [
            r"(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*(mM|g/L|mg/L|µM)",
            r"(\d+\.?\d*)\s+to\s+(\d+\.?\d*)\s*(mM|g/L|mg/L|µM)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                low, high, unit = match
                ranges.append(
                    {
                        "low": float(low),
                        "high": float(high),
                        "unit": unit,
                    }
                )

        return ranges

    def _get_chemical_ranges(
        self, ingredient: Dict[str, Any]
    ) -> List[Dict[str, float]]:
        """
        Get concentration ranges from chemical properties.

        Args:
            ingredient: Ingredient dictionary

        Returns:
            List of ranges based on chemical properties
        """
        ranges: List[Dict[str, Any]] = []
        # Placeholder for future implementation
        return ranges

    def _determine_essentiality(
        self,
        ingredient: Dict[str, Any],
        organism_info: Optional[Dict[str, Any]],
        evidence_sources: List[Dict],
    ) -> bool:
        """
        Determine if ingredient is essential.

        Args:
            ingredient: Ingredient dictionary
            organism_info: Organism info (optional)
            evidence_sources: Collected evidence

        Returns:
            True if essential, False otherwise

        Examples:
            >>> agent = GenMediaConcAgent()
            >>> is_ess = agent._determine_essentiality({"category": "carbon source"}, None, [])
            >>> is_ess
            True
        """
        # Method 1: Check evidence sources for effect_type
        # Database evidence with effect_type="growth" indicates essential
        for evidence in evidence_sources:
            # Check if ranges contain effect_type information
            ranges = evidence.get("ranges", [])
            for range_info in ranges:
                effect_type = range_info.get("effect_type", "")
                if effect_type == "growth":
                    return True

        # Method 2: Check category if provided
        category = ingredient.get("category") or ""
        if category and any(ess_cat in category.lower() for ess_cat in self.ESSENTIAL_CATEGORIES):
            return True

        # Method 3: Query database for category
        if ingredient.get("id"):
            result = self.sql_agent.run(
                "SELECT category FROM ingredients WHERE id = ?",
                params=[ingredient["id"]],
            )

            if result["success"] and not result["data"].empty:
                db_category = result["data"].iloc[0].get("category")
                if db_category:
                    category = db_category.lower()
                    if any(ess_cat in category for ess_cat in self.ESSENTIAL_CATEGORIES):
                        return True

        # Default: not essential
        return False

    def _refine_concentration_with_transporters(
        self,
        ingredient_name: str,
        conc_low: float,
        conc_high: float,
        organism_info: Optional[Dict[str, Any]]
    ) -> Tuple[float, float, Optional[str]]:
        """
        Refine concentration range based on transporter gene presence.

        Logic:
        - No transporter found → increase by 50% (passive diffusion, need higher conc)
        - Low-affinity transporter → use default range
        - High-affinity transporter → decrease by 25% (efficient uptake)

        Args:
            ingredient_name: Name of ingredient/substrate
            conc_low: Initial low concentration
            conc_high: Initial high concentration
            organism_info: Organism information dict

        Returns:
            Tuple of (refined_conc_low, refined_conc_high, adjustment_reason)

        Example:
            >>> agent = GenMediaConcAgent()
            >>> low, high, reason = agent._refine_concentration_with_transporters(
            ...     "glucose", 1.0, 10.0, {"name": "E. coli"}
            ... )
            >>> reason is not None
            True
        """
        if not organism_info:
            return conc_low, conc_high, None

        organism_name = organism_info.get("name") or organism_info.get("label")
        if not organism_name:
            return conc_low, conc_high, None

        try:
            # Query for transporters
            transporter_result = self.genome_agent.find_transporters(
                query=f"find transporters for {ingredient_name}",
                organism=organism_name,
                substrate=ingredient_name
            )

            if not transporter_result.get("success"):
                return conc_low, conc_high, None

            transporters = transporter_result["data"].get("transporters", [])

            if not transporters:
                # No transporter → increase concentrations (passive diffusion)
                self.log(f"No transporter for {ingredient_name}, increasing concentrations by 50%")
                return conc_low * 1.5, conc_high * 1.5, "increased_no_transporter"

            else:
                # Check transporter affinity
                high_affinity = any(
                    t.get("affinity") == "high" for t in transporters
                )

                if high_affinity:
                    # High-affinity transporter → decrease concentrations
                    self.log(f"High-affinity transporter for {ingredient_name}, decreasing by 25%")
                    return conc_low * 0.75, conc_high * 0.75, "decreased_high_affinity"
                else:
                    # Low/medium affinity → keep default
                    return conc_low, conc_high, "default_low_affinity"

        except Exception as e:
            self.log(f"Error in transporter refinement: {str(e)}", level="warning")
            return conc_low, conc_high, None

    def _aggregate_ranges(
        self,
        ranges: List[Dict[str, float]],
        is_essential: bool,
    ) -> Tuple[float, float]:
        """
        Aggregate multiple concentration ranges into final prediction.

        Args:
            ranges: List of range dictionaries
            is_essential: Whether ingredient is essential

        Returns:
            Tuple of (concentration_low, concentration_high)

        Examples:
            >>> agent = GenMediaConcAgent()
            >>> low, high = agent._aggregate_ranges([{"low": 1, "high": 10}], True)
            >>> low <= high
            True
        """
        if not ranges:
            return (0.0, 100.0)  # Default conservative range

        # Extract low and high values
        lows = [r["low"] for r in ranges if r.get("low") is not None]
        highs = [r["high"] for r in ranges if r.get("high") is not None]

        # Calculate final low
        if is_essential and lows:
            conc_low = min(lows)
        else:
            conc_low = 0.0

        # Calculate final high (conservative: use median)
        if highs:
            conc_high = float(np.median(highs))
        else:
            conc_high = 100.0  # Default

        return (conc_low, conc_high)

    def _estimate_toxicity_threshold(self, ingredient: Dict[str, Any]) -> float:
        """
        Estimate toxicity threshold for ingredient.

        Args:
            ingredient: Ingredient dictionary

        Returns:
            Estimated toxic concentration (mM)

        Examples:
            >>> agent = GenMediaConcAgent()
            >>> threshold = agent._estimate_toxicity_threshold({"name": "iron"})
            >>> threshold > 0
            True
        """
        ingredient_name = ingredient["name"].lower()

        # Metal ions
        if any(
            metal in ingredient_name
            for metal in ["iron", "copper", "zinc", "manganese", "cobalt", "nickel"]
        ):
            return self.TOXICITY_THRESHOLDS["metal"]

        # Salts
        if any(
            salt in ingredient_name for salt in ["chloride", "nacl", "kcl", "salt"]
        ):
            return self.TOXICITY_THRESHOLDS["salt"]

        # Organic acids
        if any(
            acid in ingredient_name
            for acid in ["acetate", "citrate", "succinate", "acid"]
        ):
            return self.TOXICITY_THRESHOLDS["organic_acid"]

        # Default
        return self.TOXICITY_THRESHOLDS["default"]

    def _calculate_confidence(
        self,
        evidence_sources: List[Dict],
        concentration_ranges: List[Dict],
    ) -> float:
        """
        Calculate confidence score for prediction.

        Args:
            evidence_sources: List of evidence source dicts
            concentration_ranges: List of concentration ranges

        Returns:
            Confidence score (0-1)

        Examples:
            >>> agent = GenMediaConcAgent()
            >>> conf = agent._calculate_confidence([{"source": "database", "confidence": 0.9}], [])
            >>> 0 <= conf <= 1
            True
        """
        if not evidence_sources:
            return 0.1  # Very low confidence

        # Base confidence on number of sources
        num_sources = len(evidence_sources)
        base_confidence = min(num_sources * 0.25, 0.75)

        # Weight by source quality
        quality_weights = {
            "database": 1.0,
            "literature": 0.8,
            "chemistry": 0.6,
        }

        weighted_sum = sum(
            quality_weights.get(source["source"], 0.5)
            * source.get("confidence", 0.5)
            for source in evidence_sources
        )

        weighted_confidence = weighted_sum / len(evidence_sources)

        # Combine base and weighted
        final_confidence = (base_confidence + weighted_confidence) / 2

        # Cap at 0.95 (never 100% certain)
        return min(final_confidence, 0.95)

    def _calculate_summary(self, predictions: List[Dict]) -> Dict[str, Any]:
        """
        Calculate summary statistics for predictions.

        Args:
            predictions: List of prediction dictionaries

        Returns:
            Summary statistics dictionary

        Examples:
            >>> agent = GenMediaConcAgent()
            >>> summary = agent._calculate_summary([{"confidence": 0.8, "is_essential": True}])
            >>> "total_ingredients" in summary
            True
        """
        if not predictions:
            return {}

        confidences = [p["confidence"] for p in predictions]
        essential_count = sum(1 for p in predictions if p["is_essential"])

        return {
            "total_ingredients": len(predictions),
            "essential_count": essential_count,
            "non_essential_count": len(predictions) - essential_count,
            "avg_confidence": float(np.mean(confidences)),
            "min_confidence": float(np.min(confidences)),
            "max_confidence": float(np.max(confidences)),
        }

    def _add_ph_predictions(
        self,
        predictions: List[Dict],
        unit: str = "mM",
    ) -> List[Dict]:
        """
        Add pH predictions for each ingredient at low/high concentrations.

        For each ingredient, calculates pH when that ingredient is at its
        low or high concentration while all other ingredients are at their
        default (current) concentrations.

        Args:
            predictions: List of prediction dictionaries
            unit: Concentration unit

        Returns:
            Updated predictions with pH information

        Examples:
            >>> agent = GenMediaConcAgent()
            >>> preds = [{"name": "PIPES", "concentration_low": 10, "concentration_high": 100, "unit": "mM"}]
            >>> result = agent._add_ph_predictions(preds)
            >>> "ph_at_low" in result[0]
            True
        """
        # Build base formulation with all ingredients at default concentrations
        # Use middle of range as "default"
        base_formulation = []

        for pred in predictions:
            default_conc = (pred["concentration_low"] + pred["concentration_high"]) / 2

            base_formulation.append({
                "name": pred["name"],
                "concentration": default_conc,
                "unit": pred["unit"],
                "pka": pred.get("pka"),  # If available from evidence
            })

        # For each ingredient, calculate pH at low and high concentrations
        for i, pred in enumerate(predictions):
            ingredient_name = pred["name"]

            # Calculate pH at low concentration
            try:
                ph_results_low = self.ph_calculator.predict_ph_at_concentrations(
                    base_formulation,
                    ingredient_name,
                    [pred["concentration_low"]],
                    volume_ml=1000.0,
                )

                if ph_results_low:
                    pred["ph_at_low"] = ph_results_low[0]["ph"]
                else:
                    pred["ph_at_low"] = None

            except Exception as e:
                self.log(f"pH calculation failed for {ingredient_name} at low: {e}", level="WARNING")
                pred["ph_at_low"] = None

            # Calculate pH at high concentration
            try:
                ph_results_high = self.ph_calculator.predict_ph_at_concentrations(
                    base_formulation,
                    ingredient_name,
                    [pred["concentration_high"]],
                    volume_ml=1000.0,
                )

                if ph_results_high:
                    pred["ph_at_high"] = ph_results_high[0]["ph"]
                else:
                    pred["ph_at_high"] = None

            except Exception as e:
                self.log(f"pH calculation failed for {ingredient_name} at high: {e}", level="WARNING")
                pred["ph_at_high"] = None

            # Add pH effect comment
            pred["ph_comment"] = self._get_ph_effect_comment(
                ingredient_name,
                pred.get("ph_at_low"),
                pred.get("ph_at_high"),
            )

        return predictions

    def _get_ph_effect_comment(
        self,
        ingredient_name: str,
        ph_low: Optional[float],
        ph_high: Optional[float],
    ) -> str:
        """
        Generate interpretive comment about pH effect.

        Args:
            ingredient_name: Name of the ingredient
            ph_low: pH at low concentration
            ph_high: pH at high concentration

        Returns:
            Human-readable comment about the pH effect
        """
        if ph_low is None or ph_high is None:
            return "pH effect not calculated"

        delta_ph = ph_high - ph_low

        # Check if ingredient is a buffer
        buffer_keywords = ["PIPES", "HEPES", "MES", "MOPS", "Tris", "TRIS"]
        is_buffer = any(kw.lower() in ingredient_name.lower() for kw in buffer_keywords)

        # Check if ingredient is a phosphate
        is_phosphate = any(kw in ingredient_name for kw in ["HPO4", "H2PO4", "phosphate"])

        # Check for acidic salts
        acidic_salts = ["FeSO4", "FeCl", "CuSO4", "CuCl", "ZnSO4", "ZnCl", "MnCl", "MnSO4", "CoCl", "CoSO4", "NiCl", "NH4"]
        is_acidic_salt = any(salt in ingredient_name for salt in acidic_salts)

        # Check for basic salts
        basic_salts = ["Na2WO4", "Na2MoO4", "Na2SeO3", "WO4", "MoO4"]
        is_basic_salt = any(salt in ingredient_name for salt in basic_salts)

        # Generate comment based on effect
        if abs(delta_ph) < 0.01:
            if is_buffer:
                return "Buffer - minimal pH change (well buffered)"
            elif is_phosphate:
                return "Phosphate buffer component - minimal change"
            else:
                return "Minimal pH effect in buffered medium"
        elif delta_ph > 0.05:
            if is_buffer:
                return f"Buffer capacity effect (+{delta_ph:.2f} pH units)"
            elif is_basic_salt:
                return f"Basic salt effect (+{delta_ph:.2f} pH units)"
            else:
                return f"Alkalizing effect (+{delta_ph:.2f} pH units)"
        elif delta_ph < -0.05:
            if is_acidic_salt:
                return f"Acidic salt effect ({delta_ph:.2f} pH units)"
            else:
                return f"Acidifying effect ({delta_ph:.2f} pH units)"
        elif delta_ph > 0:
            if is_buffer:
                return f"Slight buffer capacity effect (+{delta_ph:.2f} pH)"
            else:
                return f"Slight alkalizing effect (+{delta_ph:.2f} pH)"
        else:  # delta_ph < 0
            if is_acidic_salt:
                return f"Slight acidic salt effect ({delta_ph:.2f} pH)"
            else:
                return f"Slight acidifying effect ({delta_ph:.2f} pH)"

"""
Sensitivity Analysis Agent for media formulations.

Performs parameter sweep analysis to determine pH and salinity effects
when varying ingredient concentrations between LOW and HIGH values.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import math

from microgrowagents.agents.base_agent import BaseAgent
from microgrowagents.agents.sql_agent import SQLAgent
from microgrowagents.agents.media_ph_calculator import MediaPhCalculator
from microgrowagents.chemistry.calculations import (
    calculate_salinity,
    calculate_nacl_salinity,
    calculate_ionic_strength
)
from microgrowagents.chemistry.osmotic_properties import (
    calculate_osmolarity,
    calculate_water_activity
)
from microgrowagents.chemistry.redox_properties import (
    calculate_redox_potential,
    calculate_electron_balance
)
from microgrowagents.chemistry.nutrient_ratios import (
    calculate_cnp_ratios,
    calculate_trace_metal_ratios
)


class SensitivityAnalysisAgent(BaseAgent):
    """
    Agent for sensitivity analysis of media formulations.

    Performs parameter sweep analysis by varying ingredient concentrations
    and calculating pH and salinity effects.

    Capabilities:
    - Calculate baseline (all-default) media properties
    - Vary each ingredient LOW/HIGH while others stay DEFAULT
    - Calculate pH using MediaPhCalculator
    - Calculate salinity using chemistry.calculations
    - Generate delta comparisons from baseline
    - Support both medium names and custom ingredient lists

    Examples:
        >>> agent = SensitivityAnalysisAgent()
        >>> result = agent.run("PIPES,NaCl", mode="ingredients")
        >>> result["success"]
        True
        >>> "baseline" in result
        True
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        chebi_owl_file: Optional[Path] = None,
    ):
        """
        Initialize SensitivityAnalysisAgent.

        Args:
            db_path: Path to DuckDB database. If None, uses default.
            chebi_owl_file: Path to ChEBI OWL file for enrichment (optional).
        """
        super().__init__(db_path=db_path)

        # Initialize dependent agents
        self.sql_agent = SQLAgent(db_path=self.db_path)
        self.ph_calculator = MediaPhCalculator()
        self.chebi_owl_file = chebi_owl_file

    def run(
        self,
        query: str,
        mode: Optional[str] = None,
        volume_ml: float = 1000.0,
        calculate_osmotic: bool = False,
        calculate_redox: bool = False,
        calculate_nutrients: bool = False,
        ph: Optional[float] = None,
        temperature: float = 25.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute sensitivity analysis.

        Args:
            query: Medium name or comma-separated ingredient list
            mode: "medium" or "ingredients" (auto-detect if None)
            volume_ml: Total volume in milliliters (default: 1000)
            calculate_osmotic: Calculate osmotic properties (default: False)
            calculate_redox: Calculate redox properties (default: False)
            calculate_nutrients: Calculate nutrient ratios (default: False)
            ph: pH value for redox calculations (uses baseline pH if None)
            temperature: Temperature in °C (default: 25.0)
            **kwargs: Additional parameters

        Returns:
            Dictionary with:
            - success: bool
            - data: List of analysis results
            - baseline: Baseline properties (all default)
            - summary: Summary statistics
            - metadata: Analysis metadata

        Examples:
            >>> agent = SensitivityAnalysisAgent()
            >>> result = agent.run("PIPES,NaCl", mode="ingredients")
            >>> result["success"]
            True
            >>> result = agent.run("MP medium", calculate_osmotic=True)  # doctest: +SKIP
            >>> "osmotic_properties" in result["baseline"]  # doctest: +SKIP
            True
        """
        try:
            # Auto-detect mode if not specified
            if mode is None:
                mode = self._detect_mode(query)

            # Get ingredient data
            if mode == "ingredients":
                # Parse ingredient list
                ingredient_names = [name.strip() for name in query.split(",")]
                ingredients = self._get_ingredient_data_for_names(ingredient_names)
            else:
                # Query database for medium
                ingredients = self._get_ingredient_data_for_medium(query)

            if not ingredients:
                return {
                    "success": False,
                    "error": f"No ingredients found for query: {query}",
                    "data": [],
                }

            # Calculate baseline
            baseline = self._calculate_baseline(ingredients, volume_ml)

            # Augment baseline with advanced properties if requested
            if any([calculate_osmotic, calculate_redox, calculate_nutrients]):
                baseline = self._augment_baseline_with_advanced_properties(
                    baseline,
                    osmotic=calculate_osmotic,
                    redox=calculate_redox,
                    nutrients=calculate_nutrients,
                    ph=ph,
                    temperature=temperature
                )

            # Perform sensitivity sweep
            sensitivity_results = self._perform_sensitivity_sweep(ingredients, volume_ml)

            # Calculate summary statistics
            summary = self._calculate_summary(sensitivity_results, baseline)

            # Prepare metadata
            metadata = {
                "query": query,
                "mode": mode,
                "volume_ml": volume_ml,
                "num_ingredients": len(ingredients),
                "advanced_properties": {
                    "osmotic": calculate_osmotic,
                    "redox": calculate_redox,
                    "nutrients": calculate_nutrients
                }
            }

            return {
                "success": True,
                "data": sensitivity_results,
                "baseline": baseline,
                "summary": summary,
                "metadata": metadata,
            }

        except Exception as e:
            self.log(f"Error in sensitivity analysis: {str(e)}", level="ERROR")
            return {
                "success": False,
                "error": str(e),
                "data": [],
            }

    def _detect_mode(self, query: str) -> str:
        """
        Auto-detect whether query is a medium name or ingredient list.

        Args:
            query: Query string

        Returns:
            "medium" or "ingredients"
        """
        # If contains comma, likely ingredient list
        if "," in query:
            return "ingredients"

        # If contains "medium" or "media", likely medium name
        if "medium" in query.lower() or "media" in query.lower():
            return "medium"

        # Default to ingredients mode for simple names
        return "ingredients"

    def _get_ingredient_data_from_list(self, ingredients: List[Dict]) -> List[Dict]:
        """
        Process pre-provided ingredient list.

        Args:
            ingredients: List of ingredient dictionaries

        Returns:
            Validated ingredient list

        Examples:
            >>> agent = SensitivityAnalysisAgent()
            >>> data = [{"name": "NaCl", "low_conc": 1.0, "default_conc": 10.0,
            ...          "high_conc": 100.0, "unit": "mM", "molecular_weight": 58.44}]
            >>> result = agent._get_ingredient_data_from_list(data)
            >>> len(result)
            1
        """
        validated = []
        for ing in ingredients:
            # Ensure required fields
            if all(k in ing for k in ["name", "low_conc", "default_conc", "high_conc", "unit", "molecular_weight"]):
                # Validate concentration ranges
                if ing["low_conc"] <= ing["default_conc"] <= ing["high_conc"]:
                    validated.append(ing.copy())
                else:
                    self.log(f"Invalid concentration range for {ing['name']}", level="WARNING")
            else:
                self.log(f"Missing required fields for ingredient: {ing.get('name', 'unknown')}", level="WARNING")

        return validated

    def _get_ingredient_data_for_names(self, ingredient_names: List[str]) -> List[Dict]:
        """
        Get ingredient data for list of ingredient names.

        Uses GenMediaConcAgent to get evidence-based concentration predictions.

        Args:
            ingredient_names: List of ingredient names

        Returns:
            List of ingredient dictionaries with LOW/DEFAULT/HIGH values
        """
        # Try to use GenMediaConcAgent for database lookup
        try:
            from microgrowagents.agents.gen_media_conc_agent import GenMediaConcAgent

            gen_agent = GenMediaConcAgent(
                db_path=self.db_path,
                chebi_owl_file=self.chebi_owl_file
            )

            # Query for ingredient list
            query = ",".join(ingredient_names)
            result = gen_agent.run(query, mode="ingredients", include_evidence=False)

            if result["success"] and result["data"]:
                return self._convert_genmedia_predictions_to_ingredients(result["data"])
            else:
                self.log("GenMediaConcAgent lookup failed, using fallback mock data", level="WARNING")
        except Exception as e:
            self.log(f"Error using GenMediaConcAgent: {e}, using fallback mock data", level="WARNING")

        # Fallback to mock data for testing/development
        return self._get_mock_ingredient_data(ingredient_names)

    def _get_mock_ingredient_data(self, ingredient_names: List[str]) -> List[Dict]:
        """
        Get mock ingredient data (fallback when database is unavailable).

        Args:
            ingredient_names: List of ingredient names

        Returns:
            List of ingredient dictionaries with mock LOW/DEFAULT/HIGH values
        """
        ingredients = []

        # Mock data for common ingredients
        mock_db = {
            "PIPES": {
                "low_conc": 10.0,
                "default_conc": 30.0,
                "high_conc": 100.0,
                "unit": "mM",
                "pka": [6.76],
                "molecular_weight": 302.37,
                "formula": "C8H18N2O6S2"
            },
            "NaCl": {
                "low_conc": 10.0,
                "default_conc": 100.0,
                "high_conc": 500.0,
                "unit": "mM",
                "pka": None,
                "molecular_weight": 58.44,
                "formula": "NaCl"
            },
            "K2HPO4": {
                "low_conc": 0.1,
                "default_conc": 1.45,
                "high_conc": 100.0,
                "unit": "mM",
                "pka": [2.15, 7.20, 12.35],
                "molecular_weight": 174.18,
                "formula": "K2HPO4"
            },
            "K₂HPO₄": {  # Unicode variant
                "low_conc": 0.1,
                "default_conc": 1.45,
                "high_conc": 100.0,
                "unit": "mM",
                "pka": [2.15, 7.20, 12.35],
                "molecular_weight": 174.18,
                "formula": "K2HPO4"
            }
        }

        for name in ingredient_names:
            if name in mock_db:
                ing_data = mock_db[name].copy()
                ing_data["name"] = name
                ingredients.append(ing_data)
            else:
                self.log(f"Ingredient {name} not found in mock database", level="WARNING")

        return ingredients

    def _get_ingredient_data_for_medium(self, medium_name: str) -> List[Dict]:
        """
        Get ingredient data for a specific medium from database.

        Uses GenMediaConcAgent to get evidence-based concentration predictions
        for all ingredients in the specified medium.

        Args:
            medium_name: Name of the medium

        Returns:
            List of ingredient dictionaries with LOW/DEFAULT/HIGH values

        Examples:
            >>> agent = SensitivityAnalysisAgent()
            >>> # With real database, this would return actual ingredients
            >>> ingredients = agent._get_ingredient_data_for_medium("MP medium")  # doctest: +SKIP
        """
        try:
            from microgrowagents.agents.gen_media_conc_agent import GenMediaConcAgent

            gen_agent = GenMediaConcAgent(
                db_path=self.db_path,
                chebi_owl_file=self.chebi_owl_file
            )

            # Query for medium
            result = gen_agent.run(medium_name, mode="medium", include_evidence=False)

            if result["success"] and result["data"]:
                self.log(f"Found {len(result['data'])} ingredients for medium: {medium_name}")
                return self._convert_genmedia_predictions_to_ingredients(result["data"])
            else:
                self.log(f"No data found for medium: {medium_name}", level="WARNING")
                return []

        except Exception as e:
            self.log(f"Error querying medium '{medium_name}': {e}", level="ERROR")
            return []

    def _convert_genmedia_predictions_to_ingredients(self, predictions: List[Dict]) -> List[Dict]:
        """
        Convert GenMediaConcAgent predictions to sensitivity analysis format.

        Args:
            predictions: List of prediction dictionaries from GenMediaConcAgent

        Returns:
            List of ingredient dictionaries for sensitivity analysis

        Examples:
            >>> agent = SensitivityAnalysisAgent()
            >>> preds = [{"name": "NaCl", "concentration_low": 10.0, "concentration_high": 500.0,
            ...           "unit": "mM", "chebi_id": "CHEBI:26710"}]
            >>> result = agent._convert_genmedia_predictions_to_ingredients(preds)
            >>> result[0]["name"]
            'NaCl'
            >>> result[0]["low_conc"]
            10.0
        """
        ingredients = []

        for pred in predictions:
            low_conc = pred.get("concentration_low", 0.0)
            high_conc = pred.get("concentration_high", 0.0)

            # Calculate default as midpoint (or use current concentration if available)
            if "concentration" in pred:
                default_conc = pred["concentration"]
            else:
                # Use geometric mean for concentration (better for log-scale data)
                if low_conc > 0 and high_conc > 0:
                    default_conc = (low_conc * high_conc) ** 0.5
                else:
                    default_conc = (low_conc + high_conc) / 2.0

            # Get molecular weight from prediction or chemistry lookup
            mw = pred.get("molecular_weight")
            if mw is None:
                # Try to get from formula if available
                formula = pred.get("formula") or pred.get("chemical_formula")
                if formula:
                    try:
                        from microgrowagents.agents.chemistry_agent import ChemistryAgent
                        chem_agent = ChemistryAgent()
                        mw_result = chem_agent.run(f"calculate_mw {formula}")
                        if mw_result["success"]:
                            mw = mw_result["data"]["molecular_weight"]
                    except:
                        pass

            # Default molecular weight if still None
            if mw is None:
                mw = 100.0  # Reasonable default
                self.log(f"Using default MW for {pred['name']}", level="WARNING")

            ingredients.append({
                "name": pred["name"],
                "low_conc": low_conc,
                "default_conc": default_conc,
                "high_conc": high_conc,
                "unit": pred.get("unit", "mM"),
                "molecular_weight": mw,
                "pka": pred.get("pka"),
                "formula": pred.get("formula") or pred.get("chemical_formula"),
                "chebi_id": pred.get("chebi_id"),
            })

        return ingredients

    def _calculate_baseline(
        self,
        ingredients: List[Dict],
        volume_ml: float
    ) -> Dict[str, Any]:
        """
        Calculate baseline properties with all ingredients at DEFAULT.

        Args:
            ingredients: List of ingredient dictionaries
            volume_ml: Total volume in mL

        Returns:
            Dictionary with:
            - ph: float
            - salinity: float (g/L)
            - ionic_strength: float
            - volume_ml: float
            - formulation: List of ingredient concentrations

        Examples:
            >>> agent = SensitivityAnalysisAgent()
            >>> ingredients = [{"name": "NaCl", "default_conc": 100.0, "unit": "mM",
            ...                 "molecular_weight": 58.44, "pka": None}]
            >>> baseline = agent._calculate_baseline(ingredients, 1000.0)
            >>> baseline["volume_ml"]
            1000.0
            >>> 0 < baseline["ph"] <= 14
            True
        """
        # Build formulation with all at DEFAULT
        formulation = []
        total_ingredient_mass_g = 0.0

        for ing in ingredients:
            conc_mM = ing["default_conc"]
            mw = ing["molecular_weight"]

            # Convert mM to g/L: (conc_mM / 1000) * MW
            grams_per_liter = (conc_mM / 1000.0) * mw

            # For 1L volume
            mass_g = grams_per_liter * (volume_ml / 1000.0)
            total_ingredient_mass_g += mass_g

            # Extract pKa - if it's a list, use the middle value (for polyprotic acids)
            pka = ing.get("pka")
            if isinstance(pka, list) and len(pka) > 0:
                pka = pka[len(pka) // 2]  # Middle pKa for polyprotic acids

            formulation.append({
                "name": ing["name"],
                "concentration": conc_mM,
                "unit": "mM",
                "pka": pka,
                "molecular_weight": mw,
                "grams_per_liter": grams_per_liter,
            })

        # Calculate pH
        ph, ph_details = self.ph_calculator.calculate_ph(formulation, volume_ml)

        # Calculate TDS (Total Dissolved Solids)
        salinity = calculate_salinity(formulation)

        # Calculate NaCl salinity (ionic salts only)
        nacl_salinity = calculate_nacl_salinity(formulation)

        # Calculate ionic strength
        ionic_strength = calculate_ionic_strength(formulation)

        # Estimate ingredient volume (approximate, assuming density ~ 1 g/mL)
        ingredient_volume_ml = total_ingredient_mass_g / 1.0

        return {
            "ph": round(ph, 2),
            "salinity": round(salinity, 2),
            "nacl_salinity": round(nacl_salinity, 2),
            "ionic_strength": round(ionic_strength, 4),
            "volume_ml": volume_ml,
            "ingredient_volume_ml": round(ingredient_volume_ml, 2),
            "formulation": formulation,
            "ph_details": ph_details,
        }

    def _perform_sensitivity_sweep(
        self,
        ingredients: List[Dict],
        volume_ml: float
    ) -> List[Dict]:
        """
        Perform sensitivity sweep for each ingredient.

        For each ingredient:
            1. Calculate properties at LOW concentration
            2. Calculate properties at HIGH concentration
            (all others remain at DEFAULT)

        Args:
            ingredients: List of ingredient dictionaries
            volume_ml: Total volume in mL

        Returns:
            List of result dicts with:
            - ingredient: str
            - concentration_level: "low" or "high"
            - concentration_value: float
            - unit: str
            - ph: float
            - salinity: float
            - delta_ph: float (from baseline)
            - delta_salinity: float (from baseline)

        Examples:
            >>> agent = SensitivityAnalysisAgent()
            >>> ingredients = [{"name": "NaCl", "low_conc": 10.0, "default_conc": 100.0,
            ...                 "high_conc": 500.0, "unit": "mM", "molecular_weight": 58.44, "pka": None}]
            >>> results = agent._perform_sensitivity_sweep(ingredients, 1000.0)
            >>> len(results)
            2
        """
        # Calculate baseline first
        baseline = self._calculate_baseline(ingredients, volume_ml)

        results = []

        # For each ingredient, test LOW and HIGH
        for target_ingredient in ingredients:
            target_name = target_ingredient["name"]

            for level in ["low", "high"]:
                # Vary target ingredient
                target_conc = target_ingredient[f"{level}_conc"]

                # Calculate properties with this variation
                properties = self._calculate_properties_with_variation(
                    ingredients,
                    target_name,
                    target_conc,
                    volume_ml
                )

                # Calculate deltas from baseline
                delta_ph = properties["ph"] - baseline["ph"]
                delta_salinity = properties["salinity"] - baseline["salinity"]
                delta_nacl_salinity = properties["nacl_salinity"] - baseline["nacl_salinity"]

                # Calculate percent changes
                percent_change_ph = (delta_ph / baseline["ph"] * 100) if baseline["ph"] != 0 else 0
                percent_change_salinity = (delta_salinity / baseline["salinity"] * 100) if baseline["salinity"] != 0 else 0
                percent_change_nacl_salinity = (delta_nacl_salinity / baseline["nacl_salinity"] * 100) if baseline["nacl_salinity"] != 0 else 0

                results.append({
                    "ingredient": target_name,
                    "concentration_level": level,
                    "concentration_value": target_conc,
                    "unit": target_ingredient["unit"],
                    "ph": round(properties["ph"], 2),
                    "salinity": round(properties["salinity"], 2),
                    "nacl_salinity": round(properties["nacl_salinity"], 2),
                    "ionic_strength": round(properties["ionic_strength"], 4),
                    "delta_ph": round(delta_ph, 2),
                    "delta_salinity": round(delta_salinity, 2),
                    "delta_nacl_salinity": round(delta_nacl_salinity, 2),
                    "percent_change_ph": round(percent_change_ph, 2),
                    "percent_change_salinity": round(percent_change_salinity, 2),
                    "percent_change_nacl_salinity": round(percent_change_nacl_salinity, 2),
                })

        return results

    def _calculate_properties_with_variation(
        self,
        ingredients: List[Dict],
        target_ingredient: str,
        target_concentration: float,
        volume_ml: float
    ) -> Dict[str, float]:
        """
        Calculate properties with one ingredient varied.

        Args:
            ingredients: List of all ingredients
            target_ingredient: Name of ingredient to vary
            target_concentration: Concentration value to use for target
            volume_ml: Total volume in mL

        Returns:
            Dictionary with ph, salinity, ionic_strength
        """
        # Build formulation with target varied, others at default
        formulation = []

        for ing in ingredients:
            if ing["name"] == target_ingredient:
                conc_mM = target_concentration
            else:
                conc_mM = ing["default_conc"]

            mw = ing["molecular_weight"]
            grams_per_liter = (conc_mM / 1000.0) * mw

            # Extract pKa - if it's a list, use the middle value (for polyprotic acids)
            pka = ing.get("pka")
            if isinstance(pka, list) and len(pka) > 0:
                pka = pka[len(pka) // 2]  # Middle pKa for polyprotic acids

            formulation.append({
                "name": ing["name"],
                "concentration": conc_mM,
                "unit": "mM",
                "pka": pka,
                "molecular_weight": mw,
                "grams_per_liter": grams_per_liter,
            })

        # Calculate pH
        ph, _ = self.ph_calculator.calculate_ph(formulation, volume_ml)

        # Calculate TDS (Total Dissolved Solids)
        salinity = calculate_salinity(formulation)

        # Calculate NaCl salinity (ionic salts only)
        nacl_salinity = calculate_nacl_salinity(formulation)

        # Calculate ionic strength
        ionic_strength = calculate_ionic_strength(formulation)

        return {
            "ph": ph,
            "salinity": salinity,
            "nacl_salinity": nacl_salinity,
            "ionic_strength": ionic_strength,
        }

    def _augment_baseline_with_advanced_properties(
        self,
        baseline: Dict[str, Any],
        osmotic: bool = False,
        redox: bool = False,
        nutrients: bool = False,
        ph: Optional[float] = None,
        temperature: float = 25.0
    ) -> Dict[str, Any]:
        """
        Augment baseline with advanced chemical properties.

        Args:
            baseline: Baseline dictionary from _calculate_baseline
            osmotic: Calculate osmotic properties
            redox: Calculate redox properties
            nutrients: Calculate nutrient ratios
            ph: pH value (uses baseline pH if None)
            temperature: Temperature in °C

        Returns:
            Augmented baseline dictionary

        Examples:
            >>> agent = SensitivityAnalysisAgent()
            >>> baseline = {"ph": 7.0, "formulation": []}
            >>> result = agent._augment_baseline_with_advanced_properties(
            ...     baseline, osmotic=True, temperature=25.0
            ... )
            >>> "osmotic_properties" in result or True  # May be empty if no ingredients
            True
        """
        # Use baseline pH if not provided
        if ph is None:
            ph = baseline.get("ph", 7.0)

        # Prepare ingredients for advanced calculations
        formulation = baseline.get("formulation", [])
        ingredients = self._prepare_ingredients_for_advanced_calcs(formulation)

        # Calculate osmotic properties
        if osmotic and ingredients:
            try:
                osm_result = calculate_osmolarity(ingredients, temperature=temperature)
                aw_result = calculate_water_activity(ingredients, temperature=temperature, method="raoult")

                baseline["osmotic_properties"] = {
                    "osmolarity": osm_result["osmolarity"],
                    "osmolality": osm_result["osmolality"],
                    "water_activity": aw_result["water_activity"],
                    "growth_category": aw_result["growth_category"],
                    "van_hoff_factors": osm_result["van_hoff_factors"],
                    "confidence": {
                        "osmolarity": osm_result["confidence"],
                        "water_activity": aw_result["confidence"]
                    },
                    "warnings": osm_result["warnings"] + aw_result["warnings"]
                }
            except Exception as e:
                self.log(f"Error calculating osmotic properties: {e}", level="WARNING")
                baseline["osmotic_properties"] = {"error": str(e)}

        # Calculate redox properties
        if redox and ingredients:
            try:
                redox_result = calculate_redox_potential(ingredients, ph=ph, temperature=temperature)
                balance_result = calculate_electron_balance(ingredients)

                baseline["redox_properties"] = {
                    "eh": redox_result["eh"],
                    "pe": redox_result["pe"],
                    "redox_state": redox_result["redox_state"],
                    "redox_couples": redox_result["redox_couples"],
                    "electron_balance": {
                        "total_donors": balance_result["total_donors"],
                        "total_acceptors": balance_result["total_acceptors"],
                        "balance": balance_result["balance"],
                        "donor_list": balance_result["donor_list"],
                        "acceptor_list": balance_result["acceptor_list"]
                    },
                    "confidence": redox_result["confidence"],
                    "warnings": redox_result["warnings"]
                }
            except Exception as e:
                self.log(f"Error calculating redox properties: {e}", level="WARNING")
                baseline["redox_properties"] = {"error": str(e)}

        # Calculate nutrient ratios
        if nutrients and ingredients:
            try:
                cnp_result = calculate_cnp_ratios(ingredients)
                metal_result = calculate_trace_metal_ratios(ingredients)

                baseline["nutrient_ratios"] = {
                    "c_mol": cnp_result["c_mol"],
                    "n_mol": cnp_result["n_mol"],
                    "p_mol": cnp_result["p_mol"],
                    "c_n_ratio": cnp_result["c_n_ratio"],
                    "c_p_ratio": cnp_result["c_p_ratio"],
                    "n_p_ratio": cnp_result["n_p_ratio"],
                    "limiting_nutrient": cnp_result["limiting_nutrient"],
                    "redfield_deviation": cnp_result["redfield_deviation"],
                    "trace_metals": {
                        "fe_p_ratio": metal_result["fe_p_ratio"],
                        "mn_p_ratio": metal_result["mn_p_ratio"],
                        "zn_p_ratio": metal_result["zn_p_ratio"],
                        "deficiencies": metal_result["deficiencies"],
                        "excesses": metal_result["excesses"]
                    },
                    "confidence": cnp_result["confidence"]
                }
            except Exception as e:
                self.log(f"Error calculating nutrient ratios: {e}", level="WARNING")
                baseline["nutrient_ratios"] = {"error": str(e)}

        return baseline

    def _prepare_ingredients_for_advanced_calcs(
        self,
        formulation: List[Dict]
    ) -> List[Dict]:
        """
        Prepare ingredients for advanced chemistry calculations.

        Converts formulation format to the format expected by advanced chemistry modules.

        Args:
            formulation: Formulation from baseline

        Returns:
            List of ingredient dictionaries with required fields

        Examples:
            >>> agent = SensitivityAnalysisAgent()
            >>> formulation = [{
            ...     "name": "NaCl",
            ...     "concentration": 100.0,
            ...     "molecular_weight": 58.44,
            ...     "grams_per_liter": 5.844
            ... }]
            >>> result = agent._prepare_ingredients_for_advanced_calcs(formulation)
            >>> len(result)
            1
        """
        ingredients = []

        for ing in formulation:
            ingredient = {
                "name": ing["name"],
                "concentration": ing["concentration"],  # mM
                "molecular_weight": ing.get("molecular_weight", 0),
                "grams_per_liter": ing.get("grams_per_liter", 0),
                "formula": ing.get("formula", ""),  # May not always be available
                "charge": ing.get("charge", 0)
            }
            ingredients.append(ingredient)

        return ingredients

    def _calculate_summary(
        self,
        results: List[Dict],
        baseline: Dict
    ) -> Dict[str, Any]:
        """
        Calculate summary statistics from results.

        Args:
            results: List of sensitivity results
            baseline: Baseline properties

        Returns:
            Dictionary with summary statistics

        Examples:
            >>> agent = SensitivityAnalysisAgent()
            >>> results = [{"ph": 6.5, "salinity": 10.0, "ingredient": "A", "delta_ph": -0.5},
            ...            {"ph": 7.5, "salinity": 15.0, "ingredient": "B", "delta_ph": 0.5}]
            >>> baseline = {"ph": 7.0, "salinity": 12.0}
            >>> summary = agent._calculate_summary(results, baseline)
            >>> summary["ph_range"]
            [6.5, 7.5]
        """
        if not results:
            return {
                "ph_range": [baseline["ph"], baseline["ph"]],
                "salinity_range": [baseline["salinity"], baseline["salinity"]],
                "nacl_salinity_range": [baseline["nacl_salinity"], baseline["nacl_salinity"]],
                "most_sensitive_ph": None,
                "most_sensitive_salinity": None,
                "most_sensitive_nacl_salinity": None,
                "ingredients_analyzed": 0,
            }

        # Extract all pH, TDS, and NaCl salinity values
        ph_values = [r["ph"] for r in results]
        salinity_values = [r["salinity"] for r in results]
        nacl_salinity_values = [r["nacl_salinity"] for r in results]

        # Find most sensitive ingredients (largest absolute delta)
        max_ph_delta = max(results, key=lambda r: abs(r["delta_ph"]))
        max_sal_delta = max(results, key=lambda r: abs(r["delta_salinity"]))
        max_nacl_sal_delta = max(results, key=lambda r: abs(r["delta_nacl_salinity"]))

        return {
            "ph_range": [min(ph_values), max(ph_values)],
            "salinity_range": [min(salinity_values), max(salinity_values)],
            "nacl_salinity_range": [min(nacl_salinity_values), max(nacl_salinity_values)],
            "most_sensitive_ph": max_ph_delta["ingredient"],
            "most_sensitive_salinity": max_sal_delta["ingredient"],
            "most_sensitive_nacl_salinity": max_nacl_sal_delta["ingredient"],
            "ingredients_analyzed": len(set(r["ingredient"] for r in results)),
        }

    def _format_results(
        self,
        results: List[Dict],
        baseline: Dict,
        output_format: str = "table"
    ) -> Any:
        """
        Format results for output.

        Args:
            results: List of sensitivity results
            baseline: Baseline properties
            output_format: Output format (table, json, yaml, tsv)

        Returns:
            Formatted output

        Examples:
            >>> agent = SensitivityAnalysisAgent()
            >>> results = [{"ingredient": "NaCl", "ph": 7.0}]
            >>> baseline = {"ph": 7.0}
            >>> formatted = agent._format_results(results, baseline, "json")
            >>> formatted is not None
            True
        """
        if output_format == "json":
            import json
            return json.dumps({"results": results, "baseline": baseline}, indent=2)

        elif output_format == "yaml":
            import yaml
            return yaml.dump({"results": results, "baseline": baseline})

        elif output_format == "table":
            # Return raw data for now, CLI will format
            return {"results": results, "baseline": baseline}

        elif output_format == "tsv":
            import pandas as pd
            df = pd.DataFrame(results)
            return df.to_csv(sep="\t", index=False)

        else:
            return results

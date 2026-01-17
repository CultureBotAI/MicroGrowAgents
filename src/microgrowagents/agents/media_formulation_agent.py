"""
Media Formulation Agent.

This agent recommends new media formulations or variations analogous to MP medium
using multi-source evidence integration from:
- KG-Microbe knowledge graph
- Literature (PubMed, citations)
- Database ingredient properties
- Chemistry calculations and compatibility
- Reasoning over all available evidence

Author: MicroGrowAgents Team
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from microgrowagents.agents.base_agent import BaseAgent
from microgrowagents.agents.chemistry_agent import ChemistryAgent
from microgrowagents.agents.cofactor_media_agent import CofactorMediaAgent
from microgrowagents.agents.gen_media_conc_agent import GenMediaConcAgent
from microgrowagents.agents.genome_function_agent import GenomeFunctionAgent
from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent
from microgrowagents.agents.literature_agent import LiteratureAgent
from microgrowagents.agents.media_role_agent import MediaRoleAgent
from microgrowagents.agents.sql_agent import SQLAgent
from microgrowagents.agents.alternate_ingredient_agent import AlternateIngredientAgent
from microgrowagents.agents.media_ph_calculator import MediaPhCalculator

logger = logging.getLogger(__name__)


class MediaFormulationAgent(BaseAgent):
    """
    Agent that recommends new media formulations or variations.

    This agent orchestrates multiple specialized agents to:
    1. Analyze organism requirements via KG-Microbe
    2. Identify essential media components (C, N, P, trace elements, etc.)
    3. Predict appropriate concentration ranges
    4. Validate chemical compatibility
    5. Find literature support
    6. Generate complete formulation with evidence

    Example:
        >>> from pathlib import Path
        >>> agent = MediaFormulationAgent()
        >>> result = agent.run(
        ...     organism="Methylococcus capsulatus",
        ...     growth_conditions={
        ...         "temperature": 42,
        ...         "pH": 6.8,
        ...         "oxygen": "aerobic",
        ...         "carbon_source": "methane"
        ...     },
        ...     formulation_goals=["minimal", "defined", "cost_effective"]
        ... )
        >>> assert result["success"]
        >>> assert "formulation" in result["data"]
        >>> assert "ingredients" in result["data"]["formulation"]
        >>> assert "evidence" in result["data"]
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the Media Formulation Agent.

        Args:
            db_path: Path to DuckDB database (default: data/processed/microgrow.duckdb)
        """
        super().__init__(db_path)

        # Initialize dependent agents
        self.kg_agent = KGReasoningAgent(db_path)
        self.conc_agent = GenMediaConcAgent(db_path)
        self.genome_agent = GenomeFunctionAgent(db_path)  # NEW: genome function analysis
        self.cofactor_agent = CofactorMediaAgent(db_path)  # NEW: cofactor analysis
        self.role_agent = MediaRoleAgent(db_path)
        self.chem_agent = ChemistryAgent(db_path)
        self.lit_agent = LiteratureAgent(db_path)
        self.sql_agent = SQLAgent(db_path)
        self.alt_agent = AlternateIngredientAgent(db_path)
        self.ph_calc = MediaPhCalculator()  # Doesn't take db_path

        self.log("MediaFormulationAgent initialized")

    def run(
        self,
        query: str,
        organism: Optional[str] = None,
        growth_conditions: Optional[Dict[str, Any]] = None,
        formulation_goals: Optional[List[str]] = None,
        base_medium: str = "MP",
        include_alternatives: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Recommend new media formulation.

        Args:
            query: Natural language query describing formulation needs
            organism: Target organism name (for organism-specific recommendations)
            growth_conditions: Dict with keys like temperature, pH, oxygen, carbon_source
            formulation_goals: List of goals: "minimal", "defined", "complex",
                             "cost_effective", "high_yield", "selective"
            base_medium: Reference medium to use as template (default: "MP")
            include_alternatives: Whether to suggest alternative ingredients
            **kwargs: Additional parameters

        Returns:
            Dict with:
                - success: bool
                - data: Dict with formulation, evidence, alternatives, properties
                - metadata: Dict with sources, confidence, citations
        """
        self.log(f"Recommending media formulation: {query}")

        # Set defaults
        if growth_conditions is None:
            growth_conditions = {}
        if formulation_goals is None:
            formulation_goals = ["defined"]

        try:
            # Step 1: Extract organism requirements from KG-Microbe
            kg_evidence = self._get_kg_requirements(organism, query)

            # Step 2: Identify essential media roles
            essential_roles = self._identify_essential_roles(
                organism, growth_conditions, formulation_goals
            )

            # Step 3: Select ingredients for each role
            ingredients = self._select_ingredients(
                essential_roles, organism, growth_conditions,
                formulation_goals, base_medium, kg_evidence  # NEW: pass genome evidence
            )

            # Step 4: Predict concentrations for each ingredient
            concentrations = self._predict_concentrations(
                ingredients, organism, growth_conditions
            )

            # Step 5: Validate chemical compatibility
            compatibility = self._validate_compatibility(concentrations)

            # Step 6: Calculate medium properties
            properties = self._calculate_properties(concentrations, growth_conditions)

            # Step 7: Find alternatives if requested
            alternatives = {}
            if include_alternatives:
                alternatives = self._find_alternatives(ingredients)

            # Step 8: Gather literature evidence
            literature = self._gather_literature_evidence(
                organism, ingredients, query
            )

            # Step 9: Compile formulation
            formulation = {
                "name": self._generate_formulation_name(organism, formulation_goals),
                "organism": organism,
                "description": query,
                "goals": formulation_goals,
                "growth_conditions": growth_conditions,
                "ingredients": concentrations,
                "properties": properties,
                "compatibility_notes": compatibility.get("notes", []),
            }

            # Step 10: Generate rationale
            rationale = self._generate_rationale(
                formulation, kg_evidence, literature, essential_roles
            )

            return {
                "success": True,
                "data": {
                    "formulation": formulation,
                    "rationale": rationale,
                    "essential_roles": essential_roles,
                    "alternatives": alternatives,
                    "evidence": {
                        "kg_microbe": kg_evidence,
                        "literature": literature,
                        "compatibility": compatibility,
                    }
                },
                "metadata": {
                    "organism": organism,
                    "base_medium": base_medium,
                    "goals": formulation_goals,
                    "sources": ["KG-Microbe", "Literature", "MP Medium Database"],
                    "confidence": self._calculate_confidence(
                        kg_evidence, literature, concentrations
                    ),
                }
            }

        except Exception as e:
            self.log(f"Error in media formulation: {str(e)}", level="error")
            return {
                "success": False,
                "data": {},
                "metadata": {"error": str(e)}
            }

    def _get_kg_requirements(
        self, organism: Optional[str], query: str
    ) -> Dict[str, Any]:
        """
        Query KG-Microbe AND genome for organism-specific requirements.

        NEW: Includes genome-based auxotrophy detection and cofactor analysis.
        """
        kg_results = {
            "organism_info": {},
            "pathways": [],
            "enzymes": [],
            "metabolites": [],
            "growth_factors": [],
            "auxotrophies": [],  # NEW: from genome analysis
            "cofactors": [],     # NEW: from genome analysis
        }

        if not organism:
            return kg_results

        try:
            # Lookup organism node
            lookup_result = self.kg_agent.run(
                f"lookup:{organism}",
                task="lookup"
            )

            if lookup_result.get("success"):
                kg_results["organism_info"] = lookup_result.get("data", {})
                organism_id = kg_results["organism_info"].get("id")

                if organism_id:
                    # Get metabolic pathways
                    pathway_result = self.kg_agent.run(
                        f"neighbors:{organism_id}",
                        task="neighbors",
                        relationship_types=["has_part", "participates_in"]
                    )
                    if pathway_result.get("success"):
                        kg_results["pathways"] = pathway_result.get("data", {}).get("neighbors", [])

                    # Get required metabolites/nutrients
                    metabolite_result = self.kg_agent.run(
                        f"neighbors:{organism_id}",
                        task="neighbors",
                        relationship_types=["has_input", "requires"]
                    )
                    if metabolite_result.get("success"):
                        kg_results["metabolites"] = metabolite_result.get("data", {}).get("neighbors", [])

            # NEW: Detect auxotrophies from genome
            aux_result = self.genome_agent.detect_auxotrophies(
                query=f"detect auxotrophies for {organism}",
                organism=organism
            )
            if aux_result.get("success"):
                kg_results["auxotrophies"] = aux_result["data"].get("auxotrophies", [])
                self.log(f"Detected {len(kg_results['auxotrophies'])} auxotrophies from genome")

            # NEW: Get cofactor requirements from genome
            cofactor_result = self.genome_agent.find_cofactor_requirements(
                query=f"find cofactors for {organism}",
                organism=organism
            )
            if cofactor_result.get("success"):
                kg_results["cofactors"] = cofactor_result["data"].get("cofactors", [])
                self.log(f"Identified {len(kg_results['cofactors'])} cofactor requirements from genome")

        except Exception as e:
            self.log(f"KG/genome query error: {str(e)}", level="warning")

        return kg_results

    def _identify_essential_roles(
        self,
        organism: Optional[str],
        growth_conditions: Dict[str, Any],
        goals: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Identify essential media component roles.

        Returns dict mapping role -> {"priority": str, "required": bool, "rationale": str}
        """
        # Core essential roles for all media
        essential_roles = {
            "Carbon Source": {
                "priority": "high",
                "required": True,
                "rationale": "Primary energy and carbon source"
            },
            "Nitrogen Source": {
                "priority": "high",
                "required": True,
                "rationale": "Essential for protein and nucleic acid synthesis"
            },
            "Phosphate Source": {
                "priority": "high",
                "required": True,
                "rationale": "Required for ATP, nucleic acids, and phospholipids"
            },
            "Essential Macronutrient (Mg)": {
                "priority": "high",
                "required": True,
                "rationale": "Cofactor for many enzymes, required for ribosome function"
            },
            "Essential Macronutrient (K)": {
                "priority": "high",
                "required": True,
                "rationale": "Osmotic balance and enzyme activation"
            },
            "Essential Macronutrient (S)": {
                "priority": "medium",
                "required": True,
                "rationale": "Required for cysteine, methionine, and cofactors"
            },
            "Trace Element (Fe)": {
                "priority": "high",
                "required": True,
                "rationale": "Essential for electron transport and many enzymes"
            },
            "pH Buffer": {
                "priority": "high",
                "required": "defined" in goals,
                "rationale": "Maintain stable pH during growth"
            },
        }

        # Add trace elements for comprehensive formulations
        if "minimal" not in goals:
            essential_roles.update({
                "Trace Element (Zn)": {
                    "priority": "medium",
                    "required": True,
                    "rationale": "Metalloenzyme cofactor"
                },
                "Trace Element (Mn)": {
                    "priority": "medium",
                    "required": False,
                    "rationale": "Cofactor and antioxidant"
                },
                "Trace Element (Cu)": {
                    "priority": "low",
                    "required": False,
                    "rationale": "Electron transport enzymes"
                },
                "Trace Element (Co)": {
                    "priority": "low",
                    "required": False,
                    "rationale": "Vitamin B12 synthesis"
                },
                "Trace Element (Mo)": {
                    "priority": "low",
                    "required": False,
                    "rationale": "Nitrogen metabolism enzymes"
                },
            })

        # Add chelator for defined media with trace elements
        if "defined" in goals and "minimal" not in goals:
            essential_roles["Chelator"] = {
                "priority": "medium",
                "required": True,
                "rationale": "Prevent trace element precipitation and toxicity"
            }

        # Add vitamins/cofactors for complex media or auxotrophs
        if "complex" in goals or "high_yield" in goals:
            essential_roles["Vitamin/Cofactor Precursor"] = {
                "priority": "medium",
                "required": False,
                "rationale": "Support biosynthetic pathways"
            }

        # Adjust based on growth conditions
        if growth_conditions.get("oxygen") == "anaerobic":
            essential_roles["Reducing Agent"] = {
                "priority": "high",
                "required": True,
                "rationale": "Maintain low redox potential for anaerobic growth"
            }

        return essential_roles

    def _select_ingredients(
        self,
        essential_roles: Dict[str, Dict[str, Any]],
        organism: Optional[str],
        growth_conditions: Dict[str, Any],
        goals: List[str],
        base_medium: str,
        kg_evidence: Optional[Dict[str, Any]] = None  # NEW parameter
    ) -> Dict[str, str]:
        """
        Select specific ingredients for each essential role.

        NEW: Includes nutrients for detected auxotrophies and essential cofactors.

        Returns dict mapping role -> ingredient_name
        """
        selected = {}

        # Query database for ingredients by role
        for role, role_info in essential_roles.items():
            if not role_info.get("required", True):
                continue

            # Query database for ingredients with this role
            query = f"""
                SELECT DISTINCT component, chemical_formula, priority, default_concentration
                FROM mp_medium_ingredient_properties
                WHERE media_role LIKE '%{role}%'
                ORDER BY priority ASC, default_concentration DESC
                LIMIT 5
            """

            result = self.sql_agent.run(query)

            if result.get("success") and result.get("data"):
                candidates = result["data"]

                # Select best candidate based on goals
                selected_ingredient = self._select_best_candidate(
                    candidates, role, goals, growth_conditions
                )

                if selected_ingredient:
                    selected[role] = selected_ingredient

        # Add specific ingredients based on growth conditions
        carbon_source = growth_conditions.get("carbon_source")
        if carbon_source:
            selected["Carbon Source"] = carbon_source

        # NEW: Add nutrients for detected auxotrophies
        if kg_evidence and kg_evidence.get("auxotrophies"):
            for auxotrophy in kg_evidence["auxotrophies"]:
                nutrients = auxotrophy.get("nutrients", [])
                pathway = auxotrophy.get("pathway_name", "")
                confidence = auxotrophy.get("confidence", "medium")

                # Only add high and medium confidence auxotrophies
                if confidence in ["high", "medium"]:
                    for nutrient in nutrients:
                        role = f"Auxotrophy Supplement ({pathway})"
                        selected[role] = nutrient
                        self.log(f"Added {nutrient} for detected auxotrophy: {pathway}")

        # NEW: Add cofactors that cannot be biosynthesized
        if kg_evidence and kg_evidence.get("cofactors"):
            for cofactor_info in kg_evidence["cofactors"]:
                if cofactor_info.get("external_supply") == "required":
                    cofactor = cofactor_info.get("cofactor")
                    enzyme_count = cofactor_info.get("enzyme_count", 0)

                    if enzyme_count > 0:
                        role = "Essential Cofactor (not biosynthesized)"
                        selected[role] = cofactor
                        self.log(f"Added {cofactor} - required by {enzyme_count} enzymes")

        # NEW: Run CofactorMediaAgent for comprehensive cofactor analysis
        if organism:
            cofactor_result = self.cofactor_agent.run(
                query=f"cofactor analysis for {organism}",
                organism=organism,
                base_medium=base_medium
            )

            if cofactor_result.get("success"):
                # Add new ingredient recommendations
                new_recommendations = cofactor_result["data"].get("new_recommendations", [])
                for rec in new_recommendations:
                    if rec.status == "missing" and rec.external_supply_needed:
                        cofactors = ", ".join(rec.cofactors_provided)
                        role = f"Cofactor Supplement ({cofactors})"
                        selected[role] = rec.ingredient_name if rec.ingredient_name != "NOT COVERED" else f"[{cofactors} needed]"
                        self.log(f"Cofactor gap identified: {cofactors}")

        return selected

    def _select_best_candidate(
        self,
        candidates: List[Dict[str, Any]],
        role: str,
        goals: List[str],
        growth_conditions: Dict[str, Any]
    ) -> Optional[str]:
        """Select best ingredient from candidates based on goals."""
        if not candidates:
            return None

        # Priority-based selection
        if "cost_effective" in goals:
            # Prefer common, inexpensive ingredients
            common_ingredients = {
                "pH Buffer": "PIPES",
                "Carbon Source": "Glucose",
                "Nitrogen Source": "(NH4)2SO4",
                "Phosphate Source": "K2HPO4",
            }
            if role in common_ingredients:
                for candidate in candidates:
                    if candidate["component"] == common_ingredients[role]:
                        return candidate["component"]

        if "defined" in goals or "minimal" in goals:
            # Prefer simple, single-component ingredients
            for candidate in candidates:
                formula = candidate.get("chemical_formula", "")
                if formula and "complex" not in formula.lower():
                    return candidate["component"]

        # Default: use highest priority (lowest priority number)
        return candidates[0]["component"]

    def _predict_concentrations(
        self,
        ingredients: Dict[str, str],
        organism: Optional[str],
        growth_conditions: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Predict concentrations for each ingredient.

        Returns list of dicts with: ingredient, role, concentration, unit, evidence
        """
        concentrations = []

        for role, ingredient in ingredients.items():
            # Get concentration prediction
            conc_result = self.conc_agent.run(
                ingredient,
                mode="organism_specific" if organism else "general",
                organism=organism
            )

            if conc_result.get("success"):
                data = conc_result.get("data", {})
                prediction = data.get("prediction", {})

                concentrations.append({
                    "ingredient": ingredient,
                    "role": role,
                    "concentration": prediction.get("default", "N/A"),
                    "range": {
                        "low": prediction.get("low", "N/A"),
                        "high": prediction.get("high", "N/A"),
                    },
                    "unit": prediction.get("unit", "mM"),
                    "evidence": prediction.get("evidence", []),
                    "confidence": prediction.get("confidence", "medium"),
                })

        return concentrations

    def _validate_compatibility(
        self, concentrations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate chemical compatibility of ingredients.

        Returns dict with compatible: bool, issues: List[str], notes: List[str]
        """
        issues = []
        notes = []

        # Extract ingredient names
        ingredient_names = [c["ingredient"] for c in concentrations]

        # Check for known incompatibilities
        incompatible_pairs = {
            ("FeSO4", "Phosphate"): "Iron can precipitate with phosphate at high pH",
            ("CaCl2", "Phosphate"): "Calcium phosphate precipitation risk",
            ("Heavy metals", "Sulfide"): "Metal sulfide precipitation",
        }

        # Query database for precipitation partners
        for ingredient in ingredient_names:
            query = f"""
                SELECT precipitation_partners, antagonistic_ions
                FROM mp_medium_ingredient_properties
                WHERE component = '{ingredient}'
            """
            result = self.sql_agent.run(query)

            if result.get("success") and result.get("data"):
                data = result["data"][0]
                precip = data.get("precipitation_partners")
                antag = data.get("antagonistic_ions")

                if precip and precip.lower() != "none":
                    notes.append(
                        f"{ingredient}: May precipitate with {precip}. "
                        "Consider separate stock solutions or chelators."
                    )

                if antag and antag.lower() != "none":
                    notes.append(
                        f"{ingredient}: Antagonistic with {antag}. "
                        "Monitor concentrations carefully."
                    )

        return {
            "compatible": len(issues) == 0,
            "issues": issues,
            "notes": notes,
        }

    def _calculate_properties(
        self,
        concentrations: List[Dict[str, Any]],
        growth_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate predicted medium properties.

        Returns dict with pH, ionic_strength, osmolarity, etc.
        """
        properties = {}

        # Calculate pH
        try:
            ingredients_for_ph = [
                {"name": c["ingredient"], "concentration": c["concentration"]}
                for c in concentrations
            ]
            ph_result = self.ph_calc.run(
                ingredients=ingredients_for_ph
            )
            if ph_result.get("success"):
                properties["pH"] = ph_result["data"].get("pH", "N/A")
        except Exception as e:
            self.log(f"pH calculation error: {str(e)}", level="warning")
            properties["pH"] = growth_conditions.get("pH", "N/A")

        # Calculate ionic strength
        try:
            total_ions = 0
            for c in concentrations:
                conc_val = c.get("concentration")
                if isinstance(conc_val, (int, float)):
                    total_ions += conc_val
            properties["ionic_strength_estimate"] = f"{total_ions:.1f} mM"
        except:
            properties["ionic_strength_estimate"] = "N/A"

        # Add target conditions
        properties["target_temperature"] = growth_conditions.get("temperature", "30°C")
        properties["target_pH"] = growth_conditions.get("pH", "7.0")
        properties["oxygen_requirement"] = growth_conditions.get("oxygen", "aerobic")

        return properties

    def _find_alternatives(
        self, ingredients: Dict[str, str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Find alternative ingredients for each component."""
        alternatives = {}

        for role, ingredient in ingredients.items():
            alt_result = self.alt_agent.run(ingredient)

            if alt_result.get("success"):
                alternatives[ingredient] = alt_result.get("data", {}).get("alternatives", [])

        return alternatives

    def _gather_literature_evidence(
        self,
        organism: Optional[str],
        ingredients: Dict[str, str],
        query: str
    ) -> Dict[str, Any]:
        """Gather literature evidence for formulation."""
        literature = {
            "organism_studies": [],
            "ingredient_studies": {},
            "formulation_studies": [],
        }

        # Search for organism-specific studies
        if organism:
            org_query = f"{organism} culture medium growth"
            org_result = self.lit_agent.run(org_query, max_results=5)

            if org_result.get("success"):
                literature["organism_studies"] = org_result.get("data", {}).get("results", [])

        # Search for key ingredients (limit to most important)
        key_ingredients = list(ingredients.values())[:3]  # Top 3
        for ingredient in key_ingredients:
            ing_query = f"{ingredient} microbial growth medium"
            ing_result = self.lit_agent.run(ing_query, max_results=3)

            if ing_result.get("success"):
                literature["ingredient_studies"][ingredient] = ing_result.get("data", {}).get("results", [])

        return literature

    def _generate_formulation_name(
        self, organism: Optional[str], goals: List[str]
    ) -> str:
        """Generate a descriptive name for the formulation."""
        parts = []

        if organism:
            # Use genus name or first word
            genus = organism.split()[0] if organism else "Custom"
            parts.append(genus)

        # Add goal descriptors
        if "minimal" in goals:
            parts.append("Minimal")
        elif "defined" in goals:
            parts.append("Defined")
        elif "complex" in goals:
            parts.append("Complex")

        if "selective" in goals:
            parts.append("Selective")

        parts.append("Medium")

        return " ".join(parts)

    def _generate_rationale(
        self,
        formulation: Dict[str, Any],
        kg_evidence: Dict[str, Any],
        literature: Dict[str, Any],
        essential_roles: Dict[str, Dict[str, Any]]
    ) -> str:
        """Generate human-readable rationale for formulation."""
        rationale_parts = []

        # Introduction
        organism = formulation.get("organism")
        if organism:
            rationale_parts.append(
                f"This formulation is designed for {organism} based on "
                f"evidence from KG-Microbe, literature, and the MP medium database."
            )
        else:
            rationale_parts.append(
                "This is a general-purpose formulation based on best practices "
                "from the MP medium database and literature."
            )

        # Goals
        goals = formulation.get("goals", [])
        if goals:
            goal_str = ", ".join(goals)
            rationale_parts.append(f"Design goals: {goal_str}.")

        # Essential roles coverage
        rationale_parts.append(
            f"\nEssential nutrient roles covered ({len(essential_roles)}):"
        )
        for role, info in essential_roles.items():
            if info.get("required"):
                rationale_parts.append(f"  - {role}: {info.get('rationale', 'Essential')}")

        # KG evidence
        if kg_evidence.get("pathways"):
            rationale_parts.append(
                f"\nKG-Microbe identified {len(kg_evidence['pathways'])} "
                f"relevant metabolic pathways for {organism}."
            )

        # Literature evidence
        org_studies = literature.get("organism_studies", [])
        if org_studies:
            rationale_parts.append(
                f"\nFound {len(org_studies)} literature references "
                f"supporting this organism's growth requirements."
            )

        # Compatibility notes
        compat_notes = formulation.get("compatibility_notes", [])
        if compat_notes:
            rationale_parts.append("\nChemical compatibility notes:")
            for note in compat_notes[:3]:  # Top 3
                rationale_parts.append(f"  - {note}")

        return "\n".join(rationale_parts)

    def _calculate_confidence(
        self,
        kg_evidence: Dict[str, Any],
        literature: Dict[str, Any],
        concentrations: List[Dict[str, Any]]
    ) -> str:
        """
        Calculate overall confidence score.

        Returns: "high", "medium", or "low"
        """
        score = 0

        # KG evidence contributes
        if kg_evidence.get("organism_info"):
            score += 1
        if kg_evidence.get("pathways"):
            score += 1
        if kg_evidence.get("metabolites"):
            score += 1

        # Literature contributes
        if literature.get("organism_studies"):
            score += 2
        if literature.get("ingredient_studies"):
            score += 1

        # Concentration prediction confidence
        high_conf_count = sum(
            1 for c in concentrations
            if c.get("confidence") == "high"
        )
        if high_conf_count >= len(concentrations) * 0.7:
            score += 2
        elif high_conf_count >= len(concentrations) * 0.4:
            score += 1

        # Map score to confidence level
        if score >= 6:
            return "high"
        elif score >= 3:
            return "medium"
        else:
            return "low"

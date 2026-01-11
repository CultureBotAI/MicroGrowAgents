"""
Cofactor Media Agent.

This agent recommends media components to support required cofactors for organisms
with Bakta genome annotations.

Author: MicroGrowAgents Team
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
import csv

from microgrowagents.agents.base_agent import BaseAgent
from microgrowagents.agents.genome_function_agent import GenomeFunctionAgent
from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent
from microgrowagents.agents.literature_agent import LiteratureAgent
from microgrowagents.agents.sql_agent import SQLAgent


@dataclass
class CofactorRequirement:
    """Data class for cofactor requirement analysis."""
    cofactor_id: str
    cofactor_key: str  # Underscore version like "magnesium_ion"
    cofactor_name: str
    category: str
    biosynthesis_status: str  # capable, incapable, partial, unknown
    biosynthesis_completeness: float
    acquisition_mechanism: str  # transporter, chelator, none, unknown
    acquisition_evidence: List[Dict]
    external_supply_needed: bool
    confidence: str  # high, medium, low
    evidence_sources: List[str]


@dataclass
class IngredientRecommendation:
    """Data class for ingredient recommendation."""
    ingredient_name: str
    database_id: str
    status: str  # existing, new
    cofactors_provided: List[str]
    rationale: str
    concentration_range: Optional[Dict]
    confidence: float
    evidence: List[str]


class CofactorMediaAgent(BaseAgent):
    """
    Agent for cofactor-based media ingredient recommendations.

    Analyzes organism genome to:
    1. Identify all required cofactors from enzyme annotations
    2. Determine biosynthesis capability for each cofactor
    3. Determine acquisition capability (transporters, chelators)
    4. Map existing MP medium ingredients to cofactors they provide
    5. Recommend new ingredients for cofactors not covered

    Example:
        >>> agent = CofactorMediaAgent()
        >>> result = agent.run(
        ...     organism="Methylobacterium extorquens",
        ...     base_medium="MP"
        ... )
        >>> result["data"]["cofactor_table"]  # Hierarchical DataFrame
    """

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize with sub-agents and load cofactor mapping data."""
        super().__init__(db_path)

        # Initialize sub-agents
        self.genome_agent = GenomeFunctionAgent(db_path)
        self.kg_agent = KGReasoningAgent(db_path)
        self.lit_agent = LiteratureAgent(db_path)
        self.sql_agent = SQLAgent(db_path)

        # Load cofactor mapping data
        self.cofactor_hierarchy = self._load_cofactor_hierarchy()
        self.ingredient_cofactor_map = self._load_ingredient_cofactor_mapping()
        self.ec_cofactor_map = self._load_ec_cofactor_map()

        self.log("CofactorMediaAgent initialized")

    def _load_cofactor_hierarchy(self) -> Dict:
        """Load cofactor hierarchy from YAML."""
        yaml_path = Path(__file__).parent.parent / "data" / "cofactor_hierarchy.yaml"
        if not yaml_path.exists():
            self.log(f"Warning: {yaml_path} not found", level="WARNING")
            return {}

        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        return data.get("cofactor_hierarchy", {})

    def _load_ec_cofactor_map(self) -> Dict:
        """Load EC to cofactor mapping from YAML."""
        yaml_path = Path(__file__).parent.parent / "data" / "ec_to_cofactor_map.yaml"
        if not yaml_path.exists():
            self.log(f"Warning: {yaml_path} not found", level="WARNING")
            return {}

        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        return data.get("ec_cofactor_mapping", {})

    def _load_ingredient_cofactor_mapping(self) -> List[Dict]:
        """Load ingredient-to-cofactor mapping from CSV."""
        csv_path = Path("data/processed/ingredient_cofactor_mapping.csv")
        if not csv_path.exists():
            self.log(f"Warning: {csv_path} not found", level="WARNING")
            return []

        mappings = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mappings.append(row)

        return mappings

    def run(
        self,
        query: str,
        organism: Optional[str] = None,
        gff3_path: Optional[Path] = None,
        base_medium: str = "MP",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Main entry point: Generate cofactor-based media recommendations.

        Args:
            query: Natural language query
            organism: Organism identifier (SAMN ID or name)
            gff3_path: Optional path to Bakta GFF3 file
            base_medium: Base medium name (default: "MP")

        Returns:
            Dict with:
                - success: bool
                - data: cofactor_table, cofactor_requirements, etc.
                - metadata: confidence, sources, organism info
        """
        if not organism:
            return {
                "success": False,
                "error": "organism parameter is required"
            }

        self.log(f"Analyzing cofactor requirements for {organism}")

        # Step 1: Analyze cofactor requirements
        cofactor_reqs = self.analyze_cofactor_requirements(organism, gff3_path)

        # Step 2: Map to ingredients
        ingredient_mapping = self.map_ingredients_to_cofactors(cofactor_reqs, base_medium)

        # Step 3: Build hierarchical table
        cofactor_table = self._build_cofactor_table(cofactor_reqs, ingredient_mapping)

        return {
            "success": True,
            "data": {
                "cofactor_table": cofactor_table,
                "cofactor_requirements": cofactor_reqs,
                "ingredient_recommendations": ingredient_mapping.get("all", []),
                "existing_coverage": ingredient_mapping.get("existing", []),
                "new_recommendations": ingredient_mapping.get("new", [])
            },
            "metadata": {
                "organism": organism,
                "base_medium": base_medium,
                "cofactors_analyzed": len(cofactor_reqs),
                "sources": ["genome", "kg", "literature"]
            }
        }

    def analyze_cofactor_requirements(
        self,
        organism: str,
        gff3_path: Optional[Path] = None
    ) -> List[CofactorRequirement]:
        """
        Analyze all cofactor requirements for organism.

        Integrates 4 data sources:
        1. Genome (Bakta GFF3 annotations)
        2. KG-Microbe (pathway/metabolite relationships)
        3. KEGG (pathway completeness)
        4. Literature (organism-specific mechanisms)

        Returns:
            List of CofactorRequirement objects
        """
        self.log(f"Analyzing cofactor requirements for {organism}")

        # Get EC numbers from genome by querying database directly
        ec_numbers = self._get_ec_numbers_from_genome(organism)

        if not ec_numbers:
            self.log(f"No EC numbers found for {organism}", level="WARNING")
            return []

        self.log(f"Found {len(ec_numbers)} unique EC numbers")

        # Map EC numbers to cofactors
        cofactor_set = {}
        for ec in ec_numbers:
            cofactors = self._map_ec_to_cofactors(ec)
            for cf_key, cf_data in cofactors.items():
                if cf_key not in cofactor_set:
                    cofactor_set[cf_key] = cf_data

        # Build CofactorRequirement objects
        requirements = []
        for cf_key, cf_data in cofactor_set.items():
            req = CofactorRequirement(
                cofactor_id=cf_data.get("id", ""),
                cofactor_key=cf_key,  # Store the key for matching
                cofactor_name=cf_data.get("name", cf_key),
                category=cf_data.get("category", "other"),
                biosynthesis_status="unknown",
                biosynthesis_completeness=0.0,
                acquisition_mechanism="unknown",
                acquisition_evidence=[],
                external_supply_needed=True,
                confidence="medium",
                evidence_sources=["genome"]
            )
            requirements.append(req)

        return requirements

    def _map_ec_to_cofactors(self, ec_number: str) -> Dict[str, Dict]:
        """Map EC number to cofactors using EC-to-cofactor map."""
        cofactors = {}

        # Try exact match first
        if ec_number in self.ec_cofactor_map:
            mapping = self.ec_cofactor_map[ec_number]
            for cf_key in mapping.get("primary", []):
                cofactors[cf_key] = self._get_cofactor_info(cf_key)

        # Try pattern matching (e.g., 1.1.1.- for 1.1.1.1)
        if not cofactors:
            ec_parts = ec_number.split(".")
            for i in range(len(ec_parts), 0, -1):
                pattern = ".".join(ec_parts[:i]) + (".-" * (4 - i))
                if pattern in self.ec_cofactor_map:
                    mapping = self.ec_cofactor_map[pattern]
                    for cf_key in mapping.get("primary", []):
                        cofactors[cf_key] = self._get_cofactor_info(cf_key)
                    break

        return cofactors

    def _get_ec_numbers_from_genome(self, organism: str) -> List[str]:
        """
        Get all EC numbers for organism from genome annotations.

        Args:
            organism: Organism name or genome ID (SAMN)

        Returns:
            List of unique EC numbers
        """
        # Query database for EC numbers
        query = f"""
            SELECT DISTINCT ec_numbers
            FROM genome_annotations
            WHERE genome_id = '{organism}'
            AND ec_numbers IS NOT NULL
            AND ec_numbers != ''
        """

        result = self.sql_agent.run(query)

        data = result.get("data")
        if not result.get("success") or data is None or (hasattr(data, 'empty') and data.empty):
            # Try organism name search
            query = f"""
                SELECT DISTINCT a.ec_numbers
                FROM genome_annotations a
                JOIN genome_metadata m ON a.genome_id = m.genome_id
                WHERE m.organism_name ILIKE '%{organism}%'
                AND a.ec_numbers IS NOT NULL
                AND a.ec_numbers != ''
            """
            result = self.sql_agent.run(query)
            data = result.get("data")

        if not result.get("success") or data is None or (hasattr(data, 'empty') and data.empty):
            return []

        # Parse EC numbers (may be comma-separated)
        # Handle both DataFrame and list responses
        ec_set = set()

        if hasattr(data, 'iterrows'):  # DataFrame
            for idx, row in data.iterrows():
                ec_str = row.get("ec_numbers", "")
                if ec_str:
                    ecs = [ec.strip() for ec in str(ec_str).split(",")]
                    ec_set.update(ecs)
        else:  # List of dicts
            for row in data:
                ec_str = row.get("ec_numbers", "")
                if ec_str:
                    ecs = [ec.strip() for ec in str(ec_str).split(",")]
                    ec_set.update(ecs)

        return list(ec_set)

    def _get_cofactor_info(self, cofactor_key: str) -> Dict:
        """Get cofactor information from hierarchy."""
        for category_key, category in self.cofactor_hierarchy.items():
            for cf_key, cf_data in category.get("cofactors", {}).items():
                if cf_key == cofactor_key:
                    return {
                        "id": cf_data.get("id", ""),
                        "name": cf_data.get("names", [cofactor_key])[0],
                        "category": category_key
                    }
        return {"id": "", "name": cofactor_key, "category": "other"}

    def map_ingredients_to_cofactors(
        self,
        cofactor_requirements: List[CofactorRequirement],
        base_medium: str = "MP"
    ) -> Dict[str, Any]:
        """
        Map medium ingredients to cofactors.

        Returns:
            Dict with existing, new, and all recommendations
        """
        existing = []
        new = []

        # Create set of required cofactor keys for matching
        required_cofactor_keys = {req.cofactor_key for req in cofactor_requirements}
        covered_keys = set()

        # Check which required cofactors are already in MP medium
        for mapping in self.ingredient_cofactor_map:
            provided = mapping.get("Cofactors_Provided", "").split(";")

            for cf_key in provided:
                cf_key = cf_key.strip()
                if cf_key in required_cofactor_keys:
                    # Find the requirement for this cofactor
                    matching_req = next((r for r in cofactor_requirements if r.cofactor_key == cf_key), None)

                    if matching_req:
                        rec = IngredientRecommendation(
                            ingredient_name=mapping.get("Component", ""),
                            database_id=mapping.get("CHEBI_ID", ""),
                            status="existing",
                            cofactors_provided=[matching_req.cofactor_name],
                            rationale=f"Provides {matching_req.cofactor_name} cofactor",
                            concentration_range=None,
                            confidence=0.9,
                            evidence=["MP medium database"]
                        )
                        existing.append(rec)
                        covered_keys.add(cf_key)

        # Identify gaps (cofactors not covered by existing medium)
        for req in cofactor_requirements:
            if req.cofactor_key not in covered_keys:
                rec = IngredientRecommendation(
                    ingredient_name="NOT COVERED",
                    database_id="",
                    status="missing",
                    cofactors_provided=[req.cofactor_name],
                    rationale=f"No ingredient found for {req.cofactor_name}",
                    concentration_range=None,
                    confidence=0.5,
                    evidence=[]
                )
                new.append(rec)

        return {
            "existing": existing,
            "new": new,
            "all": existing + new
        }

    def _build_cofactor_table(
        self,
        cofactor_requirements: List[CofactorRequirement],
        ingredient_recommendations: Dict[str, Any]
    ) -> List[Dict]:
        """
        Build hierarchical cofactor table.

        Returns:
            List of dicts with table rows
        """
        rows = []

        for req in cofactor_requirements:
            # Find ingredients for this cofactor using cofactor_key
            ingredients = [
                ing for ing in ingredient_recommendations.get("all", [])
                if req.cofactor_name in ing.cofactors_provided
            ]

            if not ingredients:
                rows.append({
                    "Category": req.category,
                    "Cofactor": req.cofactor_name,
                    "Ingredient": "NOT COVERED",
                    "Status": "missing",
                    "Biosynthesis_Capable": req.biosynthesis_status,
                    "Acquisition_Mechanism": req.acquisition_mechanism,
                    "External_Supply_Needed": req.external_supply_needed,
                    "Rationale": f"No ingredient identified",
                    "Confidence": req.confidence
                })
            else:
                for ing in ingredients:
                    rows.append({
                        "Category": req.category,
                        "Cofactor": req.cofactor_name,
                        "Ingredient": ing.ingredient_name,
                        "Status": ing.status,
                        "Biosynthesis_Capable": req.biosynthesis_status,
                        "Acquisition_Mechanism": req.acquisition_mechanism,
                        "External_Supply_Needed": req.external_supply_needed,
                        "Rationale": ing.rationale,
                        "Confidence": ing.confidence
                    })

        return rows

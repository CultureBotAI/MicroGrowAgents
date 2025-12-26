"""
Chemistry agent for compound analysis and media formulation.

Integrates:
- PubChem and ChEBI API clients
- Molecular weight calculations
- pH/pKa calculations
- Media comparison
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from microgrowagents.agents.base_agent import BaseAgent
from microgrowagents.chemistry.api_clients.chebi_client import ChEBIClient
from microgrowagents.chemistry.api_clients.pubchem_client import PubChemClient
from microgrowagents.chemistry.calculations import (
    calculate_ionic_strength,
    calculate_mixture_ph,
    compare_media_chemistry,
    estimate_pka,
)
from microgrowagents.chemistry.molecular_weight import (
    calculate_molecular_weight,
    extract_hydration_number,
)


class ChemistryAgent(BaseAgent):
    """
    Agent for chemistry calculations and compound lookups.

    Capabilities:
    - Compound lookup (PubChem, ChEBI)
    - Molecular weight calculation
    - pH/pKa calculation
    - Media comparison
    - Chemical property analysis

    Examples:
        >>> agent = ChemistryAgent()
        >>> result = agent.run("calculate_mw H2O")
        >>> result["data"]["molecular_weight"]
        18.015

        >>> result = agent.run("calculate_ph", ingredients=[...])
        >>> result["data"]["ph"]
        7.2
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        chebi_owl_file: Optional[Path] = None,
        pubchem_email: str = "microgrowagents@example.com",
    ):
        """
        Initialize ChemistryAgent.

        Args:
            db_path: Path to DuckDB database (optional)
            chebi_owl_file: Path to ChEBI OWL file (optional, for ChEBI lookups)
            pubchem_email: Email for PubChem API User-Agent
        """
        super().__init__(db_path)

        # Initialize API clients
        self.pubchem_client = PubChemClient(email=pubchem_email)

        # ChEBI client only if OWL file provided
        self.chebi_client = None
        if chebi_owl_file:
            try:
                self.chebi_client = ChEBIClient(chebi_owl_file)
                self.log(f"Loaded ChEBI OWL file: {chebi_owl_file}")
            except FileNotFoundError:
                self.log(f"ChEBI OWL file not found: {chebi_owl_file}", level="WARNING")

    def run(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute chemistry task.

        Supports multiple operations:
        - lookup <compound>: Look up compound info
        - calculate_mw <formula> [hydration]: Calculate molecular weight
        - calculate_ph: Calculate pH of mixture
        - calculate_ionic_strength: Calculate ionic strength
        - compare_media: Compare two media formulations
        - analyze <compound>: Comprehensive analysis
        - estimate_pka <compound>: Estimate pKa values

        Args:
            query: Query string (e.g., "calculate_mw H2O")
            **kwargs: Additional parameters
                - operation: Explicit operation name
                - source: "pubchem" or "chebi" (for lookup)
                - formula: Chemical formula (for calculate_mw)
                - hydration_number: Hydration state (for calculate_mw)
                - ingredients: List of ingredient dicts (for pH calculations)
                - media1, media2: Media ingredient lists (for comparison)
                - compound_name: Compound name (for analysis)

        Returns:
            Dictionary with:
            - success: bool
            - data: Result data
            - error: Error message (if failed)
            - operation: Operation performed

        Examples:
            >>> agent.run("calculate_mw H2O")
            {'success': True, 'data': {'molecular_weight': 18.015, ...}}

            >>> agent.run("lookup glucose", source="pubchem")
            {'success': True, 'data': {'cid': 5793, ...}}
        """
        # Parse operation from query or kwargs
        operation = kwargs.get("operation")
        if not operation:
            # Extract operation from query string
            parts = query.strip().split(maxsplit=1)
            if parts:
                operation = parts[0].lower()
            else:
                return {
                    "success": False,
                    "error": "No operation specified",
                }

        # Route to appropriate handler
        try:
            if operation == "lookup":
                return self._handle_lookup(query, **kwargs)
            elif operation == "calculate_mw":
                return self._handle_calculate_mw(query, **kwargs)
            elif operation == "calculate_ph":
                return self._handle_calculate_ph(query, **kwargs)
            elif operation == "calculate_ionic_strength":
                return self._handle_ionic_strength(query, **kwargs)
            elif operation == "compare_media":
                return self._handle_compare_media(query, **kwargs)
            elif operation == "analyze":
                return self._handle_analyze(query, **kwargs)
            elif operation == "estimate_pka":
                return self._handle_estimate_pka(query, **kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}",
                    "operation": operation,
                }

        except Exception as e:
            self.log(f"Error in operation {operation}: {e}", level="ERROR")
            return {
                "success": False,
                "error": str(e),
                "operation": operation,
            }

    def _handle_lookup(self, query: str, **kwargs) -> Dict[str, Any]:
        """Handle compound lookup."""
        source = kwargs.get("source", "pubchem")

        # Extract compound name from query
        parts = query.split(maxsplit=1)
        compound_name = kwargs.get("compound_name", parts[1] if len(parts) > 1 else "")

        if not compound_name:
            return {"success": False, "error": "No compound name provided"}

        if source == "pubchem":
            info = self.pubchem_client.get_compound_info(compound_name)
            if info:
                return {
                    "success": True,
                    "data": info,
                    "operation": "lookup",
                    "source": "pubchem",
                }
            else:
                return {
                    "success": False,
                    "error": f"Compound not found: {compound_name}",
                    "operation": "lookup",
                }

        elif source == "chebi":
            if not self.chebi_client:
                return {
                    "success": False,
                    "error": "ChEBI client not initialized (requires OWL file)",
                }

            info = self.chebi_client.get_compound_info(compound_name)
            if info:
                return {
                    "success": True,
                    "data": info,
                    "operation": "lookup",
                    "source": "chebi",
                }
            else:
                return {
                    "success": False,
                    "error": f"Compound not found in ChEBI: {compound_name}",
                    "operation": "lookup",
                }

        else:
            return {"success": False, "error": f"Unknown source: {source}"}

    def _handle_calculate_mw(self, query: str, **kwargs) -> Dict[str, Any]:
        """Handle molecular weight calculation."""
        # Extract formula from query or kwargs
        parts = query.split()
        formula = kwargs.get("formula", parts[1] if len(parts) > 1 else "")
        hydration_number = kwargs.get("hydration_number", 0)

        # Check if hydration number in query (e.g., "calculate_mw CaCl2 2")
        if len(parts) > 2 and parts[2].isdigit():
            hydration_number = int(parts[2])

        if not formula:
            return {"success": False, "error": "No formula provided"}

        mw = calculate_molecular_weight(formula, hydration_number)

        if mw is not None:
            return {
                "success": True,
                "data": {
                    "molecular_weight": mw,
                    "formula": formula,
                    "hydration_number": hydration_number,
                },
                "operation": "calculate_mw",
            }
        else:
            return {
                "success": False,
                "error": f"Could not calculate MW for: {formula}",
                "operation": "calculate_mw",
            }

    def _handle_calculate_ph(self, query: str, **kwargs) -> Dict[str, Any]:
        """Handle pH calculation."""
        ingredients = kwargs.get("ingredients")

        if not ingredients:
            return {
                "success": False,
                "error": "No ingredients provided",
                "operation": "calculate_ph",
            }

        result = calculate_mixture_ph(ingredients)

        return {
            "success": True,
            "data": result,
            "operation": "calculate_ph",
        }

    def _handle_ionic_strength(self, query: str, **kwargs) -> Dict[str, Any]:
        """Handle ionic strength calculation."""
        ingredients = kwargs.get("ingredients")

        if not ingredients:
            return {
                "success": False,
                "error": "No ingredients provided",
                "operation": "calculate_ionic_strength",
            }

        ionic_strength = calculate_ionic_strength(ingredients)

        return {
            "success": True,
            "data": {"ionic_strength": ionic_strength},
            "operation": "calculate_ionic_strength",
        }

    def _handle_compare_media(self, query: str, **kwargs) -> Dict[str, Any]:
        """Handle media comparison."""
        media1 = kwargs.get("media1")
        media2 = kwargs.get("media2")

        if not media1 or not media2:
            return {
                "success": False,
                "error": "Both media1 and media2 required",
                "operation": "compare_media",
            }

        result = compare_media_chemistry(media1, media2)

        return {
            "success": True,
            "data": result,
            "operation": "compare_media",
        }

    def _handle_analyze(self, query: str, **kwargs) -> Dict[str, Any]:
        """Handle comprehensive compound analysis."""
        # Extract compound name from query
        parts = query.split(maxsplit=1)
        compound_name = kwargs.get("compound_name", parts[1] if len(parts) > 1 else "")

        if not compound_name:
            return {"success": False, "error": "No compound name provided"}

        analysis = {}

        # Try to get ChEBI info
        if self.chebi_client:
            chebi_info = self.chebi_client.get_compound_info(compound_name)
            if chebi_info:
                analysis.update(chebi_info)

        # Try to calculate MW if we have a formula-like name
        # Extract base name and hydration
        base_name, hydration = extract_hydration_number(compound_name)
        mw = calculate_molecular_weight(base_name, hydration)
        if mw:
            analysis["molecular_weight"] = mw

        # Estimate pKa
        pka_values = estimate_pka(compound_name)
        if pka_values:
            analysis["pka_values"] = pka_values

        if analysis:
            return {
                "success": True,
                "data": analysis,
                "operation": "analyze",
            }
        else:
            return {
                "success": False,
                "error": f"Could not analyze compound: {compound_name}",
                "operation": "analyze",
            }

    def _handle_estimate_pka(self, query: str, **kwargs) -> Dict[str, Any]:
        """Handle pKa estimation."""
        # Extract compound name from query
        parts = query.split(maxsplit=1)
        compound_name = kwargs.get("compound_name", parts[1] if len(parts) > 1 else "")

        if not compound_name:
            return {"success": False, "error": "No compound name provided"}

        pka_values = estimate_pka(compound_name)

        return {
            "success": True,
            "data": {"compound_name": compound_name, "pka_values": pka_values},
            "operation": "estimate_pka",
        }

"""
Chemistry module for MicroGrowAgents.

This module provides chemical calculations and API integrations.
Incorporates functionality from MicroMediaParam repository with extensions.

Modules:
- calculations: pH, pKa, ionic strength, buffer capacity
- molecular_weight: MW calculations with hydrate support
- compound_normalizer: Compound name normalization (from MicroMediaParam)
- hydration: Hydration state parsing and correction
- api_clients: PubChem, ChEBI, CAS, OLS API clients
- mappings: ChEBI mapping integration
- element_extractor: Extract key elements from chemical formulas
"""

from microgrowagents.chemistry.element_extractor import ElementExtractor

__all__ = ["ElementExtractor"]

"""
Extract key elements from chemical formulas.

This module provides utilities to extract the primary functional element
from chemical compound names and formulas, useful for finding alternate
ingredients with similar chemical properties.
"""

import re
from typing import Optional, List


class ElementExtractor:
    """
    Extract key elements from chemical formulas.

    Handles hydrates, salts, and complex formulas to identify the primary
    functional element (e.g., Fe from FeSO₄·7H₂O, Mg from MgCl₂).

    Examples:
        >>> extractor = ElementExtractor()
        >>> extractor.extract("FeSO₄·7H₂O")
        'Fe'
        >>> extractor.extract("MgCl₂·6H₂O")
        'Mg'
        >>> extractor.extract("Zinc sulfate")
        'Zn'
    """

    # Priority order for element extraction (most to least important)
    # We prioritize trace metals and macronutrients over common ions
    ELEMENT_PRIORITY = [
        # Trace metals (highest priority)
        "Fe", "Zn", "Mn", "Cu", "Co", "Mo", "Ni", "Se", "W",
        # Macronutrients - N before S for ammonium sulfate
        "Mg", "Ca", "K", "Na", "P", "N", "S",
        # Rare earth elements
        "Dy", "Nd", "Pr", "La", "Ce", "Eu", "Sm", "Gd",
        # Other metals
        "Al", "Cr", "V", "B",
    ]

    # Valid chemical elements (to prevent matching non-elements like "Gl" in "Glucose")
    VALID_ELEMENTS = {
        "Fe", "Zn", "Mn", "Cu", "Co", "Mo", "Ni", "Se", "W",
        "Mg", "Ca", "K", "Na", "P", "N", "S",
        "Dy", "Nd", "Pr", "La", "Ce", "Eu", "Sm", "Gd",
        "Al", "Cr", "V", "B", "C", "Si", "Li", "Be"
    }

    # Common element name to symbol mapping
    ELEMENT_NAMES = {
        "iron": "Fe",
        "ferrous": "Fe",
        "ferric": "Fe",
        "zinc": "Zn",
        "manganese": "Mn",
        "copper": "Cu",
        "cupric": "Cu",
        "cuprous": "Cu",
        "cobalt": "Co",
        "molybdenum": "Mo",
        "molybdate": "Mo",
        "nickel": "Ni",
        "selenium": "Se",
        "selenite": "Se",
        "tungsten": "W",
        "tungstate": "W",
        "magnesium": "Mg",
        "calcium": "Ca",
        "potassium": "K",
        "sodium": "Na",
        "phosphate": "P",
        "phosphorus": "P",
        "sulfate": "S",
        "sulfur": "S",
        "nitrogen": "N",
        "ammonium": "N",
        "dysprosium": "Dy",
        "neodymium": "Nd",
        "praseodymium": "Pr",
        "lanthanum": "La",
        "cerium": "Ce",
        "europium": "Eu",
    }

    def extract(self, compound: str) -> Optional[str]:
        """
        Extract the key element from a compound name or formula.

        Args:
            compound: Compound name or chemical formula

        Returns:
            Element symbol (e.g., "Fe", "Mg") or None if not found

        Examples:
            >>> extractor = ElementExtractor()
            >>> extractor.extract("FeSO₄·7H₂O")
            'Fe'
            >>> extractor.extract("K₂HPO₄·3H₂O")
            'P'
            >>> extractor.extract("Glucose")
            None
        """
        if not compound:
            return None

        compound_lower = compound.lower()

        # Special case: Check if it's an organic buffer (return None)
        organic_buffers = ["pipes", "hepes", "mops", "mes", "tris", "glucose", "methanol",
                          "glycerol", "acetate", "succinate", "pyruvate", "lactate",
                          "biotin", "thiamin", "riboflavin"]
        if any(buf in compound_lower for buf in organic_buffers):
            return None

        # Method 1: Check element names in the compound string
        for name, symbol in self.ELEMENT_NAMES.items():
            if name in compound_lower:
                return symbol

        # Method 2: Extract from chemical formula using regex
        # Remove hydration (·nH₂O or .nH2O)
        formula = re.sub(r"[·\.]\d*[Hh]₂?[Oo]₂?", "", compound)

        # Special case: Phosphate compounds - prioritize P over K/Na
        if "po4" in formula.lower() or "po₄" in formula.lower() or "hpo" in formula.lower():
            if "P" in formula:
                return "P"

        # Find all element symbols in the formula
        elements_found = self._find_elements_in_formula(formula)

        if not elements_found:
            return None

        # Return the highest priority element
        for priority_element in self.ELEMENT_PRIORITY:
            if priority_element in elements_found:
                return priority_element

        # If no priority element found, return the first one
        return elements_found[0] if elements_found else None

    def _find_elements_in_formula(self, formula: str) -> List[str]:
        """
        Find all chemical element symbols in a formula.

        Args:
            formula: Chemical formula (e.g., "FeSO₄", "K₂HPO₄")

        Returns:
            List of element symbols found

        Examples:
            >>> extractor = ElementExtractor()
            >>> extractor._find_elements_in_formula("FeSO₄")
            ['Fe', 'S']
            >>> extractor._find_elements_in_formula("K₂HPO₄")
            ['K', 'P']
        """
        # Pattern: Capital letter optionally followed by lowercase letter(s)
        # This matches element symbols like Fe, Mg, Mn, Cu, etc.
        element_pattern = r'[A-Z][a-z]?'

        # Find all matches
        matches = re.findall(element_pattern, formula)

        # Filter out common non-element patterns
        exclude = {"H", "O", "Cl", "Br", "I", "F"}  # Common ions we want to exclude

        # Keep only valid elements that are not in exclude list
        valid_elements = []
        for match in matches:
            if match in self.ELEMENT_PRIORITY:
                valid_elements.append(match)
            elif match in self.VALID_ELEMENTS and match not in exclude:
                # Check if it's a valid element we know about
                valid_elements.append(match)

        # Remove duplicates while preserving order
        seen = set()
        result = []
        for elem in valid_elements:
            if elem not in seen:
                seen.add(elem)
                result.append(elem)

        return result

    def extract_all(self, compound: str) -> List[str]:
        """
        Extract all functional elements from a compound.

        Useful for compounds with multiple important elements
        (e.g., (NH₄)₂SO₄ contains both N and S).

        Args:
            compound: Compound name or chemical formula

        Returns:
            List of element symbols (e.g., ["N", "S"])

        Examples:
            >>> extractor = ElementExtractor()
            >>> extractor.extract_all("(NH₄)₂SO₄")
            ['N', 'S']
            >>> extractor.extract_all("FeSO₄·7H₂O")
            ['Fe', 'S']
        """
        if not compound:
            return []

        # Remove hydration
        formula = re.sub(r"[·\.]\d*[Hh]₂?[Oo]₂?", "", compound)

        # Find all elements
        elements = self._find_elements_in_formula(formula)

        # Sort by priority
        priority_dict = {elem: i for i, elem in enumerate(self.ELEMENT_PRIORITY)}
        sorted_elements = sorted(
            elements,
            key=lambda x: priority_dict.get(x, len(self.ELEMENT_PRIORITY))
        )

        return sorted_elements

    def get_element_class(self, element: str) -> str:
        """
        Get the functional class of an element.

        Args:
            element: Element symbol (e.g., "Fe", "Mg")

        Returns:
            Element class: "trace_metal", "macronutrient", "rare_earth", or "other"

        Examples:
            >>> extractor = ElementExtractor()
            >>> extractor.get_element_class("Fe")
            'trace_metal'
            >>> extractor.get_element_class("Mg")
            'macronutrient'
        """
        if element in ["Fe", "Zn", "Mn", "Cu", "Co", "Mo", "Ni", "Se", "W"]:
            return "trace_metal"
        elif element in ["Mg", "Ca", "K", "Na", "P", "S", "N"]:
            return "macronutrient"
        elif element in ["Dy", "Nd", "Pr", "La", "Ce", "Eu", "Sm", "Gd"]:
            return "rare_earth"
        else:
            return "other"

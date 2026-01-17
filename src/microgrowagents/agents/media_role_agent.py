"""
Media Role Assignment Agent.

This agent classifies media ingredient functional roles in growth media using
hierarchical pattern matching. Can be used for single queries or batch CSV processing.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import pandas as pd

from microgrowagents.agents.base_agent import BaseAgent


class MediaRoleAgent(BaseAgent):
    """
    Classify ingredient functional roles in growth media.

    This agent determines the media role of ingredients (pH buffer, trace element,
    carbon source, etc.) using hierarchical pattern matching on ingredient names
    and chemical formulas.

    Examples:
        Query mode - single ingredient:
        >>> agent = MediaRoleAgent()
        >>> result = agent.run("query", ingredient_name="FeSO₄·7H₂O")
        >>> result["data"]["media_role"]
        'Trace Element (Fe)'

        Batch mode - process CSV:
        >>> result = agent.run(
        ...     "batch",
        ...     csv_path="data/raw/ingredients.csv",
        ...     output_path="data/processed/ingredients_with_roles.csv"
        ... )
        >>> result["data"]["total_ingredients"]
        20
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize MediaRoleAgent.

        Args:
            db_path: Optional path to DuckDB database (unused for this agent)
        """
        super().__init__(db_path)

    def run(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute media role classification.

        Args:
            query: "query" (single ingredient) or "batch" (CSV processing)
            **kwargs:
                For query mode:
                    - ingredient_name (str, required): Ingredient name or formula
                    - metabolic_role (str, optional): Metabolic role for fallback classification
                For batch mode:
                    - csv_path (str, required): Path to input CSV file
                    - output_path (str, optional): Path to output CSV (auto-generated if not provided)
                    - report_path (str, optional): Path to classification report markdown file

        Returns:
            Dictionary with success status, data, and metadata
            For query mode:
                {
                    "success": True,
                    "data": {
                        "ingredient": "FeSO₄·7H₂O",
                        "media_role": "Trace Element (Fe)",
                        "confidence": "high",
                        "method": "pattern_match"
                    }
                }
            For batch mode:
                {
                    "success": True,
                    "data": {
                        "output_path": "data/processed/ingredients_with_roles.csv",
                        "classification_report": "classification_report.md",
                        "total_ingredients": 20,
                        "classified": 20,
                        "unknown": 0
                    }
                }
        """
        if query == "query":
            return self._classify_single(**kwargs)
        elif query == "batch":
            return self._classify_batch(**kwargs)
        else:
            return {
                "success": False,
                "error": f"Unknown mode: {query}. Use 'query' or 'batch'."
            }

    def infer_media_role(
        self,
        component: str,
        metabolic_role: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Infer media role from component name and optional metabolic role.

        Uses hierarchical pattern matching in priority order:
        1. Rare earth elements (dysprosium, neodymium, etc.)
        2. Buffer compounds (PIPES, HEPES, MOPS, etc.)
        3. Phosphate sources (phosphate, HPO₄, H₂PO₄)
        4. Carbon sources (glucose, glycerol, methanol, etc.)
        5. Nitrogen + Sulfur sources ((NH₄)₂SO₄)
        6. Nitrogen sources (ammonium, urea, etc.)
        7. Chelators (citrate, EDTA)
        8. Sulfur sources (sulfate, cysteine)
        9. Essential macronutrients (Mg, Ca)
        10. Electrolytes (K, Na)
        11. Trace elements (Fe, Zn, Mn, Cu, Co, Mo, Ni, Se, W)
        12. Vitamins (thiamin, biotin, etc.)
        13. Tungsten cofactors
        14. Fallback based on metabolic role

        Args:
            component: Component name or chemical formula
            metabolic_role: Optional metabolic role description for fallback

        Returns:
            Tuple of (media_role: str, confidence: str)
            - media_role: Classification string (may be semicolon-separated for dual roles)
            - confidence: "high" (pattern match), "medium" (fallback), or "low" (unknown)

        Examples:
            >>> agent = MediaRoleAgent()
            >>> agent.infer_media_role("FeSO₄·7H₂O")
            ('Trace Element (Fe)', 'high')

            >>> agent.infer_media_role("K₂HPO₄")
            ('Phosphate Source; pH Buffer', 'high')

            >>> agent.infer_media_role("UnknownCompound")
            ('Unknown', 'low')
        """
        if component is None:
            return ("Unknown", "low")

        component_lower = component.lower()
        metabolic_lower = str(metabolic_role).lower() if pd.notna(metabolic_role) and metabolic_role else ""

        # 1. Rare earth elements (check first to avoid Se misclassification)
        rare_earth = [
            "dysprosium", "neodymium", "lanthanum", "cerium",
            "europium", "praseodymium", "samarium", "gadolinium"
        ]
        if any(re in component_lower for re in rare_earth):
            return ("Rare Earth Element", "high")

        # 2. Buffer compounds
        buffers = ["pipes", "hepes", "mes", "mops", "tris", "bicarbonate"]
        if any(b in component_lower for b in buffers):
            return ("pH Buffer", "high")

        # 3. Phosphate sources (check before potassium/sodium)
        phosphate_patterns = [
            "phosphate", "hpo4", "h2po4",
            "₂hpo₄", "h₂po₄", "hpo₄"
        ]
        if any(p in component_lower for p in phosphate_patterns):
            return ("Phosphate Source; pH Buffer", "high")

        # 4. Carbon sources
        carbon_sources = [
            "glucose", "glycerol", "succinate", "methanol",
            "acetate", "pyruvate", "lactate", "citrate"
        ]
        if any(cs in component_lower for cs in carbon_sources):
            # Citrate is special case - it's both carbon source and chelator
            if "citrate" in component_lower:
                return ("Chelator; Metal Buffer", "high")
            return ("Carbon Source", "high")

        # 5. Nitrogen AND Sulfur sources (ammonium sulfate)
        nh4_so4_patterns = ["(nh4)2so4", "(nh₄)₂so₄", "ammonium sulfate"]
        if any(p in component_lower for p in nh4_so4_patterns):
            return ("Nitrogen Source; Sulfur Source", "high")

        # 5b. Check for ammonium molybdate BEFORE general nitrogen check
        if "mo7o24" in component_lower or "mo₇o₂₄" in component_lower:
            return ("Trace Element (Mo)", "high")

        # 6. Nitrogen sources
        nitrogen_patterns = [
            "nh4", "nh₄", "ammonium", "glutamate", "glutamine", "urea"
        ]
        if any(n in component_lower for n in nitrogen_patterns):
            return ("Nitrogen Source", "high")

        # 7. Chelator/citrate (already handled citrate above, check EDTA)
        if "edta" in component_lower:
            return ("Chelator; Metal Buffer", "high")

        # 8. Essential metals (high concentration) - Mg and Ca
        if "mgcl" in component_lower or ("mg" in component_lower and "cl" in component_lower and len(component_lower) < 15):
            return ("Essential Macronutrient (Mg)", "high")
        elif "cacl" in component_lower or ("ca" in component_lower and "cl" in component_lower and len(component_lower) < 15):
            return ("Essential Macronutrient (Ca)", "high")

        # 9. Electrolytes (K, Na) - check after phosphates
        if component_lower.startswith("k") and "cl" in component_lower:
            return ("Electrolyte (K)", "high")
        elif component_lower.startswith("na") and "cl" in component_lower:
            return ("Electrolyte (Na)", "high")

        # 10. Trace metals (check BEFORE sulfur sources to avoid misclassification)
        # Note: Molybdenum is checked earlier (before nitrogen check)
        trace_metals = [
            ("feso4", "Fe"), ("feso₄", "Fe"),
            ("znso4", "Zn"), ("znso₄", "Zn"),
            ("mncl", "Mn"),
            ("cuso4", "Cu"), ("cuso₄", "Cu"),
            ("cocl", "Co"),
            ("nicl", "Ni"),
            ("na2seo3", "Se"), ("na₂seo₃", "Se"), ("selenite", "Se"),
        ]
        for pattern, metal_name in trace_metals:
            if pattern in component_lower:
                # Avoid false positives for Co (e.g., "cofactor", "compound")
                if metal_name == "Co" and len(component_lower) > 10:
                    continue
                # Avoid false positives for Mo in "compound", "mops"
                if metal_name == "Mo" and ("mops" in component_lower or "compound" in component_lower):
                    continue
                return (f"Trace Element ({metal_name})", "high")

        # 11. Vitamins
        vitamins = [
            "thiamin", "biotin", "riboflavin", "pyridoxine", "cobalamin",
            "nicotinamide", "pantothenate", "folate", "vitamin"
        ]
        if any(vit in component_lower for vit in vitamins):
            return ("Vitamin/Cofactor Precursor", "high")

        # 12. Tungsten
        if "wo4" in component_lower or "wo₄" in component_lower or "tungstate" in component_lower:
            return ("Trace Element (W); Cofactor", "high")

        # 13. Sulfur sources (check AFTER trace metals to avoid misclassifying FeSO4, ZnSO4, etc.)
        sulfur_patterns = ["sulfate", "so4", "so₄", "cysteine", "thiosulfate"]
        if any(s in component_lower for s in sulfur_patterns):
            return ("Sulfur Source", "high")

        # 14. Fallback: check metabolic role
        if metabolic_lower:
            if "buffer" in metabolic_lower:
                return ("pH Buffer", "medium")
            elif "essential" in metabolic_lower or "atp" in metabolic_lower:
                return ("Essential Nutrient", "medium")
            elif "cofactor" in metabolic_lower or "enzyme" in metabolic_lower:
                return ("Cofactor/Enzyme Activator", "medium")

        # Unknown
        return ("Unknown", "low")

    def _classify_single(
        self,
        ingredient_name: Optional[str] = None,
        metabolic_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classify a single ingredient.

        Args:
            ingredient_name: Ingredient name or formula (required)
            metabolic_role: Optional metabolic role for fallback classification

        Returns:
            Dictionary with classification results
        """
        if ingredient_name is None:
            return {
                "success": False,
                "error": "Missing required parameter: ingredient_name"
            }

        media_role, confidence = self.infer_media_role(ingredient_name, metabolic_role)

        return {
            "success": True,
            "data": {
                "ingredient": ingredient_name,
                "media_role": media_role,
                "confidence": confidence,
                "method": "pattern_match"
            }
        }

    def _classify_batch(
        self,
        csv_path: Optional[str] = None,
        output_path: Optional[str] = None,
        report_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classify all ingredients in a CSV file.

        Args:
            csv_path: Path to input CSV file (required)
            output_path: Path to output CSV file (optional, auto-generated if not provided)
            report_path: Path to classification report markdown file (optional)

        Returns:
            Dictionary with batch processing results
        """
        if csv_path is None:
            return {
                "success": False,
                "error": "Missing required parameter: csv_path"
            }

        csv_path_obj = Path(csv_path)
        if not csv_path_obj.exists():
            return {
                "success": False,
                "error": f"CSV file not found: {csv_path}"
            }

        try:
            # Read input CSV
            df = pd.read_csv(csv_path_obj)

            # Verify required columns
            if "Component" not in df.columns:
                return {
                    "success": False,
                    "error": "CSV must contain 'Component' column"
                }

            # Add Media Role column
            media_roles = []
            confidences = []
            for idx, row in df.iterrows():
                component = row.get("Component", "")
                metabolic_role = row.get("Metabolic Role", None)
                media_role, confidence = self.infer_media_role(component, metabolic_role)
                media_roles.append(media_role)
                confidences.append(confidence)

            # Insert Media Role columns after Component column
            component_idx = df.columns.get_loc("Component")
            df.insert(component_idx + 1, "Media Role", media_roles)
            df.insert(component_idx + 2, "Media Role DOI", "")

            # Rename "Metabolic Role" to "Cellular Role" if it exists
            if "Metabolic Role" in df.columns:
                df.rename(columns={"Metabolic Role": "Cellular Role"}, inplace=True)

            # Rename or create "Cellular Role DOI" column
            if "Metabolic Role DOI" in df.columns:
                df.rename(columns={"Metabolic Role DOI": "Cellular Role DOI"}, inplace=True)
            elif "Cellular Role" in df.columns:
                # If we renamed Metabolic Role but there's no Metabolic Role DOI, create empty DOI column
                cellular_role_idx = df.columns.get_loc("Cellular Role")
                df.insert(cellular_role_idx + 1, "Cellular Role DOI", "")

            # Generate output path if not provided
            if output_path is None:
                output_path_obj = csv_path_obj.parent / f"{csv_path_obj.stem}_with_roles.csv"
            else:
                output_path_obj = Path(output_path)

            # Save output CSV
            df.to_csv(output_path_obj, index=False)

            # Count classifications
            unknown_count = sum(1 for role in media_roles if role == "Unknown")
            classified_count = len(media_roles) - unknown_count

            # Generate classification report if requested
            report_path_result = None
            if report_path:
                report_path_obj = Path(report_path)
                self._generate_report(df, media_roles, report_path_obj)
                report_path_result = str(report_path_obj)

            return {
                "success": True,
                "data": {
                    "output_path": str(output_path_obj),
                    "classification_report": report_path_result,
                    "total_ingredients": len(media_roles),
                    "classified": classified_count,
                    "unknown": unknown_count
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error processing CSV: {str(e)}"
            }

    def _generate_report(
        self,
        df: pd.DataFrame,
        media_roles: list,
        report_path: Path
    ) -> None:
        """
        Generate classification report.

        Args:
            df: DataFrame with classified data
            media_roles: List of media role classifications
            report_path: Path to save report
        """
        report = []
        report.append("# Media Role Classification Report")
        report.append("")
        report.append("## Summary")
        report.append("")

        # Count media roles
        role_counts = pd.Series(media_roles).value_counts()
        report.append(f"**Total components:** {len(media_roles)}")
        report.append(f"**Unique media roles:** {len(role_counts)}")
        report.append("")

        report.append("## Media Role Distribution")
        report.append("")
        report.append("| Media Role | Count |")
        report.append("|------------|-------|")

        for role, count in role_counts.items():
            report.append(f"| {role} | {count} |")

        report.append("")

        # List components by role
        report.append("## Components by Media Role")
        report.append("")

        for role in sorted(role_counts.index):
            components = df[df["Media Role"] == role]["Component"].tolist()
            report.append(f"### {role}")
            report.append("")
            for comp in components:
                report.append(f"- {comp}")
            report.append("")

        with open(report_path, "w") as f:
            f.write("\n".join(report))

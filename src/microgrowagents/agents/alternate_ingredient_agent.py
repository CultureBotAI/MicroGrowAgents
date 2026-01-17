"""
Alternate Ingredient Recommendation Agent.

This agent recommends substitute ingredients for media components using multiple
data sources: KG-Microbe database, literature search, and built-in chemical knowledge.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import duckdb

from microgrowagents.agents.base_agent import BaseAgent
from microgrowagents.agents.media_role_agent import MediaRoleAgent
from microgrowagents.chemistry.element_extractor import ElementExtractor


class AlternateIngredientAgent(BaseAgent):
    """
    Recommend substitute ingredients with rationale and evidence.

    This agent searches multiple sources to find alternate ingredients that can
    substitute for a given media component:
    1. KG-Microbe DuckDB (search by element/functional group)
    2. Literature search (via LiteratureAgent)
    3. Built-in chemical knowledge

    Examples:
        Query mode - single ingredient:
        >>> agent = AlternateIngredientAgent()
        >>> result = agent.run("query", ingredient_name="FeSO₄·7H₂O", max_alternates=5)
        >>> for alt in result["data"]["alternates"]:
        ...     print(f"{alt['alternate_ingredient']}: {alt['rationale']}")

        Batch mode - process CSV:
        >>> result = agent.run(
        ...     "batch",
        ...     csv_path="ingredients.csv",
        ...     output_path="alternates.csv"
        ... )
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize AlternateIngredientAgent.

        Args:
            db_path: Path to DuckDB database with KG-Microbe data
        """
        super().__init__(db_path)

        # Initialize dependencies
        self.role_agent = MediaRoleAgent(db_path)
        self.element_extractor = ElementExtractor()

        # Verify database
        self._verify_kg_tables()

    def run(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Execute alternate ingredient recommendation.

        Args:
            query: "query" (single ingredient) or "batch" (CSV processing)
            **kwargs:
                For query mode:
                    - ingredient_name (str, required): Ingredient name or formula
                    - max_alternates (int, optional): Maximum number of alternates to return (default: 5)
                For batch mode:
                    - csv_path (str, required): Path to input CSV file
                    - output_path (str, optional): Path to output CSV (auto-generated if not provided)

        Returns:
            Dictionary with success status, data, and metadata
            For query mode:
                {
                    "success": True,
                    "data": {
                        "ingredient": "FeSO₄·7H₂O",
                        "ingredient_role": "Trace Element (Fe)",
                        "alternates": [
                            {
                                "alternate_ingredient": "FeCl₃·6H₂O",
                                "rationale": "Alternative iron(III) source...",
                                "alternate_role": "Trace Element (Fe)",
                                "doi_citation": "10.1128/AEM.01234-15",
                                "kg_node_id": "CHEBI:30916",
                                "kg_node_label": "iron(3+) chloride hexahydrate",
                                "source": "kg_microbe"
                            }
                        ]
                    }
                }
        """
        if query == "query":
            return self._recommend_single(**kwargs)
        elif query == "batch":
            return self._recommend_batch(**kwargs)
        else:
            return {
                "success": False,
                "error": f"Unknown mode: {query}. Use 'query' or 'batch'."
            }

    def _recommend_single(
        self,
        ingredient_name: Optional[str] = None,
        max_alternates: int = 5
    ) -> Dict[str, Any]:
        """
        Recommend alternates for a single ingredient.

        Process:
        1. Get ingredient role (via MediaRoleAgent)
        2. Extract key element/functional group
        3. Search KG-Microbe for chemicals with same element
        4. Add built-in knowledge recommendations
        5. Rank and deduplicate
        6. Add KG node IDs and labels
        7. Format with rationale and citations

        Args:
            ingredient_name: Ingredient name or formula (required)
            max_alternates: Maximum number of alternates to return

        Returns:
            Dictionary with recommendation results
        """
        if ingredient_name is None:
            return {
                "success": False,
                "error": "Missing required parameter: ingredient_name"
            }

        if not ingredient_name or not ingredient_name.strip():
            return {
                "success": False,
                "error": "Ingredient name cannot be empty"
            }

        try:
            # Step 1: Get ingredient role
            role_result = self.role_agent.run("query", ingredient_name=ingredient_name)
            ingredient_role = role_result.get("data", {}).get("media_role", "Unknown")

            # Step 2: Extract key element
            element = self.element_extractor.extract(ingredient_name)

            # Step 3: Collect recommendations from all sources
            alternates = []

            # Source 1: KG-Microbe database search
            if element:
                kg_alternates = self._search_kg_by_element(element, ingredient_name)
                alternates.extend(kg_alternates)

            # Source 2: Built-in knowledge
            builtin_alternates = self._builtin_recommendations(ingredient_name, ingredient_role)
            alternates.extend(builtin_alternates)

            # Step 4: Deduplicate and rank
            alternates = self._deduplicate_and_rank(alternates, element)

            # Step 5: Limit to max_alternates
            alternates = alternates[:max_alternates]

            # Step 6: Add KG node information
            for alt in alternates:
                if "kg_node_id" not in alt or not alt["kg_node_id"]:
                    node_info = self.find_kg_node(alt["alternate_ingredient"])
                    if node_info:
                        alt["kg_node_id"] = node_info["node_id"]
                        alt["kg_node_label"] = node_info["node_label"]
                    else:
                        alt["kg_node_id"] = None
                        alt["kg_node_label"] = None

            return {
                "success": True,
                "data": {
                    "ingredient": ingredient_name,
                    "ingredient_role": ingredient_role,
                    "element": element,
                    "alternates": alternates
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating recommendations: {str(e)}"
            }

    def _recommend_batch(
        self,
        csv_path: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recommend alternates for all ingredients in a CSV file.

        Args:
            csv_path: Path to input CSV file (required)
            output_path: Path to output CSV file (optional, auto-generated if not provided)

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

            # Generate output path if not provided
            if output_path is None:
                output_path_obj = csv_path_obj.parent / f"{csv_path_obj.stem}_alternates.csv"
            else:
                output_path_obj = Path(output_path)

            # Collect all alternates
            all_alternates = []
            total_ingredients = len(df)
            ingredients_with_alternates = 0

            for idx, row in df.iterrows():
                ingredient_name = row.get("Component", "")

                # Get alternates for this ingredient
                result = self._recommend_single(ingredient_name, max_alternates=5)

                if result["success"] and result["data"]["alternates"]:
                    ingredients_with_alternates += 1

                    for alt in result["data"]["alternates"]:
                        all_alternates.append({
                            "Ingredient": ingredient_name,
                            "Alternate Ingredient": alt["alternate_ingredient"],
                            "Rationale": alt["rationale"],
                            "Alternate Role": alt["alternate_role"],
                            "DOI Citation": alt.get("doi_citation", ""),
                            "KG Node ID": alt.get("kg_node_id", ""),
                            "KG Node Label": alt.get("kg_node_label", "")
                        })

            # Create output DataFrame
            df_output = pd.DataFrame(all_alternates)

            # Save to CSV
            df_output.to_csv(output_path_obj, index=False)

            return {
                "success": True,
                "data": {
                    "output_path": str(output_path_obj),
                    "total_ingredients": total_ingredients,
                    "alternates_found": ingredients_with_alternates,
                    "total_recommendations": len(all_alternates)
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error processing CSV: {str(e)}"
            }

    def _search_kg_by_element(
        self,
        element: str,
        exclude_ingredient: str
    ) -> List[Dict[str, Any]]:
        """
        Search KG-Microbe for chemicals with the same element.

        Args:
            element: Element symbol (e.g., "Fe", "Mg")
            exclude_ingredient: Ingredient to exclude from results

        Returns:
            List of alternate recommendations from KG
        """
        if not self.validate_database():
            return []

        try:
            conn = duckdb.connect(str(self.db_path), read_only=True)

            # Search for chemicals containing the element
            query = """
            SELECT DISTINCT n.id, n.name, n.category
            FROM kg_nodes n
            WHERE n.category = 'biolink:ChemicalSubstance'
              AND (LOWER(n.name) LIKE ?
                   OR LOWER(n.name) LIKE ?
                   OR LOWER(n.name) LIKE ?)
              AND LOWER(n.name) NOT LIKE ?
            LIMIT 10
            """

            element_lower = element.lower()
            element_patterns = [
                f"%{element_lower}%",
                f"%{element}%",
                f"%{self._get_element_name(element).lower()}%"
            ]

            exclude_pattern = f"%{exclude_ingredient.lower()}%"

            results = conn.execute(
                query,
                [*element_patterns, exclude_pattern]
            ).fetchall()

            conn.close()

            alternates = []
            for row in results:
                node_id, name, category = row
                alternates.append({
                    "alternate_ingredient": name,
                    "rationale": f"Contains {element} like the original ingredient, found in KG-Microbe database",
                    "alternate_role": f"Trace Element ({element})" if element in ["Fe", "Zn", "Mn", "Cu", "Co", "Mo"] else "Similar Element Source",
                    "doi_citation": "",
                    "kg_node_id": node_id,
                    "kg_node_label": name,
                    "source": "kg_microbe"
                })

            return alternates

        except Exception as e:
            self.log(f"Error searching KG by element: {str(e)}", level="WARNING")
            return []

    def _builtin_recommendations(
        self,
        ingredient_name: str,
        role: str
    ) -> List[Dict[str, Any]]:
        """
        Built-in chemical knowledge for common substitutions.

        Args:
            ingredient_name: Ingredient name or formula
            role: Media role of the ingredient

        Returns:
            List of alternate recommendations from built-in knowledge
        """
        recommendations = []

        # Extract element for element-specific recommendations
        element = self.element_extractor.extract(ingredient_name)

        # Trace metals - recommend other salts of the same metal
        if "Trace Element" in role and element:
            if element == "Fe":
                recommendations.extend([
                    {
                        "alternate_ingredient": "FeCl₃·6H₂O",
                        "rationale": "Alternative iron(III) source with higher solubility in acidic conditions",
                        "alternate_role": "Trace Element (Fe)",
                        "doi_citation": "",
                        "source": "builtin"
                    },
                    {
                        "alternate_ingredient": "Ferric citrate",
                        "rationale": "Chelated iron source that reduces precipitation with phosphate",
                        "alternate_role": "Trace Element (Fe); Chelator",
                        "doi_citation": "",
                        "source": "builtin"
                    },
                    {
                        "alternate_ingredient": "Fe-EDTA",
                        "rationale": "Stable chelated iron that remains soluble across pH ranges",
                        "alternate_role": "Trace Element (Fe); Chelator",
                        "doi_citation": "",
                        "source": "builtin"
                    }
                ])
            elif element == "Zn":
                recommendations.extend([
                    {
                        "alternate_ingredient": "ZnCl₂",
                        "rationale": "Alternative zinc source with higher solubility",
                        "alternate_role": "Trace Element (Zn)",
                        "doi_citation": "",
                        "source": "builtin"
                    },
                    {
                        "alternate_ingredient": "Zinc acetate",
                        "rationale": "Well-soluble zinc source used in microbial culture",
                        "alternate_role": "Trace Element (Zn)",
                        "doi_citation": "",
                        "source": "builtin"
                    }
                ])
            elif element == "Mg":
                recommendations.extend([
                    {
                        "alternate_ingredient": "MgSO₄·7H₂O",
                        "rationale": "Alternative magnesium source that also provides sulfate",
                        "alternate_role": "Essential Macronutrient (Mg); Sulfur Source",
                        "doi_citation": "",
                        "source": "builtin"
                    }
                ])
            elif element == "Ca":
                recommendations.extend([
                    {
                        "alternate_ingredient": "CaSO₄",
                        "rationale": "Alternative calcium source with lower solubility (useful for controlled release)",
                        "alternate_role": "Essential Macronutrient (Ca)",
                        "doi_citation": "",
                        "source": "builtin"
                    }
                ])
            elif element == "Cu":
                recommendations.extend([
                    {
                        "alternate_ingredient": "CuCl₂·2H₂O",
                        "rationale": "Alternative copper source with different counterion",
                        "alternate_role": "Trace Element (Cu)",
                        "doi_citation": "",
                        "source": "builtin"
                    }
                ])
            elif element == "Mn":
                recommendations.extend([
                    {
                        "alternate_ingredient": "MnSO₄·H₂O",
                        "rationale": "Alternative manganese source that also provides sulfate",
                        "alternate_role": "Trace Element (Mn); Sulfur Source",
                        "doi_citation": "",
                        "source": "builtin"
                    }
                ])

        # pH Buffers
        elif "pH Buffer" in role or "Buffer" in role:
            recommendations.extend([
                {
                    "alternate_ingredient": "HEPES",
                    "rationale": "Good buffer at pH 6.8-8.2, commonly used in biological applications",
                    "alternate_role": "pH Buffer",
                    "doi_citation": "",
                    "source": "builtin"
                },
                {
                    "alternate_ingredient": "MOPS",
                    "rationale": "Effective buffer at pH 6.5-7.9, minimal metal binding",
                    "alternate_role": "pH Buffer",
                    "doi_citation": "",
                    "source": "builtin"
                },
                {
                    "alternate_ingredient": "Tris",
                    "rationale": "Widely used buffer at pH 7-9, temperature-sensitive",
                    "alternate_role": "pH Buffer",
                    "doi_citation": "",
                    "source": "builtin"
                },
                {
                    "alternate_ingredient": "MES",
                    "rationale": "Effective buffer at pH 5.5-6.7, useful for acidic conditions",
                    "alternate_role": "pH Buffer",
                    "doi_citation": "",
                    "source": "builtin"
                }
            ])

        # Carbon Sources
        elif "Carbon Source" in role:
            recommendations.extend([
                {
                    "alternate_ingredient": "Glucose",
                    "rationale": "Common carbon and energy source for heterotrophic growth",
                    "alternate_role": "Carbon Source",
                    "doi_citation": "",
                    "source": "builtin"
                },
                {
                    "alternate_ingredient": "Glycerol",
                    "rationale": "Alternative carbon source, often used for slower growth",
                    "alternate_role": "Carbon Source",
                    "doi_citation": "",
                    "source": "builtin"
                },
                {
                    "alternate_ingredient": "Acetate",
                    "rationale": "Simple carbon source for acetate-utilizing organisms",
                    "alternate_role": "Carbon Source",
                    "doi_citation": "",
                    "source": "builtin"
                }
            ])

        # Nitrogen Sources
        elif "Nitrogen Source" in role:
            recommendations.extend([
                {
                    "alternate_ingredient": "NH₄Cl",
                    "rationale": "Simple ammonium source without sulfate",
                    "alternate_role": "Nitrogen Source",
                    "doi_citation": "",
                    "source": "builtin"
                },
                {
                    "alternate_ingredient": "(NH₄)₂SO₄",
                    "rationale": "Dual nitrogen and sulfur source",
                    "alternate_role": "Nitrogen Source; Sulfur Source",
                    "doi_citation": "",
                    "source": "builtin"
                },
                {
                    "alternate_ingredient": "Urea",
                    "rationale": "Organic nitrogen source, hydrolyzed to ammonia by urease",
                    "alternate_role": "Nitrogen Source",
                    "doi_citation": "",
                    "source": "builtin"
                }
            ])

        # Phosphate Sources
        elif "Phosphate" in role:
            recommendations.extend([
                {
                    "alternate_ingredient": "KH₂PO₄",
                    "rationale": "Alternative phosphate source with different pH buffering",
                    "alternate_role": "Phosphate Source; pH Buffer",
                    "doi_citation": "",
                    "source": "builtin"
                },
                {
                    "alternate_ingredient": "Na₂HPO₄",
                    "rationale": "Alternative phosphate source, more basic pH buffering",
                    "alternate_role": "Phosphate Source; pH Buffer",
                    "doi_citation": "",
                    "source": "builtin"
                }
            ])

        return recommendations

    def _deduplicate_and_rank(
        self,
        alternates: List[Dict[str, Any]],
        element: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate and rank alternate recommendations.

        Ranking priority:
        1. KG-Microbe database matches (highest confidence)
        2. Built-in recommendations with element match
        3. Built-in recommendations by role

        Args:
            alternates: List of alternate recommendations
            element: Primary element of original ingredient

        Returns:
            Deduplicated and ranked list of alternates
        """
        # Deduplicate by alternate ingredient name (case-insensitive)
        seen = set()
        unique_alternates = []

        for alt in alternates:
            name_lower = alt["alternate_ingredient"].lower()
            if name_lower not in seen:
                seen.add(name_lower)
                unique_alternates.append(alt)

        # Rank by source and element match
        def rank_key(alt):
            score = 0

            # Source priority
            if alt.get("source") == "kg_microbe":
                score += 100
            elif alt.get("source") == "builtin":
                score += 50

            # Element match bonus
            if element:
                alt_element = self.element_extractor.extract(alt["alternate_ingredient"])
                if alt_element == element:
                    score += 30

            return -score  # Negative for descending order

        ranked_alternates = sorted(unique_alternates, key=rank_key)

        return ranked_alternates

    def find_kg_node(self, ingredient_name: str) -> Optional[Dict[str, str]]:
        """
        Find KG-Microbe node with hierarchical matching.

        Priority order:
        1. Exact name match
        2. Synonym match
        3. Fuzzy match

        Args:
            ingredient_name: Ingredient name to search for

        Returns:
            Dictionary with node_id and node_label, or None if not found
        """
        if not self.validate_database():
            return None

        try:
            conn = duckdb.connect(str(self.db_path), read_only=True)

            # Method 1: Exact name match
            query = """
            SELECT id, name FROM kg_nodes
            WHERE LOWER(name) = LOWER(?)
              AND category = 'biolink:ChemicalSubstance'
            LIMIT 1
            """
            result = conn.execute(query, [ingredient_name]).fetchone()

            if result:
                conn.close()
                return {"node_id": result[0], "node_label": result[1]}

            # Method 2: Synonym match (if synonym column exists)
            query = """
            SELECT id, name FROM kg_nodes
            WHERE category = 'biolink:ChemicalSubstance'
              AND (LOWER(synonym) LIKE LOWER(?) OR LOWER(name) LIKE LOWER(?))
            LIMIT 1
            """
            result = conn.execute(query, [f"%{ingredient_name}%", f"%{ingredient_name}%"]).fetchone()

            conn.close()

            if result:
                return {"node_id": result[0], "node_label": result[1]}

            return None

        except Exception as e:
            self.log(f"Error finding KG node: {str(e)}", level="WARNING")
            return None

    def _get_element_name(self, symbol: str) -> str:
        """
        Get element name from symbol.

        Args:
            symbol: Element symbol (e.g., "Fe")

        Returns:
            Element name (e.g., "iron")
        """
        element_map = {
            "Fe": "iron",
            "Zn": "zinc",
            "Mn": "manganese",
            "Cu": "copper",
            "Co": "cobalt",
            "Mo": "molybdenum",
            "Ni": "nickel",
            "Se": "selenium",
            "W": "tungsten",
            "Mg": "magnesium",
            "Ca": "calcium",
            "K": "potassium",
            "Na": "sodium",
            "P": "phosphorus",
            "S": "sulfur",
            "N": "nitrogen"
        }
        return element_map.get(symbol, symbol.lower())

    def _verify_kg_tables(self) -> None:
        """Check that kg_nodes and kg_edges tables exist."""
        if not self.validate_database():
            self.log(
                "KG tables not available. Some features will be limited.",
                level="WARNING"
            )

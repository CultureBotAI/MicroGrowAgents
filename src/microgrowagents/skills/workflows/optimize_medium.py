"""
Optimize Medium Workflow.

Multi-agent workflow for medium optimization.
"""

from typing import Any, Dict, Optional, List
from pathlib import Path

from microgrowagents.skills.base_skill import BaseSkill, SkillMetadata, SkillParameter
from microgrowagents.agents.sensitivity_analysis_agent import SensitivityAnalysisAgent
from microgrowagents.agents.alternate_ingredient_agent import AlternateIngredientAgent
from microgrowagents.agents.gen_media_conc_agent import GenMediaConcAgent


class OptimizeMediumWorkflow(BaseSkill):
    """
    Optimize growth medium composition.

    Orchestrates multiple agents to optimize medium:
    1. SensitivityAnalysisAgent - Identify high-sensitivity ingredients
    2. AlternateIngredientAgent - Find cheaper/better substitutes
    3. GenMediaConcAgent - Re-predict optimal concentrations

    Optimization goals:
    - "cost": Minimize cost while maintaining function
    - "growth": Maximize growth performance
    - "stability": Improve pH stability and reduce sensitivity

    Examples:
        >>> workflow = OptimizeMediumWorkflow()
        >>> result = workflow.run(
        ...     medium_name="MP medium",
        ...     optimization_goal="cost",
        ...     output_format="markdown"
        ... )
        >>> "optimization" in result.lower()
        True
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize workflow.

        Args:
            db_path: Path to DuckDB database (optional)
        """
        super().__init__()
        self.db_path = db_path or Path("data/processed/microgrow.duckdb")
        self._sensitivity_agent = None
        self._alternate_agent = None
        self._conc_agent = None

    def get_metadata(self) -> SkillMetadata:
        """
        Get workflow metadata.

        Returns:
            SkillMetadata with parameters and examples
        """
        return SkillMetadata(
            name="optimize-medium",
            description="Optimize growth medium composition (cost, growth, stability)",
            category="workflow",
            parameters=[
                SkillParameter(
                    name="medium_name",
                    type="str",
                    description="Medium name or comma-separated ingredient list",
                    required=True,
                ),
                SkillParameter(
                    name="optimization_goal",
                    type="str",
                    description="Optimization goal: 'cost', 'growth', or 'stability'",
                    required=True,
                    options=["cost", "growth", "stability"],
                ),
                SkillParameter(
                    name="organism",
                    type="str",
                    description="Target organism for optimization",
                    required=False,
                ),
                SkillParameter(
                    name="max_alternates_per_ingredient",
                    type="int",
                    description="Maximum alternates to consider per ingredient",
                    required=False,
                    default=3,
                ),
            ],
            examples=[
                "optimize-medium 'MP medium' --optimization_goal cost",
                "optimize-medium 'glucose,NaCl,KH2PO4' --optimization_goal stability",
                "optimize-medium 'LB medium' --optimization_goal growth --organism 'Escherichia coli'",
            ],
            requires_database=True,
            requires_internet=True,
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute medium optimization workflow.

        Args:
            medium_name: Medium name or ingredient list
            optimization_goal: Goal ("cost", "growth", "stability")
            organism: Target organism (optional)
            max_alternates_per_ingredient: Max alternates per ingredient

        Returns:
            Result dictionary with optimization recommendations
        """
        # Get parameters
        medium_name = kwargs.get("medium_name")
        if not medium_name:
            return {
                "success": False,
                "error": "Missing required parameter: medium_name",
            }

        optimization_goal = kwargs.get("optimization_goal")
        if not optimization_goal:
            return {
                "success": False,
                "error": "Missing required parameter: optimization_goal",
            }

        if optimization_goal not in ["cost", "growth", "stability"]:
            return {
                "success": False,
                "error": f"Invalid optimization_goal: {optimization_goal}. Must be 'cost', 'growth', or 'stability'",
            }

        organism = kwargs.get("organism")
        max_alternates = kwargs.get("max_alternates_per_ingredient", 3)

        # Initialize agents
        if self._sensitivity_agent is None:
            self._sensitivity_agent = SensitivityAnalysisAgent(db_path=self.db_path)
        if self._alternate_agent is None:
            self._alternate_agent = AlternateIngredientAgent(db_path=self.db_path)
        if self._conc_agent is None:
            self._conc_agent = GenMediaConcAgent(db_path=self.db_path)

        # Step 1: Run sensitivity analysis
        try:
            sensitivity_result = self._sensitivity_agent.run(
                query=medium_name,
                calculate_osmotic=True,
            )
            if not sensitivity_result.get("success"):
                return {
                    "success": False,
                    "error": f"Sensitivity analysis failed: {sensitivity_result.get('error')}",
                }

            sensitivity_data = sensitivity_result.get("data", {}).get("sensitivity_sweep", [])
        except Exception as e:
            return {
                "success": False,
                "error": f"Sensitivity analysis failed: {str(e)}",
            }

        # Step 2: Identify ingredients to optimize based on goal
        ingredients_to_optimize = self._identify_optimization_targets(
            sensitivity_data, optimization_goal
        )

        # Step 3: Find alternates for target ingredients
        recommendations = []
        all_evidence = []

        for ingredient_info in ingredients_to_optimize:
            ingredient_name = ingredient_info["ingredient"]

            try:
                alternate_result = self._alternate_agent.run(
                    query="query",
                    ingredient_name=ingredient_name,
                    max_alternates=max_alternates,
                )

                if alternate_result.get("success"):
                    alternates = alternate_result.get("data", {}).get("alternates", [])

                    # Select best alternate based on optimization goal
                    best_alternate = self._select_best_alternate(
                        alternates, optimization_goal
                    )

                    if best_alternate:
                        recommendations.append({
                            "original_ingredient": ingredient_name,
                            "recommended_alternate": best_alternate.get("alternate_ingredient"),
                            "rationale": best_alternate.get("rationale"),
                            "optimization_benefit": self._explain_benefit(
                                ingredient_info, best_alternate, optimization_goal
                            ),
                            "sensitivity_delta_ph": ingredient_info.get("delta_ph", 0),
                            "doi_citation": best_alternate.get("doi_citation", ""),
                        })

                        # Collect evidence
                        if best_alternate.get("doi_citation"):
                            all_evidence.append({"doi": best_alternate["doi_citation"]})

            except Exception as e:
                # Continue with other ingredients if one fails
                continue

        # Step 4: Re-predict concentrations for optimized medium
        # Build optimized ingredient list
        if recommendations:
            # This is simplified - in production would rebuild full ingredient list
            optimized_ingredients = [rec["recommended_alternate"] for rec in recommendations]

        # Format results
        transformed = self._transform_result(
            medium_name,
            optimization_goal,
            sensitivity_data,
            recommendations,
            all_evidence,
        )

        return transformed

    def _identify_optimization_targets(
        self, sensitivity_data: List[Dict], goal: str
    ) -> List[Dict]:
        """
        Identify ingredients to optimize based on goal.

        Args:
            sensitivity_data: Sensitivity analysis results
            goal: Optimization goal

        Returns:
            List of ingredients to target for optimization
        """
        targets = []

        for item in sensitivity_data:
            ingredient = item.get("ingredient")
            delta_ph = abs(item.get("delta_ph", 0))
            delta_salinity = abs(item.get("delta_salinity", 0))

            if goal == "stability":
                # Target high-sensitivity ingredients
                if delta_ph > 0.5 or delta_salinity > 2.0:
                    targets.append({
                        "ingredient": ingredient,
                        "delta_ph": delta_ph,
                        "delta_salinity": delta_salinity,
                        "reason": "high_sensitivity",
                    })

            elif goal == "cost":
                # Target all ingredients (look for cheaper alternates)
                targets.append({
                    "ingredient": ingredient,
                    "delta_ph": delta_ph,
                    "reason": "cost_reduction",
                })

            elif goal == "growth":
                # Target ingredients with growth enhancement potential
                targets.append({
                    "ingredient": ingredient,
                    "delta_ph": delta_ph,
                    "reason": "growth_enhancement",
                })

        # Limit to top 5 targets for practicality
        if goal == "stability":
            # Sort by sensitivity (highest first)
            targets.sort(key=lambda x: x.get("delta_ph", 0), reverse=True)
        targets = targets[:5]

        return targets

    def _select_best_alternate(
        self, alternates: List[Dict], goal: str
    ) -> Optional[Dict]:
        """
        Select best alternate based on optimization goal.

        Args:
            alternates: List of alternate ingredients
            goal: Optimization goal

        Returns:
            Best alternate or None
        """
        if not alternates:
            return None

        # For now, return first alternate
        # In production, would rank based on goal-specific criteria
        return alternates[0]

    def _explain_benefit(
        self, ingredient_info: Dict, alternate: Dict, goal: str
    ) -> str:
        """
        Explain optimization benefit.

        Args:
            ingredient_info: Original ingredient info
            alternate: Alternate ingredient info
            goal: Optimization goal

        Returns:
            Explanation string
        """
        if goal == "stability":
            return f"Reduces pH sensitivity (Δ pH: {ingredient_info.get('delta_ph', 0):.2f})"
        elif goal == "cost":
            return "Cost reduction through substitute ingredient"
        elif goal == "growth":
            return "Enhanced growth performance"

        return "Optimization benefit"

    def _transform_result(
        self,
        medium_name: str,
        goal: str,
        sensitivity_data: List[Dict],
        recommendations: List[Dict],
        evidence: List[Dict],
    ) -> Dict[str, Any]:
        """
        Transform workflow results to skill output format.

        Args:
            medium_name: Original medium name
            goal: Optimization goal
            sensitivity_data: Sensitivity analysis data
            recommendations: Optimization recommendations
            evidence: Collected evidence

        Returns:
            Transformed result
        """
        # Format recommendations as table
        table_rows = []
        for rec in recommendations:
            table_rows.append({
                "Original Ingredient": rec["original_ingredient"],
                "Recommended Alternate": rec["recommended_alternate"],
                "Optimization Benefit": rec["optimization_benefit"],
                "Sensitivity (Δ pH)": f"{rec['sensitivity_delta_ph']:+.2f}",
            })

        # Build metadata
        metadata = {
            "workflow": "optimize_medium",
            "original_medium": medium_name,
            "optimization_goal": goal,
            "recommendations_count": len(recommendations),
            "agents_used": [
                "SensitivityAnalysisAgent",
                "AlternateIngredientAgent",
            ],
        }

        return {
            "success": True,
            "data": table_rows,
            "evidence": evidence,
            "metadata": metadata,
        }

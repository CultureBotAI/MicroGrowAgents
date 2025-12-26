"""
Sensitivity analysis visualization functions.

Creates comprehensive plots for media formulation sensitivity analysis.
"""

from typing import Dict, List
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import seaborn as sns


def generate_sensitivity_plots(
    result: Dict,
    output_path: str = "sensitivity_plot.png",
    figsize: tuple = (20, 12)
) -> None:
    """
    Generate comprehensive sensitivity analysis plots.

    Creates 6-panel figure:
    1. pH sensitivity bar chart
    2. TDS (Total Dissolved Solids) sensitivity bar chart
    3. NaCl salinity sensitivity bar chart
    4. Delta heatmap (pH, TDS, NaCl)
    5. pH vs TDS scatter plot
    6. pH vs NaCl scatter plot

    Args:
        result: Sensitivity analysis result dictionary from SensitivityAnalysisAgent
        output_path: Path to save the plot
        figsize: Figure size (width, height) in inches

    Examples:
        >>> from microgrowagents.agents.sensitivity_analysis_agent import SensitivityAnalysisAgent
        >>> agent = SensitivityAnalysisAgent()
        >>> result = agent.run("PIPES,NaCl", mode="ingredients")
        >>> if result["success"]:
        ...     generate_sensitivity_plots(result, "test_plot.png")  # doctest: +SKIP
    """
    fig, axes = plt.subplots(2, 3, figsize=figsize)

    # Extract data
    data = result["data"]
    baseline = result["baseline"]

    # 1. pH Sensitivity Bar Chart
    _plot_ph_sensitivity(axes[0, 0], data, baseline)

    # 2. TDS Sensitivity Bar Chart
    _plot_salinity_sensitivity(axes[0, 1], data, baseline)

    # 3. NaCl Salinity Sensitivity Bar Chart
    _plot_nacl_salinity_sensitivity(axes[0, 2], data, baseline)

    # 4. Delta Heatmap
    _plot_delta_heatmap(axes[1, 0], data)

    # 5. pH vs TDS Scatter
    _plot_ph_salinity_scatter(axes[1, 1], data, baseline)

    # 6. pH vs NaCl Salinity Scatter
    _plot_ph_nacl_scatter(axes[1, 2], data, baseline)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def _plot_ph_sensitivity(ax, data: List[Dict], baseline: Dict) -> None:
    """
    Plot pH sensitivity bar chart.

    Shows pH values at LOW and HIGH concentrations for each ingredient.

    Args:
        ax: Matplotlib axes object
        data: List of sensitivity results
        baseline: Baseline properties dictionary
    """
    # Group by ingredient
    ingredients = sorted(set(d["ingredient"] for d in data))

    low_vals = []
    high_vals = []

    for ing in ingredients:
        ing_data = [d for d in data if d["ingredient"] == ing]

        low = next((d["ph"] for d in ing_data if d["concentration_level"] == "low"), None)
        high = next((d["ph"] for d in ing_data if d["concentration_level"] == "high"), None)

        low_vals.append(low if low is not None else baseline["ph"])
        high_vals.append(high if high is not None else baseline["ph"])

    x = np.arange(len(ingredients))
    width = 0.35

    ax.bar(x - width/2, low_vals, width, label='Low', color='skyblue', edgecolor='black')
    ax.bar(x + width/2, high_vals, width, label='High', color='salmon', edgecolor='black')

    ax.axhline(y=baseline["ph"], color='green', linestyle='--',
               linewidth=2, label=f'Baseline ({baseline["ph"]:.2f})', zorder=0)

    ax.set_xlabel('Ingredient', fontsize=12, fontweight='bold')
    ax.set_ylabel('pH', fontsize=12, fontweight='bold')
    ax.set_title('pH Sensitivity Analysis', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(ingredients, rotation=45, ha='right')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle=':')


def _plot_salinity_sensitivity(ax, data: List[Dict], baseline: Dict) -> None:
    """
    Plot TDS (Total Dissolved Solids) sensitivity bar chart.

    Shows TDS values at LOW and HIGH concentrations for each ingredient.

    Args:
        ax: Matplotlib axes object
        data: List of sensitivity results
        baseline: Baseline properties dictionary
    """
    # Group by ingredient
    ingredients = sorted(set(d["ingredient"] for d in data))

    low_vals = []
    high_vals = []

    for ing in ingredients:
        ing_data = [d for d in data if d["ingredient"] == ing]

        low = next((d["salinity"] for d in ing_data if d["concentration_level"] == "low"), None)
        high = next((d["salinity"] for d in ing_data if d["concentration_level"] == "high"), None)

        low_vals.append(low if low is not None else baseline["salinity"])
        high_vals.append(high if high is not None else baseline["salinity"])

    x = np.arange(len(ingredients))
    width = 0.35

    ax.bar(x - width/2, low_vals, width, label='Low', color='skyblue', edgecolor='black')
    ax.bar(x + width/2, high_vals, width, label='High', color='salmon', edgecolor='black')

    ax.axhline(y=baseline["salinity"], color='green', linestyle='--',
               linewidth=2, label=f'Baseline ({baseline["salinity"]:.2f} g/L)', zorder=0)

    ax.set_xlabel('Ingredient', fontsize=12, fontweight='bold')
    ax.set_ylabel('TDS - Total Dissolved Solids (g/L)', fontsize=12, fontweight='bold')
    ax.set_title('TDS Sensitivity Analysis', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(ingredients, rotation=45, ha='right')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle=':')


def _plot_nacl_salinity_sensitivity(ax, data: List[Dict], baseline: Dict) -> None:
    """
    Plot NaCl salinity sensitivity bar chart.

    Shows NaCl salinity values at LOW and HIGH concentrations for each ingredient.

    Args:
        ax: Matplotlib axes object
        data: List of sensitivity results
        baseline: Baseline properties dictionary
    """
    # Group by ingredient
    ingredients = sorted(set(d["ingredient"] for d in data))

    low_vals = []
    high_vals = []

    for ing in ingredients:
        ing_data = [d for d in data if d["ingredient"] == ing]

        low = next((d["nacl_salinity"] for d in ing_data if d["concentration_level"] == "low"), None)
        high = next((d["nacl_salinity"] for d in ing_data if d["concentration_level"] == "high"), None)

        low_vals.append(low if low is not None else baseline["nacl_salinity"])
        high_vals.append(high if high is not None else baseline["nacl_salinity"])

    x = np.arange(len(ingredients))
    width = 0.35

    ax.bar(x - width/2, low_vals, width, label='Low', color='skyblue', edgecolor='black')
    ax.bar(x + width/2, high_vals, width, label='High', color='salmon', edgecolor='black')

    ax.axhline(y=baseline["nacl_salinity"], color='green', linestyle='--',
               linewidth=2, label=f'Baseline ({baseline["nacl_salinity"]:.2f} g/L)', zorder=0)

    ax.set_xlabel('Ingredient', fontsize=12, fontweight='bold')
    ax.set_ylabel('NaCl Salinity - Ionic Salts (g/L)', fontsize=12, fontweight='bold')
    ax.set_title('NaCl Salinity Sensitivity Analysis', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(ingredients, rotation=45, ha='right')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle=':')


def _plot_delta_heatmap(ax, data: List[Dict]) -> None:
    """
    Plot delta heatmap.

    Shows change from baseline for pH, TDS, and NaCl salinity at LOW and HIGH concentrations.

    Args:
        ax: Matplotlib axes object
        data: List of sensitivity results
    """
    ingredients = sorted(set(d["ingredient"] for d in data))

    # Build matrix
    matrix = []
    for ing in ingredients:
        ing_data = [d for d in data if d["ingredient"] == ing]

        low_data = next((d for d in ing_data if d["concentration_level"] == "low"), None)
        high_data = next((d for d in ing_data if d["concentration_level"] == "high"), None)

        row = [
            low_data["delta_ph"] if low_data else 0,
            high_data["delta_ph"] if high_data else 0,
            low_data["delta_salinity"] if low_data else 0,
            high_data["delta_salinity"] if high_data else 0,
            low_data["delta_nacl_salinity"] if low_data else 0,
            high_data["delta_nacl_salinity"] if high_data else 0,
        ]
        matrix.append(row)

    matrix = np.array(matrix)

    # Determine color scale limits based on data range
    vmax = max(abs(matrix.min()), abs(matrix.max()))
    vmax = max(vmax, 0.1)  # Ensure non-zero scale

    # Plot heatmap using seaborn for better aesthetics
    sns.heatmap(
        matrix,
        annot=True,
        fmt='.2f',
        cmap='RdBu_r',
        center=0,
        vmin=-vmax,
        vmax=vmax,
        xticklabels=['ΔpH\n(Low)', 'ΔpH\n(High)', 'ΔTDS\n(Low)', 'ΔTDS\n(High)', 'ΔNaCl\n(Low)', 'ΔNaCl\n(High)'],
        yticklabels=ingredients,
        cbar_kws={'label': 'Change from Baseline'},
        ax=ax,
        linewidths=0.5,
        linecolor='gray'
    )

    ax.set_title('Delta from Baseline Heatmap', fontsize=14, fontweight='bold')
    ax.set_xlabel('Metric', fontsize=12, fontweight='bold')
    ax.set_ylabel('Ingredient', fontsize=12, fontweight='bold')


def _plot_ph_salinity_scatter(ax, data: List[Dict], baseline: Dict) -> None:
    """
    Plot pH vs TDS scatter plot.

    Shows the relationship between pH and TDS for all concentration levels.

    Args:
        ax: Matplotlib axes object
        data: List of sensitivity results
        baseline: Baseline properties dictionary
    """
    ingredients = sorted(set(d["ingredient"] for d in data))
    colors = plt.cm.tab10(np.linspace(0, 1, len(ingredients)))

    for i, ing in enumerate(ingredients):
        ing_data = [d for d in data if d["ingredient"] == ing]

        ph_vals = [d["ph"] for d in ing_data]
        sal_vals = [d["salinity"] for d in ing_data]

        # Plot points with different markers for low/high
        for d in ing_data:
            marker = 'o' if d["concentration_level"] == "low" else '^'
            ax.scatter(d["ph"], d["salinity"], color=colors[i], marker=marker,
                      s=100, alpha=0.7, edgecolors='black', linewidths=1)

    # Plot baseline
    ax.scatter(baseline["ph"], baseline["salinity"],
              marker='*', s=400, color='gold', edgecolor='black',
              linewidths=2, label='Baseline', zorder=10)

    # Create legend
    legend_elements = [
        mpatches.Patch(color=colors[i], label=ing, alpha=0.7)
        for i, ing in enumerate(ingredients)
    ]
    legend_elements.append(
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray',
                  markersize=8, label='Low Conc', markeredgecolor='black')
    )
    legend_elements.append(
        plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='gray',
                  markersize=8, label='High Conc', markeredgecolor='black')
    )
    legend_elements.append(
        plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='gold',
                  markersize=12, label='Baseline', markeredgecolor='black')
    )

    ax.set_xlabel('pH', fontsize=12, fontweight='bold')
    ax.set_ylabel('TDS (g/L)', fontsize=12, fontweight='bold')
    ax.set_title('pH vs TDS Space', fontsize=14, fontweight='bold')
    ax.legend(handles=legend_elements, loc='best', fontsize=9)
    ax.grid(alpha=0.3, linestyle=':')


def _plot_ph_nacl_scatter(ax, data: List[Dict], baseline: Dict) -> None:
    """
    Plot pH vs NaCl salinity scatter plot.

    Shows the relationship between pH and NaCl salinity for all concentration levels.

    Args:
        ax: Matplotlib axes object
        data: List of sensitivity results
        baseline: Baseline properties dictionary
    """
    ingredients = sorted(set(d["ingredient"] for d in data))
    colors = plt.cm.tab10(np.linspace(0, 1, len(ingredients)))

    for i, ing in enumerate(ingredients):
        ing_data = [d for d in data if d["ingredient"] == ing]

        # Plot points with different markers for low/high
        for d in ing_data:
            marker = 'o' if d["concentration_level"] == "low" else '^'
            ax.scatter(d["ph"], d["nacl_salinity"], color=colors[i], marker=marker,
                      s=100, alpha=0.7, edgecolors='black', linewidths=1)

    # Plot baseline
    ax.scatter(baseline["ph"], baseline["nacl_salinity"],
              marker='*', s=400, color='gold', edgecolor='black',
              linewidths=2, label='Baseline', zorder=10)

    # Create legend
    legend_elements = [
        mpatches.Patch(color=colors[i], label=ing, alpha=0.7)
        for i, ing in enumerate(ingredients)
    ]
    legend_elements.append(
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray',
                  markersize=8, label='Low Conc', markeredgecolor='black')
    )
    legend_elements.append(
        plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='gray',
                  markersize=8, label='High Conc', markeredgecolor='black')
    )
    legend_elements.append(
        plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='gold',
                  markersize=12, label='Baseline', markeredgecolor='black')
    )

    ax.set_xlabel('pH', fontsize=12, fontweight='bold')
    ax.set_ylabel('NaCl Salinity (g/L)', fontsize=12, fontweight='bold')
    ax.set_title('pH vs NaCl Salinity Space', fontsize=14, fontweight='bold')
    ax.legend(handles=legend_elements, loc='best', fontsize=9)
    ax.grid(alpha=0.3, linestyle=':')

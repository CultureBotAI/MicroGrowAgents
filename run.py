"""Run script with CLI."""

import click

from microgrowagents.download import download as mga_download


@click.group()
def cli():
    """MicroGrowAgents command-line interface."""
    pass


@cli.command()
@click.option(
    "yaml_file",
    "-y",
    required=True,
    default="download.yaml",
    type=click.Path(exists=True),
)
@click.option("output_dir", "-o", required=True, default="data/raw")
@click.option(
    "ignore_cache",
    "-i",
    is_flag=True,
    default=False,
    help="ignore cache and download files even if they exist [false]",
)
@click.option(
    "snippet_only",
    "-s",
    is_flag=True,
    default=False,
    help="download only the first 5 kB of each file for testing [false]",
)
def download(*args, **kwargs) -> None:
    """
    Downloads data files from list of URLs (default: download.yaml) into data
    directory (default: data/raw).

    :param yaml_file: Specify the YAML file containing a list of datasets to download.
    :param output_dir: A string pointing to the directory to download data to.
    :param ignore_cache: If specified, will ignore existing files and download again.
    :param snippet_only: If specified, will download only the first 5 kB of each file.
    :return: None.
    """
    mga_download(*args, **kwargs)

    return None


@cli.command()
@click.option("--data-dir", "-d", default="data/raw", type=click.Path(exists=True))
@click.option("--db-path", "-o", default="data/processed/microgrow.duckdb")
@click.option("--force", "-f", is_flag=True, help="Recreate database from scratch")
@click.option("--chebi-owl", "-c", type=click.Path(exists=True), help="Path to ChEBI OWL file for category enrichment")
def load_data(data_dir: str, db_path: str, force: bool, chebi_owl: str) -> None:
    """
    Load downloaded data into DuckDB database.

    Reads TSV/CSV files from data/raw and creates indexed DuckDB database
    for fast agent queries. Optionally enriches ingredients with ChEBI categories
    from OWL file.
    """
    from microgrowagents.database.loader import load_data as load_data_fn

    load_data_fn(data_dir, db_path, force, chebi_owl_path=chebi_owl)


@cli.command()
@click.argument("query")
@click.option("--db-path", "-d", default="data/processed/microgrow.duckdb")
@click.option("--max-rows", "-n", default=100, help="Maximum rows to return")
@click.option("--format", "-f", default="table", type=click.Choice(["table", "csv", "json"]))
def query(query: str, db_path: str, max_rows: int, format: str) -> None:
    """
    Run SQL query on database.

    QUERY can be a SQL statement or natural language.

    Examples:
        python run.py query "SELECT * FROM media LIMIT 5"
        python run.py query "ingredients for LB medium"
        python run.py query "media by organism" --max-rows 20
    """
    from pathlib import Path
    from microgrowagents.agents.sql_agent import SQLAgent
    import json

    sql_agent = SQLAgent(Path(db_path))
    result = sql_agent.run(query, max_rows=max_rows)

    if not result["success"]:
        click.echo(f"Error: {result['error']}", err=True)
        return

    df = result["data"]

    if format == "csv":
        click.echo(df.to_csv(index=False))
    elif format == "json":
        click.echo(json.dumps(df.to_dict(orient="records"), indent=2))
    else:  # table
        click.echo(f"\nSQL: {result['sql']}\n")
        click.echo(df.to_string(index=False))
        click.echo(f"\n{result['row_count']} rows returned")


@cli.command()
@click.argument("compound")
@click.option("--source", "-s", default="pubchem", type=click.Choice(["pubchem", "chebi"]))
@click.option("--chebi-owl", "-c", type=click.Path(exists=True), help="Path to ChEBI OWL file (for ChEBI lookups)")
@click.option("--format", "-f", default="yaml", type=click.Choice(["yaml", "json"]))
def analyze(compound: str, source: str, chebi_owl: str, format: str) -> None:
    """
    Analyze chemical properties of a compound.

    COMPOUND can be a name, formula, or identifier.

    Examples:
        python run.py analyze glucose
        python run.py analyze NaCl --format json
        python run.py analyze "tris buffer" --source chebi --chebi-owl data/chebi.owl
    """
    from pathlib import Path
    from microgrowagents.agents.chemistry_agent import ChemistryAgent
    import json
    import yaml

    # Initialize agent
    chebi_owl_path = Path(chebi_owl) if chebi_owl else None
    agent = ChemistryAgent(chebi_owl_file=chebi_owl_path)

    # Try comprehensive analysis first
    result = agent.run(f"analyze {compound}")

    # If analysis fails, try lookup
    if not result["success"]:
        result = agent.run(f"lookup {compound}", source=source)

    if not result["success"]:
        click.echo(f"Error: {result['error']}", err=True)
        return

    # Format output
    if format == "json":
        click.echo(json.dumps(result["data"], indent=2))
    else:  # yaml
        click.echo(f"\nAnalysis for: {compound}")
        click.echo(f"Source: {result.get('source', 'local calculations')}\n")
        click.echo(yaml.dump(result["data"], default_flow_style=False))


@cli.command()
@click.argument("query")
@click.option("--mode", "-m", type=click.Choice(["medium", "ingredients", "auto"]), default="auto", help="Input mode (auto-detect by default)")
@click.option("--organism", "-org", help="NCBITaxon ID or organism name for organism-specific predictions")
@click.option("--unit", "-u", type=click.Choice(["mM", "g/L"]), default="mM", help="Output concentration unit")
@click.option("--db-path", "-d", default="data/processed/microgrow.duckdb")
@click.option("--chebi-owl", "-c", type=click.Path(exists=True), help="Path to ChEBI OWL file (for role lookups)")
@click.option("--format", "-f", default="yaml", type=click.Choice(["yaml", "json", "table", "tsv"]))
@click.option("--no-evidence", is_flag=True, help="Exclude evidence details from output")
@click.option("--output", "-o", type=click.Path(), help="Output file path (for TSV format)")
def gen_media_conc(query: str, mode: str, organism: str, unit: str, db_path: str, chebi_owl: str, format: str, no_evidence: bool, output: str) -> None:
    """
    Generate media ingredient concentration predictions.

    QUERY can be a medium name (e.g., "MP medium") or comma-separated ingredient list.

    Examples:
        python run.py gen-media-conc "MP medium"
        python run.py gen-media-conc "glucose,NaCl,tris" --mode ingredients
        python run.py gen-media-conc "LB medium" --organism "NCBITaxon:562"
        python run.py gen-media-conc "M9 medium" --unit g/L --format table
        python run.py gen-media-conc "MP medium" --format tsv --output mp_medium.tsv
    """
    from pathlib import Path
    from microgrowagents.agents.gen_media_conc_agent import GenMediaConcAgent
    import json
    import yaml

    # Initialize agent
    chebi_owl_path = Path(chebi_owl) if chebi_owl else None
    agent = GenMediaConcAgent(
        db_path=Path(db_path),
        chebi_owl_file=chebi_owl_path,
    )

    # Run prediction
    result = agent.run(
        query,
        mode=mode if mode != "auto" else None,
        organism=organism,
        unit=unit,
        include_evidence=not no_evidence,
    )

    if not result["success"]:
        click.echo(f"Error: {result['error']}", err=True)
        return

    # Format output
    if format == "json":
        click.echo(json.dumps(result, indent=2))
    elif format == "yaml":
        click.echo(f"\n=== Concentration Predictions ===")
        click.echo(f"Query: {query}")
        click.echo(f"Mode: {result.get('mode', 'auto')}")
        click.echo(f"Unit: {unit}")
        if result.get("organism"):
            click.echo(f"Organism: {result['organism']['name']} ({result['organism']['id']})")
        click.echo()

        # Summary
        if "summary" in result:
            summary = result["summary"]
            click.echo("Summary:")
            click.echo(f"  Total ingredients: {summary['total_ingredients']}")
            click.echo(f"  Essential: {summary['essential_count']}")
            click.echo(f"  Non-essential: {summary['non_essential_count']}")
            click.echo(f"  Average confidence: {summary['avg_confidence']:.2f}")
            click.echo()

        # Predictions
        click.echo("Predictions:")
        for pred in result["data"]:
            pred_copy = dict(pred)
            if no_evidence and "evidence" in pred_copy:
                del pred_copy["evidence"]
            click.echo(yaml.dump([pred_copy], default_flow_style=False))
    elif format in ["table", "tsv"]:  # table or tsv
        import pandas as pd

        # Create table
        table_data = []
        for pred in result["data"]:
            row = {
                "Ingredient": pred["name"],
                "Min": f"{pred['concentration_low']:.2f}",
                "Max": f"{pred['concentration_high']:.2f}",
                "Unit": pred["unit"],
                "Essential": "Yes" if pred["is_essential"] else "No",
                "Confidence": f"{pred['confidence']:.2f}",
            }

            # Add pH columns if available
            if "ph_at_low" in pred and pred["ph_at_low"] is not None:
                row["pH@Low"] = f"{pred['ph_at_low']:.2f}"
            if "ph_at_high" in pred and pred["ph_at_high"] is not None:
                row["pH@High"] = f"{pred['ph_at_high']:.2f}"

            # Add pH comment column
            if "ph_comment" in pred:
                row["pH Effect"] = pred["ph_comment"]

            table_data.append(row)

        df = pd.DataFrame(table_data)

        if format == "tsv":
            # TSV output
            if output:
                # Write to file
                df.to_csv(output, sep="\t", index=False)
                click.echo(f"Saved TSV output to: {output}")

                # Also show summary
                if "summary" in result:
                    summary = result["summary"]
                    click.echo(f"\nTotal: {summary['total_ingredients']} ingredients")
                    click.echo(f"Essential: {summary['essential_count']}, Non-essential: {summary['non_essential_count']}")
                    click.echo(f"Average confidence: {summary['avg_confidence']:.2f}")
            else:
                # Print to stdout
                click.echo(df.to_csv(sep="\t", index=False))
        else:  # table
            click.echo(f"\n=== Concentration Predictions: {query} ===\n")
            click.echo(df.to_string(index=False))

            # Summary
            if "summary" in result:
                summary = result["summary"]
                click.echo(f"\nTotal: {summary['total_ingredients']} ingredients")
                click.echo(f"Essential: {summary['essential_count']}, Non-essential: {summary['non_essential_count']}")
                click.echo(f"Average confidence: {summary['avg_confidence']:.2f}")


@cli.command()
@click.argument("medium1")
@click.argument("medium2")
@click.option("--db-path", "-d", default="data/processed/microgrow.duckdb")
@click.option("--format", "-f", default="yaml", type=click.Choice(["yaml", "json", "table"]))
def compare(medium1: str, medium2: str, db_path: str, format: str) -> None:
    """
    Compare chemical properties of two media formulations.

    MEDIUM1 and MEDIUM2 can be media names from the database.

    Examples:
        python run.py compare "LB medium" "M9 minimal medium"
        python run.py compare "medium_1" "medium_2" --format json
    """
    from pathlib import Path
    from microgrowagents.agents.sql_agent import SQLAgent
    from microgrowagents.agents.chemistry_agent import ChemistryAgent
    import json
    import yaml

    # Initialize agents
    sql_agent = SQLAgent(Path(db_path))
    chemistry_agent = ChemistryAgent()

    # Get ingredients for both media from database
    result1 = sql_agent.run(f"ingredients for {medium1}")
    result2 = sql_agent.run(f"ingredients for {medium2}")

    if not result1["success"]:
        click.echo(f"Error finding medium 1: {result1['error']}", err=True)
        return

    if not result2["success"]:
        click.echo(f"Error finding medium 2: {result2['error']}", err=True)
        return

    # Convert dataframes to ingredient lists
    df1 = result1["data"]
    df2 = result2["data"]

    media1_ingredients = []
    for _, row in df1.iterrows():
        media1_ingredients.append({
            "name": row.get("name", ""),
            "concentration": row.get("mmol_per_liter", row.get("amount", 0)),
            "grams_per_liter": row.get("grams_per_liter", 0),
        })

    media2_ingredients = []
    for _, row in df2.iterrows():
        media2_ingredients.append({
            "name": row.get("name", ""),
            "concentration": row.get("mmol_per_liter", row.get("amount", 0)),
            "grams_per_liter": row.get("grams_per_liter", 0),
        })

    # Compare media
    result = chemistry_agent.run("compare_media", media1=media1_ingredients, media2=media2_ingredients)

    if not result["success"]:
        click.echo(f"Error: {result['error']}", err=True)
        return

    # Format output
    if format == "json":
        click.echo(json.dumps(result["data"], indent=2))
    elif format == "yaml":
        click.echo(f"\nComparison: {medium1} vs {medium2}\n")
        click.echo(yaml.dump(result["data"], default_flow_style=False))
    else:  # table
        click.echo(f"\n=== Comparison: {medium1} vs {medium2} ===\n")
        data = result["data"]

        click.echo(f"pH difference: {data['ph_diff']}")
        click.echo(f"Ionic strength difference: {data['ionic_strength_diff']}")
        click.echo(f"Ingredient overlap: {data['ingredient_overlap']:.1%}\n")

        if data["unique_to_media1"]:
            click.echo(f"Unique to {medium1}:")
            for ing in data["unique_to_media1"]:
                click.echo(f"  - {ing}")
            click.echo()

        if data["unique_to_media2"]:
            click.echo(f"Unique to {medium2}:")
            for ing in data["unique_to_media2"]:
                click.echo(f"  - {ing}")
            click.echo()

        if data["concentration_differences"]:
            click.echo("Concentration differences:")
            for ing, diff in data["concentration_differences"].items():
                click.echo(f"  - {ing}: {diff['media1']:.4f} vs {diff['media2']:.4f} ({diff['percent_diff']:+.1f}%)")


@cli.command()
@click.argument("query", required=False)
@click.option("--mode", "-m", type=click.Choice(["medium", "ingredients", "auto"]), default="auto", help="Input mode (auto-detect by default)")
@click.option("--volume", "-v", default=1000.0, type=float, help="Total volume in milliliters (default: 1000)")
@click.option("--db-path", "-d", default="data/processed/microgrow.duckdb")
@click.option("--chebi-owl", "-c", type=click.Path(exists=True), help="Path to ChEBI OWL file")
@click.option("--input-file", "-i", type=click.Path(exists=True), help="Read gen-media-conc JSON output from file")
@click.option("--format", "-f", default="table", type=click.Choice(["table", "json", "yaml", "tsv"]))
@click.option("--output", "-o", type=click.Path(), help="Output file path (for TSV/JSON/YAML)")
@click.option("--plot", "-p", is_flag=True, help="Generate visualization plots")
@click.option("--plot-output", type=click.Path(), help="Output path for plot (default: sensitivity_plot.png)")
@click.option("--calculate-osmotic", is_flag=True, help="Calculate osmotic properties (osmolarity, water activity)")
@click.option("--calculate-redox", is_flag=True, help="Calculate redox properties (Eh, pE, electron balance)")
@click.option("--calculate-nutrients", is_flag=True, help="Calculate nutrient ratios (C:N:P, limiting nutrients)")
@click.option("--ph", type=float, help="pH value for redox calculations (uses baseline pH if not specified)")
@click.option("--temperature", "-t", default=25.0, type=float, help="Temperature in °C (default: 25.0)")
def sensitivity(query: str, mode: str, volume: float, db_path: str, chebi_owl: str, input_file: str, format: str, output: str, plot: bool, plot_output: str, calculate_osmotic: bool, calculate_redox: bool, calculate_nutrients: bool, ph: float, temperature: float) -> None:
    """
    Perform sensitivity analysis for media formulation.

    QUERY can be a medium name (e.g., "MP medium") or comma-separated
    ingredient list (e.g., "glucose,NaCl,PIPES").

    Calculates pH and salinity when varying each ingredient between
    LOW and HIGH concentrations while holding others at DEFAULT.

    ADVANCED PROPERTIES:
        Use --calculate-osmotic, --calculate-redox, or --calculate-nutrients
        to augment baseline results with advanced chemical property calculations.

    INTEGRATION WITH gen-media-conc:
        Option 1 - Direct: sensitivity automatically uses gen-media-conc predictions
        Option 2 - Pipeline: Read gen-media-conc JSON output via --input-file

    Examples:
        # Basic analysis
        python run.py sensitivity "MP medium"
        python run.py sensitivity "glucose,NaCl,PIPES" --mode ingredients

        # With advanced properties
        python run.py sensitivity "MP medium" --calculate-osmotic
        python run.py sensitivity "MP medium" --calculate-redox --calculate-nutrients
        python run.py sensitivity "MP medium" --calculate-osmotic --plot

        # Pipeline mode (read from gen-media-conc output)
        python run.py gen-media-conc "MP medium" --format json > predictions.json
        python run.py sensitivity --input-file predictions.json

        # With visualization
        python run.py sensitivity "MP medium" --plot --plot-output mp_analysis.png

        # Custom parameters
        python run.py sensitivity "MP medium" --volume 500 --temperature 37
        python run.py sensitivity "MP medium" --calculate-redox --ph 6.5

        # Export results
        python run.py sensitivity "MP medium" --format json --output results.json
    """
    from pathlib import Path
    from microgrowagents.agents.sensitivity_analysis_agent import SensitivityAnalysisAgent
    import json
    import yaml
    import pandas as pd

    # Handle input-file mode (pipeline from gen-media-conc)
    if input_file:
        with open(input_file, 'r') as f:
            genmedia_result = json.load(f)

        if not genmedia_result.get("success"):
            click.echo(f"Error: Input file contains failed gen-media-conc result", err=True)
            return

        # Extract query from metadata
        query = genmedia_result.get("metadata", {}).get("query", "Unknown")

        # Initialize agent
        chebi_owl_path = Path(chebi_owl) if chebi_owl else None
        agent = SensitivityAnalysisAgent(
            db_path=Path(db_path),
            chebi_owl_file=chebi_owl_path
        )

        # Convert gen-media-conc predictions and run sensitivity
        ingredients = agent._convert_genmedia_predictions_to_ingredients(genmedia_result["data"])

        # Calculate baseline and perform sweep directly
        baseline = agent._calculate_baseline(ingredients, volume)

        # Augment baseline with advanced properties if requested
        if any([calculate_osmotic, calculate_redox, calculate_nutrients]):
            baseline = agent._augment_baseline_with_advanced_properties(
                baseline,
                osmotic=calculate_osmotic,
                redox=calculate_redox,
                nutrients=calculate_nutrients,
                ph=ph,
                temperature=temperature
            )

        sensitivity_results = agent._perform_sensitivity_sweep(ingredients, volume)
        summary = agent._calculate_summary(sensitivity_results, baseline)

        result = {
            "success": True,
            "data": sensitivity_results,
            "baseline": baseline,
            "summary": summary,
            "metadata": {
                "query": query,
                "mode": "pipeline",
                "volume_ml": volume,
                "num_ingredients": len(ingredients),
                "source": "gen-media-conc pipeline",
                "advanced_properties": {
                    "osmotic": calculate_osmotic,
                    "redox": calculate_redox,
                    "nutrients": calculate_nutrients
                }
            }
        }
    else:
        # Direct mode - use query
        if not query:
            click.echo("Error: Either QUERY or --input-file must be provided", err=True)
            return

        # Initialize agent
        chebi_owl_path = Path(chebi_owl) if chebi_owl else None
        agent = SensitivityAnalysisAgent(
            db_path=Path(db_path),
            chebi_owl_file=chebi_owl_path
        )

        # Run sensitivity analysis
        result = agent.run(
            query,
            mode=mode if mode != "auto" else None,
            volume_ml=volume,
            calculate_osmotic=calculate_osmotic,
            calculate_redox=calculate_redox,
            calculate_nutrients=calculate_nutrients,
            ph=ph,
            temperature=temperature
        )

    if not result["success"]:
        click.echo(f"Error: {result['error']}", err=True)
        return

    # Format and output results
    if format == "json":
        output_str = json.dumps(result, indent=2)
        if output:
            with open(output, 'w') as f:
                f.write(output_str)
            click.echo(f"Saved JSON output to: {output}")
        else:
            click.echo(output_str)

    elif format == "yaml":
        output_str = yaml.dump(result, default_flow_style=False)
        if output:
            with open(output, 'w') as f:
                f.write(output_str)
            click.echo(f"Saved YAML output to: {output}")
        else:
            click.echo(output_str)

    elif format == "tsv":
        df = pd.DataFrame(result["data"])
        if output:
            df.to_csv(output, sep="\t", index=False)
            click.echo(f"Saved TSV output to: {output}")
        else:
            click.echo(df.to_csv(sep="\t", index=False))

    else:  # table
        _print_sensitivity_table(result)

    # Generate plots if requested
    if plot:
        try:
            from microgrowagents.visualization.sensitivity_plots import generate_sensitivity_plots
            plot_path = plot_output or "sensitivity_plot.png"
            generate_sensitivity_plots(result, plot_path)
            click.echo(f"\nSaved plots to: {plot_path}")
        except ImportError:
            click.echo("Warning: Visualization module not yet available. Skipping plots.", err=True)


def _print_sensitivity_table(result: dict) -> None:
    """Print formatted table output for sensitivity analysis."""
    import pandas as pd

    click.echo(f"\n=== Sensitivity Analysis: {result['metadata']['query']} ===\n")

    # Baseline
    baseline = result["baseline"]
    click.echo("BASELINE (All ingredients at DEFAULT):")
    click.echo(f"  pH: {baseline['ph']:.2f}")
    click.echo(f"  TDS (Total Dissolved Solids): {baseline['salinity']:.2f} g/L")
    click.echo(f"  NaCl Salinity (Ionic Salts): {baseline['nacl_salinity']:.2f} g/L")
    click.echo(f"  Ionic Strength: {baseline['ionic_strength']:.4f} M")
    click.echo(f"  Volume: {baseline['volume_ml']:.0f} mL\n")

    # Results table
    df = pd.DataFrame(result["data"])

    # Select columns for display and rename for clarity
    display_cols = [
        "ingredient", "concentration_level", "concentration_value",
        "unit", "ph", "salinity", "nacl_salinity", "delta_ph", "delta_salinity", "delta_nacl_salinity"
    ]

    # Rename columns for output
    display_df = df[display_cols].copy()
    display_df = display_df.rename(columns={
        "salinity": "tds (g/L)",
        "nacl_salinity": "nacl (g/L)",
        "delta_salinity": "delta_tds",
        "delta_nacl_salinity": "delta_nacl"
    })

    click.echo("SENSITIVITY RESULTS:\n")
    click.echo(display_df.to_string(index=False))

    # Summary
    summary = result["summary"]
    click.echo(f"\n\nSUMMARY:")
    click.echo(f"  pH Range: {summary['ph_range'][0]:.2f} - {summary['ph_range'][1]:.2f}")
    click.echo(f"  TDS Range: {summary['salinity_range'][0]:.2f} - {summary['salinity_range'][1]:.2f} g/L")
    click.echo(f"  NaCl Salinity Range: {summary['nacl_salinity_range'][0]:.2f} - {summary['nacl_salinity_range'][1]:.2f} g/L")
    click.echo(f"  Most pH-sensitive ingredient: {summary['most_sensitive_ph']}")
    click.echo(f"  Most TDS-sensitive ingredient: {summary['most_sensitive_salinity']}")
    click.echo(f"  Most NaCl-sensitive ingredient: {summary['most_sensitive_nacl_salinity']}")
    click.echo(f"  Ingredients analyzed: {summary['ingredients_analyzed']}\n")


if __name__ == "__main__":
    cli()

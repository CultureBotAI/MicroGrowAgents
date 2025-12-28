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


@cli.command()
@click.argument("query")
@click.option("--db-path", "-d", default="data/processed/microgrow.duckdb")
@click.option("--max-hops", default=5, type=int, help="Maximum path length for path queries")
@click.option("--limit", default=100, type=int, help="Maximum results to return")
@click.option("--algorithm", type=click.Choice(["betweenness", "closeness", "pagerank", "degree", "harmonic"]), help="Algorithm for centrality queries")
@click.option("--radius", default=2, type=int, help="Radius for subgraph extraction")
@click.option("--format", "-f", default="table", type=click.Choice(["table", "json", "yaml"]))
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def kg_query(query: str, db_path: str, max_hops: int, limit: int, algorithm: str, radius: int, format: str, output: str) -> None:
    """
    Execute Knowledge Graph reasoning query.

    QUERY format: "<type> <args>"

    Query types:
        lookup <node_id>              - Get node details
        neighbors <node_id> [pred]    - Get adjacent nodes (optionally filtered by predicate)
        path <source> <target>        - Find shortest path between nodes
        filter <category>             - Filter nodes by biolink category
        enzymes_using <substrate_id>  - Find enzymes using substrate (USE CASE 3)
        media_ingredients <media_id>  - Get media ingredients pathway (USE CASE 1)
        phenotype_media <phenotype>   - Find media for phenotypes (USE CASE 2)
        centrality <category>         - Calculate graph centrality (requires --algorithm)
        subgraph <node_ids>           - Extract neighborhood subgraph

    Examples:
        # Lookup node
        python run.py kg-query "lookup CHEBI:16828"

        # Find neighbors
        python run.py kg-query "neighbors CHEBI:16828"
        python run.py kg-query "neighbors CHEBI:16828 biolink:subclass_of"

        # Find shortest path
        python run.py kg-query "path NCBITaxon:562 CHEBI:16828" --max-hops 5

        # Find enzymes using substrate
        python run.py kg-query "enzymes_using CHEBI:16828" --limit 20

        # Get media ingredients
        python run.py kg-query "media_ingredients METPO:2000517"

        # Find media for phenotype
        python run.py kg-query "phenotype_media METPO:2000303"

        # Calculate centrality
        python run.py kg-query "centrality biolink:ChemicalSubstance" --algorithm pagerank

        # Extract subgraph
        python run.py kg-query "subgraph CHEBI:16828,CHEBI:15841" --radius 2

        # Filter by category
        python run.py kg-query "filter biolink:ChemicalSubstance" --limit 50

        # Output formats
        python run.py kg-query "lookup CHEBI:16828" --format json
        python run.py kg-query "path NCBITaxon:562 CHEBI:16828" --format yaml --output path.yaml
    """
    from pathlib import Path
    from microgrowagents.agents.kg_reasoning_agent import KGReasoningAgent
    from microgrowagents.kg.graph_builder import GRAPE_AVAILABLE
    import json
    import yaml

    # Check if GRAPE is available for graph-based queries
    graph_queries = ["path", "centrality", "subgraph"]
    query_type = query.split()[0].lower() if query else ""

    if query_type in graph_queries and not GRAPE_AVAILABLE:
        click.echo(
            f"Error: Query type '{query_type}' requires GRAPE, which is not available on this system.\n"
            f"See docs/grape_installation.md for installation instructions.\n"
            f"Supported queries without GRAPE: lookup, neighbors, filter, enzymes_using, "
            f"media_ingredients, phenotype_media",
            err=True
        )
        return

    # Initialize agent
    try:
        agent = KGReasoningAgent(db_path=Path(db_path))
    except Exception as e:
        click.echo(f"Error initializing KG agent: {e}", err=True)
        click.echo(f"Make sure database exists at {db_path}. Run 'python run.py load-data' first.", err=True)
        return

    # Execute query
    result = agent.run(
        query,
        max_hops=max_hops,
        limit=limit,
        algorithm=algorithm,
        radius=radius
    )

    # Handle errors
    if not result["success"]:
        click.echo(f"Error: {result['error']}", err=True)
        return

    # Format output
    output_str = None

    if format == "json":
        # Remove non-JSON-serializable objects (like GRAPE Graph)
        result_copy = dict(result)
        if "subgraph" in result_copy:
            result_copy["subgraph"] = f"<Graph: {result_copy.get('node_count', 0)} nodes, {result_copy.get('edge_count', 0)} edges>"

        output_str = json.dumps(result_copy, indent=2)

    elif format == "yaml":
        # Remove non-YAML-serializable objects
        result_copy = dict(result)
        if "subgraph" in result_copy:
            result_copy["subgraph"] = f"<Graph: {result_copy.get('node_count', 0)} nodes, {result_copy.get('edge_count', 0)} edges>"

        output_str = yaml.dump(result_copy, default_flow_style=False)

    else:  # table
        output_str = _format_kg_result_table(result)

    # Output results
    if output:
        with open(output, 'w') as f:
            f.write(output_str)
        click.echo(f"Saved output to: {output}")
    else:
        click.echo(output_str)


@cli.command()
@click.argument("organism_id")
@click.option("--db-path", "-d", default="data/processed/microgrow.duckdb")
@click.option("--format", "-f", default="table", type=click.Choice(["table", "json", "yaml", "tsv"]))
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def kg_pathway(organism_id: str, db_path: str, format: str, output: str) -> None:
    """
    Get full pathway from organism to media to ingredients.

    Traces the complete pathway: organism → media (where it grows) → ingredients → chemical properties.
    This corresponds to USE CASE 1 from the KG reasoning agent.

    ORGANISM_ID should be an NCBITaxon ID (e.g., "NCBITaxon:562" for E. coli).

    Examples:
        # Get pathway for E. coli
        python run.py kg-pathway "NCBITaxon:562"

        # Export as JSON
        python run.py kg-pathway "NCBITaxon:562" --format json --output ecoli_pathway.json

        # Export as TSV
        python run.py kg-pathway "NCBITaxon:562" --format tsv --output ecoli_pathway.tsv

        # Show as YAML
        python run.py kg-pathway "NCBITaxon:562" --format yaml
    """
    from pathlib import Path
    from microgrowagents.kg.query_patterns import QueryPatterns
    import json
    import yaml
    import pandas as pd

    # Initialize query patterns
    try:
        patterns = QueryPatterns(Path(db_path))
    except Exception as e:
        click.echo(f"Error connecting to database: {e}", err=True)
        click.echo(f"Make sure database exists at {db_path}. Run 'python run.py load-data' first.", err=True)
        return

    # Get pathway
    try:
        pathway_df = patterns.organism_to_media_pathway(organism_id)
    except Exception as e:
        click.echo(f"Error querying pathway: {e}", err=True)
        return

    if pathway_df.empty:
        click.echo(f"No pathway found for organism: {organism_id}", err=True)
        return

    # Format output
    output_str = None

    if format == "json":
        output_str = pathway_df.to_json(orient="records", indent=2)

    elif format == "yaml":
        records = pathway_df.to_dict(orient="records")
        output_str = yaml.dump(records, default_flow_style=False)

    elif format == "tsv":
        output_str = pathway_df.to_csv(sep="\t", index=False)

    else:  # table
        click.echo(f"\n=== Organism to Media Pathway: {organism_id} ===\n")

        # Group by media
        media_groups = pathway_df.groupby(["media_id", "media_name"])

        for (media_id, media_name), group in media_groups:
            click.echo(f"Medium: {media_name} ({media_id})")
            click.echo(f"  Ingredients ({len(group)}):")

            for _, row in group.iterrows():
                click.echo(f"    - {row['ingredient_name']} ({row['ingredient_id']})")
                click.echo(f"      Category: {row['ingredient_category']}")
            click.echo()

        output_str = f"\nTotal: {len(pathway_df)} ingredient-media associations across {pathway_df['media_id'].nunique()} media"

    # Output results
    if output:
        with open(output, 'w') as f:
            f.write(output_str)
        click.echo(f"Saved output to: {output}")
    else:
        click.echo(output_str)


def _format_kg_result_table(result: dict) -> str:
    """Format KG query result as human-readable table."""
    import pandas as pd
    from io import StringIO

    output = StringIO()
    query_type = result.get("query_type", "unknown")

    output.write(f"\n=== KG Query Result: {query_type} ===\n\n")

    if query_type == "lookup":
        # Format node details
        output.write(f"Node ID: {result['node_id']}\n")
        output.write(f"Name: {result.get('name', 'N/A')}\n")
        output.write(f"Category: {result.get('category', 'N/A')}\n")
        if result.get('description'):
            output.write(f"Description: {result['description']}\n")
        if result.get('xref'):
            output.write(f"Cross-references: {result['xref']}\n")

    elif query_type == "neighbors":
        # Format neighbors as table
        if result['neighbors']:
            df = pd.DataFrame(result['neighbors'])
            output.write(f"Node: {result['node_id']}\n")
            output.write(f"Neighbors ({len(result['neighbors'])}):\n\n")
            output.write(df.to_string(index=False))
        else:
            output.write(f"No neighbors found for {result['node_id']}")

    elif query_type == "path":
        # Format path
        output.write(f"Source: {result['source']}\n")
        output.write(f"Target: {result['target']}\n")
        output.write(f"Path length: {result['length']} hops\n\n")
        output.write("Path:\n")
        for i, node in enumerate(result['path']):
            output.write(f"  {i}. {node}\n")

    elif query_type == "filter":
        # Format filtered nodes as table
        if result['nodes']:
            df = pd.DataFrame(result['nodes'])
            output.write(f"Category: {result['category']}\n")
            output.write(f"Results ({result['count']}):\n\n")
            output.write(df.to_string(index=False))
        else:
            output.write(f"No nodes found for category: {result['category']}")

    elif query_type == "enzymes_using":
        # Format enzymes as table
        if result['enzymes']:
            df = pd.DataFrame(result['enzymes'])
            output.write(f"Substrate: {result['substrate_id']}\n")
            output.write(f"Enzymes found ({result['count']}):\n\n")
            output.write(df.to_string(index=False))
        else:
            output.write(f"No enzymes found using substrate: {result['substrate_id']}")

    elif query_type == "media_ingredients":
        # Format media ingredients
        media_info = result['media_info']
        if media_info:
            output.write(f"Medium: {media_info['media_name']} ({media_info['media_id']})\n")
            output.write(f"Category: {media_info['category']}\n\n")

            if result['ingredients']:
                output.write(f"Ingredients ({result['ingredient_count']}):\n\n")
                df = pd.DataFrame(result['ingredients'])
                output.write(df.to_string(index=False))
            else:
                output.write("No ingredients found")
        else:
            output.write("Media not found")

    elif query_type == "phenotype_media":
        # Format recommended media
        if result['recommended_media']:
            df = pd.DataFrame(result['recommended_media'])
            output.write(f"Phenotypes: {', '.join(result['phenotype_ids'])}\n")
            output.write(f"Recommended media ({result['count']}):\n\n")
            output.write(df.to_string(index=False))
        else:
            output.write(f"No media found for phenotypes: {', '.join(result['phenotype_ids'])}")

    elif query_type == "centrality":
        # Format centrality scores
        output.write(f"Category: {result['category']}\n")
        output.write(f"Algorithm: {result['algorithm']}\n\n")
        output.write("Top 20 nodes by centrality:\n\n")

        # Sort by score and take top 20
        scores = sorted(result['centrality_scores'].items(), key=lambda x: x[1], reverse=True)[:20]
        df = pd.DataFrame(scores, columns=["Node ID", "Score"])
        output.write(df.to_string(index=False))

    elif query_type == "subgraph":
        # Format subgraph info
        output.write(f"Center nodes: {', '.join(result['center_nodes'])}\n")
        output.write(f"Radius: {result['radius']} hops\n\n")
        output.write(f"Subgraph:\n")
        output.write(f"  Nodes: {result['node_count']}\n")
        output.write(f"  Edges: {result['edge_count']}\n")

    else:
        # Generic output
        output.write(str(result))

    return output.getvalue()


if __name__ == "__main__":
    cli()

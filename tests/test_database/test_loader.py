"""Test data loader."""

import pytest
from pathlib import Path
import duckdb
import pandas as pd

from microgrowagents.database.loader import DataLoader


@pytest.fixture
def test_data_dir(tmp_path):
    """Create test data directory with sample files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create sample compound mappings TSV
    compound_data = pd.DataFrame(
        {
            "original": ["glucose", "NaCl", "KCl"],
            "mapped": ["CHEBI:17234", "CHEBI:26710", "CHEBI:32588"],
            "chebi_id": ["CHEBI:17234", "CHEBI:26710", "CHEBI:32588"],
            "base_molecular_weight": [180.16, 58.44, 74.55],
            "hydration_state": ["anhydrous", "anhydrous", "anhydrous"],
            "base_chebi_id": ["CHEBI:17234", "CHEBI:26710", "CHEBI:32588"],
            "hydrated_molecular_weight": [180.16, 58.44, 74.55],
        }
    )
    compound_data.to_csv(
        data_dir / "compound_mappings_strict_final.tsv", sep="\t", index=False
    )

    # Create sample MP medium CSV
    mp_data = pd.DataFrame(
        {
            "Ingredient": ["glucose", "NaCl"],
            "ChEBI_ID": ["CHEBI:17234", "CHEBI:26710"],
            "Concentration": [10.0, 5.0],
            "Unit": ["g/L", "g/L"],
        }
    )
    mp_data.to_csv(data_dir / "mp_medium_ingredient_properties.csv", index=False)

    return data_dir


@pytest.fixture
def test_db_path(tmp_path):
    """Create test database path."""
    return tmp_path / "test.duckdb"


def test_data_loader_init(test_db_path):
    """Test DataLoader initialization."""
    loader = DataLoader(test_db_path)
    assert test_db_path.exists()
    loader.close()


def test_load_compound_mappings(test_data_dir, test_db_path):
    """Test loading compound mappings."""
    loader = DataLoader(test_db_path)
    loader._load_compound_mappings(test_data_dir)

    # Check that ingredients were loaded
    result = loader.conn.execute("SELECT COUNT(*) FROM ingredients").fetchone()
    assert result[0] == 3, "Should load 3 ingredients"

    # Check specific ingredient
    glucose = loader.conn.execute(
        "SELECT * FROM ingredients WHERE name = 'glucose'"
    ).fetchone()
    assert glucose is not None, "Glucose should be loaded"

    loader.close()


def test_load_all(test_data_dir, test_db_path):
    """Test loading all data sources."""
    loader = DataLoader(test_db_path)

    # This will only load the files that exist (compound mappings and MP medium)
    loader.load_all(test_data_dir)

    # Check that tables have data
    ing_count = loader.conn.execute("SELECT COUNT(*) FROM ingredients").fetchone()[0]
    assert ing_count > 0, "Ingredients table should have data"

    loader.close()

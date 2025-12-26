"""
DuckDB schema for microbial growth media data.

This module defines the database schema for storing and querying
microbial growth media, ingredients, organisms, and their relationships.

Tables:
1. media - Growth media definitions
2. ingredients - Chemical ingredients (ChEBI, PubChem, CAS-RN)
3. media_ingredients - Many-to-many relationships with concentrations
4. organisms - NCBITaxon organisms
5. organism_media - Many-to-many growth associations
6. chemical_properties - pH, pKa, solubility from MicroMediaParam
7. ingredient_effects - Effects from MP medium template + literature
"""

SCHEMA_SQL = """
-- Core media table
CREATE TABLE IF NOT EXISTS media (
    id VARCHAR PRIMARY KEY,                    -- mediadive.medium:123
    name VARCHAR NOT NULL,
    medium_type VARCHAR,                       -- complex/defined
    ph_min DOUBLE,
    ph_max DOUBLE,
    description TEXT,
    source VARCHAR,                            -- MediaDive, custom
    reference VARCHAR
);

-- Ingredients table (normalized chemical entities)
CREATE TABLE IF NOT EXISTS ingredients (
    id VARCHAR PRIMARY KEY,                    -- CHEBI:12345, PubChem:67890, CAS-RN:...
    name VARCHAR NOT NULL,
    chebi_id VARCHAR,                          -- Canonical ChEBI mapping
    pubchem_id VARCHAR,
    cas_rn VARCHAR,
    kegg_id VARCHAR,
    molecular_weight DOUBLE,
    category VARCHAR                           -- ingredient, solution, role
);

-- Media-Ingredient associations with concentrations
CREATE TABLE IF NOT EXISTS media_ingredients (
    id INTEGER PRIMARY KEY,
    media_id VARCHAR,  -- REFERENCES media(id)
    ingredient_id VARCHAR,  -- REFERENCES ingredients(id)
    amount DOUBLE,
    unit VARCHAR,                              -- g/L, mM, etc.
    grams_per_liter DOUBLE,
    mmol_per_liter DOUBLE,
    role VARCHAR                               -- from ChEBI roles
);

-- Organisms
CREATE TABLE IF NOT EXISTS organisms (
    id VARCHAR PRIMARY KEY,                    -- NCBITaxon:562
    name VARCHAR NOT NULL,
    rank VARCHAR,                              -- species, strain, etc.
    lineage TEXT
);

-- Organism-Media growth associations
CREATE TABLE IF NOT EXISTS organism_media (
    id INTEGER PRIMARY KEY,
    organism_id VARCHAR,  -- REFERENCES organisms(id)
    media_id VARCHAR,  -- REFERENCES media(id)
    source VARCHAR,                            -- BacDive, MediaDive
    reference VARCHAR
);

-- Chemical properties (from MicroMediaParam mappings)
CREATE TABLE IF NOT EXISTS chemical_properties (
    ingredient_id VARCHAR PRIMARY KEY,  -- REFERENCES ingredients(id)
    hydration_state VARCHAR,
    anhydrous_chebi VARCHAR,                   -- For hydrates
    molecular_weight DOUBLE,
    pka_values TEXT,                           -- JSON array of pKa values
    solubility TEXT                            -- Solubility info
);

-- Ingredient effects (from MP medium template and literature)
CREATE TABLE IF NOT EXISTS ingredient_effects (
    id INTEGER PRIMARY KEY,
    ingredient_id VARCHAR,  -- REFERENCES ingredients(id)
    media_id VARCHAR,  -- REFERENCES media(id) - Optional: specific to medium
    concentration_low DOUBLE,                  -- Concentration range
    concentration_high DOUBLE,
    unit VARCHAR,
    effect_type VARCHAR,                       -- growth, pH_buffering, osmotic, etc.
    effect_description TEXT,
    evidence TEXT,                             -- Literature citation
    source VARCHAR                             -- MP_medium, PubMed:12345, etc.
);
"""

INDEX_SQL = """
-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_media_name ON media(name);
CREATE INDEX IF NOT EXISTS idx_ingredient_name ON ingredients(name);
CREATE INDEX IF NOT EXISTS idx_media_ing_media ON media_ingredients(media_id);
CREATE INDEX IF NOT EXISTS idx_media_ing_ingredient ON media_ingredients(ingredient_id);
CREATE INDEX IF NOT EXISTS idx_org_media_organism ON organism_media(organism_id);
CREATE INDEX IF NOT EXISTS idx_org_media_media ON organism_media(media_id);
CREATE INDEX IF NOT EXISTS idx_chem_props_ingredient ON chemical_properties(ingredient_id);
CREATE INDEX IF NOT EXISTS idx_ing_effects_ingredient ON ingredient_effects(ingredient_id);
"""


def create_schema(conn) -> None:
    """
    Create database schema.

    Args:
        conn: DuckDB connection
    """
    conn.execute(SCHEMA_SQL)
    conn.execute(INDEX_SQL)


def drop_schema(conn) -> None:
    """
    Drop all tables (for testing/rebuilding).

    Args:
        conn: DuckDB connection
    """
    tables = [
        "ingredient_effects",
        "chemical_properties",
        "organism_media",
        "media_ingredients",
        "organisms",
        "ingredients",
        "media",
    ]
    for table in tables:
        conn.execute(f"DROP TABLE IF EXISTS {table}")

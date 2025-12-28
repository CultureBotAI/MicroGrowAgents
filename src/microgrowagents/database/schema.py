"""
DuckDB schema for microbial growth media data and KG-Microbe integration.

This module defines the database schema for storing and querying
microbial growth media, ingredients, organisms, and their relationships,
plus Knowledge Graph (KG-Microbe) data.

Core Media Tables:
1. media - Growth media definitions
2. ingredients - Chemical ingredients (ChEBI, PubChem, CAS-RN)
3. media_ingredients - Many-to-many relationships with concentrations
4. organisms - NCBITaxon organisms
5. organism_media - Many-to-many growth associations
6. chemical_properties - pH, pKa, solubility from MicroMediaParam
7. ingredient_effects - Effects from MP medium template + literature

Knowledge Graph Tables (KG-Microbe):
8. kg_nodes - 1.5M nodes (biolink:OrganismTaxon, ChemicalSubstance, etc.)
9. kg_edges - 5.1M edges (biolink:subclass_of, has_phenotype, METPO predicates)
10. kg_hierarchies - Materialized transitive closure for fast ontology queries
11. kg_predicate_index - Edge type statistics and metadata
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

-- ============================================================================
-- Knowledge Graph (KG-Microbe) Tables
-- ============================================================================

-- KG Nodes (1.5M rows from merged-kg_nodes.tsv)
-- Represents entities: OrganismTaxon, ChemicalSubstance, MolecularActivity, etc.
CREATE TABLE IF NOT EXISTS kg_nodes (
    id VARCHAR PRIMARY KEY,                    -- CHEBI:16828, NCBITaxon:562, etc.
    category VARCHAR NOT NULL,                 -- biolink:ChemicalSubstance, biolink:OrganismTaxon
    name VARCHAR,                              -- Human-readable name
    description TEXT,                          -- Entity description
    xref TEXT,                                 -- Cross-references (pipe-separated)
    synonym TEXT,                              -- Synonyms (pipe-separated)
    iri VARCHAR,                               -- IRI/URL for entity
    provided_by VARCHAR,                       -- Source database (chebi, ncbitaxon, etc.)
    deprecated BOOLEAN DEFAULT FALSE,          -- Whether entity is deprecated
    subsets VARCHAR                            -- Subset classifications
);

-- KG Edges (5.1M rows from merged-kg_edges.tsv)
-- Represents relationships between entities
CREATE TABLE IF NOT EXISTS kg_edges (
    id VARCHAR PRIMARY KEY,                    -- Unique edge identifier
    subject VARCHAR NOT NULL,                  -- Source node ID
    predicate VARCHAR NOT NULL,                -- Relationship type (biolink:subclass_of, etc.)
    object VARCHAR NOT NULL,                   -- Target node ID
    relation VARCHAR,                          -- Additional relation info
    knowledge_source VARCHAR,                  -- Source of this edge
    primary_knowledge_source VARCHAR           -- Primary source (for provenance)
);

-- Materialized Hierarchies (for fast ontology queries)
-- Pre-computed transitive closure of biolink:subclass_of edges
CREATE TABLE IF NOT EXISTS kg_hierarchies (
    ancestor_id VARCHAR NOT NULL,              -- Ancestor node in hierarchy
    descendant_id VARCHAR NOT NULL,            -- Descendant node in hierarchy
    path_length INTEGER NOT NULL,              -- Number of hops in path
    path TEXT,                                 -- Pipe-separated path of IDs
    PRIMARY KEY (ancestor_id, descendant_id)
);

-- Predicate Index (metadata about edge types)
-- Statistics and metadata for each predicate type
CREATE TABLE IF NOT EXISTS kg_predicate_index (
    predicate VARCHAR PRIMARY KEY,             -- Predicate URI (biolink:subclass_of)
    edge_count INTEGER,                        -- Number of edges with this predicate
    description VARCHAR,                       -- Human-readable description
    domain_category VARCHAR,                   -- Typical subject category
    range_category VARCHAR                     -- Typical object category
);
"""

INDEX_SQL = """
-- Indexes for fast queries (Core Media Tables)
CREATE INDEX IF NOT EXISTS idx_media_name ON media(name);
CREATE INDEX IF NOT EXISTS idx_ingredient_name ON ingredients(name);
CREATE INDEX IF NOT EXISTS idx_media_ing_media ON media_ingredients(media_id);
CREATE INDEX IF NOT EXISTS idx_media_ing_ingredient ON media_ingredients(ingredient_id);
CREATE INDEX IF NOT EXISTS idx_org_media_organism ON organism_media(organism_id);
CREATE INDEX IF NOT EXISTS idx_org_media_media ON organism_media(media_id);
CREATE INDEX IF NOT EXISTS idx_chem_props_ingredient ON chemical_properties(ingredient_id);
CREATE INDEX IF NOT EXISTS idx_ing_effects_ingredient ON ingredient_effects(ingredient_id);

-- ============================================================================
-- Knowledge Graph Indexes (8 critical indexes for 5M edge queries)
-- ============================================================================

-- Node indexes for category and name lookups
CREATE INDEX IF NOT EXISTS idx_kg_nodes_category ON kg_nodes(category);
CREATE INDEX IF NOT EXISTS idx_kg_nodes_name ON kg_nodes(name);

-- Edge indexes for fast graph traversal
CREATE INDEX IF NOT EXISTS idx_kg_edges_subject ON kg_edges(subject);
CREATE INDEX IF NOT EXISTS idx_kg_edges_object ON kg_edges(object);
CREATE INDEX IF NOT EXISTS idx_kg_edges_predicate ON kg_edges(predicate);

-- Composite indexes for common query patterns
-- For queries like: "find all edges from X with predicate Y"
CREATE INDEX IF NOT EXISTS idx_kg_edges_subj_pred ON kg_edges(subject, predicate);

-- For reverse lookups: "find all edges to Y with predicate X"
CREATE INDEX IF NOT EXISTS idx_kg_edges_pred_obj ON kg_edges(predicate, object);

-- Hierarchy index for fast ancestor queries
CREATE INDEX IF NOT EXISTS idx_kg_hier_ancestor ON kg_hierarchies(ancestor_id);
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

    Drops both core media tables and KG tables in correct order
    (respecting potential foreign key dependencies).

    Args:
        conn: DuckDB connection
    """
    tables = [
        # KG tables (drop first to avoid conflicts)
        "kg_predicate_index",
        "kg_hierarchies",
        "kg_edges",
        "kg_nodes",
        # Core media tables
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

"""
DuckDB schema for microbial growth media data and KG-Microbe integration.

This module defines the database schema for storing and querying
microbial growth media, ingredients, organisms, and their relationships,
plus Knowledge Graph (KG-Microbe) data and genome annotations.

Core Media Tables:
1. media - Growth media definitions
2. ingredients - Chemical ingredients (ChEBI, PubChem, CAS-RN)
3. media_ingredients - Many-to-many relationships with concentrations
4. organisms - NCBITaxon organisms
5. organism_media - Many-to-many growth associations
6. chemical_properties - pH, pKa, solubility from MicroMediaParam
7. ingredient_effects - Effects with evidence (DOI, organism, snippets, cellular role, toxicity)

Genome Annotation Tables:
8. genome_metadata - Genome assembly and annotation metadata (57 genomes)
9. genome_annotations - Gene annotations from Bakta GFF3 files (~250k annotations)

Knowledge Graph Tables (KG-Microbe):
10. kg_nodes - 1.5M nodes (biolink:OrganismTaxon, ChemicalSubstance, etc.)
11. kg_edges - 5.1M edges (biolink:subclass_of, has_phenotype, METPO predicates)
12. kg_hierarchies - Materialized transitive closure for fast ontology queries
13. kg_predicate_index - Edge type statistics and metadata
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
    solubility TEXT,                           -- Solubility info
    solubility_doi VARCHAR                     -- DOI citation for solubility data
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
    evidence TEXT,                             -- Literature citation (DOI)
    evidence_organism VARCHAR,                 -- Organism(s) relevant to this evidence
    evidence_snippet TEXT,                     -- Supporting text from paper
    source VARCHAR,                            -- MP_medium, PubMed:12345, etc.
    cellular_role VARCHAR,                     -- Cellular role/function
    cellular_requirements TEXT,                -- Specific cellular requirements
    toxicity_value DOUBLE,                     -- Minimal/observed concentration eliciting toxicity
    toxicity_unit VARCHAR,                     -- Unit for toxicity value
    toxicity_species_specific BOOLEAN,         -- Whether toxicity is species-specific
    toxicity_cellular_effects TEXT,            -- Description of cellular effects at toxic levels
    toxicity_evidence TEXT,                    -- DOI/citation for toxicity data
    toxicity_evidence_snippet TEXT             -- Supporting text for toxicity claim
);

-- ============================================================================
-- Genome Annotation Tables (Bakta GFF3 files)
-- ============================================================================

-- Genome metadata (57 bacterial genomes)
CREATE TABLE IF NOT EXISTS genome_metadata (
    genome_id VARCHAR PRIMARY KEY,             -- SAMN00114986 (BioSample ID)
    organism_id VARCHAR,                       -- Link to organisms.id (NCBITaxon)
    organism_name VARCHAR,                     -- E.g., "Escherichia coli K-12"
    biosample_id VARCHAR,                      -- SAMN ID (same as genome_id)
    assembly_size INTEGER,                     -- Total genome size in bp
    contig_count INTEGER,                      -- Number of contigs/scaffolds
    gene_count INTEGER,                        -- Total genes annotated
    cds_count INTEGER,                         -- Protein-coding genes (CDS features)
    trna_count INTEGER,                        -- tRNA genes
    rrna_count INTEGER,                        -- rRNA genes
    ncrna_count INTEGER,                       -- Other ncRNA genes
    annotation_tool VARCHAR,                   -- "Bakta"
    annotation_version VARCHAR,                -- "v1.9.4"
    annotation_database VARCHAR,               -- "v5.1, full"
    annotation_date DATE,                      -- Date annotated
    metadata_json TEXT                         -- Flexible JSON for extra fields
);

-- Genome annotations (~250,000 gene annotations from 57 genomes)
CREATE TABLE IF NOT EXISTS genome_annotations (
    id INTEGER PRIMARY KEY,
    genome_id VARCHAR NOT NULL,                -- REFERENCES genome_metadata(genome_id)
    feature_id VARCHAR NOT NULL,               -- PJIGLD_00005 (unique within genome)
    feature_type VARCHAR NOT NULL,             -- CDS, tRNA, rRNA, ncRNA, tmRNA, CRISPR, region
    contig_id VARCHAR,                         -- contig00001
    start_pos INTEGER,                         -- Start position on contig
    end_pos INTEGER,                           -- End position on contig
    strand VARCHAR,                            -- +, -, ?
    locus_tag VARCHAR,                         -- Systematic locus tag
    gene_symbol VARCHAR,                       -- Gene name (e.g., "fur", "hemolysin")
    product TEXT,                              -- Product description
    ec_numbers TEXT,                           -- Comma-separated: "2.3.2.30,1.1.1.1"
    go_terms TEXT,                             -- Comma-separated GO IDs: "0005575,0008150"
    kegg_ids TEXT,                             -- Comma-separated KEGG IDs: "K22310,K00001"
    cog_ids TEXT,                              -- Comma-separated COG IDs: "COG2202,COG0001"
    cog_categories TEXT,                       -- Comma-separated COG categories: "T,E"
    protein_id VARCHAR,                        -- RefSeq/UniRef ID (WP_017839628.1)
    dbxref TEXT,                               -- Full Dbxref string for reference
    source VARCHAR,                            -- Pyrodigal, tRNAscan-SE, Infernal, PILER-CR
    score DOUBLE,                              -- Prediction score (if available)
    phase INTEGER                              -- Reading frame phase (0, 1, 2 for CDS)
);

-- ============================================================================
-- Information Sheets Tables (Extended Data Collections)
-- ============================================================================

-- Sheet Collections Registry (metadata for each sheets_* directory)
CREATE TABLE IF NOT EXISTS sheet_collections (
    collection_id VARCHAR PRIMARY KEY,         -- 'cmm', 'xyz', etc.
    collection_name VARCHAR NOT NULL,          -- 'CMM Extended Data'
    directory_path VARCHAR NOT NULL,           -- 'data/sheets_cmm'
    loaded_at TIMESTAMP,                       -- When collection was loaded
    table_count INTEGER,                       -- Number of TSV tables loaded
    total_rows INTEGER,                        -- Total data rows across all tables
    description TEXT                           -- Collection description
);

-- Sheet Tables Registry (metadata for each TSV file)
CREATE TABLE IF NOT EXISTS sheet_tables (
    table_id VARCHAR PRIMARY KEY,              -- 'cmm_chemicals', 'cmm_genes'
    collection_id VARCHAR NOT NULL,            -- FK to sheet_collections
    table_name VARCHAR NOT NULL,               -- 'chemicals', 'genes_and_proteins'
    source_file VARCHAR NOT NULL,              -- 'BER_CMM_Data_for_AI_chemicals_extended.tsv'
    row_count INTEGER,                         -- Number of rows in table
    column_count INTEGER,                      -- Number of columns
    columns_json TEXT,                         -- JSON array of column names
    loaded_at TIMESTAMP                        -- When table was loaded
);

-- Unified Sheet Data Storage (EAV pattern for flexible schemas)
-- Stores all data from TSV files with JSON for flexible column storage
CREATE SEQUENCE IF NOT EXISTS sheet_data_seq START 1;
CREATE TABLE IF NOT EXISTS sheet_data (
    id INTEGER PRIMARY KEY DEFAULT nextval('sheet_data_seq'),
    table_id VARCHAR NOT NULL,                 -- FK to sheet_tables
    row_id INTEGER NOT NULL,                   -- Row number within source table
    entity_id VARCHAR,                         -- Primary ID (chemical_id, gene_id, strain_id, etc.)
    entity_name VARCHAR,                       -- Primary name (chemical_name, gene_symbol, etc.)
    entity_type VARCHAR,                       -- 'chemical', 'gene', 'strain', 'publication', etc.
    data_json TEXT NOT NULL,                   -- Complete row as JSON (all columns)
    searchable_text TEXT                       -- Concatenated text fields for full-text search
);

-- Publication Full-Text Index (markdown files from publications/ subdirs)
CREATE SEQUENCE IF NOT EXISTS sheet_publications_seq START 1;
CREATE TABLE IF NOT EXISTS sheet_publications (
    id INTEGER PRIMARY KEY DEFAULT nextval('sheet_publications_seq'),
    collection_id VARCHAR NOT NULL,            -- FK to sheet_collections
    file_name VARCHAR NOT NULL,                -- 'PMID_24816778.md', 'doi_10_1038-nature16174.md'
    publication_id VARCHAR,                    -- Extracted ID: 'pmid:24816778', 'doi:10.1038/nature16174'
    publication_type VARCHAR,                  -- 'pmid', 'doi', 'pmc', 'arxiv'
    title TEXT,                                -- Publication title (if parseable)
    authors TEXT,                              -- Authors (if parseable)
    year INTEGER,                              -- Publication year (if parseable)
    journal TEXT,                              -- Journal name (if parseable)
    abstract TEXT,                             -- Abstract (if parseable)
    full_text TEXT,                            -- Complete markdown content
    word_count INTEGER,                        -- Word count for metadata
    loaded_at TIMESTAMP                        -- When publication was loaded
);

-- Cross-References Between Entities and Publications
-- Links entities in sheet_data to publications they reference
CREATE SEQUENCE IF NOT EXISTS sheet_publication_references_seq START 1;
CREATE TABLE IF NOT EXISTS sheet_publication_references (
    id INTEGER PRIMARY KEY DEFAULT nextval('sheet_publication_references_seq'),
    publication_id INTEGER NOT NULL,           -- FK to sheet_publications.id
    table_id VARCHAR NOT NULL,                 -- FK to sheet_tables
    entity_id VARCHAR NOT NULL,                -- Entity referencing this publication
    reference_column VARCHAR,                  -- Column where reference appears (URL, DOI, etc.)
    reference_value VARCHAR                    -- Actual reference value (URL, DOI string)
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

-- ============================================================================
-- Provenance Tracking Tables (Hybrid system with file-based tracking)
-- ============================================================================

-- Provenance Sessions: Records each agent execution
CREATE TABLE IF NOT EXISTS provenance_sessions (
    session_id VARCHAR PRIMARY KEY,
    agent_type VARCHAR NOT NULL,
    agent_version VARCHAR,
    query TEXT NOT NULL,
    kwargs JSON,
    user_context JSON,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_ms INTEGER,
    success BOOLEAN,
    result_summary JSON,
    error_message TEXT,
    python_version VARCHAR,
    dependencies JSON,
    db_path VARCHAR,
    parent_session_id VARCHAR,
    depth INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_session_id) REFERENCES provenance_sessions(session_id)
);

-- Provenance Events: Detailed step-by-step event log
CREATE TABLE IF NOT EXISTS provenance_events (
    event_id VARCHAR PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,
    event_name VARCHAR NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    sequence_number INTEGER NOT NULL,
    details JSON NOT NULL,
    duration_ms INTEGER,
    related_event_id VARCHAR,
    FOREIGN KEY (session_id) REFERENCES provenance_sessions(session_id)
);

-- Provenance Tool Calls: Database queries, API calls, file operations
CREATE TABLE IF NOT EXISTS provenance_tool_calls (
    call_id VARCHAR PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    event_id VARCHAR NOT NULL,
    tool_type VARCHAR NOT NULL,
    tool_name VARCHAR NOT NULL,
    input_params JSON NOT NULL,
    output_data JSON,
    output_size_bytes INTEGER,
    call_time TIMESTAMP NOT NULL,
    duration_ms INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE,
    cache_key VARCHAR,
    cache_source VARCHAR,
    rate_limit_delay_ms INTEGER,
    retry_count INTEGER DEFAULT 0,
    success BOOLEAN NOT NULL,
    error_type VARCHAR,
    error_message TEXT,
    FOREIGN KEY (session_id) REFERENCES provenance_sessions(session_id)
);

-- Provenance Decisions: Decision points and reasoning
CREATE TABLE IF NOT EXISTS provenance_decisions (
    decision_id VARCHAR PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    event_id VARCHAR NOT NULL,
    decision_type VARCHAR NOT NULL,
    decision_point VARCHAR NOT NULL,
    input_values JSON NOT NULL,
    condition_evaluated TEXT,
    branch_taken VARCHAR,
    branches_available JSON,
    reason TEXT,
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (session_id) REFERENCES provenance_sessions(session_id)
);

-- Provenance Transformations: Data transformations and mappings
CREATE TABLE IF NOT EXISTS provenance_transformations (
    transformation_id VARCHAR PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    event_id VARCHAR NOT NULL,
    transformation_type VARCHAR NOT NULL,
    transformation_name VARCHAR NOT NULL,
    input_schema JSON,
    input_sample JSON,
    input_size INTEGER,
    output_schema JSON,
    output_sample JSON,
    output_size INTEGER,
    method VARCHAR,
    parameters JSON,
    timestamp TIMESTAMP NOT NULL,
    duration_ms INTEGER,
    FOREIGN KEY (session_id) REFERENCES provenance_sessions(session_id)
);

-- Provenance Entity Links: Connect provenance to domain entities
CREATE TABLE IF NOT EXISTS provenance_entity_links (
    link_id INTEGER PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    event_id VARCHAR,
    entity_table VARCHAR NOT NULL,
    entity_id VARCHAR NOT NULL,
    link_type VARCHAR NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (session_id) REFERENCES provenance_sessions(session_id)
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
-- Genome Annotation Indexes (8 strategic indexes for 250k annotation queries)
-- ============================================================================

-- Genome metadata indexes
CREATE INDEX IF NOT EXISTS idx_genome_meta_organism ON genome_metadata(organism_id);
CREATE INDEX IF NOT EXISTS idx_genome_meta_biosample ON genome_metadata(biosample_id);

-- Genome annotation indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_genome_ann_genome ON genome_annotations(genome_id);
CREATE INDEX IF NOT EXISTS idx_genome_ann_type ON genome_annotations(feature_type);
CREATE INDEX IF NOT EXISTS idx_genome_ann_gene ON genome_annotations(gene_symbol);
CREATE INDEX IF NOT EXISTS idx_genome_ann_product ON genome_annotations(product);

-- Functional annotation indexes (for EC, GO, KEGG searches)
-- Note: DuckDB doesn't have GIN indexes like PostgreSQL, but B-tree indexes work for LIKE queries
CREATE INDEX IF NOT EXISTS idx_genome_ann_ec ON genome_annotations(ec_numbers);
CREATE INDEX IF NOT EXISTS idx_genome_ann_go ON genome_annotations(go_terms);
CREATE INDEX IF NOT EXISTS idx_genome_ann_kegg ON genome_annotations(kegg_ids);

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

-- ============================================================================
-- Information Sheets Indexes (9 strategic indexes for query performance)
-- ============================================================================

-- Entity lookup indexes (Query Type 1: Entity Lookup by ID/name)
CREATE INDEX IF NOT EXISTS idx_sheet_data_entity_id ON sheet_data(entity_id);
CREATE INDEX IF NOT EXISTS idx_sheet_data_entity_name ON sheet_data(entity_name);
CREATE INDEX IF NOT EXISTS idx_sheet_data_entity_type ON sheet_data(entity_type);

-- Cross-reference indexes (Query Type 2: Cross-Reference Queries)
CREATE INDEX IF NOT EXISTS idx_sheet_data_composite ON sheet_data(table_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_sheet_pub_refs_entity ON sheet_publication_references(entity_id);

-- Full-text search indexes (Query Type 3: Publication Search)
CREATE INDEX IF NOT EXISTS idx_sheet_pubs_pub_id ON sheet_publications(publication_id);
CREATE INDEX IF NOT EXISTS idx_sheet_data_searchable ON sheet_data(searchable_text);

-- Collection and table lookups (Query Type 4: Filtered Queries)
CREATE INDEX IF NOT EXISTS idx_sheet_tables_collection ON sheet_tables(collection_id);
CREATE INDEX IF NOT EXISTS idx_sheet_data_table ON sheet_data(table_id);

-- ============================================================================
-- Provenance Tracking Indexes (6 strategic indexes for session analytics)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_prov_sessions_agent ON provenance_sessions(agent_type, created_at);
CREATE INDEX IF NOT EXISTS idx_prov_events_session ON provenance_events(session_id, sequence_number);
CREATE INDEX IF NOT EXISTS idx_prov_tools_session ON provenance_tool_calls(session_id, call_time);
CREATE INDEX IF NOT EXISTS idx_prov_decisions_session ON provenance_decisions(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_prov_transformations_session ON provenance_transformations(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_prov_entity_links_entity ON provenance_entity_links(entity_table, entity_id);
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
        # Provenance tables (drop first due to potential dependencies)
        "provenance_entity_links",
        "provenance_transformations",
        "provenance_decisions",
        "provenance_tool_calls",
        "provenance_events",
        "provenance_sessions",
        # KG tables (drop first to avoid conflicts)
        "kg_predicate_index",
        "kg_hierarchies",
        "kg_edges",
        "kg_nodes",
        # Information sheets tables
        "sheet_publication_references",
        "sheet_publications",
        "sheet_data",
        "sheet_tables",
        "sheet_collections",
        # Genome annotation tables
        "genome_annotations",
        "genome_metadata",
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

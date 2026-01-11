# Cofactor Data Sources and KG-Microbe Integration

This document provides comprehensive documentation of the datasets, resources, and citations that inform the CofactorMediaAgent's cofactor analysis pipeline.

## Overview

The CofactorMediaAgent integrates **6 major biological databases** plus specialized literature to analyze cofactor requirements for microbial organisms. The system combines:

1. **Curated reference data** (cofactor hierarchies, EC mappings)
2. **Organism genome data** (Bakta annotations)
3. **Knowledge graph queries** (KG-Microbe via KGReasoningAgent)
4. **Literature evidence** (organism-specific mechanisms)

## Cofactor Analysis Pipeline

```
Bakta GFF3 Genome Annotation
         ↓
Extract EC Numbers (from genome_annotations table)
         ↓
Map EC → Cofactors (ec_to_cofactor_map.yaml)
         ↓
Enrich with Details (cofactor_hierarchy.yaml)
         ↓
Query KG-Microbe for Evidence (KGReasoningAgent)
         ├→ Enzyme-substrate relationships
         ├→ Biosynthesis pathway context
         └→ Acquisition mechanisms (transporters)
         ↓
Map to MP Ingredients (ingredient_cofactor_mapping.csv)
         ↓
Generate Hierarchical Table (CofactorMediaAgent._build_cofactor_table)
```

## Primary Data Sources

| Resource | Coverage | Primary Use | DOI | Integration Point |
|----------|----------|-------------|-----|-------------------|
| **ChEBI** | 44 cofactors | Chemical IDs, names, synonyms | [10.1093/nar/gkv1031](https://doi.org/10.1093/nar/gkv1031) | `cofactor_hierarchy.yaml` IDs |
| **KEGG** | 30+ pathways | Biosynthesis pathway definitions | [10.1093/nar/gkac963](https://doi.org/10.1093/nar/gkac963) | `cofactor_hierarchy.yaml` pathways |
| **EC Nomenclature** | 68 EC patterns | Enzyme classification | [10.1093/nar/gkn582](https://doi.org/10.1093/nar/gkn582) | `ec_to_cofactor_map.yaml` |
| **BRENDA** | 68 EC mappings | EC-cofactor relationships | [10.1093/nar/gky1048](https://doi.org/10.1093/nar/gky1048) | `ec_to_cofactor_map.yaml` |
| **KG-Microbe** | 1.5M nodes, 5.1M edges | Enzyme-substrate queries | N/A (project data) | `KGReasoningAgent` runtime |
| **MP Medium CSV** | 158 ingredients | Ingredient chemical properties | Various (90.5% coverage) | `ingredient_cofactor_mapping.csv` |

### Supporting Databases

- **MetaCyc**: Pathway-cofactor relationship validation ([DOI: 10.1093/nar/gkz862](https://doi.org/10.1093/nar/gkz862))
- **UniProt**: Enzyme examples and annotations ([DOI: 10.1093/nar/gkac1052](https://doi.org/10.1093/nar/gkac1052))
- **Reactome**: Cofactor reaction roles ([DOI: 10.1093/nar/gkab1028](https://doi.org/10.1093/nar/gkab1028))

### Specialized Literature

- **Lanthanide cofactors**: Good NM, et al. (2019) *J Biol Chem.* 294(21):8437-8446 ([DOI: 10.1074/jbc.RA119.008197](https://doi.org/10.1074/jbc.RA119.008197))
- **PQQ**: Anthony C. (2001) *Antioxid Redox Signal.* 3(5):757-774 ([DOI: 10.1089/15230860152664966](https://doi.org/10.1089/15230860152664966))
- **Methanogen cofactors**: Thauer RK, et al. (2008) *Nat Rev Microbiol.* 6(8):579-591 ([DOI: 10.1038/nrmicro1931](https://doi.org/10.1038/nrmicro1931))

## Reference Files

### 1. cofactor_hierarchy.yaml

**Location**: `src/microgrowagents/data/cofactor_hierarchy.yaml`

**Content**: 44 distinct cofactors organized into 5 functional categories:
- **Vitamins** (14 cofactors): TPP, Biotin, Cobalamin, PLP, FMN, FAD, NAD/NADP, Folate, THF, Menaquinone, Ubiquinone, Lipoic acid
- **Metals** (13 cofactors): Fe-S clusters, Heme (a/b/c/d1), Siroheme, Fe, Zn, Cu, Mg, Ca, Mn, Mo, Co, Ni, W, Lanthanides
- **Nucleotides** (11 cofactors): NAD/NADH, NADP/NADPH, ATP, ADP, GTP, CTP, UTP
- **Energy Cofactors** (7 cofactors): CoA, Acetyl-CoA, SAM, PAPS, cAMP, cGMP
- **Other Specialized** (9 cofactors): PQQ, Methanofuran, H4MPT, CoM, CoB, Biotin CCCP, Retinal, Mycofactocin, F420, Methanophenazine

**Data Sources**:
- ChEBI IDs for all 44 cofactors
- KEGG pathway IDs (30+ biosynthesis pathways: ko00730, ko00760, ko00780, etc.)
- EC number associations (100+ enzyme-cofactor relationships)
- Enzyme examples from UniProt
- Specialized literature for rare cofactors

**Structure**:
```yaml
cofactor_hierarchy:
  vitamins:
    cofactors:
      thiamine_pyrophosphate:
        id: "CHEBI:9532"
        names: ["TPP", "ThDP"]
        precursor: "thiamine"
        ec_associations: ["2.2.1.-", "4.1.1.-"]
        kegg_pathways: ["ko00730"]
```

### 2. ec_to_cofactor_map.yaml

**Location**: `src/microgrowagents/data/ec_to_cofactor_map.yaml`

**Content**: 68 EC number patterns mapped to required and optional cofactors

**Data Sources**:
- BRENDA: Primary EC-to-cofactor relationship data
- ExplorEnz: EC number classification and validation
- MetaCyc: Pathway-based cofactor validation

**Pattern Matching**:
- Supports wildcards (e.g., `"1.1.1.-"` matches all EC 1.1.1.X enzymes)
- Exact match takes precedence over pattern match
- Pattern hierarchy: 4-level > 3-level > 2-level > 1-level

**Example**:
```yaml
ec_cofactor_mapping:
  "1.1.1.-": {primary: ["nad", "nadp"], optional: ["zinc_ion"]}
  "2.6.1.-": {primary: ["pyridoxal_phosphate"]}
```

### 3. ingredient_cofactor_mapping.csv

**Location**: `data/processed/ingredient_cofactor_mapping.csv`

**Content**: 13 MP medium ingredients identified as cofactor providers

**Generation Method**:
- **NOT generated from KG-Microbe**
- Source: `data/raw/mp_medium_ingredient_properties.csv` (158 ingredients)
- Method: Rule-based pattern matching on component names
- Script: `scripts/generate_ingredient_cofactor_mapping.py`

**Example Mappings**:
```
MgCl₂·6H₂O → magnesium_ion (CHEBI:18420)
FeSO₄·7H₂O → iron_ion, heme, iron_sulfur_clusters
Thiamin → thiamine_pyrophosphate (CHEBI:9532)
CoCl₂·6H₂O → cobalamin, cobalt_ion
```

## KG-Microbe Integration

### What KG-Microbe IS Used For

KG-Microbe (1.5M nodes, 5.1M edges) provides **runtime evidence integration** via the `KGReasoningAgent`:

1. **Enzyme-Substrate Relationship Queries**
   - SQL query pattern (USE CASE 3):
     ```sql
     SELECT enzyme_id, enzyme_name, relationship
     FROM kg_edges e
     JOIN kg_nodes n ON e.subject = n.id
     WHERE e.object = ? (substrate CHEBI ID)
     AND e.predicate IN ('biolink:has_input', 'biolink:has_participant')
     AND n.category = 'biolink:MolecularActivity'
     ```
   - Finds all enzymes using a specific cofactor substrate

2. **Biosynthesis Pathway Context**
   - Query pathway completeness for cofactor biosynthesis capability
   - Determines if organism can produce cofactor de novo

3. **Acquisition Mechanisms**
   - Transporter detection: Genome annotations + KG relationships
   - Identifies uptake systems for external cofactors
   - Detects secreted chelators and binding molecules

4. **Multi-Source Evidence Integration**
   - Combines genome, KG, literature, and KEGG data
   - Confidence scoring based on evidence source count
   - File: `src/microgrowagents/agents/cofactor_media_agent.py:183-237`

### What KG-Microbe is NOT Used For

1. **Cofactor Hierarchy Definition**
   - Manually curated from ChEBI, KEGG, BRENDA databases
   - NOT derived from KG-Microbe relationships

2. **EC-to-Cofactor Mapping**
   - BRENDA-based curation with ExplorEnz validation
   - Independent of KG-Microbe

3. **Ingredient Mapping Generation**
   - Rule-based parsing of MP medium CSV
   - Pattern matching on component names
   - NO KG-Microbe queries involved

### KGReasoningAgent Query Patterns

**File**: `src/microgrowagents/agents/kg_reasoning_agent.py`

**Query capabilities**:
- **USE CASE 1**: Organism → Media → Ingredients pathway
- **USE CASE 2**: Phenotype → Media recommendations
- **USE CASE 3**: Enzyme-substrate relationships (cofactor analysis)

**Database**: DuckDB-loaded KG data (`data/raw/kg_microbe_core/merged-kg_*.tsv`)

**Graph algorithms**: GRAPE (Graph Representation leArning) for 10-100x performance

## ChEBI Ontology Access

**Direct OWL file parsing** (not through KG-Microbe):
- **Client**: `src/microgrowagents/chemistry/api_clients/chebi_client.py`
- **Features**: Exact + fuzzy matching, synonym support, normalization
- **Source**: [https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.owl](https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.owl)
- **Used for**: Ingredient name → ChEBI ID matching

## Multi-Source Evidence Integration

The `CofactorMediaAgent.analyze_cofactor_requirements()` method integrates:

1. **Genome** (Bakta GFF3 EC numbers)
   - Direct SQL query: `genome_annotations` table
   - Method: `_get_ec_numbers_from_genome()`

2. **KG-Microbe** (pathway context)
   - Via `KGReasoningAgent` runtime queries
   - Enzyme-substrate relationships
   - Biosynthesis pathway validation

3. **KEGG** (biosynthesis completeness)
   - Reference data from `cofactor_hierarchy.yaml`
   - Pathway IDs: ko00730, ko00760, etc.

4. **Literature** (organism mechanisms)
   - Via `LiteratureAgent` searches
   - Organism-specific evidence

**Confidence scoring**:
- High: 3-4 evidence sources agree
- Medium: 2 evidence sources
- Low: 1 evidence source

## Data Flow in CofactorMediaAgent

```python
# Step 1: Extract EC numbers from genome
ec_numbers = self._get_ec_numbers_from_genome(organism)
# Query: SELECT DISTINCT ec_numbers FROM genome_annotations WHERE genome_id = ?

# Step 2: Map EC → Cofactors
for ec in ec_numbers:
    cofactors = self._map_ec_to_cofactors(ec)
    # Uses ec_to_cofactor_map.yaml with pattern matching

# Step 3: Enrich with cofactor details
for cofactor_key in cofactors:
    info = self._get_cofactor_info(cofactor_key)
    # Loads from cofactor_hierarchy.yaml

# Step 4: Query KG-Microbe (optional, for evidence)
# Via KGReasoningAgent for enzyme-substrate relationships

# Step 5: Map to MP ingredients
ingredient_mapping = self.map_ingredients_to_cofactors(requirements, "MP")
# Uses ingredient_cofactor_mapping.csv

# Step 6: Build hierarchical output table
table = self._build_cofactor_table(requirements, ingredient_mapping)
```

## Coverage Metrics

- **Cofactors defined**: 44 across 5 categories
- **KEGG pathways referenced**: 30+
- **EC number associations**: 100+
- **EC pattern mappings**: 68
- **MP medium ingredients mapped**: 13/158 (8.2% are cofactor providers)
- **Pattern coverage**: ~80% of common microbial enzymes

## Citation Summary

### Core Databases (Required)
1. ChEBI: [10.1093/nar/gkv1031](https://doi.org/10.1093/nar/gkv1031)
2. KEGG: [10.1093/nar/gkac963](https://doi.org/10.1093/nar/gkac963)
3. BRENDA: [10.1093/nar/gky1048](https://doi.org/10.1093/nar/gky1048)
4. ExplorEnz: [10.1093/nar/gkn582](https://doi.org/10.1093/nar/gkn582)

### Supporting Databases
5. MetaCyc: [10.1093/nar/gkz862](https://doi.org/10.1093/nar/gkz862)
6. UniProt: [10.1093/nar/gkac1052](https://doi.org/10.1093/nar/gkac1052)
7. Reactome: [10.1093/nar/gkab1028](https://doi.org/10.1093/nar/gkab1028)

### Specialized Literature
8. Lanthanides: [10.1074/jbc.RA119.008197](https://doi.org/10.1074/jbc.RA119.008197)
9. PQQ: [10.1089/15230860152664966](https://doi.org/10.1089/15230860152664966)
10. Methanogens: [10.1038/nrmicro1931](https://doi.org/10.1038/nrmicro1931)

For BibTeX format, see: [`docs/references/cofactor_sources.bib`](references/cofactor_sources.bib)

## Related Documentation

- [Cofactor Curation Methodology](cofactor_curation_methodology.md) - Detailed curation workflow
- [CofactorMediaAgent API](../src/microgrowagents/agents/cofactor_media_agent.py) - Implementation
- [KGReasoningAgent](../src/microgrowagents/agents/kg_reasoning_agent.py) - KG-Microbe integration
- [MP Medium Dataset](../data/raw/mp_medium_ingredient_properties.csv) - Source ingredient data

## Version History

- **v1.0** (2025-01-10): Initial documentation with comprehensive citations and KG-Microbe integration details

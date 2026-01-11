# Cofactor Curation Methodology

This document describes the detailed methodology used to create and maintain the cofactor reference data for the MicroGrowAgents system.

## Overview

The cofactor curation process integrates data from multiple authoritative biological databases into structured reference files that power the CofactorMediaAgent. The methodology emphasizes:

1. **Multi-source validation**: Cross-referencing across ChEBI, KEGG, BRENDA, and ExplorEnz
2. **Literature-based curation**: Specialized cofactors validated against primary literature
3. **Pattern-based mapping**: Scalable EC-to-cofactor relationships using wildcards
4. **Reproducibility**: All curation steps documented with version control

## 1. Cofactor Hierarchy Curation

### File: `cofactor_hierarchy.yaml`

### Step 1: Initial Cofactor Identification

**Data Sources**:
- ChEBI ontology search for term "cofactor" (CHEBI:23357)
- KEGG compound search for "coenzyme" and "prosthetic group"
- Literature review for specialized cofactors (lanthanides, PQQ, archaeal cofactors)

**Inclusion Criteria**:
- Essential for enzyme catalysis or electron transfer
- Chemically well-defined structure
- Present in at least one known microbial enzyme
- Has a ChEBI ID or KEGG compound ID

**Exclusion Criteria**:
- Generic terms (e.g., "organic cofactor")
- Insufficiently characterized compounds
- Eukaryote-specific cofactors not found in bacteria/archaea

### Step 2: Functional Categorization

**Categories defined**:
1. **Vitamins** - Organic cofactors derived from dietary vitamins
2. **Metals** - Metal ions and metalloenzyme prosthetic groups
3. **Nucleotides** - Nucleotide-based redox carriers and energy currencies
4. **Energy Cofactors** - Group transfer and energy metabolism cofactors
5. **Other** - Specialized cofactors (PQQ, archaeal cofactors, etc.)

**Categorization Process**:
```python
# Pseudo-algorithm
for cofactor in candidate_list:
    if has_vitamin_precursor(cofactor):
        category = "vitamins"
    elif contains_metal(cofactor):
        category = "metals"
    elif is_nucleotide_derivative(cofactor):
        category = "nucleotides"
    elif is_group_transfer_cofactor(cofactor):
        category = "energy_cofactors"
    else:
        category = "other"
```

### Step 3: ChEBI ID Assignment

**Process**:
1. Search ChEBI ontology by cofactor name
2. Verify chemical structure matches expected cofactor
3. Select most specific ChEBI ID (e.g., CHEBI:15846 for NAD+ vs CHEBI:13389 for NAD)
4. Record primary ID and all synonyms

**ChEBI Search Tool**: https://www.ebi.ac.uk/chebi/advancedSearchFT.do

**Example**:
```yaml
thiamine_pyrophosphate:
  id: "CHEBI:9532"  # Exact match from ChEBI search
  names: ["TPP", "ThDP", "Thiamine diphosphate"]  # All synonyms
```

### Step 4: KEGG Pathway Mapping

**Process**:
1. Search KEGG pathway database for cofactor biosynthesis
2. Record pathway IDs (ko##### format)
3. Validate pathway relevance to bacterial/archaeal metabolism

**KEGG Resources**:
- Pathway database: https://www.genome.jp/kegg/pathway.html
- Compound database: https://www.genome.jp/kegg/compound/

**Example Pathways**:
- ko00730: Thiamine metabolism (for TPP)
- ko00760: Nicotinate and nicotinamide metabolism (for NAD/NADP)
- ko00780: Biotin metabolism

### Step 5: EC Association Assignment

**Process**:
1. Query BRENDA for enzymes requiring specific cofactor
2. Extract EC numbers from enzyme entries
3. Generalize to EC patterns where appropriate
4. Validate against ExplorEnz classifications

**Example**:
```yaml
pyridoxal_phosphate:
  ec_associations: ["2.6.1.-", "4.1.1.-", "5.1.1.-"]  # All aminotransferases, decarboxylases, racemases
```

### Step 6: Quality Control

**Validation Checks**:
- [ ] All cofactors have valid ChEBI IDs
- [ ] All synonyms verified against ChEBI
- [ ] KEGG pathway IDs are valid
- [ ] EC associations match BRENDA/ExplorEnz
- [ ] No duplicate cofactor entries
- [ ] All categories properly defined

## 2. EC-to-Cofactor Mapping

### File: `ec_to_cofactor_map.yaml`

### Step 1: BRENDA Data Mining

**Process**:
1. For each EC class (1-6), query BRENDA for cofactor requirements
2. Extract cofactor-EC relationships from enzyme entries
3. Identify patterns across EC subclasses

**BRENDA Query Example**:
```
EC 1.1.1.- (NAD/NADP-dependent dehydrogenases)
→ Primary: NAD+, NADP+
→ Optional: Zn2+ (for some alcohol dehydrogenases)
```

### Step 2: Pattern Generalization

**Pattern Hierarchy**:
1. **Exact match** (highest priority): `"1.1.1.27"` - specific enzyme
2. **3-digit pattern**: `"1.1.1.-"` - EC subclass
3. **2-digit pattern**: `"1.1.-.-"` - EC sub-subclass (rarely used)
4. **1-digit pattern**: Never used (too broad)

**Generalization Rules**:
- If >80% of enzymes in EC subclass share cofactor → create pattern
- If cofactor is optional in <50% of enzymes → mark as "optional"
- If conflicting evidence → use exact EC number

### Step 3: Primary vs Optional Classification

**Definitions**:
- **Primary**: Absolutely required for catalytic activity
- **Optional**: Enhances activity or is alternative substrate

**Classification Process**:
```yaml
"1.1.1.-":
  primary: ["nad", "nadp"]     # Required for all dehydrogenases
  optional: ["zinc_ion"]       # Only for alcohol dehydrogenases
```

### Step 4: Cross-Validation with MetaCyc

**Process**:
1. Query MetaCyc for EC number
2. Verify cofactor requirements match BRENDA
3. Resolve conflicts by checking primary literature

### Step 5: Quality Control

**Validation Checks**:
- [ ] All EC patterns are valid (e.g., "1.1.1.-" not "1.1.1")
- [ ] No conflicting mappings (same EC → different cofactors)
- [ ] All cofactor keys reference `cofactor_hierarchy.yaml` entries
- [ ] Pattern hierarchy respected (exact > 3-digit > 2-digit)
- [ ] Primary/optional classification justified

## 3. Ingredient-to-Cofactor Mapping

### File: `ingredient_cofactor_mapping.csv`

### Data Source
**Input**: `data/raw/mp_medium_ingredient_properties.csv` (158 ingredients)

### Mapping Algorithm

**Script**: `scripts/generate_ingredient_cofactor_mapping.py`

**Step 1: Component Name Parsing**
```python
def extract_cofactor_from_component(component_name, chebi_id):
    """
    Rule-based pattern matching on component names.

    Examples:
    - "Thiamin" → thiamine_pyrophosphate
    - "FeSO₄·7H₂O" → iron_ion, heme, iron_sulfur_clusters
    - "MgCl₂·6H₂O" → magnesium_ion
    """
    cofactors = []

    # Vitamin mappings
    if "thiamin" in component_name.lower():
        cofactors.append("thiamine_pyrophosphate")
    elif "biotin" in component_name.lower():
        cofactors.append("biotin")
    elif "cobal" in component_name.lower():  # Cobalamin, cobalt
        cofactors.extend(["cobalamin", "cobalt_ion"])

    # Metal mappings (extract from chemical formula)
    if extract_metal(component_name) == "Mg":
        cofactors.append("magnesium_ion")
    elif extract_metal(component_name) == "Fe":
        cofactors.extend(["iron_ion", "heme", "iron_sulfur_clusters"])
    elif extract_metal(component_name) == "Zn":
        cofactors.append("zinc_ion")
    # ... etc for all metals

    return cofactors
```

**Step 2: ChEBI ID Validation**
- Verify ChEBI ID from source CSV matches expected chemical
- Cross-check with ChEBI ontology using `chebi_client.py`

**Step 3: Manual Curation**
- Review edge cases (e.g., rare earth elements → lanthanides)
- Add lanthanide mapping for NdCl₃, PrCl₃, etc.
- Verify multi-cofactor assignments (e.g., Fe → iron_ion + heme + Fe-S)

### Quality Control

**Validation Checks**:
- [ ] All ingredient names from MP medium CSV present
- [ ] ChEBI IDs match source data
- [ ] Cofactor keys reference `cofactor_hierarchy.yaml`
- [ ] No missing cofactor assignments for known cofactor-providing ingredients
- [ ] Multi-cofactor assignments justified (e.g., Fe provides multiple forms)

## 4. Integration Testing

### Test Organisms

**E. coli K-12**: Well-characterized model organism
- Expected cofactors: NAD, FAD, CoA, Fe, Mg, etc.
- Biosynthesis: Capable for most vitamins
- Validation: Compare to EcoCyc pathways

**M. radiotolerans**: Methylotroph representative
- Expected cofactors: PQQ, lanthanides (XoxF-MDH)
- Validation: Compare to published genome analysis

### Test Cases

**Test 1: Cofactor Identification**
```python
def test_cofactor_identification():
    """Test that all expected cofactors are identified from genome."""
    agent = CofactorMediaAgent()
    result = agent.analyze_cofactor_requirements("SAMN02604091")  # E. coli

    expected_cofactors = ["nad", "fad", "thiamine_pyrophosphate", "iron_ion"]
    found_cofactors = [req.cofactor_key for req in result]

    assert all(cf in found_cofactors for cf in expected_cofactors)
```

**Test 2: Ingredient Mapping**
```python
def test_ingredient_mapping():
    """Test that MP medium ingredients map to cofactors."""
    agent = CofactorMediaAgent()
    requirements = [
        CofactorRequirement(cofactor_key="magnesium_ion", ...)
    ]

    mapping = agent.map_ingredients_to_cofactors(requirements, "MP")

    # Mg should be mapped to MgCl₂·6H₂O
    assert any("MgCl" in ing.ingredient_name for ing in mapping["existing"])
```

**Test 3: Cross-Validation with Literature**
```python
def test_literature_validation():
    """Validate lanthanide cofactor for M. extorquens."""
    agent = CofactorMediaAgent()
    result = agent.analyze_cofactor_requirements("Methylobacterium_extorquens")

    # Should detect lanthanide requirement for XoxF
    cofactors = [req.cofactor_key for req in result]
    assert "lanthanides" in cofactors
```

## 5. Version Control and Updates

### Versioning Strategy

**Version Format**: `MAJOR.MINOR` (e.g., 1.0, 1.1, 2.0)

**Version Increments**:
- **MAJOR**: Breaking changes (e.g., restructure categories, change keys)
- **MINOR**: Additions (e.g., new cofactors, new EC mappings)

**Current Version**: 1.0 (as of 2025-01-10)

### Update Procedure

**Adding New Cofactor**:
1. Verify ChEBI ID exists
2. Assign to appropriate category
3. Map EC associations from BRENDA
4. Identify KEGG biosynthesis pathway
5. Update `cofactor_hierarchy.yaml`
6. Run tests to verify integration
7. Increment MINOR version

**Adding New EC Mapping**:
1. Query BRENDA for EC number
2. Identify cofactor requirements
3. Determine if pattern or exact match
4. Update `ec_to_cofactor_map.yaml`
5. Run tests
6. Increment MINOR version

**Citation Updates**:
- Review annually for database updates (ChEBI, KEGG, BRENDA)
- Update DOIs if new papers published
- Maintain backward compatibility with existing ChEBI IDs

## 6. Future Enhancements

### Planned Improvements

1. **Automated ChEBI ID Validation**
   - Script to check all ChEBI IDs are still valid
   - Detect deprecated IDs and suggest replacements

2. **BRENDA API Integration**
   - Automate EC-to-cofactor mapping updates
   - Quarterly refresh of cofactor-enzyme relationships

3. **Quantitative Cofactor Requirements**
   - Add stoichiometry information (e.g., 2 Mg2+ per enzyme)
   - Concentration ranges for optimal activity

4. **Organism-Specific Cofactor Variants**
   - Expand lanthanide mapping (La, Ce, Nd, Pr, Dy specificities)
   - Quinone pool variations (ubiquinone vs menaquinone preferences)

## 7. Citation Management

### Citation Update Process

**Annual Review** (recommended: January each year):
1. Check for updated versions of ChEBI, KEGG, BRENDA
2. Update DOIs in YAML headers
3. Verify URL accessibility
4. Update BibTeX file (`docs/references/cofactor_sources.bib`)

**Adding New Citations**:
1. Add to BibTeX file first
2. Update YAML header with citation format: "Author et al. (YEAR) Journal. Vol(Issue):Pages"
3. Include DOI

**Citation Format**:
```yaml
# Citation: LastName F, et al. (YEAR) Journal Name. Vol(Issue):Pages
# DOI: 10.####/######
```

## Appendix: Tools and Resources

### Database Access

| Database | Access Method | Update Frequency |
|----------|---------------|------------------|
| ChEBI | OWL download + API | Monthly |
| KEGG | Web interface | Quarterly |
| BRENDA | Web interface | Annually |
| ExplorEnz | Web interface | Annually |
| MetaCyc | Web interface | Biannually |

### Scripts

- `scripts/generate_ingredient_cofactor_mapping.py` - Ingredient mapping generator
- `scripts/validate_cofactor_hierarchy.py` - Quality control validator (TODO)
- `scripts/update_chebi_ids.py` - ChEBI ID validator (TODO)

### Contacts

For questions about curation methodology:
- GitHub Issues: https://github.com/CultureBotAI/MicroGrowAgents/issues
- Maintainer: MicroGrowAgents Team

---

**Last Updated**: 2025-01-10
**Version**: 1.0
**Related Documentation**: [Cofactor Data Sources](cofactor_data_sources.md)

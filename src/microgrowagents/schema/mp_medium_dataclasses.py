# Auto generated from mp_medium_schema.yaml by pythongen.py version: 0.0.1
# Generation date: 2026-01-10T18:09:00
# Schema: mp-medium-schema
#
# id: https://w3id.org/microgrow/mp-medium
# description: LinkML schema for MP (Methylotroph) medium ingredient properties and predictions. Covers ingredient properties, concentration predictions, and alternate recommendations.
#   This schema models four main data tables: 1. MP Medium Ingredient Properties (49 columns with DOI citations) 2. MP Medium Concentration Predictions (9 columns) 3. Alternate Ingredients Table (7 columns) 4. Media formulations and compositions
# license: MIT

import dataclasses
import re
from dataclasses import dataclass
from datetime import (
    date,
    datetime,
    time
)
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Union
)

from jsonasobj2 import (
    JsonObj,
    as_dict
)
from linkml_runtime.linkml_model.meta import (
    EnumDefinition,
    PermissibleValue,
    PvFormulaOptions
)
from linkml_runtime.utils.curienamespace import CurieNamespace
from linkml_runtime.utils.enumerations import EnumDefinitionImpl
from linkml_runtime.utils.formatutils import (
    camelcase,
    sfx,
    underscore
)
from linkml_runtime.utils.metamodelcore import (
    bnode,
    empty_dict,
    empty_list
)
from linkml_runtime.utils.slot import Slot
from linkml_runtime.utils.yamlutils import (
    YAMLRoot,
    extended_float,
    extended_int,
    extended_str
)
from rdflib import (
    Namespace,
    URIRef
)

from linkml_runtime.linkml_model.types import Boolean, Float, String, Uriorcurie
from linkml_runtime.utils.metamodelcore import Bool, URIorCURIE

metamodel_version = "1.7.0"
version = None

# Namespaces
CHEBI = CurieNamespace('CHEBI', 'http://purl.obolibrary.org/obo/CHEBI_')
BIOLINK = CurieNamespace('biolink', 'https://w3id.org/biolink/vocab/')
LINKML = CurieNamespace('linkml', 'https://w3id.org/linkml/')
MICROGROW = CurieNamespace('microgrow', 'https://w3id.org/microgrow/')
SCHEMA = CurieNamespace('schema', 'http://schema.org/')
DEFAULT_ = MICROGROW


# Types
class DOI(Uriorcurie):
    """ Digital Object Identifier """
    type_class_uri = SCHEMA["identifier"]
    type_class_curie = "schema:identifier"
    type_name = "DOI"
    type_model_uri = MICROGROW.DOI


# Class references
class MPMediumIngredientKgNodeId(extended_str):
    pass


class ConcentrationPredictionIngredient(extended_str):
    pass


class IngredientPropertyKgNodeId(extended_str):
    pass


class ConcentrationRangeDetailedIngredient(extended_str):
    pass


class SolubilityToxicitySummaryIngredient(extended_str):
    pass


class MediumPredictionExtendedIngredient(extended_str):
    pass


@dataclass(repr=False)
class MPMediumDataset(YAMLRoot):
    """
    Complete MP medium dataset including ingredient properties, concentration predictions, alternate recommendations,
    and detailed concentration ranges with provenance.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = MICROGROW["MPMediumDataset"]
    class_class_curie: ClassVar[str] = "microgrow:MPMediumDataset"
    class_name: ClassVar[str] = "MPMediumDataset"
    class_model_uri: ClassVar[URIRef] = MICROGROW.MPMediumDataset

    ingredients: Optional[Union[dict[Union[str, MPMediumIngredientKgNodeId], Union[dict, "MPMediumIngredient"]], list[Union[dict, "MPMediumIngredient"]]]] = empty_dict()
    ingredient_properties: Optional[Union[dict[Union[str, IngredientPropertyKgNodeId], Union[dict, "IngredientProperty"]], list[Union[dict, "IngredientProperty"]]]] = empty_dict()
    concentration_ranges: Optional[Union[dict[Union[str, ConcentrationRangeDetailedIngredient], Union[dict, "ConcentrationRangeDetailed"]], list[Union[dict, "ConcentrationRangeDetailed"]]]] = empty_dict()
    solubility_toxicity: Optional[Union[dict[Union[str, SolubilityToxicitySummaryIngredient], Union[dict, "SolubilityToxicitySummary"]], list[Union[dict, "SolubilityToxicitySummary"]]]] = empty_dict()
    predictions: Optional[Union[dict[Union[str, ConcentrationPredictionIngredient], Union[dict, "ConcentrationPrediction"]], list[Union[dict, "ConcentrationPrediction"]]]] = empty_dict()
    predictions_extended: Optional[Union[dict[Union[str, MediumPredictionExtendedIngredient], Union[dict, "MediumPredictionExtended"]], list[Union[dict, "MediumPredictionExtended"]]]] = empty_dict()
    alternates: Optional[Union[Union[dict, "AlternateIngredient"], list[Union[dict, "AlternateIngredient"]]]] = empty_list()

    def __post_init__(self, *_: str, **kwargs: Any):
        self._normalize_inlined_as_list(slot_name="ingredients", slot_type=MPMediumIngredient, key_name="kg_node_id", keyed=True)

        self._normalize_inlined_as_list(slot_name="ingredient_properties", slot_type=IngredientProperty, key_name="kg_node_id", keyed=True)

        self._normalize_inlined_as_list(slot_name="concentration_ranges", slot_type=ConcentrationRangeDetailed, key_name="ingredient", keyed=True)

        self._normalize_inlined_as_list(slot_name="solubility_toxicity", slot_type=SolubilityToxicitySummary, key_name="ingredient", keyed=True)

        self._normalize_inlined_as_list(slot_name="predictions", slot_type=ConcentrationPrediction, key_name="ingredient", keyed=True)

        self._normalize_inlined_as_list(slot_name="predictions_extended", slot_type=MediumPredictionExtended, key_name="ingredient", keyed=True)

        if not isinstance(self.alternates, list):
            self.alternates = [self.alternates] if self.alternates is not None else []
        self.alternates = [v if isinstance(v, AlternateIngredient) else AlternateIngredient(**as_dict(v)) for v in self.alternates]

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class MPMediumIngredient(YAMLRoot):
    """
    A chemical component of MP medium with comprehensive properties including concentrations, stability data,
    toxicity, biological roles, and literature citations. Maps to: mp_medium_ingredient_properties.csv (68 columns
    with organism context)
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = MICROGROW["MPMediumIngredient"]
    class_class_curie: ClassVar[str] = "microgrow:MPMediumIngredient"
    class_name: ClassVar[str] = "MPMediumIngredient"
    class_model_uri: ClassVar[URIRef] = MICROGROW.MPMediumIngredient

    kg_node_id: Union[str, MPMediumIngredientKgNodeId] = None
    component: str = None
    media_role: Union[Union[str, "MediaRoleEnum"], list[Union[str, "MediaRoleEnum"]]] = None
    priority: Optional[float] = None
    chemical_formula: Optional[str] = None
    concentration: Optional[str] = None
    media_role_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    solubility: Optional[str] = None
    solubility_citation_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    solubility_citation_organism: Optional[str] = None
    lower_bound: Optional[str] = None
    lower_bound_citation: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    lower_bound_citation_organism: Optional[str] = None
    upper_bound: Optional[str] = None
    upper_bound_citation: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    upper_bound_citation_organism: Optional[str] = None
    limit_of_toxicity: Optional[str] = None
    toxicity_citation: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    toxicity_citation_organism: Optional[str] = None
    ph_effect: Optional[str] = None
    ph_effect_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    ph_effect_organism: Optional[str] = None
    pka: Optional[str] = None
    pka_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    pka_organism: Optional[str] = None
    oxidation_state_stability: Optional[str] = None
    oxidation_stability_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    oxidation_stability_organism: Optional[str] = None
    light_sensitivity: Optional[Union[str, "LightSensitivityEnum"]] = None
    light_sensitivity_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    light_sensitivity_organism: Optional[str] = None
    autoclave_stability: Optional[Union[str, "AutoclaveStabilityEnum"]] = None
    autoclave_stability_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    autoclave_stability_organism: Optional[str] = None
    stock_concentration: Optional[str] = None
    stock_concentration_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    stock_concentration_organism: Optional[str] = None
    precipitation_partners: Optional[str] = None
    precipitation_partners_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    precipitation_partners_organism: Optional[str] = None
    antagonistic_ions: Optional[str] = None
    antagonistic_ions_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    antagonistic_ions_organism: Optional[str] = None
    chelator_sensitivity: Optional[str] = None
    chelator_sensitivity_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    chelator_sensitivity_organism: Optional[str] = None
    redox_contribution: Optional[str] = None
    redox_contribution_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    redox_contribution_organism: Optional[str] = None
    cellular_role: Optional[str] = None
    cellular_role_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    cellular_role_organism: Optional[str] = None
    essential_conditional: Optional[Union[str, "EssentialityEnum"]] = None
    essential_conditional_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    essential_conditional_organism: Optional[str] = None
    uptake_transporter: Optional[str] = None
    uptake_transporter_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    uptake_transporter_organism: Optional[str] = None
    regulatory_effects: Optional[str] = None
    regulatory_effects_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    regulatory_effects_organism: Optional[str] = None
    gram_differential: Optional[str] = None
    gram_differential_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    gram_differential_organism: Optional[str] = None
    aerobe_anaerobe_differential: Optional[str] = None
    aerobe_anaerobe_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    aerobe_anaerobe_organism: Optional[str] = None
    optimal_concentration_model_organisms: Optional[str] = None
    optimal_concentration_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    optimal_concentration_organism: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.kg_node_id):
            self.MissingRequiredField("kg_node_id")
        if not isinstance(self.kg_node_id, MPMediumIngredientKgNodeId):
            self.kg_node_id = MPMediumIngredientKgNodeId(self.kg_node_id)

        if self._is_empty(self.component):
            self.MissingRequiredField("component")
        if not isinstance(self.component, str):
            self.component = str(self.component)

        if self._is_empty(self.media_role):
            self.MissingRequiredField("media_role")
        if not isinstance(self.media_role, list):
            self.media_role = [self.media_role] if self.media_role is not None else []
        self.media_role = [v if isinstance(v, MediaRoleEnum) else MediaRoleEnum(v) for v in self.media_role]

        if self.priority is not None and not isinstance(self.priority, float):
            self.priority = float(self.priority)

        if self.chemical_formula is not None and not isinstance(self.chemical_formula, str):
            self.chemical_formula = str(self.chemical_formula)

        if self.concentration is not None and not isinstance(self.concentration, str):
            self.concentration = str(self.concentration)

        if not isinstance(self.media_role_doi, list):
            self.media_role_doi = [self.media_role_doi] if self.media_role_doi is not None else []
        self.media_role_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.media_role_doi]

        if self.solubility is not None and not isinstance(self.solubility, str):
            self.solubility = str(self.solubility)

        if not isinstance(self.solubility_citation_doi, list):
            self.solubility_citation_doi = [self.solubility_citation_doi] if self.solubility_citation_doi is not None else []
        self.solubility_citation_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.solubility_citation_doi]

        if self.solubility_citation_organism is not None and not isinstance(self.solubility_citation_organism, str):
            self.solubility_citation_organism = str(self.solubility_citation_organism)

        if self.lower_bound is not None and not isinstance(self.lower_bound, str):
            self.lower_bound = str(self.lower_bound)

        if not isinstance(self.lower_bound_citation, list):
            self.lower_bound_citation = [self.lower_bound_citation] if self.lower_bound_citation is not None else []
        self.lower_bound_citation = [v if isinstance(v, DOI) else DOI(v) for v in self.lower_bound_citation]

        if self.lower_bound_citation_organism is not None and not isinstance(self.lower_bound_citation_organism, str):
            self.lower_bound_citation_organism = str(self.lower_bound_citation_organism)

        if self.upper_bound is not None and not isinstance(self.upper_bound, str):
            self.upper_bound = str(self.upper_bound)

        if not isinstance(self.upper_bound_citation, list):
            self.upper_bound_citation = [self.upper_bound_citation] if self.upper_bound_citation is not None else []
        self.upper_bound_citation = [v if isinstance(v, DOI) else DOI(v) for v in self.upper_bound_citation]

        if self.upper_bound_citation_organism is not None and not isinstance(self.upper_bound_citation_organism, str):
            self.upper_bound_citation_organism = str(self.upper_bound_citation_organism)

        if self.limit_of_toxicity is not None and not isinstance(self.limit_of_toxicity, str):
            self.limit_of_toxicity = str(self.limit_of_toxicity)

        if not isinstance(self.toxicity_citation, list):
            self.toxicity_citation = [self.toxicity_citation] if self.toxicity_citation is not None else []
        self.toxicity_citation = [v if isinstance(v, DOI) else DOI(v) for v in self.toxicity_citation]

        if self.toxicity_citation_organism is not None and not isinstance(self.toxicity_citation_organism, str):
            self.toxicity_citation_organism = str(self.toxicity_citation_organism)

        if self.ph_effect is not None and not isinstance(self.ph_effect, str):
            self.ph_effect = str(self.ph_effect)

        if not isinstance(self.ph_effect_doi, list):
            self.ph_effect_doi = [self.ph_effect_doi] if self.ph_effect_doi is not None else []
        self.ph_effect_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.ph_effect_doi]

        if self.ph_effect_organism is not None and not isinstance(self.ph_effect_organism, str):
            self.ph_effect_organism = str(self.ph_effect_organism)

        if self.pka is not None and not isinstance(self.pka, str):
            self.pka = str(self.pka)

        if not isinstance(self.pka_doi, list):
            self.pka_doi = [self.pka_doi] if self.pka_doi is not None else []
        self.pka_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.pka_doi]

        if self.pka_organism is not None and not isinstance(self.pka_organism, str):
            self.pka_organism = str(self.pka_organism)

        if self.oxidation_state_stability is not None and not isinstance(self.oxidation_state_stability, str):
            self.oxidation_state_stability = str(self.oxidation_state_stability)

        if not isinstance(self.oxidation_stability_doi, list):
            self.oxidation_stability_doi = [self.oxidation_stability_doi] if self.oxidation_stability_doi is not None else []
        self.oxidation_stability_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.oxidation_stability_doi]

        if self.oxidation_stability_organism is not None and not isinstance(self.oxidation_stability_organism, str):
            self.oxidation_stability_organism = str(self.oxidation_stability_organism)

        if self.light_sensitivity is not None and not isinstance(self.light_sensitivity, LightSensitivityEnum):
            self.light_sensitivity = LightSensitivityEnum(self.light_sensitivity)

        if not isinstance(self.light_sensitivity_doi, list):
            self.light_sensitivity_doi = [self.light_sensitivity_doi] if self.light_sensitivity_doi is not None else []
        self.light_sensitivity_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.light_sensitivity_doi]

        if self.light_sensitivity_organism is not None and not isinstance(self.light_sensitivity_organism, str):
            self.light_sensitivity_organism = str(self.light_sensitivity_organism)

        if self.autoclave_stability is not None and not isinstance(self.autoclave_stability, AutoclaveStabilityEnum):
            self.autoclave_stability = AutoclaveStabilityEnum(self.autoclave_stability)

        if not isinstance(self.autoclave_stability_doi, list):
            self.autoclave_stability_doi = [self.autoclave_stability_doi] if self.autoclave_stability_doi is not None else []
        self.autoclave_stability_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.autoclave_stability_doi]

        if self.autoclave_stability_organism is not None and not isinstance(self.autoclave_stability_organism, str):
            self.autoclave_stability_organism = str(self.autoclave_stability_organism)

        if self.stock_concentration is not None and not isinstance(self.stock_concentration, str):
            self.stock_concentration = str(self.stock_concentration)

        if not isinstance(self.stock_concentration_doi, list):
            self.stock_concentration_doi = [self.stock_concentration_doi] if self.stock_concentration_doi is not None else []
        self.stock_concentration_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.stock_concentration_doi]

        if self.stock_concentration_organism is not None and not isinstance(self.stock_concentration_organism, str):
            self.stock_concentration_organism = str(self.stock_concentration_organism)

        if self.precipitation_partners is not None and not isinstance(self.precipitation_partners, str):
            self.precipitation_partners = str(self.precipitation_partners)

        if not isinstance(self.precipitation_partners_doi, list):
            self.precipitation_partners_doi = [self.precipitation_partners_doi] if self.precipitation_partners_doi is not None else []
        self.precipitation_partners_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.precipitation_partners_doi]

        if self.precipitation_partners_organism is not None and not isinstance(self.precipitation_partners_organism, str):
            self.precipitation_partners_organism = str(self.precipitation_partners_organism)

        if self.antagonistic_ions is not None and not isinstance(self.antagonistic_ions, str):
            self.antagonistic_ions = str(self.antagonistic_ions)

        if not isinstance(self.antagonistic_ions_doi, list):
            self.antagonistic_ions_doi = [self.antagonistic_ions_doi] if self.antagonistic_ions_doi is not None else []
        self.antagonistic_ions_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.antagonistic_ions_doi]

        if self.antagonistic_ions_organism is not None and not isinstance(self.antagonistic_ions_organism, str):
            self.antagonistic_ions_organism = str(self.antagonistic_ions_organism)

        if self.chelator_sensitivity is not None and not isinstance(self.chelator_sensitivity, str):
            self.chelator_sensitivity = str(self.chelator_sensitivity)

        if not isinstance(self.chelator_sensitivity_doi, list):
            self.chelator_sensitivity_doi = [self.chelator_sensitivity_doi] if self.chelator_sensitivity_doi is not None else []
        self.chelator_sensitivity_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.chelator_sensitivity_doi]

        if self.chelator_sensitivity_organism is not None and not isinstance(self.chelator_sensitivity_organism, str):
            self.chelator_sensitivity_organism = str(self.chelator_sensitivity_organism)

        if self.redox_contribution is not None and not isinstance(self.redox_contribution, str):
            self.redox_contribution = str(self.redox_contribution)

        if not isinstance(self.redox_contribution_doi, list):
            self.redox_contribution_doi = [self.redox_contribution_doi] if self.redox_contribution_doi is not None else []
        self.redox_contribution_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.redox_contribution_doi]

        if self.redox_contribution_organism is not None and not isinstance(self.redox_contribution_organism, str):
            self.redox_contribution_organism = str(self.redox_contribution_organism)

        if self.cellular_role is not None and not isinstance(self.cellular_role, str):
            self.cellular_role = str(self.cellular_role)

        if not isinstance(self.cellular_role_doi, list):
            self.cellular_role_doi = [self.cellular_role_doi] if self.cellular_role_doi is not None else []
        self.cellular_role_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.cellular_role_doi]

        if self.cellular_role_organism is not None and not isinstance(self.cellular_role_organism, str):
            self.cellular_role_organism = str(self.cellular_role_organism)

        if self.essential_conditional is not None and not isinstance(self.essential_conditional, EssentialityEnum):
            self.essential_conditional = EssentialityEnum(self.essential_conditional)

        if not isinstance(self.essential_conditional_doi, list):
            self.essential_conditional_doi = [self.essential_conditional_doi] if self.essential_conditional_doi is not None else []
        self.essential_conditional_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.essential_conditional_doi]

        if self.essential_conditional_organism is not None and not isinstance(self.essential_conditional_organism, str):
            self.essential_conditional_organism = str(self.essential_conditional_organism)

        if self.uptake_transporter is not None and not isinstance(self.uptake_transporter, str):
            self.uptake_transporter = str(self.uptake_transporter)

        if not isinstance(self.uptake_transporter_doi, list):
            self.uptake_transporter_doi = [self.uptake_transporter_doi] if self.uptake_transporter_doi is not None else []
        self.uptake_transporter_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.uptake_transporter_doi]

        if self.uptake_transporter_organism is not None and not isinstance(self.uptake_transporter_organism, str):
            self.uptake_transporter_organism = str(self.uptake_transporter_organism)

        if self.regulatory_effects is not None and not isinstance(self.regulatory_effects, str):
            self.regulatory_effects = str(self.regulatory_effects)

        if not isinstance(self.regulatory_effects_doi, list):
            self.regulatory_effects_doi = [self.regulatory_effects_doi] if self.regulatory_effects_doi is not None else []
        self.regulatory_effects_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.regulatory_effects_doi]

        if self.regulatory_effects_organism is not None and not isinstance(self.regulatory_effects_organism, str):
            self.regulatory_effects_organism = str(self.regulatory_effects_organism)

        if self.gram_differential is not None and not isinstance(self.gram_differential, str):
            self.gram_differential = str(self.gram_differential)

        if not isinstance(self.gram_differential_doi, list):
            self.gram_differential_doi = [self.gram_differential_doi] if self.gram_differential_doi is not None else []
        self.gram_differential_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.gram_differential_doi]

        if self.gram_differential_organism is not None and not isinstance(self.gram_differential_organism, str):
            self.gram_differential_organism = str(self.gram_differential_organism)

        if self.aerobe_anaerobe_differential is not None and not isinstance(self.aerobe_anaerobe_differential, str):
            self.aerobe_anaerobe_differential = str(self.aerobe_anaerobe_differential)

        if not isinstance(self.aerobe_anaerobe_doi, list):
            self.aerobe_anaerobe_doi = [self.aerobe_anaerobe_doi] if self.aerobe_anaerobe_doi is not None else []
        self.aerobe_anaerobe_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.aerobe_anaerobe_doi]

        if self.aerobe_anaerobe_organism is not None and not isinstance(self.aerobe_anaerobe_organism, str):
            self.aerobe_anaerobe_organism = str(self.aerobe_anaerobe_organism)

        if self.optimal_concentration_model_organisms is not None and not isinstance(self.optimal_concentration_model_organisms, str):
            self.optimal_concentration_model_organisms = str(self.optimal_concentration_model_organisms)

        if not isinstance(self.optimal_concentration_doi, list):
            self.optimal_concentration_doi = [self.optimal_concentration_doi] if self.optimal_concentration_doi is not None else []
        self.optimal_concentration_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.optimal_concentration_doi]

        if self.optimal_concentration_organism is not None and not isinstance(self.optimal_concentration_organism, str):
            self.optimal_concentration_organism = str(self.optimal_concentration_organism)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class ConcentrationPrediction(YAMLRoot):
    """
    Predicted concentration ranges for a media ingredient with pH effects. Maps to: mp_medium_predictions.tsv (9
    columns)
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = MICROGROW["ConcentrationPrediction"]
    class_class_curie: ClassVar[str] = "microgrow:ConcentrationPrediction"
    class_name: ClassVar[str] = "ConcentrationPrediction"
    class_model_uri: ClassVar[URIRef] = MICROGROW.ConcentrationPrediction

    ingredient: Union[str, ConcentrationPredictionIngredient] = None
    min_concentration: Optional[float] = None
    max_concentration: Optional[float] = None
    unit: Optional[Union[str, "ConcentrationUnitEnum"]] = None
    essential: Optional[Union[bool, Bool]] = None
    confidence: Optional[float] = None
    ph_at_low: Optional[float] = None
    ph_at_high: Optional[float] = None
    ph_effect: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.ingredient):
            self.MissingRequiredField("ingredient")
        if not isinstance(self.ingredient, ConcentrationPredictionIngredient):
            self.ingredient = ConcentrationPredictionIngredient(self.ingredient)

        if self.min_concentration is not None and not isinstance(self.min_concentration, float):
            self.min_concentration = float(self.min_concentration)

        if self.max_concentration is not None and not isinstance(self.max_concentration, float):
            self.max_concentration = float(self.max_concentration)

        if self.unit is not None and not isinstance(self.unit, ConcentrationUnitEnum):
            self.unit = ConcentrationUnitEnum(self.unit)

        if self.essential is not None and not isinstance(self.essential, Bool):
            self.essential = Bool(self.essential)

        if self.confidence is not None and not isinstance(self.confidence, float):
            self.confidence = float(self.confidence)

        if self.ph_at_low is not None and not isinstance(self.ph_at_low, float):
            self.ph_at_low = float(self.ph_at_low)

        if self.ph_at_high is not None and not isinstance(self.ph_at_high, float):
            self.ph_at_high = float(self.ph_at_high)

        if self.ph_effect is not None and not isinstance(self.ph_effect, str):
            self.ph_effect = str(self.ph_effect)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class AlternateIngredient(YAMLRoot):
    """
    Alternative ingredient recommendation with rationale and evidence. Maps to: alternate_ingredients_table.csv (7
    columns)
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = MICROGROW["AlternateIngredient"]
    class_class_curie: ClassVar[str] = "microgrow:AlternateIngredient"
    class_name: ClassVar[str] = "AlternateIngredient"
    class_model_uri: ClassVar[URIRef] = MICROGROW.AlternateIngredient

    original_ingredient: str = None
    alternate_ingredient: str = None
    rationale: Optional[str] = None
    alternate_role: Optional[Union[str, "MediaRoleEnum"]] = None
    doi_citation: Optional[Union[str, DOI]] = None
    kg_node_id: Optional[str] = None
    kg_node_label: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.original_ingredient):
            self.MissingRequiredField("original_ingredient")
        if not isinstance(self.original_ingredient, str):
            self.original_ingredient = str(self.original_ingredient)

        if self._is_empty(self.alternate_ingredient):
            self.MissingRequiredField("alternate_ingredient")
        if not isinstance(self.alternate_ingredient, str):
            self.alternate_ingredient = str(self.alternate_ingredient)

        if self.rationale is not None and not isinstance(self.rationale, str):
            self.rationale = str(self.rationale)

        if self.alternate_role is not None and not isinstance(self.alternate_role, MediaRoleEnum):
            self.alternate_role = MediaRoleEnum(self.alternate_role)

        if self.doi_citation is not None and not isinstance(self.doi_citation, DOI):
            self.doi_citation = DOI(self.doi_citation)

        if self.kg_node_id is not None and not isinstance(self.kg_node_id, str):
            self.kg_node_id = str(self.kg_node_id)

        if self.kg_node_label is not None and not isinstance(self.kg_node_label, str):
            self.kg_node_label = str(self.kg_node_label)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class IngredientProperty(YAMLRoot):
    """
    Core ingredient properties including media role, cellular role, concentration ranges, and chemical properties.
    Maps to: ingredient_properties_YYYYMMDD.tsv (20 rows, 32-33 columns)
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = MICROGROW["IngredientProperty"]
    class_class_curie: ClassVar[str] = "microgrow:IngredientProperty"
    class_name: ClassVar[str] = "IngredientProperty"
    class_model_uri: ClassVar[URIRef] = MICROGROW.IngredientProperty

    kg_node_id: Union[str, IngredientPropertyKgNodeId] = None
    component: str = None
    media_role: Union[Union[str, "MediaRoleEnum"], list[Union[str, "MediaRoleEnum"]]] = None
    chemical_formula: Optional[str] = None
    priority: Optional[float] = None
    concentration: Optional[str] = None
    lower_bound: Optional[str] = None
    upper_bound: Optional[str] = None
    optimal_concentration_model_organisms: Optional[str] = None
    solubility: Optional[str] = None
    limit_of_toxicity: Optional[str] = None
    ph_effect: Optional[str] = None
    pka: Optional[str] = None
    oxidation_state_stability: Optional[str] = None
    light_sensitivity: Optional[Union[str, "LightSensitivityEnum"]] = None
    autoclave_stability: Optional[Union[str, "AutoclaveStabilityEnum"]] = None
    stock_concentration: Optional[str] = None
    precipitation_partners: Optional[str] = None
    antagonistic_ions: Optional[str] = None
    chelator_sensitivity: Optional[str] = None
    redox_contribution: Optional[str] = None
    cellular_role_specific: Optional[Union[str, "CellularRoleEnum"]] = None
    cellular_role_broad: Optional[Union[Union[str, "BroadCellularRoleEnum"], list[Union[str, "BroadCellularRoleEnum"]]]] = empty_list()
    essential_conditional: Optional[Union[str, "EssentialityEnum"]] = None
    uptake_transporter: Optional[str] = None
    regulatory_effects: Optional[str] = None
    gram_differential: Optional[str] = None
    aerobe_anaerobe_differential: Optional[str] = None
    solubility_citation_organism: Optional[str] = None
    lower_bound_citation_organism: Optional[str] = None
    upper_bound_citation_organism: Optional[str] = None
    toxicity_citation_organism: Optional[str] = None
    optimal_concentration_organism: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.kg_node_id):
            self.MissingRequiredField("kg_node_id")
        if not isinstance(self.kg_node_id, IngredientPropertyKgNodeId):
            self.kg_node_id = IngredientPropertyKgNodeId(self.kg_node_id)

        if self._is_empty(self.component):
            self.MissingRequiredField("component")
        if not isinstance(self.component, str):
            self.component = str(self.component)

        if self._is_empty(self.media_role):
            self.MissingRequiredField("media_role")
        if not isinstance(self.media_role, list):
            self.media_role = [self.media_role] if self.media_role is not None else []
        self.media_role = [v if isinstance(v, MediaRoleEnum) else MediaRoleEnum(v) for v in self.media_role]

        if self.chemical_formula is not None and not isinstance(self.chemical_formula, str):
            self.chemical_formula = str(self.chemical_formula)

        if self.priority is not None and not isinstance(self.priority, float):
            self.priority = float(self.priority)

        if self.concentration is not None and not isinstance(self.concentration, str):
            self.concentration = str(self.concentration)

        if self.lower_bound is not None and not isinstance(self.lower_bound, str):
            self.lower_bound = str(self.lower_bound)

        if self.upper_bound is not None and not isinstance(self.upper_bound, str):
            self.upper_bound = str(self.upper_bound)

        if self.optimal_concentration_model_organisms is not None and not isinstance(self.optimal_concentration_model_organisms, str):
            self.optimal_concentration_model_organisms = str(self.optimal_concentration_model_organisms)

        if self.solubility is not None and not isinstance(self.solubility, str):
            self.solubility = str(self.solubility)

        if self.limit_of_toxicity is not None and not isinstance(self.limit_of_toxicity, str):
            self.limit_of_toxicity = str(self.limit_of_toxicity)

        if self.ph_effect is not None and not isinstance(self.ph_effect, str):
            self.ph_effect = str(self.ph_effect)

        if self.pka is not None and not isinstance(self.pka, str):
            self.pka = str(self.pka)

        if self.oxidation_state_stability is not None and not isinstance(self.oxidation_state_stability, str):
            self.oxidation_state_stability = str(self.oxidation_state_stability)

        if self.light_sensitivity is not None and not isinstance(self.light_sensitivity, LightSensitivityEnum):
            self.light_sensitivity = LightSensitivityEnum(self.light_sensitivity)

        if self.autoclave_stability is not None and not isinstance(self.autoclave_stability, AutoclaveStabilityEnum):
            self.autoclave_stability = AutoclaveStabilityEnum(self.autoclave_stability)

        if self.stock_concentration is not None and not isinstance(self.stock_concentration, str):
            self.stock_concentration = str(self.stock_concentration)

        if self.precipitation_partners is not None and not isinstance(self.precipitation_partners, str):
            self.precipitation_partners = str(self.precipitation_partners)

        if self.antagonistic_ions is not None and not isinstance(self.antagonistic_ions, str):
            self.antagonistic_ions = str(self.antagonistic_ions)

        if self.chelator_sensitivity is not None and not isinstance(self.chelator_sensitivity, str):
            self.chelator_sensitivity = str(self.chelator_sensitivity)

        if self.redox_contribution is not None and not isinstance(self.redox_contribution, str):
            self.redox_contribution = str(self.redox_contribution)

        if self.cellular_role_specific is not None and not isinstance(self.cellular_role_specific, CellularRoleEnum):
            self.cellular_role_specific = CellularRoleEnum(self.cellular_role_specific)

        if not isinstance(self.cellular_role_broad, list):
            self.cellular_role_broad = [self.cellular_role_broad] if self.cellular_role_broad is not None else []
        self.cellular_role_broad = [v if isinstance(v, BroadCellularRoleEnum) else BroadCellularRoleEnum(v) for v in self.cellular_role_broad]

        if self.essential_conditional is not None and not isinstance(self.essential_conditional, EssentialityEnum):
            self.essential_conditional = EssentialityEnum(self.essential_conditional)

        if self.uptake_transporter is not None and not isinstance(self.uptake_transporter, str):
            self.uptake_transporter = str(self.uptake_transporter)

        if self.regulatory_effects is not None and not isinstance(self.regulatory_effects, str):
            self.regulatory_effects = str(self.regulatory_effects)

        if self.gram_differential is not None and not isinstance(self.gram_differential, str):
            self.gram_differential = str(self.gram_differential)

        if self.aerobe_anaerobe_differential is not None and not isinstance(self.aerobe_anaerobe_differential, str):
            self.aerobe_anaerobe_differential = str(self.aerobe_anaerobe_differential)

        if self.solubility_citation_organism is not None and not isinstance(self.solubility_citation_organism, str):
            self.solubility_citation_organism = str(self.solubility_citation_organism)

        if self.lower_bound_citation_organism is not None and not isinstance(self.lower_bound_citation_organism, str):
            self.lower_bound_citation_organism = str(self.lower_bound_citation_organism)

        if self.upper_bound_citation_organism is not None and not isinstance(self.upper_bound_citation_organism, str):
            self.upper_bound_citation_organism = str(self.upper_bound_citation_organism)

        if self.toxicity_citation_organism is not None and not isinstance(self.toxicity_citation_organism, str):
            self.toxicity_citation_organism = str(self.toxicity_citation_organism)

        if self.optimal_concentration_organism is not None and not isinstance(self.optimal_concentration_organism, str):
            self.optimal_concentration_organism = str(self.optimal_concentration_organism)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class ConcentrationRangeDetailed(YAMLRoot):
    """
    Detailed concentration measurements with organism-specific evidence and DOI citations for each measurement type.
    Maps to: concentration_ranges_detailed_YYYYMMDD.tsv (288 rows, 24 columns)
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = MICROGROW["ConcentrationRangeDetailed"]
    class_class_curie: ClassVar[str] = "microgrow:ConcentrationRangeDetailed"
    class_name: ClassVar[str] = "ConcentrationRangeDetailed"
    class_model_uri: ClassVar[URIRef] = MICROGROW.ConcentrationRangeDetailed

    ingredient: Union[str, ConcentrationRangeDetailedIngredient] = None
    formula: Optional[str] = None
    kg_node_id: Optional[str] = None
    priority: Optional[float] = None
    standard_concentration: Optional[str] = None
    lower_bound: Optional[str] = None
    lower_bound_organism: Optional[str] = None
    lower_bound_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    lower_bound_evidence: Optional[str] = None
    upper_bound: Optional[str] = None
    upper_bound_organism: Optional[str] = None
    upper_bound_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    upper_bound_evidence: Optional[str] = None
    optimal_concentration: Optional[str] = None
    optimal_conc_organism: Optional[str] = None
    optimal_conc_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    optimal_conc_evidence: Optional[str] = None
    solubility: Optional[str] = None
    solubility_organism: Optional[str] = None
    solubility_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    solubility_evidence: Optional[str] = None
    toxicity_limit: Optional[str] = None
    toxicity_organism: Optional[str] = None
    toxicity_doi: Optional[Union[Union[str, DOI], list[Union[str, DOI]]]] = empty_list()
    toxicity_evidence: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.ingredient):
            self.MissingRequiredField("ingredient")
        if not isinstance(self.ingredient, ConcentrationRangeDetailedIngredient):
            self.ingredient = ConcentrationRangeDetailedIngredient(self.ingredient)

        if self.formula is not None and not isinstance(self.formula, str):
            self.formula = str(self.formula)

        if self.kg_node_id is not None and not isinstance(self.kg_node_id, str):
            self.kg_node_id = str(self.kg_node_id)

        if self.priority is not None and not isinstance(self.priority, float):
            self.priority = float(self.priority)

        if self.standard_concentration is not None and not isinstance(self.standard_concentration, str):
            self.standard_concentration = str(self.standard_concentration)

        if self.lower_bound is not None and not isinstance(self.lower_bound, str):
            self.lower_bound = str(self.lower_bound)

        if self.lower_bound_organism is not None and not isinstance(self.lower_bound_organism, str):
            self.lower_bound_organism = str(self.lower_bound_organism)

        if not isinstance(self.lower_bound_doi, list):
            self.lower_bound_doi = [self.lower_bound_doi] if self.lower_bound_doi is not None else []
        self.lower_bound_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.lower_bound_doi]

        if self.lower_bound_evidence is not None and not isinstance(self.lower_bound_evidence, str):
            self.lower_bound_evidence = str(self.lower_bound_evidence)

        if self.upper_bound is not None and not isinstance(self.upper_bound, str):
            self.upper_bound = str(self.upper_bound)

        if self.upper_bound_organism is not None and not isinstance(self.upper_bound_organism, str):
            self.upper_bound_organism = str(self.upper_bound_organism)

        if not isinstance(self.upper_bound_doi, list):
            self.upper_bound_doi = [self.upper_bound_doi] if self.upper_bound_doi is not None else []
        self.upper_bound_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.upper_bound_doi]

        if self.upper_bound_evidence is not None and not isinstance(self.upper_bound_evidence, str):
            self.upper_bound_evidence = str(self.upper_bound_evidence)

        if self.optimal_concentration is not None and not isinstance(self.optimal_concentration, str):
            self.optimal_concentration = str(self.optimal_concentration)

        if self.optimal_conc_organism is not None and not isinstance(self.optimal_conc_organism, str):
            self.optimal_conc_organism = str(self.optimal_conc_organism)

        if not isinstance(self.optimal_conc_doi, list):
            self.optimal_conc_doi = [self.optimal_conc_doi] if self.optimal_conc_doi is not None else []
        self.optimal_conc_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.optimal_conc_doi]

        if self.optimal_conc_evidence is not None and not isinstance(self.optimal_conc_evidence, str):
            self.optimal_conc_evidence = str(self.optimal_conc_evidence)

        if self.solubility is not None and not isinstance(self.solubility, str):
            self.solubility = str(self.solubility)

        if self.solubility_organism is not None and not isinstance(self.solubility_organism, str):
            self.solubility_organism = str(self.solubility_organism)

        if not isinstance(self.solubility_doi, list):
            self.solubility_doi = [self.solubility_doi] if self.solubility_doi is not None else []
        self.solubility_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.solubility_doi]

        if self.solubility_evidence is not None and not isinstance(self.solubility_evidence, str):
            self.solubility_evidence = str(self.solubility_evidence)

        if self.toxicity_limit is not None and not isinstance(self.toxicity_limit, str):
            self.toxicity_limit = str(self.toxicity_limit)

        if self.toxicity_organism is not None and not isinstance(self.toxicity_organism, str):
            self.toxicity_organism = str(self.toxicity_organism)

        if not isinstance(self.toxicity_doi, list):
            self.toxicity_doi = [self.toxicity_doi] if self.toxicity_doi is not None else []
        self.toxicity_doi = [v if isinstance(v, DOI) else DOI(v) for v in self.toxicity_doi]

        if self.toxicity_evidence is not None and not isinstance(self.toxicity_evidence, str):
            self.toxicity_evidence = str(self.toxicity_evidence)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class SolubilityToxicitySummary(YAMLRoot):
    """
    Simplified summary of solubility and toxicity properties. Maps to: solubility_toxicity_YYYYMMDD.tsv (20 rows, 9
    columns)
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = MICROGROW["SolubilityToxicitySummary"]
    class_class_curie: ClassVar[str] = "microgrow:SolubilityToxicitySummary"
    class_name: ClassVar[str] = "SolubilityToxicitySummary"
    class_model_uri: ClassVar[URIRef] = MICROGROW.SolubilityToxicitySummary

    ingredient: Union[str, SolubilityToxicitySummaryIngredient] = None
    formula: Optional[str] = None
    kg_node_id: Optional[str] = None
    solubility_mM: Optional[str] = None
    solubility_organism: Optional[str] = None
    solubility_doi: Optional[Union[str, DOI]] = None
    toxicity_limit: Optional[str] = None
    toxicity_organism: Optional[str] = None
    toxicity_doi: Optional[Union[str, DOI]] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.ingredient):
            self.MissingRequiredField("ingredient")
        if not isinstance(self.ingredient, SolubilityToxicitySummaryIngredient):
            self.ingredient = SolubilityToxicitySummaryIngredient(self.ingredient)

        if self.formula is not None and not isinstance(self.formula, str):
            self.formula = str(self.formula)

        if self.kg_node_id is not None and not isinstance(self.kg_node_id, str):
            self.kg_node_id = str(self.kg_node_id)

        if self.solubility_mM is not None and not isinstance(self.solubility_mM, str):
            self.solubility_mM = str(self.solubility_mM)

        if self.solubility_organism is not None and not isinstance(self.solubility_organism, str):
            self.solubility_organism = str(self.solubility_organism)

        if self.solubility_doi is not None and not isinstance(self.solubility_doi, DOI):
            self.solubility_doi = DOI(self.solubility_doi)

        if self.toxicity_limit is not None and not isinstance(self.toxicity_limit, str):
            self.toxicity_limit = str(self.toxicity_limit)

        if self.toxicity_organism is not None and not isinstance(self.toxicity_organism, str):
            self.toxicity_organism = str(self.toxicity_organism)

        if self.toxicity_doi is not None and not isinstance(self.toxicity_doi, DOI):
            self.toxicity_doi = DOI(self.toxicity_doi)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class MediumPredictionExtended(YAMLRoot):
    """
    Medium concentration predictions with extended ingredient properties. Maps to:
    medium_predictions_extended_YYYYMMDD.tsv (20 rows, 13 columns)
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = MICROGROW["MediumPredictionExtended"]
    class_class_curie: ClassVar[str] = "microgrow:MediumPredictionExtended"
    class_name: ClassVar[str] = "MediumPredictionExtended"
    class_model_uri: ClassVar[URIRef] = MICROGROW.MediumPredictionExtended

    ingredient: Union[str, MediumPredictionExtendedIngredient] = None
    min_concentration: Optional[float] = None
    max_concentration: Optional[float] = None
    unit: Optional[Union[str, "ConcentrationUnitEnum"]] = None
    essential: Optional[Union[bool, Bool]] = None
    confidence: Optional[float] = None
    ph_at_low: Optional[float] = None
    ph_at_high: Optional[float] = None
    ph_effect: Optional[str] = None
    chemical_formula: Optional[str] = None
    kg_node_id: Optional[str] = None
    solubility: Optional[str] = None
    limit_of_toxicity: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.ingredient):
            self.MissingRequiredField("ingredient")
        if not isinstance(self.ingredient, MediumPredictionExtendedIngredient):
            self.ingredient = MediumPredictionExtendedIngredient(self.ingredient)

        if self.min_concentration is not None and not isinstance(self.min_concentration, float):
            self.min_concentration = float(self.min_concentration)

        if self.max_concentration is not None and not isinstance(self.max_concentration, float):
            self.max_concentration = float(self.max_concentration)

        if self.unit is not None and not isinstance(self.unit, ConcentrationUnitEnum):
            self.unit = ConcentrationUnitEnum(self.unit)

        if self.essential is not None and not isinstance(self.essential, Bool):
            self.essential = Bool(self.essential)

        if self.confidence is not None and not isinstance(self.confidence, float):
            self.confidence = float(self.confidence)

        if self.ph_at_low is not None and not isinstance(self.ph_at_low, float):
            self.ph_at_low = float(self.ph_at_low)

        if self.ph_at_high is not None and not isinstance(self.ph_at_high, float):
            self.ph_at_high = float(self.ph_at_high)

        if self.ph_effect is not None and not isinstance(self.ph_effect, str):
            self.ph_effect = str(self.ph_effect)

        if self.chemical_formula is not None and not isinstance(self.chemical_formula, str):
            self.chemical_formula = str(self.chemical_formula)

        if self.kg_node_id is not None and not isinstance(self.kg_node_id, str):
            self.kg_node_id = str(self.kg_node_id)

        if self.solubility is not None and not isinstance(self.solubility, str):
            self.solubility = str(self.solubility)

        if self.limit_of_toxicity is not None and not isinstance(self.limit_of_toxicity, str):
            self.limit_of_toxicity = str(self.limit_of_toxicity)

        super().__post_init__(**kwargs)


# Enumerations
class MediaRoleEnum(EnumDefinitionImpl):
    """
    Functional roles of ingredients in microbial growth media. Based on actual roles in MP medium ingredient
    properties.
    """
    CARBON_SOURCE = PermissibleValue(
        text="CARBON_SOURCE",
        description="Primary carbon and energy source",
        meaning=CHEBI["33284"])
    NITROGEN_SOURCE = PermissibleValue(
        text="NITROGEN_SOURCE",
        description="Nitrogen source for amino acids and nucleotides",
        meaning=CHEBI["33273"])
    SULFUR_SOURCE = PermissibleValue(
        text="SULFUR_SOURCE",
        description="Sulfur source for cysteine and methionine",
        meaning=CHEBI["33261"])
    PHOSPHATE_SOURCE = PermissibleValue(
        text="PHOSPHATE_SOURCE",
        description="Phosphate source for nucleotides and ATP",
        meaning=CHEBI["26020"])
    PH_BUFFER = PermissibleValue(
        text="PH_BUFFER",
        description="pH buffering agent (6.0-8.0 range)",
        meaning=CHEBI["35225"])
    TRACE_ELEMENT_FE = PermissibleValue(
        text="TRACE_ELEMENT_FE",
        description="Iron trace element (Fe²⁺/Fe³⁺)",
        meaning=CHEBI["18248"])
    TRACE_ELEMENT_ZN = PermissibleValue(
        text="TRACE_ELEMENT_ZN",
        description="Zinc trace element",
        meaning=CHEBI["27363"])
    TRACE_ELEMENT_MN = PermissibleValue(
        text="TRACE_ELEMENT_MN",
        description="Manganese trace element",
        meaning=CHEBI["18291"])
    TRACE_ELEMENT_CU = PermissibleValue(
        text="TRACE_ELEMENT_CU",
        description="Copper trace element",
        meaning=CHEBI["28694"])
    TRACE_ELEMENT_CO = PermissibleValue(
        text="TRACE_ELEMENT_CO",
        description="Cobalt trace element (B12 cofactor)",
        meaning=CHEBI["27638"])
    TRACE_ELEMENT_MO = PermissibleValue(
        text="TRACE_ELEMENT_MO",
        description="Molybdenum trace element",
        meaning=CHEBI["28685"])
    ESSENTIAL_MACRONUTRIENT_MG = PermissibleValue(
        text="ESSENTIAL_MACRONUTRIENT_MG",
        description="Magnesium - enzyme cofactor, ribosome stabilization",
        meaning=CHEBI["18420"])
    ESSENTIAL_MACRONUTRIENT_CA = PermissibleValue(
        text="ESSENTIAL_MACRONUTRIENT_CA",
        description="Calcium - cell wall stability, signaling",
        meaning=CHEBI["22984"])
    VITAMIN_COFACTOR_PRECURSOR = PermissibleValue(
        text="VITAMIN_COFACTOR_PRECURSOR",
        description="Vitamin or cofactor precursor (biotin, thiamin)",
        meaning=CHEBI["27027"])
    CHELATOR_METAL_BUFFER = PermissibleValue(
        text="CHELATOR_METAL_BUFFER",
        description="Chelating agent for metal buffering (citrate, EDTA)",
        meaning=CHEBI["38161"])
    RARE_EARTH_ELEMENT = PermissibleValue(
        text="RARE_EARTH_ELEMENT",
        description="Rare earth element (Dy, Nd, Pr for methanol dehydrogenase)",
        meaning=CHEBI["33319"])
    NITROGEN_SULFUR_SOURCE = PermissibleValue(
        text="NITROGEN_SULFUR_SOURCE",
        description="Combined nitrogen and sulfur source (e.g., ammonium sulfate)")
    PHOSPHATE_PH_BUFFER = PermissibleValue(
        text="PHOSPHATE_PH_BUFFER",
        description="Combined phosphate source and pH buffer (e.g., K₂HPO₄)")

    _defn = EnumDefinition(
        name="MediaRoleEnum",
        description="""Functional roles of ingredients in microbial growth media. Based on actual roles in MP medium ingredient properties.""",
    )

class CellularRoleEnum(EnumDefinitionImpl):
    """
    Specific cellular and metabolic roles of media ingredients. Based on detailed functional characterization from
    literature.
    """
    NUCLEOTIDE_PHOSPHOLIPID_METABOLISM = PermissibleValue(
        text="NUCLEOTIDE_PHOSPHOLIPID_METABOLISM",
        description="ATP/GTP, DNA/RNA, phospholipids, signaling",
        meaning=CHEBI["26020"])
    CARBOXYLASE_COFACTOR = PermissibleValue(
        text="CARBOXYLASE_COFACTOR",
        description="Carboxylase cofactor for ACC, PC, PCC enzymes",
        meaning=CHEBI["27638"])
    COPPER_OXIDASE_SOD = PermissibleValue(
        text="COPPER_OXIDASE_SOD",
        description="Cytochrome c oxidase, Cu/Zn-SOD (SodC), CueO oxidase",
        meaning=CHEBI["28694"])
    VITAMIN_B12_COBALAMIN = PermissibleValue(
        text="VITAMIN_B12_COBALAMIN",
        description="Essential B12 (cobalamin) for methionine synthase, methylmalonyl-CoA mutase",
        meaning=CHEBI["27638"])
    PHOSPHATE_SOURCE = PermissibleValue(
        text="PHOSPHATE_SOURCE",
        description="Essential phosphate source for all bacteria",
        meaning=CHEBI["26020"])
    IRON_SULFUR_CLUSTERS = PermissibleValue(
        text="IRON_SULFUR_CLUSTERS",
        description="Fe-S clusters, cytochromes, ribonucleotide reductase",
        meaning=CHEBI["18248"])
    LANTHANIDE_HEAVY_LOW_ACTIVITY = PermissibleValue(
        text="LANTHANIDE_HEAVY_LOW_ACTIVITY",
        description="Heavy lanthanides with greatly reduced XoxF-MDH activity",
        meaning=CHEBI["33319"])
    METHANOL_DEHYDROGENASE_SUBSTRATE = PermissibleValue(
        text="METHANOL_DEHYDROGENASE_SUBSTRATE",
        description="MDH substrate for PQQ-dependent oxidation in C1 metabolism",
        meaning=CHEBI["17790"])
    MANGANESE_SOD_PHOTOSYSTEM = PermissibleValue(
        text="MANGANESE_SOD_PHOTOSYSTEM",
        description="Mn-SOD (SodA) and photosystem II (Mn₄CaO₅)",
        meaning=CHEBI["18291"])
    MOLYBDENUM_COFACTOR = PermissibleValue(
        text="MOLYBDENUM_COFACTOR",
        description="Moco required for nitrogenase, nitrate reductase, DMSO reductase",
        meaning=CHEBI["28685"])
    NEODYMIUM_EFFECTIVE_MDH = PermissibleValue(
        text="NEODYMIUM_EFFECTIVE_MDH",
        description="Nd is highly effective XoxF-MDH cofactor with highest activity",
        meaning=CHEBI["33319"])
    PH_BUFFER_NON_METABOLIZED = PermissibleValue(
        text="PH_BUFFER_NON_METABOLIZED",
        description="Non-metabolized pH buffer",
        meaning=CHEBI["35225"])
    PRASEODYMIUM_MDH_SUPPORT = PermissibleValue(
        text="PRASEODYMIUM_MDH_SUPPORT",
        description="Pr supports XoxF-MDH activity in methylotrophs",
        meaning=CHEBI["33319"])
    NITROGEN_SOURCE_PRIMARY = PermissibleValue(
        text="NITROGEN_SOURCE_PRIMARY",
        description="Primary N source via glutamine synthetase to all N compounds",
        meaning=CHEBI["33273"])
    RIBOSOME_STABILIZATION_ATP = PermissibleValue(
        text="RIBOSOME_STABILIZATION_ATP",
        description="Ribosome stabilization (≥170 Mg²⁺/ribosome) and ATP neutralization",
        meaning=CHEBI["18420"])
    SIGNALING_CELL_DIVISION = PermissibleValue(
        text="SIGNALING_CELL_DIVISION",
        description="Signaling, cell division, transformation competency, sporulation",
        meaning=CHEBI["22984"])
    TCA_INTERMEDIATE_CHELATOR = PermissibleValue(
        text="TCA_INTERMEDIATE_CHELATOR",
        description="TCA intermediate, C source, Fe-citrate uptake",
        meaning=CHEBI["30769"])
    THIAMIN_PYROPHOSPHATE_COFACTOR = PermissibleValue(
        text="THIAMIN_PYROPHOSPHATE_COFACTOR",
        description="TPP cofactor for pyruvate dehydrogenase, α-KG dehydrogenase, transketolase",
        meaning=CHEBI["49105"])
    TUNGSTEN_SPECIFIC_ENZYMES = PermissibleValue(
        text="TUNGSTEN_SPECIFIC_ENZYMES",
        description="W-specific enzymes (aldehyde oxidoreductases, W-formate dehydrogenase)",
        meaning=CHEBI["27998"])
    ZINC_PROTEOME = PermissibleValue(
        text="ZINC_PROTEOME",
        description="~5-6% proteome Zn-binding (zinc fingers, proteases, RNAP)",
        meaning=CHEBI["27363"])

    _defn = EnumDefinition(
        name="CellularRoleEnum",
        description="""Specific cellular and metabolic roles of media ingredients. Based on detailed functional characterization from literature.""",
    )

class BroadCellularRoleEnum(EnumDefinitionImpl):
    """
    Broad functional categories for cellular roles. Enables hierarchical organization and simplified queries.
    """
    ENERGY_METABOLISM = PermissibleValue(
        text="ENERGY_METABOLISM",
        description="ATP/GTP synthesis, electron transport, energy generation")
    NUCLEIC_ACID_METABOLISM = PermissibleValue(
        text="NUCLEIC_ACID_METABOLISM",
        description="DNA/RNA synthesis, nucleotide metabolism")
    PROTEIN_SYNTHESIS = PermissibleValue(
        text="PROTEIN_SYNTHESIS",
        description="Ribosome function, translation, protein folding")
    MEMBRANE_STRUCTURE = PermissibleValue(
        text="MEMBRANE_STRUCTURE",
        description="Phospholipid synthesis, membrane integrity")
    ENZYMATIC_COFACTOR = PermissibleValue(
        text="ENZYMATIC_COFACTOR",
        description="Metal cofactors, vitamin cofactors for enzymes")
    REDOX_CHEMISTRY = PermissibleValue(
        text="REDOX_CHEMISTRY",
        description="Oxidation-reduction reactions, electron transport")
    ANTIOXIDANT_DEFENSE = PermissibleValue(
        text="ANTIOXIDANT_DEFENSE",
        description="Superoxide dismutase, oxidative stress response")
    CARBON_METABOLISM = PermissibleValue(
        text="CARBON_METABOLISM",
        description="C1 metabolism, TCA cycle, carbon source utilization")
    NITROGEN_METABOLISM = PermissibleValue(
        text="NITROGEN_METABOLISM",
        description="Nitrogen assimilation, amino acid synthesis")
    METAL_HOMEOSTASIS = PermissibleValue(
        text="METAL_HOMEOSTASIS",
        description="Metal chelation, metal buffering, uptake regulation")
    PH_REGULATION = PermissibleValue(
        text="PH_REGULATION",
        description="pH buffering, proton balance")
    CELL_SIGNALING = PermissibleValue(
        text="CELL_SIGNALING",
        description="Signal transduction, second messengers")
    CELL_DIVISION = PermissibleValue(
        text="CELL_DIVISION",
        description="Cell cycle regulation, division machinery")
    METHYLOTROPHY_SPECIFIC = PermissibleValue(
        text="METHYLOTROPHY_SPECIFIC",
        description="Specialized functions in methylotrophic bacteria")
    STRUCTURAL_PROTEIN = PermissibleValue(
        text="STRUCTURAL_PROTEIN",
        description="Structural roles in proteins (zinc fingers, DNA binding)")
    TRANSCRIPTION_REGULATION = PermissibleValue(
        text="TRANSCRIPTION_REGULATION",
        description="Gene expression, RNA polymerase function")

    _defn = EnumDefinition(
        name="BroadCellularRoleEnum",
        description="""Broad functional categories for cellular roles. Enables hierarchical organization and simplified queries.""",
    )

class ConcentrationUnitEnum(EnumDefinitionImpl):
    """
    Units for ingredient concentrations
    """
    MILLIMOLAR = PermissibleValue(
        text="MILLIMOLAR",
        description="Millimolar (mM)")
    MOLAR = PermissibleValue(
        text="MOLAR",
        description="Molar (M)")
    GRAMS_PER_LITER = PermissibleValue(
        text="GRAMS_PER_LITER",
        description="Grams per liter (g/L)")
    MILLIGRAMS_PER_LITER = PermissibleValue(
        text="MILLIGRAMS_PER_LITER",
        description="Milligrams per liter (mg/L)")
    MICROGRAMS_PER_LITER = PermissibleValue(
        text="MICROGRAMS_PER_LITER",
        description="Micrograms per liter (μg/L)")
    PERCENT = PermissibleValue(
        text="PERCENT",
        description="Percent (%, w/v or v/v)")

    _defn = EnumDefinition(
        name="ConcentrationUnitEnum",
        description="Units for ingredient concentrations",
    )

class LightSensitivityEnum(EnumDefinitionImpl):
    """
    Categories of light sensitivity
    """
    STABLE = PermissibleValue(
        text="STABLE",
        description="Stable under light exposure")
    SENSITIVE = PermissibleValue(
        text="SENSITIVE",
        description="Degrades under light exposure (store protected)")
    HIGHLY_SENSITIVE = PermissibleValue(
        text="HIGHLY_SENSITIVE",
        description="Rapidly degrades under light (must store dark)")
    NOT_SENSITIVE = PermissibleValue(
        text="NOT_SENSITIVE",
        description="Not sensitive to light")
    UNKNOWN = PermissibleValue(
        text="UNKNOWN",
        description="Sensitivity not characterized")

    _defn = EnumDefinition(
        name="LightSensitivityEnum",
        description="Categories of light sensitivity",
    )

class AutoclaveStabilityEnum(EnumDefinitionImpl):
    """
    Stability during autoclaving (121°C, 15 psi, 15-20 min)
    """
    STABLE = PermissibleValue(
        text="STABLE",
        description="Stable during autoclaving")
    UNSTABLE = PermissibleValue(
        text="UNSTABLE",
        description="Degrades during autoclaving - do not autoclave")
    PARTIALLY_STABLE = PermissibleValue(
        text="PARTIALLY_STABLE",
        description="Partially degrades during autoclaving")
    FILTER_STERILIZE = PermissibleValue(
        text="FILTER_STERILIZE",
        description="Must be filter sterilized (0.22 μm)")
    AUTOCLAVE_SEPARATELY = PermissibleValue(
        text="AUTOCLAVE_SEPARATELY",
        description="Stable but autoclave separately to prevent precipitation")
    UNKNOWN = PermissibleValue(
        text="UNKNOWN",
        description="Stability not characterized")

    _defn = EnumDefinition(
        name="AutoclaveStabilityEnum",
        description="Stability during autoclaving (121°C, 15 psi, 15-20 min)",
    )

class EssentialityEnum(EnumDefinitionImpl):
    """
    Essentiality classification for microbial growth
    """
    ESSENTIAL = PermissibleValue(
        text="ESSENTIAL",
        description="Required for all bacteria (e.g., phosphate, nitrogen)")
    CONDITIONALLY_ESSENTIAL = PermissibleValue(
        text="CONDITIONALLY_ESSENTIAL",
        description="Required under specific conditions")
    NON_ESSENTIAL = PermissibleValue(
        text="NON_ESSENTIAL",
        description="Not required for growth (growth factor)")
    ORGANISM_SPECIFIC = PermissibleValue(
        text="ORGANISM_SPECIFIC",
        description="Varies by organism (e.g., vitamins)")
    METHYLOTROPH_SPECIFIC = PermissibleValue(
        text="METHYLOTROPH_SPECIFIC",
        description="Specific to methylotrophic bacteria")
    UNKNOWN = PermissibleValue(
        text="UNKNOWN",
        description="Essentiality not characterized")

    _defn = EnumDefinition(
        name="EssentialityEnum",
        description="Essentiality classification for microbial growth",
    )

# Slots
class slots:
    pass

slots.priority = Slot(uri=MICROGROW.priority, name="priority", curie=MICROGROW.curie('priority'),
                   model_uri=MICROGROW.priority, domain=None, range=Optional[float])

slots.component = Slot(uri=MICROGROW.component, name="component", curie=MICROGROW.curie('component'),
                   model_uri=MICROGROW.component, domain=None, range=str)

slots.chemical_formula = Slot(uri=MICROGROW.chemical_formula, name="chemical_formula", curie=MICROGROW.curie('chemical_formula'),
                   model_uri=MICROGROW.chemical_formula, domain=None, range=Optional[str])

slots.kg_node_id = Slot(uri=MICROGROW.kg_node_id, name="kg_node_id", curie=MICROGROW.curie('kg_node_id'),
                   model_uri=MICROGROW.kg_node_id, domain=None, range=URIRef,
                   pattern=re.compile(r'^(CHEBI|PubChem|CAS|mediadive\.(ingredient|solution)):[A-Za-z0-9_.-]+$'))

slots.concentration = Slot(uri=MICROGROW.concentration, name="concentration", curie=MICROGROW.curie('concentration'),
                   model_uri=MICROGROW.concentration, domain=None, range=Optional[str])

slots.media_role = Slot(uri=MICROGROW.media_role, name="media_role", curie=MICROGROW.curie('media_role'),
                   model_uri=MICROGROW.media_role, domain=None, range=Union[Union[str, "MediaRoleEnum"], list[Union[str, "MediaRoleEnum"]]])

slots.media_role_doi = Slot(uri=MICROGROW.media_role_doi, name="media_role_doi", curie=MICROGROW.curie('media_role_doi'),
                   model_uri=MICROGROW.media_role_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.solubility = Slot(uri=MICROGROW.solubility, name="solubility", curie=MICROGROW.curie('solubility'),
                   model_uri=MICROGROW.solubility, domain=None, range=Optional[str])

slots.solubility_citation_doi = Slot(uri=MICROGROW.solubility_citation_doi, name="solubility_citation_doi", curie=MICROGROW.curie('solubility_citation_doi'),
                   model_uri=MICROGROW.solubility_citation_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.solubility_citation_organism = Slot(uri=MICROGROW.solubility_citation_organism, name="solubility_citation_organism", curie=MICROGROW.curie('solubility_citation_organism'),
                   model_uri=MICROGROW.solubility_citation_organism, domain=None, range=Optional[str])

slots.lower_bound = Slot(uri=MICROGROW.lower_bound, name="lower_bound", curie=MICROGROW.curie('lower_bound'),
                   model_uri=MICROGROW.lower_bound, domain=None, range=Optional[str])

slots.lower_bound_citation = Slot(uri=MICROGROW.lower_bound_citation, name="lower_bound_citation", curie=MICROGROW.curie('lower_bound_citation'),
                   model_uri=MICROGROW.lower_bound_citation, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.lower_bound_citation_organism = Slot(uri=MICROGROW.lower_bound_citation_organism, name="lower_bound_citation_organism", curie=MICROGROW.curie('lower_bound_citation_organism'),
                   model_uri=MICROGROW.lower_bound_citation_organism, domain=None, range=Optional[str])

slots.upper_bound = Slot(uri=MICROGROW.upper_bound, name="upper_bound", curie=MICROGROW.curie('upper_bound'),
                   model_uri=MICROGROW.upper_bound, domain=None, range=Optional[str])

slots.upper_bound_citation = Slot(uri=MICROGROW.upper_bound_citation, name="upper_bound_citation", curie=MICROGROW.curie('upper_bound_citation'),
                   model_uri=MICROGROW.upper_bound_citation, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.upper_bound_citation_organism = Slot(uri=MICROGROW.upper_bound_citation_organism, name="upper_bound_citation_organism", curie=MICROGROW.curie('upper_bound_citation_organism'),
                   model_uri=MICROGROW.upper_bound_citation_organism, domain=None, range=Optional[str])

slots.limit_of_toxicity = Slot(uri=MICROGROW.limit_of_toxicity, name="limit_of_toxicity", curie=MICROGROW.curie('limit_of_toxicity'),
                   model_uri=MICROGROW.limit_of_toxicity, domain=None, range=Optional[str])

slots.toxicity_citation = Slot(uri=MICROGROW.toxicity_citation, name="toxicity_citation", curie=MICROGROW.curie('toxicity_citation'),
                   model_uri=MICROGROW.toxicity_citation, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.toxicity_citation_organism = Slot(uri=MICROGROW.toxicity_citation_organism, name="toxicity_citation_organism", curie=MICROGROW.curie('toxicity_citation_organism'),
                   model_uri=MICROGROW.toxicity_citation_organism, domain=None, range=Optional[str])

slots.ph_effect = Slot(uri=MICROGROW.ph_effect, name="ph_effect", curie=MICROGROW.curie('ph_effect'),
                   model_uri=MICROGROW.ph_effect, domain=None, range=Optional[str])

slots.ph_effect_doi = Slot(uri=MICROGROW.ph_effect_doi, name="ph_effect_doi", curie=MICROGROW.curie('ph_effect_doi'),
                   model_uri=MICROGROW.ph_effect_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.ph_effect_organism = Slot(uri=MICROGROW.ph_effect_organism, name="ph_effect_organism", curie=MICROGROW.curie('ph_effect_organism'),
                   model_uri=MICROGROW.ph_effect_organism, domain=None, range=Optional[str])

slots.pka = Slot(uri=MICROGROW.pka, name="pka", curie=MICROGROW.curie('pka'),
                   model_uri=MICROGROW.pka, domain=None, range=Optional[str])

slots.pka_doi = Slot(uri=MICROGROW.pka_doi, name="pka_doi", curie=MICROGROW.curie('pka_doi'),
                   model_uri=MICROGROW.pka_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.pka_organism = Slot(uri=MICROGROW.pka_organism, name="pka_organism", curie=MICROGROW.curie('pka_organism'),
                   model_uri=MICROGROW.pka_organism, domain=None, range=Optional[str])

slots.oxidation_state_stability = Slot(uri=MICROGROW.oxidation_state_stability, name="oxidation_state_stability", curie=MICROGROW.curie('oxidation_state_stability'),
                   model_uri=MICROGROW.oxidation_state_stability, domain=None, range=Optional[str])

slots.oxidation_stability_doi = Slot(uri=MICROGROW.oxidation_stability_doi, name="oxidation_stability_doi", curie=MICROGROW.curie('oxidation_stability_doi'),
                   model_uri=MICROGROW.oxidation_stability_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.oxidation_stability_organism = Slot(uri=MICROGROW.oxidation_stability_organism, name="oxidation_stability_organism", curie=MICROGROW.curie('oxidation_stability_organism'),
                   model_uri=MICROGROW.oxidation_stability_organism, domain=None, range=Optional[str])

slots.light_sensitivity = Slot(uri=MICROGROW.light_sensitivity, name="light_sensitivity", curie=MICROGROW.curie('light_sensitivity'),
                   model_uri=MICROGROW.light_sensitivity, domain=None, range=Optional[Union[str, "LightSensitivityEnum"]])

slots.light_sensitivity_doi = Slot(uri=MICROGROW.light_sensitivity_doi, name="light_sensitivity_doi", curie=MICROGROW.curie('light_sensitivity_doi'),
                   model_uri=MICROGROW.light_sensitivity_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.light_sensitivity_organism = Slot(uri=MICROGROW.light_sensitivity_organism, name="light_sensitivity_organism", curie=MICROGROW.curie('light_sensitivity_organism'),
                   model_uri=MICROGROW.light_sensitivity_organism, domain=None, range=Optional[str])

slots.autoclave_stability = Slot(uri=MICROGROW.autoclave_stability, name="autoclave_stability", curie=MICROGROW.curie('autoclave_stability'),
                   model_uri=MICROGROW.autoclave_stability, domain=None, range=Optional[Union[str, "AutoclaveStabilityEnum"]])

slots.autoclave_stability_doi = Slot(uri=MICROGROW.autoclave_stability_doi, name="autoclave_stability_doi", curie=MICROGROW.curie('autoclave_stability_doi'),
                   model_uri=MICROGROW.autoclave_stability_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.autoclave_stability_organism = Slot(uri=MICROGROW.autoclave_stability_organism, name="autoclave_stability_organism", curie=MICROGROW.curie('autoclave_stability_organism'),
                   model_uri=MICROGROW.autoclave_stability_organism, domain=None, range=Optional[str])

slots.stock_concentration = Slot(uri=MICROGROW.stock_concentration, name="stock_concentration", curie=MICROGROW.curie('stock_concentration'),
                   model_uri=MICROGROW.stock_concentration, domain=None, range=Optional[str])

slots.stock_concentration_doi = Slot(uri=MICROGROW.stock_concentration_doi, name="stock_concentration_doi", curie=MICROGROW.curie('stock_concentration_doi'),
                   model_uri=MICROGROW.stock_concentration_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.stock_concentration_organism = Slot(uri=MICROGROW.stock_concentration_organism, name="stock_concentration_organism", curie=MICROGROW.curie('stock_concentration_organism'),
                   model_uri=MICROGROW.stock_concentration_organism, domain=None, range=Optional[str])

slots.precipitation_partners = Slot(uri=MICROGROW.precipitation_partners, name="precipitation_partners", curie=MICROGROW.curie('precipitation_partners'),
                   model_uri=MICROGROW.precipitation_partners, domain=None, range=Optional[str])

slots.precipitation_partners_doi = Slot(uri=MICROGROW.precipitation_partners_doi, name="precipitation_partners_doi", curie=MICROGROW.curie('precipitation_partners_doi'),
                   model_uri=MICROGROW.precipitation_partners_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.precipitation_partners_organism = Slot(uri=MICROGROW.precipitation_partners_organism, name="precipitation_partners_organism", curie=MICROGROW.curie('precipitation_partners_organism'),
                   model_uri=MICROGROW.precipitation_partners_organism, domain=None, range=Optional[str])

slots.antagonistic_ions = Slot(uri=MICROGROW.antagonistic_ions, name="antagonistic_ions", curie=MICROGROW.curie('antagonistic_ions'),
                   model_uri=MICROGROW.antagonistic_ions, domain=None, range=Optional[str])

slots.antagonistic_ions_doi = Slot(uri=MICROGROW.antagonistic_ions_doi, name="antagonistic_ions_doi", curie=MICROGROW.curie('antagonistic_ions_doi'),
                   model_uri=MICROGROW.antagonistic_ions_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.antagonistic_ions_organism = Slot(uri=MICROGROW.antagonistic_ions_organism, name="antagonistic_ions_organism", curie=MICROGROW.curie('antagonistic_ions_organism'),
                   model_uri=MICROGROW.antagonistic_ions_organism, domain=None, range=Optional[str])

slots.chelator_sensitivity = Slot(uri=MICROGROW.chelator_sensitivity, name="chelator_sensitivity", curie=MICROGROW.curie('chelator_sensitivity'),
                   model_uri=MICROGROW.chelator_sensitivity, domain=None, range=Optional[str])

slots.chelator_sensitivity_doi = Slot(uri=MICROGROW.chelator_sensitivity_doi, name="chelator_sensitivity_doi", curie=MICROGROW.curie('chelator_sensitivity_doi'),
                   model_uri=MICROGROW.chelator_sensitivity_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.chelator_sensitivity_organism = Slot(uri=MICROGROW.chelator_sensitivity_organism, name="chelator_sensitivity_organism", curie=MICROGROW.curie('chelator_sensitivity_organism'),
                   model_uri=MICROGROW.chelator_sensitivity_organism, domain=None, range=Optional[str])

slots.redox_contribution = Slot(uri=MICROGROW.redox_contribution, name="redox_contribution", curie=MICROGROW.curie('redox_contribution'),
                   model_uri=MICROGROW.redox_contribution, domain=None, range=Optional[str])

slots.redox_contribution_doi = Slot(uri=MICROGROW.redox_contribution_doi, name="redox_contribution_doi", curie=MICROGROW.curie('redox_contribution_doi'),
                   model_uri=MICROGROW.redox_contribution_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.redox_contribution_organism = Slot(uri=MICROGROW.redox_contribution_organism, name="redox_contribution_organism", curie=MICROGROW.curie('redox_contribution_organism'),
                   model_uri=MICROGROW.redox_contribution_organism, domain=None, range=Optional[str])

slots.cellular_role = Slot(uri=MICROGROW.cellular_role, name="cellular_role", curie=MICROGROW.curie('cellular_role'),
                   model_uri=MICROGROW.cellular_role, domain=None, range=Optional[str])

slots.cellular_role_doi = Slot(uri=MICROGROW.cellular_role_doi, name="cellular_role_doi", curie=MICROGROW.curie('cellular_role_doi'),
                   model_uri=MICROGROW.cellular_role_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.cellular_role_organism = Slot(uri=MICROGROW.cellular_role_organism, name="cellular_role_organism", curie=MICROGROW.curie('cellular_role_organism'),
                   model_uri=MICROGROW.cellular_role_organism, domain=None, range=Optional[str])

slots.cellular_role_specific = Slot(uri=MICROGROW.cellular_role_specific, name="cellular_role_specific", curie=MICROGROW.curie('cellular_role_specific'),
                   model_uri=MICROGROW.cellular_role_specific, domain=None, range=Optional[Union[str, "CellularRoleEnum"]])

slots.cellular_role_broad = Slot(uri=MICROGROW.cellular_role_broad, name="cellular_role_broad", curie=MICROGROW.curie('cellular_role_broad'),
                   model_uri=MICROGROW.cellular_role_broad, domain=None, range=Optional[Union[Union[str, "BroadCellularRoleEnum"], list[Union[str, "BroadCellularRoleEnum"]]]])

slots.essential_conditional = Slot(uri=MICROGROW.essential_conditional, name="essential_conditional", curie=MICROGROW.curie('essential_conditional'),
                   model_uri=MICROGROW.essential_conditional, domain=None, range=Optional[Union[str, "EssentialityEnum"]])

slots.essential_conditional_doi = Slot(uri=MICROGROW.essential_conditional_doi, name="essential_conditional_doi", curie=MICROGROW.curie('essential_conditional_doi'),
                   model_uri=MICROGROW.essential_conditional_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.essential_conditional_organism = Slot(uri=MICROGROW.essential_conditional_organism, name="essential_conditional_organism", curie=MICROGROW.curie('essential_conditional_organism'),
                   model_uri=MICROGROW.essential_conditional_organism, domain=None, range=Optional[str])

slots.uptake_transporter = Slot(uri=MICROGROW.uptake_transporter, name="uptake_transporter", curie=MICROGROW.curie('uptake_transporter'),
                   model_uri=MICROGROW.uptake_transporter, domain=None, range=Optional[str])

slots.uptake_transporter_doi = Slot(uri=MICROGROW.uptake_transporter_doi, name="uptake_transporter_doi", curie=MICROGROW.curie('uptake_transporter_doi'),
                   model_uri=MICROGROW.uptake_transporter_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.uptake_transporter_organism = Slot(uri=MICROGROW.uptake_transporter_organism, name="uptake_transporter_organism", curie=MICROGROW.curie('uptake_transporter_organism'),
                   model_uri=MICROGROW.uptake_transporter_organism, domain=None, range=Optional[str])

slots.regulatory_effects = Slot(uri=MICROGROW.regulatory_effects, name="regulatory_effects", curie=MICROGROW.curie('regulatory_effects'),
                   model_uri=MICROGROW.regulatory_effects, domain=None, range=Optional[str])

slots.regulatory_effects_doi = Slot(uri=MICROGROW.regulatory_effects_doi, name="regulatory_effects_doi", curie=MICROGROW.curie('regulatory_effects_doi'),
                   model_uri=MICROGROW.regulatory_effects_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.regulatory_effects_organism = Slot(uri=MICROGROW.regulatory_effects_organism, name="regulatory_effects_organism", curie=MICROGROW.curie('regulatory_effects_organism'),
                   model_uri=MICROGROW.regulatory_effects_organism, domain=None, range=Optional[str])

slots.gram_differential = Slot(uri=MICROGROW.gram_differential, name="gram_differential", curie=MICROGROW.curie('gram_differential'),
                   model_uri=MICROGROW.gram_differential, domain=None, range=Optional[str])

slots.gram_differential_doi = Slot(uri=MICROGROW.gram_differential_doi, name="gram_differential_doi", curie=MICROGROW.curie('gram_differential_doi'),
                   model_uri=MICROGROW.gram_differential_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.gram_differential_organism = Slot(uri=MICROGROW.gram_differential_organism, name="gram_differential_organism", curie=MICROGROW.curie('gram_differential_organism'),
                   model_uri=MICROGROW.gram_differential_organism, domain=None, range=Optional[str])

slots.aerobe_anaerobe_differential = Slot(uri=MICROGROW.aerobe_anaerobe_differential, name="aerobe_anaerobe_differential", curie=MICROGROW.curie('aerobe_anaerobe_differential'),
                   model_uri=MICROGROW.aerobe_anaerobe_differential, domain=None, range=Optional[str])

slots.aerobe_anaerobe_doi = Slot(uri=MICROGROW.aerobe_anaerobe_doi, name="aerobe_anaerobe_doi", curie=MICROGROW.curie('aerobe_anaerobe_doi'),
                   model_uri=MICROGROW.aerobe_anaerobe_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.aerobe_anaerobe_organism = Slot(uri=MICROGROW.aerobe_anaerobe_organism, name="aerobe_anaerobe_organism", curie=MICROGROW.curie('aerobe_anaerobe_organism'),
                   model_uri=MICROGROW.aerobe_anaerobe_organism, domain=None, range=Optional[str])

slots.optimal_concentration_model_organisms = Slot(uri=MICROGROW.optimal_concentration_model_organisms, name="optimal_concentration_model_organisms", curie=MICROGROW.curie('optimal_concentration_model_organisms'),
                   model_uri=MICROGROW.optimal_concentration_model_organisms, domain=None, range=Optional[str])

slots.optimal_concentration_doi = Slot(uri=MICROGROW.optimal_concentration_doi, name="optimal_concentration_doi", curie=MICROGROW.curie('optimal_concentration_doi'),
                   model_uri=MICROGROW.optimal_concentration_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.optimal_concentration_organism = Slot(uri=MICROGROW.optimal_concentration_organism, name="optimal_concentration_organism", curie=MICROGROW.curie('optimal_concentration_organism'),
                   model_uri=MICROGROW.optimal_concentration_organism, domain=None, range=Optional[str])

slots.mPMediumDataset__ingredients = Slot(uri=MICROGROW.ingredients, name="mPMediumDataset__ingredients", curie=MICROGROW.curie('ingredients'),
                   model_uri=MICROGROW.mPMediumDataset__ingredients, domain=None, range=Optional[Union[dict[Union[str, MPMediumIngredientKgNodeId], Union[dict, MPMediumIngredient]], list[Union[dict, MPMediumIngredient]]]])

slots.mPMediumDataset__ingredient_properties = Slot(uri=MICROGROW.ingredient_properties, name="mPMediumDataset__ingredient_properties", curie=MICROGROW.curie('ingredient_properties'),
                   model_uri=MICROGROW.mPMediumDataset__ingredient_properties, domain=None, range=Optional[Union[dict[Union[str, IngredientPropertyKgNodeId], Union[dict, IngredientProperty]], list[Union[dict, IngredientProperty]]]])

slots.mPMediumDataset__concentration_ranges = Slot(uri=MICROGROW.concentration_ranges, name="mPMediumDataset__concentration_ranges", curie=MICROGROW.curie('concentration_ranges'),
                   model_uri=MICROGROW.mPMediumDataset__concentration_ranges, domain=None, range=Optional[Union[dict[Union[str, ConcentrationRangeDetailedIngredient], Union[dict, ConcentrationRangeDetailed]], list[Union[dict, ConcentrationRangeDetailed]]]])

slots.mPMediumDataset__solubility_toxicity = Slot(uri=MICROGROW.solubility_toxicity, name="mPMediumDataset__solubility_toxicity", curie=MICROGROW.curie('solubility_toxicity'),
                   model_uri=MICROGROW.mPMediumDataset__solubility_toxicity, domain=None, range=Optional[Union[dict[Union[str, SolubilityToxicitySummaryIngredient], Union[dict, SolubilityToxicitySummary]], list[Union[dict, SolubilityToxicitySummary]]]])

slots.mPMediumDataset__predictions = Slot(uri=MICROGROW.predictions, name="mPMediumDataset__predictions", curie=MICROGROW.curie('predictions'),
                   model_uri=MICROGROW.mPMediumDataset__predictions, domain=None, range=Optional[Union[dict[Union[str, ConcentrationPredictionIngredient], Union[dict, ConcentrationPrediction]], list[Union[dict, ConcentrationPrediction]]]])

slots.mPMediumDataset__predictions_extended = Slot(uri=MICROGROW.predictions_extended, name="mPMediumDataset__predictions_extended", curie=MICROGROW.curie('predictions_extended'),
                   model_uri=MICROGROW.mPMediumDataset__predictions_extended, domain=None, range=Optional[Union[dict[Union[str, MediumPredictionExtendedIngredient], Union[dict, MediumPredictionExtended]], list[Union[dict, MediumPredictionExtended]]]])

slots.mPMediumDataset__alternates = Slot(uri=MICROGROW.alternates, name="mPMediumDataset__alternates", curie=MICROGROW.curie('alternates'),
                   model_uri=MICROGROW.mPMediumDataset__alternates, domain=None, range=Optional[Union[Union[dict, AlternateIngredient], list[Union[dict, AlternateIngredient]]]])

slots.concentrationPrediction__ingredient = Slot(uri=MICROGROW.ingredient, name="concentrationPrediction__ingredient", curie=MICROGROW.curie('ingredient'),
                   model_uri=MICROGROW.concentrationPrediction__ingredient, domain=None, range=URIRef)

slots.concentrationPrediction__min_concentration = Slot(uri=MICROGROW.min_concentration, name="concentrationPrediction__min_concentration", curie=MICROGROW.curie('min_concentration'),
                   model_uri=MICROGROW.concentrationPrediction__min_concentration, domain=None, range=Optional[float])

slots.concentrationPrediction__max_concentration = Slot(uri=MICROGROW.max_concentration, name="concentrationPrediction__max_concentration", curie=MICROGROW.curie('max_concentration'),
                   model_uri=MICROGROW.concentrationPrediction__max_concentration, domain=None, range=Optional[float])

slots.concentrationPrediction__unit = Slot(uri=MICROGROW.unit, name="concentrationPrediction__unit", curie=MICROGROW.curie('unit'),
                   model_uri=MICROGROW.concentrationPrediction__unit, domain=None, range=Optional[Union[str, "ConcentrationUnitEnum"]])

slots.concentrationPrediction__essential = Slot(uri=MICROGROW.essential, name="concentrationPrediction__essential", curie=MICROGROW.curie('essential'),
                   model_uri=MICROGROW.concentrationPrediction__essential, domain=None, range=Optional[Union[bool, Bool]])

slots.concentrationPrediction__confidence = Slot(uri=MICROGROW.confidence, name="concentrationPrediction__confidence", curie=MICROGROW.curie('confidence'),
                   model_uri=MICROGROW.concentrationPrediction__confidence, domain=None, range=Optional[float])

slots.concentrationPrediction__ph_at_low = Slot(uri=MICROGROW.ph_at_low, name="concentrationPrediction__ph_at_low", curie=MICROGROW.curie('ph_at_low'),
                   model_uri=MICROGROW.concentrationPrediction__ph_at_low, domain=None, range=Optional[float])

slots.concentrationPrediction__ph_at_high = Slot(uri=MICROGROW.ph_at_high, name="concentrationPrediction__ph_at_high", curie=MICROGROW.curie('ph_at_high'),
                   model_uri=MICROGROW.concentrationPrediction__ph_at_high, domain=None, range=Optional[float])

slots.concentrationPrediction__ph_effect = Slot(uri=MICROGROW.ph_effect, name="concentrationPrediction__ph_effect", curie=MICROGROW.curie('ph_effect'),
                   model_uri=MICROGROW.concentrationPrediction__ph_effect, domain=None, range=Optional[str])

slots.alternateIngredient__original_ingredient = Slot(uri=MICROGROW.original_ingredient, name="alternateIngredient__original_ingredient", curie=MICROGROW.curie('original_ingredient'),
                   model_uri=MICROGROW.alternateIngredient__original_ingredient, domain=None, range=str)

slots.alternateIngredient__alternate_ingredient = Slot(uri=MICROGROW.alternate_ingredient, name="alternateIngredient__alternate_ingredient", curie=MICROGROW.curie('alternate_ingredient'),
                   model_uri=MICROGROW.alternateIngredient__alternate_ingredient, domain=None, range=str)

slots.alternateIngredient__rationale = Slot(uri=MICROGROW.rationale, name="alternateIngredient__rationale", curie=MICROGROW.curie('rationale'),
                   model_uri=MICROGROW.alternateIngredient__rationale, domain=None, range=Optional[str])

slots.alternateIngredient__alternate_role = Slot(uri=MICROGROW.alternate_role, name="alternateIngredient__alternate_role", curie=MICROGROW.curie('alternate_role'),
                   model_uri=MICROGROW.alternateIngredient__alternate_role, domain=None, range=Optional[Union[str, "MediaRoleEnum"]])

slots.alternateIngredient__doi_citation = Slot(uri=MICROGROW.doi_citation, name="alternateIngredient__doi_citation", curie=MICROGROW.curie('doi_citation'),
                   model_uri=MICROGROW.alternateIngredient__doi_citation, domain=None, range=Optional[Union[str, DOI]])

slots.alternateIngredient__kg_node_id = Slot(uri=MICROGROW.kg_node_id, name="alternateIngredient__kg_node_id", curie=MICROGROW.curie('kg_node_id'),
                   model_uri=MICROGROW.alternateIngredient__kg_node_id, domain=None, range=Optional[str],
                   pattern=re.compile(r'^(CHEBI|PubChem|CAS):[A-Za-z0-9_-]+$'))

slots.alternateIngredient__kg_node_label = Slot(uri=MICROGROW.kg_node_label, name="alternateIngredient__kg_node_label", curie=MICROGROW.curie('kg_node_label'),
                   model_uri=MICROGROW.alternateIngredient__kg_node_label, domain=None, range=Optional[str])

slots.concentrationRangeDetailed__ingredient = Slot(uri=MICROGROW.ingredient, name="concentrationRangeDetailed__ingredient", curie=MICROGROW.curie('ingredient'),
                   model_uri=MICROGROW.concentrationRangeDetailed__ingredient, domain=None, range=URIRef)

slots.concentrationRangeDetailed__formula = Slot(uri=MICROGROW.formula, name="concentrationRangeDetailed__formula", curie=MICROGROW.curie('formula'),
                   model_uri=MICROGROW.concentrationRangeDetailed__formula, domain=None, range=Optional[str])

slots.concentrationRangeDetailed__kg_node_id = Slot(uri=MICROGROW.kg_node_id, name="concentrationRangeDetailed__kg_node_id", curie=MICROGROW.curie('kg_node_id'),
                   model_uri=MICROGROW.concentrationRangeDetailed__kg_node_id, domain=None, range=Optional[str],
                   pattern=re.compile(r'^(CHEBI|PubChem|CAS|mediadive\.(ingredient|solution)):[A-Za-z0-9_.-]+$'))

slots.concentrationRangeDetailed__priority = Slot(uri=MICROGROW.priority, name="concentrationRangeDetailed__priority", curie=MICROGROW.curie('priority'),
                   model_uri=MICROGROW.concentrationRangeDetailed__priority, domain=None, range=Optional[float])

slots.concentrationRangeDetailed__standard_concentration = Slot(uri=MICROGROW.standard_concentration, name="concentrationRangeDetailed__standard_concentration", curie=MICROGROW.curie('standard_concentration'),
                   model_uri=MICROGROW.concentrationRangeDetailed__standard_concentration, domain=None, range=Optional[str])

slots.concentrationRangeDetailed__lower_bound = Slot(uri=MICROGROW.lower_bound, name="concentrationRangeDetailed__lower_bound", curie=MICROGROW.curie('lower_bound'),
                   model_uri=MICROGROW.concentrationRangeDetailed__lower_bound, domain=None, range=Optional[str])

slots.concentrationRangeDetailed__lower_bound_organism = Slot(uri=MICROGROW.lower_bound_organism, name="concentrationRangeDetailed__lower_bound_organism", curie=MICROGROW.curie('lower_bound_organism'),
                   model_uri=MICROGROW.concentrationRangeDetailed__lower_bound_organism, domain=None, range=Optional[str])

slots.concentrationRangeDetailed__lower_bound_doi = Slot(uri=MICROGROW.lower_bound_doi, name="concentrationRangeDetailed__lower_bound_doi", curie=MICROGROW.curie('lower_bound_doi'),
                   model_uri=MICROGROW.concentrationRangeDetailed__lower_bound_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.concentrationRangeDetailed__lower_bound_evidence = Slot(uri=MICROGROW.lower_bound_evidence, name="concentrationRangeDetailed__lower_bound_evidence", curie=MICROGROW.curie('lower_bound_evidence'),
                   model_uri=MICROGROW.concentrationRangeDetailed__lower_bound_evidence, domain=None, range=Optional[str])

slots.concentrationRangeDetailed__upper_bound = Slot(uri=MICROGROW.upper_bound, name="concentrationRangeDetailed__upper_bound", curie=MICROGROW.curie('upper_bound'),
                   model_uri=MICROGROW.concentrationRangeDetailed__upper_bound, domain=None, range=Optional[str])

slots.concentrationRangeDetailed__upper_bound_organism = Slot(uri=MICROGROW.upper_bound_organism, name="concentrationRangeDetailed__upper_bound_organism", curie=MICROGROW.curie('upper_bound_organism'),
                   model_uri=MICROGROW.concentrationRangeDetailed__upper_bound_organism, domain=None, range=Optional[str])

slots.concentrationRangeDetailed__upper_bound_doi = Slot(uri=MICROGROW.upper_bound_doi, name="concentrationRangeDetailed__upper_bound_doi", curie=MICROGROW.curie('upper_bound_doi'),
                   model_uri=MICROGROW.concentrationRangeDetailed__upper_bound_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.concentrationRangeDetailed__upper_bound_evidence = Slot(uri=MICROGROW.upper_bound_evidence, name="concentrationRangeDetailed__upper_bound_evidence", curie=MICROGROW.curie('upper_bound_evidence'),
                   model_uri=MICROGROW.concentrationRangeDetailed__upper_bound_evidence, domain=None, range=Optional[str])

slots.concentrationRangeDetailed__optimal_concentration = Slot(uri=MICROGROW.optimal_concentration, name="concentrationRangeDetailed__optimal_concentration", curie=MICROGROW.curie('optimal_concentration'),
                   model_uri=MICROGROW.concentrationRangeDetailed__optimal_concentration, domain=None, range=Optional[str])

slots.concentrationRangeDetailed__optimal_conc_organism = Slot(uri=MICROGROW.optimal_conc_organism, name="concentrationRangeDetailed__optimal_conc_organism", curie=MICROGROW.curie('optimal_conc_organism'),
                   model_uri=MICROGROW.concentrationRangeDetailed__optimal_conc_organism, domain=None, range=Optional[str])

slots.concentrationRangeDetailed__optimal_conc_doi = Slot(uri=MICROGROW.optimal_conc_doi, name="concentrationRangeDetailed__optimal_conc_doi", curie=MICROGROW.curie('optimal_conc_doi'),
                   model_uri=MICROGROW.concentrationRangeDetailed__optimal_conc_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.concentrationRangeDetailed__optimal_conc_evidence = Slot(uri=MICROGROW.optimal_conc_evidence, name="concentrationRangeDetailed__optimal_conc_evidence", curie=MICROGROW.curie('optimal_conc_evidence'),
                   model_uri=MICROGROW.concentrationRangeDetailed__optimal_conc_evidence, domain=None, range=Optional[str])

slots.concentrationRangeDetailed__solubility = Slot(uri=MICROGROW.solubility, name="concentrationRangeDetailed__solubility", curie=MICROGROW.curie('solubility'),
                   model_uri=MICROGROW.concentrationRangeDetailed__solubility, domain=None, range=Optional[str])

slots.concentrationRangeDetailed__solubility_organism = Slot(uri=MICROGROW.solubility_organism, name="concentrationRangeDetailed__solubility_organism", curie=MICROGROW.curie('solubility_organism'),
                   model_uri=MICROGROW.concentrationRangeDetailed__solubility_organism, domain=None, range=Optional[str])

slots.concentrationRangeDetailed__solubility_doi = Slot(uri=MICROGROW.solubility_doi, name="concentrationRangeDetailed__solubility_doi", curie=MICROGROW.curie('solubility_doi'),
                   model_uri=MICROGROW.concentrationRangeDetailed__solubility_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.concentrationRangeDetailed__solubility_evidence = Slot(uri=MICROGROW.solubility_evidence, name="concentrationRangeDetailed__solubility_evidence", curie=MICROGROW.curie('solubility_evidence'),
                   model_uri=MICROGROW.concentrationRangeDetailed__solubility_evidence, domain=None, range=Optional[str])

slots.concentrationRangeDetailed__toxicity_limit = Slot(uri=MICROGROW.toxicity_limit, name="concentrationRangeDetailed__toxicity_limit", curie=MICROGROW.curie('toxicity_limit'),
                   model_uri=MICROGROW.concentrationRangeDetailed__toxicity_limit, domain=None, range=Optional[str])

slots.concentrationRangeDetailed__toxicity_organism = Slot(uri=MICROGROW.toxicity_organism, name="concentrationRangeDetailed__toxicity_organism", curie=MICROGROW.curie('toxicity_organism'),
                   model_uri=MICROGROW.concentrationRangeDetailed__toxicity_organism, domain=None, range=Optional[str])

slots.concentrationRangeDetailed__toxicity_doi = Slot(uri=MICROGROW.toxicity_doi, name="concentrationRangeDetailed__toxicity_doi", curie=MICROGROW.curie('toxicity_doi'),
                   model_uri=MICROGROW.concentrationRangeDetailed__toxicity_doi, domain=None, range=Optional[Union[Union[str, DOI], list[Union[str, DOI]]]])

slots.concentrationRangeDetailed__toxicity_evidence = Slot(uri=MICROGROW.toxicity_evidence, name="concentrationRangeDetailed__toxicity_evidence", curie=MICROGROW.curie('toxicity_evidence'),
                   model_uri=MICROGROW.concentrationRangeDetailed__toxicity_evidence, domain=None, range=Optional[str])

slots.solubilityToxicitySummary__ingredient = Slot(uri=MICROGROW.ingredient, name="solubilityToxicitySummary__ingredient", curie=MICROGROW.curie('ingredient'),
                   model_uri=MICROGROW.solubilityToxicitySummary__ingredient, domain=None, range=URIRef)

slots.solubilityToxicitySummary__formula = Slot(uri=MICROGROW.formula, name="solubilityToxicitySummary__formula", curie=MICROGROW.curie('formula'),
                   model_uri=MICROGROW.solubilityToxicitySummary__formula, domain=None, range=Optional[str])

slots.solubilityToxicitySummary__kg_node_id = Slot(uri=MICROGROW.kg_node_id, name="solubilityToxicitySummary__kg_node_id", curie=MICROGROW.curie('kg_node_id'),
                   model_uri=MICROGROW.solubilityToxicitySummary__kg_node_id, domain=None, range=Optional[str],
                   pattern=re.compile(r'^(CHEBI|PubChem|CAS|mediadive\.(ingredient|solution)):[A-Za-z0-9_.-]+$'))

slots.solubilityToxicitySummary__solubility_mM = Slot(uri=MICROGROW.solubility_mM, name="solubilityToxicitySummary__solubility_mM", curie=MICROGROW.curie('solubility_mM'),
                   model_uri=MICROGROW.solubilityToxicitySummary__solubility_mM, domain=None, range=Optional[str])

slots.solubilityToxicitySummary__solubility_organism = Slot(uri=MICROGROW.solubility_organism, name="solubilityToxicitySummary__solubility_organism", curie=MICROGROW.curie('solubility_organism'),
                   model_uri=MICROGROW.solubilityToxicitySummary__solubility_organism, domain=None, range=Optional[str])

slots.solubilityToxicitySummary__solubility_doi = Slot(uri=MICROGROW.solubility_doi, name="solubilityToxicitySummary__solubility_doi", curie=MICROGROW.curie('solubility_doi'),
                   model_uri=MICROGROW.solubilityToxicitySummary__solubility_doi, domain=None, range=Optional[Union[str, DOI]])

slots.solubilityToxicitySummary__toxicity_limit = Slot(uri=MICROGROW.toxicity_limit, name="solubilityToxicitySummary__toxicity_limit", curie=MICROGROW.curie('toxicity_limit'),
                   model_uri=MICROGROW.solubilityToxicitySummary__toxicity_limit, domain=None, range=Optional[str])

slots.solubilityToxicitySummary__toxicity_organism = Slot(uri=MICROGROW.toxicity_organism, name="solubilityToxicitySummary__toxicity_organism", curie=MICROGROW.curie('toxicity_organism'),
                   model_uri=MICROGROW.solubilityToxicitySummary__toxicity_organism, domain=None, range=Optional[str])

slots.solubilityToxicitySummary__toxicity_doi = Slot(uri=MICROGROW.toxicity_doi, name="solubilityToxicitySummary__toxicity_doi", curie=MICROGROW.curie('toxicity_doi'),
                   model_uri=MICROGROW.solubilityToxicitySummary__toxicity_doi, domain=None, range=Optional[Union[str, DOI]])

slots.mediumPredictionExtended__ingredient = Slot(uri=MICROGROW.ingredient, name="mediumPredictionExtended__ingredient", curie=MICROGROW.curie('ingredient'),
                   model_uri=MICROGROW.mediumPredictionExtended__ingredient, domain=None, range=URIRef)

slots.mediumPredictionExtended__min_concentration = Slot(uri=MICROGROW.min_concentration, name="mediumPredictionExtended__min_concentration", curie=MICROGROW.curie('min_concentration'),
                   model_uri=MICROGROW.mediumPredictionExtended__min_concentration, domain=None, range=Optional[float])

slots.mediumPredictionExtended__max_concentration = Slot(uri=MICROGROW.max_concentration, name="mediumPredictionExtended__max_concentration", curie=MICROGROW.curie('max_concentration'),
                   model_uri=MICROGROW.mediumPredictionExtended__max_concentration, domain=None, range=Optional[float])

slots.mediumPredictionExtended__unit = Slot(uri=MICROGROW.unit, name="mediumPredictionExtended__unit", curie=MICROGROW.curie('unit'),
                   model_uri=MICROGROW.mediumPredictionExtended__unit, domain=None, range=Optional[Union[str, "ConcentrationUnitEnum"]])

slots.mediumPredictionExtended__essential = Slot(uri=MICROGROW.essential, name="mediumPredictionExtended__essential", curie=MICROGROW.curie('essential'),
                   model_uri=MICROGROW.mediumPredictionExtended__essential, domain=None, range=Optional[Union[bool, Bool]])

slots.mediumPredictionExtended__confidence = Slot(uri=MICROGROW.confidence, name="mediumPredictionExtended__confidence", curie=MICROGROW.curie('confidence'),
                   model_uri=MICROGROW.mediumPredictionExtended__confidence, domain=None, range=Optional[float])

slots.mediumPredictionExtended__ph_at_low = Slot(uri=MICROGROW.ph_at_low, name="mediumPredictionExtended__ph_at_low", curie=MICROGROW.curie('ph_at_low'),
                   model_uri=MICROGROW.mediumPredictionExtended__ph_at_low, domain=None, range=Optional[float])

slots.mediumPredictionExtended__ph_at_high = Slot(uri=MICROGROW.ph_at_high, name="mediumPredictionExtended__ph_at_high", curie=MICROGROW.curie('ph_at_high'),
                   model_uri=MICROGROW.mediumPredictionExtended__ph_at_high, domain=None, range=Optional[float])

slots.mediumPredictionExtended__ph_effect = Slot(uri=MICROGROW.ph_effect, name="mediumPredictionExtended__ph_effect", curie=MICROGROW.curie('ph_effect'),
                   model_uri=MICROGROW.mediumPredictionExtended__ph_effect, domain=None, range=Optional[str])

slots.mediumPredictionExtended__chemical_formula = Slot(uri=MICROGROW.chemical_formula, name="mediumPredictionExtended__chemical_formula", curie=MICROGROW.curie('chemical_formula'),
                   model_uri=MICROGROW.mediumPredictionExtended__chemical_formula, domain=None, range=Optional[str])

slots.mediumPredictionExtended__kg_node_id = Slot(uri=MICROGROW.kg_node_id, name="mediumPredictionExtended__kg_node_id", curie=MICROGROW.curie('kg_node_id'),
                   model_uri=MICROGROW.mediumPredictionExtended__kg_node_id, domain=None, range=Optional[str],
                   pattern=re.compile(r'^(CHEBI|PubChem|CAS|mediadive\.(ingredient|solution)):[A-Za-z0-9_.-]+$'))

slots.mediumPredictionExtended__solubility = Slot(uri=MICROGROW.solubility, name="mediumPredictionExtended__solubility", curie=MICROGROW.curie('solubility'),
                   model_uri=MICROGROW.mediumPredictionExtended__solubility, domain=None, range=Optional[str])

slots.mediumPredictionExtended__limit_of_toxicity = Slot(uri=MICROGROW.limit_of_toxicity, name="mediumPredictionExtended__limit_of_toxicity", curie=MICROGROW.curie('limit_of_toxicity'),
                   model_uri=MICROGROW.mediumPredictionExtended__limit_of_toxicity, domain=None, range=Optional[str])


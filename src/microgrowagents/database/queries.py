"""Prebuilt SQL query templates for common operations."""

QUERY_TEMPLATES = {
    "ingredients_by_medium": """
        SELECT i.id as ingredient_id, i.name, i.chebi_id, i.category,
               mi.amount, mi.unit, mi.grams_per_liter, mi.mmol_per_liter
        FROM media_ingredients mi
        JOIN ingredients i ON mi.ingredient_id = i.id
        WHERE mi.media_id = ?
        ORDER BY mi.amount DESC
    """,
    "media_by_organism": """
        SELECT m.name, m.ph_min, m.ph_max, m.medium_type, m.description
        FROM organism_media om
        JOIN media m ON om.media_id = m.id
        WHERE om.organism_id = ?
    """,
    "similar_media": """
        SELECT m2.id, m2.name, COUNT(*) as shared_ingredients
        FROM media_ingredients mi1
        JOIN media_ingredients mi2 ON mi1.ingredient_id = mi2.ingredient_id
        JOIN media m2 ON mi2.media_id = m2.id
        WHERE mi1.media_id = ? AND mi2.media_id != ?
        GROUP BY m2.id, m2.name
        ORDER BY shared_ingredients DESC
        LIMIT 10
    """,
    "organisms_for_medium": """
        SELECT o.name, o.rank, o.id
        FROM organism_media om
        JOIN organisms o ON om.organism_id = o.id
        WHERE om.media_id = ?
    """,
    "ingredient_properties": """
        SELECT i.*, cp.hydration_state, cp.pka_values, cp.solubility
        FROM ingredients i
        LEFT JOIN chemical_properties cp ON i.id = cp.ingredient_id
        WHERE i.id = ? OR i.name = ?
    """,
    "ingredient_effects": """
        SELECT ie.*, i.name as ingredient_name
        FROM ingredient_effects ie
        JOIN ingredients i ON ie.ingredient_id = i.id
        WHERE ie.ingredient_id = ?
        ORDER BY ie.effect_type
    """,
    "media_by_ph_range": """
        SELECT id, name, ph_min, ph_max, medium_type
        FROM media
        WHERE ph_min >= ? AND ph_max <= ?
        ORDER BY ph_min
    """,
    "search_media_by_name": """
        SELECT id, name, medium_type, description
        FROM media
        WHERE LOWER(name) LIKE LOWER(?)
        ORDER BY name
        LIMIT 20
    """,
    "search_ingredients_by_name": """
        SELECT id, name, chebi_id, molecular_weight
        FROM ingredients
        WHERE LOWER(name) LIKE LOWER(?)
        ORDER BY name
        LIMIT 20
    """,
}

# Leftover Chef — Recipe & Ingredient Seed Data

This directory holds the validated local recipe and canonical ingredient catalogue used by **Leftover Chef** (`data/seed/catalogue.json`).

## Provenance and Licensing

- **Source**: Leftover Chef Verified Test Kitchen Catalogue v1.0 (Original structured reference recipes authored for Leftover Chef).
- **Licence**: CC0-1.0 Public Domain Dedication. No third-party copyrighted recipe text or unlicensed photographs are included.
- **Image Assets**: Original SVG food illustrations located in `frontend/public/images/` under CC0-1.0 / MIT project licensing.

## Key Culinary & Allergen Distinctions Preserved

To prevent unsafe ingredient conflation or inaccurate recipe results, the canonical ingredient catalogue explicitly separates:
- `ing_milk` (Dairy milk) vs. `ing_coconut_milk` (Plant-based coconut milk)
- `ing_butter` (Dairy butter) vs. `ing_margarine` (Vegetable oil spread)
- `ing_wheat_flour` (Gluten-containing wheat flour) vs. `ing_rice_flour` (Gluten-free milled rice flour)
- `ing_onion` (Bulb onion) vs. `ing_spring_onion` (Scallions / green shoots)
- `ing_fresh_chilli` (Fresh green/red chilli pepper) vs. `ing_chilli_powder` (Dried ground chilli spice)
- `ing_peanuts` (Groundnut legume allergen) vs. `ing_tree_nuts` (Cashews, almonds, walnuts)

## Validation Rules

Before seeding the database (`python scripts/seed_db.py`), the seed validator enforces:
1. Unique `id` and non-empty `canonical_name` for every ingredient.
2. No alias collisions across distinct canonical ingredients.
3. Every recipe has a non-empty name, description, positive `default_servings`, non-negative `preparation_minutes` and `cooking_minutes`, ordered `instructions`, and at least one required ingredient.
4. Every recipe ingredient references a valid `ingredient_id` and declares `requirement_type` as either `"required"` or `"optional"`.

---
**Developed by Anil Biradar**

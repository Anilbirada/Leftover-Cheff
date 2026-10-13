# Recipe Data and Matching Rules — Leftover Chef

## 1. Ingredient Normalisation Pipeline
Implemented in `backend/app/services/normalizer.py`:
1. **Tokenisation**: Splits raw strings on commas (`,`), semicolons (`;`), and newlines (`\n`), preventing comma-separated sentences from being treated as a single ingredient.
2. **String Cleaning**: Converts to lowercase, replaces hyphens with spaces, strips punctuation, and collapses repeated whitespace.
3. **Resolution Order**:
   - Exact canonical name match (`ingredients.canonical_name`).
   - Explicit approved alias match (`ingredient_aliases.normalised_alias`, e.g., `aloo` -> `potato`, `jeera` -> `cumin`, `scallions` -> `spring onion`).
   - Controlled plural-to-singular morphological rules (`potatoes` -> `potato`, `tomatoes` -> `tomato`, `chillies` -> `chilli`).
4. **Deduplication**: Deduplicates resolved canonical IDs while preserving the user's input order.

## 2. Preserved Culinary & Allergen Distinctions
The catalogue explicitly separates ingredients whose substitution alters dish structure or allergen profile:
- `milk` (`ing_milk`) vs `coconut milk` (`ing_coconut_milk`)
- `butter` (`ing_butter`) vs `margarine` (`ing_margarine`)
- `wheat flour` (`ing_wheat_flour`) vs `rice flour` (`ing_rice_flour`)
- `onion` (`ing_onion`) vs `spring onion` (`ing_spring_onion`)
- `fresh chilli` (`ing_fresh_chilli`) vs `chilli powder` (`ing_chilli_powder`)
- `peanuts` (`ing_peanuts`) vs `tree nuts` (`ing_tree_nuts`)

## 3. Matching Score Formula
$$\text{Core Coverage Score} = \text{round}\left(\frac{\text{Matched Required Ingredients}}{\text{Total Required Ingredients}} \times 100,\ 1\right)$$

- **Required Ingredients**: Every recipe ingredient with `requirement_type = "required"` (including required cooking oil, salt, and core spices) is included in the denominator.
- **Optional Ingredients**: Ingredients with `requirement_type = "optional"` are excluded from the required coverage denominator and reported in `matched_optional_ingredients` and `missing_optional_ingredients`.

## 4. Ranking Rules
Under default `best_match` sorting, recipes are ordered by:
1. Higher `core_coverage_score` descending.
2. Higher `matched_required_count` descending.
3. Lower `missing_required_count` ascending.
4. Higher `matched_optional_count` descending.
5. Shorter `total_minutes` (`preparation_minutes + cooking_minutes`) ascending.
6. Alphabetical recipe `name` ascending.

---
**Developed by Anil Biradar**

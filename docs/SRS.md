# Software Requirements Specification (SRS) — Leftover Chef

## 1. Functional Requirements

### FR-01: Ingredient Input & Normalisation
- Accept single or comma/semicolon/newline-separated ingredient strings up to 1,000 characters and 50 items per search.
- Normalise case, whitespace, and punctuation.
- Deduplicate repeated entries and aliases.
- Map known aliases (e.g., `aloo` -> `potato`, `scallions` -> `spring onion`, `garbanzo beans` -> `chickpeas`) while keeping distinct ingredients separate (`milk` vs `coconut milk`, `wheat flour` vs `rice flour`, `peanuts` vs `tree nuts`).

### FR-02: Recipe Matching & Ranking
- Calculate core required ingredient coverage: `(matched_required_count / total_required_count) * 100`.
- Exclude optional ingredients from the required denominator while returning matched/missing optional counts separately.
- Support filtering by dietary attribute, excluded ingredients, maximum total time, difficulty, and cuisine.
- Support sorting by `best_match`, `fewest_missing`, `shortest_time`, and `alphabetical`.

### FR-03: Serving Adjustment & Quantity Calculation
- Scale numeric quantities via `original_quantity * requested_servings / original_servings` for 1–50 servings.
- Preserve qualitative quantities (`"to taste"`) unchanged.
- Do not overwrite original recipe records in the database.
- Refuse mass-to-volume conversions (`g` <-> `ml` or `cup`).

### FR-04: Pantry, Favourites & Shopping List
- Full CRUD for `UserPantryItem`, `UserFavourite`, and `ShoppingListItem` scoped to the authenticated/active `X-User-ID`.
- Merge duplicate shopping list items only when units share a compatible dimension (`g`/`kg`, `ml`/`litre`, `teaspoon`/`tablespoon`).

## 2. Non-Functional Requirements
- **NFR-01 (Performance)**: Local ingredient matching and SQLite queries complete in < 100 ms for the seed catalogue.
- **NFR-02 (Security)**: Input length bounds, HTML output sanitization, parameterised ORM queries, and strict `X-User-ID` format validation.
- **NFR-03 (Accessibility & Responsiveness)**: Semantic HTML landmarks, `aria-label` attributes on interactive controls, and responsive CSS grid layouts across desktop, tablet, and mobile viewports.

---
**Developed by Anil Biradar**

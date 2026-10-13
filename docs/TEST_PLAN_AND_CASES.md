# Test Plan and Execution Report (TC-01 through TC-60) — Leftover Chef

## 1. Execution Commands & Real Verification Summary
- **Backend Automated Test Command**: `python -m pytest backend/tests/test_leftover_chef.py -v`
  - **Outcome**: `52 passed in 11.21s` (Exit Code `0`).
- **Frontend Automated Test Command**: `npm.cmd test` (`vitest run` inside `frontend/`)
  - **Outcome**: `1 passed (1 file), 8 passed (8 tests)` (Exit Code `0`).
- **Production Build Verification**: `npm.cmd run build` (`tsc -b && vite build`)
  - **Outcome**: `✓ built in 14.41s` (Exit Code `0`).

---

## 2. Detailed Test Case Execution Log

| Test ID | Test Purpose | Preconditions | Steps | Expected Result | Actual Result | Status | Defect Ref |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Submit one valid ingredient | Seeded DB | POST `["potato"]` to `/api/v1/recipes/search-by-ingredients` | Normalises to `potato` (`ing_potato`) | Resolved `ing_potato` (`is_recognised=True`) | **Pass** | None |
| **TC-02** | Submit multiple comma-separated ingredients | Seeded DB | POST `["potato, onion, tomato, rice"]` | Splits into 4 distinct canonical items | Returned `["potato", "onion", "tomato", "rice"]` | **Pass** | None |
| **TC-03** | Handle empty input | Seeded DB | POST `["   ", ""]` | Returns empty matches & helpful guidance | `matched_recipes=[]` with guidance message | **Pass** | None |
| **TC-04** | Remove repeated whitespace | Seeded DB | POST `["   spring    onions  ", "  cooking   oil! "]` | Collapses spaces and strips punctuation | Resolved `spring onion` and `cooking oil` | **Pass** | None |
| **TC-05** | Handle repeated ingredients | Seeded DB | POST `["potato", "potatoes", "aloo", "POTATO"]` | Deduplicates to a single `ing_potato` | Single entry `ing_potato` returned | **Pass** | None |
| **TC-06** | Handle case differences | Seeded DB | POST `["ToMaTo", "ONION", "rIcE"]` | Case-insensitive resolution | Matched `ing_tomato`, `ing_onion`, `ing_rice` | **Pass** | None |
| **TC-07** | Resolve approved ingredient alias | Seeded DB | POST `["scallions", "garbanzo beans", "jeera"]` | Maps aliases to canonical IDs | Resolved `ing_spring_onion`, `ing_chickpeas`, `ing_cumin_seeds` | **Pass** | None |
| **TC-08** | Do not incorrectly merge distinct ingredients | Seeded DB | Submit 6 pairs (`milk`/`coconut milk`, `butter`/`margarine`, `wheat`/`rice flour`, `onion`/`spring onion`, `fresh chilli`/`chilli powder`, `peanuts`/`tree nuts`) | All 12 resolve to separate canonical IDs | 12 distinct `ingredient_id` values verified | **Pass** | None |
| **TC-09** | Reject oversized input appropriately | Seeded DB | Submit >1000 chars in `ingredients` | HTTP 422 Unprocessable Entity | HTTP 422 returned | **Pass** | None |
| **TC-10** | Handle unknown ingredient gracefully | Seeded DB | POST `["dragonfruit_xyz", "potato", "onion"]` | Records `dragonfruit_xyz` in `unrecognised_inputs` & matches valid ones | Unrecognised listed; valid recipes matched | **Pass** | None |
| **TC-11** | Find recipe when all required ingredients available | Seeded DB | POST `["rice", "tomato", "onion", "cooking oil", "salt"]` | `rec_spiced_tomato_onion_rice` has 100.0% coverage & 0 missing | `core_coverage_score=100.0`, `missing_required_count=0` | **Pass** | None |
| **TC-12** | Identify recipe with some missing ingredients | Seeded DB | POST `["potato", "tomato", "onion"]` | `rec_potato_tomato_curry` shows 3 matched, 3 missing (50.0%) | `core_coverage_score=50.0`, missing `cooking oil`, `salt`, `turmeric powder` | **Pass** | None |
| **TC-13** | Exclude optional ingredients from required coverage | Seeded DB | POST all 6 required items for `rec_potato_tomato_curry` | Score is 100.0% while 3 optional items reported separately | `core_coverage_score=100.0`, `missing_optional_count=3` | **Pass** | None |
| **TC-14** | Return no-match guidance for unsuitable searches | Seeded DB | POST `["unknown_herb_123"]` | Empty `matched_recipes` and non-empty `no_match_guidance` | Guidance string returned mentioning `unknown_herb_123` | **Pass** | None |
| **TC-15** | Rank recipes using documented ranking rules | Seeded DB | POST 7 staple items | Higher coverage %, then higher matched required count ranks first | `rec_cheesy_tomato_rice_bake` (7/7) ranked #1 | **Pass** | None |
| **TC-16** | Confirm matching scores use actual ingredient records | Seeded DB | POST `["potato", "onion", "tomato", "cheese"]` | Score equals `round((matched_req/total_req)*100, 1)` | Verified across all returned recipes | **Pass** | None |
| **TC-17** | Do not claim ingredient is available if missing | Seeded DB | POST `["pasta", "garlic"]` | `butter` and `cheese` remain in `missing_required_ingredients` | Disjoint sets verified | **Pass** | None |
| **TC-18** | Confirm dietary filters work with supported metadata | Seeded DB | Filter `dietary_filters=["vegan"]` | Excludes dairy recipes; returns only vegan recipes | All returned recipes have `vegan` attribute | **Pass** | None |
| **TC-19** | Confirm excluded ingredients are handled correctly | Seeded DB | Exclude `["groundnuts"]` (alias for `peanuts`) | `rec_peanut_garlic_rice_bowl` excluded | Excluded from results | **Pass** | None |
| **TC-20** | Confirm result sorting behaves consistently | Seeded DB | Sort by `shortest_time` and `alphabetical` | Ordered by ascending `total_minutes` and `name` | Monotonic order verified | **Pass** | None |
| **TC-21** | Retrieve a valid recipe | Seeded DB | GET `/api/v1/recipes/rec_potato_tomato_curry` | HTTP 200 with structured ingredients & steps | HTTP 200 with 9 ingredients & 6 steps | **Pass** | None |
| **TC-22** | Handle a recipe that does not exist | Seeded DB | GET `/api/v1/recipes/rec_nonexistent_dish` | HTTP 404 Not Found | HTTP 404 returned | **Pass** | None |
| **TC-23** | Display ingredient quantities and units correctly | Seeded DB | Inspect `ing_potato` on `rec_potato_tomato_curry` | `quantity=2.0`, `unit="piece"`, `display_quantity="2 piece"` | Exact match verified | **Pass** | None |
| **TC-24** | Scale ingredients for a different serving count | Seeded DB | POST `{"servings": 4}` to `/recipes/rec_potato_tomato_curry/servings` | 2 potatoes for 2 servings scales to 4 potatoes | `adjusted_quantity=4.0`, `display_quantity="4 piece"` | **Pass** | None |
| **TC-25** | Preserve qualitative quantities such as "to taste" | Seeded DB | Scale `rec_potato_tomato_curry` to 6 servings | `salt` (`to taste`) remains `None` / `"to taste"` | `adjusted_quantity=None`, `display_quantity="to taste"` | **Pass** | None |
| **TC-26** | Do not apply unsupported mass-to-volume conversions | Unit Service | Call `combine_compatible_quantities(100, "g", 50, "ml")` | Raises `ValueError` | Raised `ValueError("Cannot safely convert...")` | **Pass** | None |
| **TC-27** | Preserve original recipe data after serving adjustments | Seeded DB | Scale to 10 servings, then GET recipe | Original recipe still has `default_servings=2` and `2 piece` potato | Original DB record untouched | **Pass** | None |
| **TC-28** | Display cooking instructions in the correct order | Seeded DB | GET `/api/v1/recipes/rec_potato_tomato_curry` | 6 ordered steps starting with peeling potatoes | Exact sequence verified | **Pass** | None |
| **TC-29** | Add a pantry item | Seeded DB | POST `{"ingredient_name": "potatoes", "quantity": 4, "unit": "piece"}` | HTTP 201 with canonical name `potato` | HTTP 201 returned | **Pass** | None |
| **TC-30** | Update a pantry quantity | Pantry item exists | PATCH `/api/v1/pantry/items/{id}` with `{"quantity": 5}` | HTTP 200 with `quantity=5.0` | Updated quantity verified | **Pass** | None |
| **TC-31** | Delete a pantry item | Pantry item exists | DELETE `/api/v1/pantry/items/{id}` | HTTP 204 and removed from GET list | HTTP 204 & item removed | **Pass** | None |
| **TC-32** | Save a favourite recipe | Seeded DB | POST `/api/v1/favourites/rec_potato_tomato_curry` | HTTP 201 and listed in `/api/v1/favourites` | Saved and retrieved | **Pass** | None |
| **TC-33** | Remove a favourite recipe | Favourite exists | DELETE `/api/v1/favourites/rec_potato_tomato_curry` | HTTP 204 and empty favourites list | Removed verified | **Pass** | None |
| **TC-34** | Prevent unauthorised access to private user data | Multi-user headers | `chef_alice` creates item; `chef_bob` lists/deletes; `private_user1` without token | `chef_bob` gets empty list / 404; `private_user1` gets 403 | Cross-user isolation and 403 verified | **Pass** | None |
| **TC-35** | Add a missing ingredient to a shopping list | Seeded DB | POST `turmeric powder` linked to `rec_potato_tomato_curry` | HTTP 201 with `related_recipe_id` | Item created with recipe reference | **Pass** | None |
| **TC-36** | Mark a shopping item as purchased | Item exists | PATCH `/api/v1/shopping-list/items/{id}` `{"completed": true}` | HTTP 200 with `completed=True` | Status updated | **Pass** | None |
| **TC-37** | Remove a shopping list item | Item exists | DELETE `/api/v1/shopping-list/items/{id}` | HTTP 204 and removed from list | Item deleted | **Pass** | None |
| **TC-38** | Handle duplicate shopping ingredients appropriately | Seeded DB | Add `60 g cheese`, `40 g cheddar`, and `1 cup cheese` | Compatible `g` merges to `100 g`; incompatible `1 cup` stays separate | 2 items (`100 g` and `1 cup`) verified | **Pass** | None |
| **TC-39** | Preserve shopping quantities and units correctly | Seeded DB | Add `200 ml coconut milk` | `display_quantity="200 ml"` | Verified | **Pass** | None |
| **TC-40** | Do not claim unverified allergen safety | Seeded DB | GET `/api/v1/recipes/rec_potato_tomato_curry` | Notice includes cross-contamination caveat | Caveat present | **Pass** | None |
| **TC-41** | Handle recipes with unknown allergen information | Seeded DB | GET `/api/v1/recipes/rec_spring_onion_soy_fried_rice` | Displays `"Allergen information not verified"` | Exact warning verified | **Pass** | None |
| **TC-42** | Ensure unverified AI suggestions are labelled appropriately | Seeded DB | Search with `include_ai_explanation=True` | `is_ai_generated=True`, `verification_status="unverified_suggestion"` | Explicit labels & disclaimer verified | **Pass** | None |
| **TC-43** | Do not claim expiry-date comparison proves food safety | Seeded DB | Add pantry item with `best_before_date="2099-12-31"` | `food_safety_reminder` warns dates do not prove safety | Warning verified | **Pass** | None |
| **TC-44** | Validate API input | Seeded DB | POST empty name and negative quantity to `/api/v1/pantry/items` | HTTP 422 validation error | HTTP 422 returned | **Pass** | None |
| **TC-45** | Return controlled errors for invalid requests | Seeded DB | GET `/api/v1/recipes/non_existent_id` | Controlled JSON `{"detail": ...}` with HTTP 404 | Controlled JSON returned | **Pass** | None |
| **TC-46** | Prevent SQL injection | Seeded DB | Submit `"potato'; DROP TABLE recipes; --"` | Treated as literal string; `recipes` table remains intact (12 rows) | Table intact (12 recipes) | **Pass** | None |
| **TC-47** | Prevent unsafe HTML rendering | Seeded DB | PUT `<script>alert('xss')</script>Chef` to `/api/v1/profile` | Escaped to `&lt;script&gt;...` | Sanitized output verified | **Pass** | None |
| **TC-48** | Protect secrets in responses and logs | Seeded DB | GET `/api/v1/health` | No `secret_key` or API key exposed | Verified | **Pass** | None |
| **TC-49** | Enforce user-specific access controls | Seeded DB | Send invalid `X-User-ID: ../admin/secret` | HTTP 400 Bad Request | HTTP 400 returned | **Pass** | None |
| **TC-50** | Handle unavailable external provider gracefully | Seeded DB | Call `generate_recipe_match_explanation(..., simulate_provider_failure=True)` | Returns deterministic fallback without throwing | `fallback_deterministic_provider_unavailable` | **Pass** | None |
| **TC-51** | Prevent invalid serving counts | Seeded DB | POST `servings=0`, `-2`, and `500` | HTTP 422 Unprocessable Entity | All rejected with 422 | **Pass** | None |
| **TC-52** | Ensure shopping-list and pantry use validated data | Seeded DB | POST unrecognised pantry ingredient & test malformed seed payload | HTTP 422 and `ValueError` | Both rejected as expected | **Pass** | None |
| **TC-53** | Complete main frontend ingredient-search workflow | Vitest / JSDOM | Enter comma-separated ingredients, click Add, view results | Splits into individual chips and renders matched cards | Verified in `App.test.tsx` | **Pass** | None |
| **TC-54** | Display loading states | Vitest / JSDOM | Hold search promise pending | Renders loading message until resolved | Verified in `App.test.tsx` | **Pass** | None |
| **TC-55** | Display understandable errors | Vitest / JSDOM | Submit empty ingredient input | Renders `role="alert"` with actionable guidance | Verified in `App.test.tsx` | **Pass** | None |
| **TC-56** | Display matching and missing ingredients | Vitest / JSDOM | Inspect card and open Recipe Detail modal | Shows `Matched Required`, `Missing Required`, `[Available]`, `[Missing]` | Verified in `App.test.tsx` | **Pass** | None |
| **TC-57** | Confirm responsive mobile layouts | Vitest / JSDOM | Inspect `.app-shell`, `.recipe-grid`, `.filters-bar` & `@media (max-width: 768px)` | Responsive grid & flex rules present | Verified in `App.test.tsx` | **Pass** | None |
| **TC-58** | Verify keyboard navigation and accessible labels | Vitest / JSDOM | Query by `aria-label` and `role` | All inputs, buttons, lists, and modals have accessible labels | Verified in `App.test.tsx` | **Pass** | None |
| **TC-59** | Confirm footer developer credit is visible | Vitest / JSDOM | Check `data-testid="footer-developer-credit"` and Credits tab | Displays `"Developed by Anil Biradar"` | Verified in `App.test.tsx` | **Pass** | None |
| **TC-60** | Confirm no decorative control appears to work when unimplemented | Vitest / JSDOM | Click each navigation tab and action button | Every button transitions view or calls backend API | Verified in `App.test.tsx` | **Pass** | None |

---
**Developed by Anil Biradar**

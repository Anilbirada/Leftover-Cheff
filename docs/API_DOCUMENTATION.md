# API Documentation — Leftover Chef

Base URL: `/api/v1`
User Workspace Header: `X-User-ID: default_chef` (optional; defaults to `default_chef`).

## 1. System & Health
- **`GET /api/v1/health`**
  - Returns application health status, version, environment, recipe/ingredient counts, and developer credit (`Developed by Anil Biradar`) without exposing secrets.

## 2. Recipes & Matching
- **`GET /api/v1/recipes`**
  - Query params: `dietary`, `cuisine`, `difficulty`, `max_total_minutes`, `sort_by` (`alphabetical` | `shortest_time`), `limit`, `offset`.
  - Returns recipe summaries with dietary badges and allergen verification summary notices.
- **`GET /api/v1/recipes/{recipe_id}`**
  - Optional query param: `available_ingredients` (comma-separated string).
  - Returns full recipe details, ordered steps, structured ingredient quantities, allergen verification notice, and food-safety precautions.
- **`POST /api/v1/recipes/search-by-ingredients`**
  - Request body:
    ```json
    {
      "ingredients": ["potato, onion, tomato, rice"],
      "dietary_filters": ["vegan"],
      "excluded_ingredients": ["peanuts"],
      "max_total_minutes": 35,
      "difficulty": "Easy",
      "sort_by": "best_match",
      "include_ai_explanation": false
    }
    ```
  - Returns normalised user ingredients, unrecognised inputs, ranked recipe matches with `core_coverage_score`, matched/missing required and optional ingredients, and no-match guidance when applicable.
- **`POST /api/v1/recipes/{recipe_id}/servings`**
  - Request body: `{"servings": 4}` (integer `1` to `50`).
  - Returns scaled ingredient quantities without mutating the stored recipe.

## 3. Ingredients Catalogue
- **`GET /api/v1/ingredients?q=...&category=...`**
- **`GET /api/v1/ingredients/suggestions?prefix=...&limit=12`**

## 4. Pantry Management
- **`GET /api/v1/pantry/items`**
- **`POST /api/v1/pantry/items`**
- **`PATCH /api/v1/pantry/items/{item_id}`**
- **`DELETE /api/v1/pantry/items/{item_id}`**

## 5. Favourites
- **`GET /api/v1/favourites`**
- **`POST /api/v1/favourites/{recipe_id}`**
- **`DELETE /api/v1/favourites/{recipe_id}`**

## 6. Shopping List & Profile
- **`GET /api/v1/shopping-list`**
- **`POST /api/v1/shopping-list/items`**
- **`PATCH /api/v1/shopping-list/items/{item_id}`**
- **`DELETE /api/v1/shopping-list/items/{item_id}`**
- **`DELETE /api/v1/shopping-list/completed`**
- **`GET /api/v1/profile`** & **`PUT /api/v1/profile`**

---
**Developed by Anil Biradar**

# Database Design — Leftover Chef

## 1. Relational Schema Overview
The database is managed via SQLAlchemy 2.0 (`backend/app/models/entities.py`) with `PRAGMA foreign_keys=ON` enforced on SQLite connections and full compatibility with PostgreSQL.

## 2. Entities & Tables

### A. `ingredients`
- `id` (PK, `VARCHAR(64)`): Canonical identifier (e.g., `ing_potato`, `ing_coconut_milk`).
- `canonical_name` (`VARCHAR(120)`, `UNIQUE`, `INDEX`): Lowercase canonical name.
- `category` (`VARCHAR(64)`, `INDEX`): e.g., `vegetable`, `grain`, `dairy`, `spice`, `legume_nut`.
- `description` (`TEXT`, nullable).
- `active` (`BOOLEAN`, default `True`).

### B. `ingredient_aliases`
- `id` (PK, `INTEGER`).
- `ingredient_id` (FK -> `ingredients.id`, `ON DELETE CASCADE`, `INDEX`).
- `alias` (`VARCHAR(120)`).
- `normalised_alias` (`VARCHAR(120)`, `UNIQUE`, `INDEX`).

### C. `recipes`
- `id` (PK, `VARCHAR(64)`).
- `name` (`VARCHAR(200)`, `INDEX`), `description` (`TEXT`).
- `preparation_minutes` (`INTEGER`), `cooking_minutes` (`INTEGER`), `default_servings` (`INTEGER`).
- `difficulty` (`VARCHAR(32)`), `cuisine` (`VARCHAR(64)`, `INDEX`).
- `instructions_json` (`TEXT`): JSON array of ordered step strings.
- `image_reference`, `source_reference`, `licence_reference` (`VARCHAR(255)`).
- `created_at`, `updated_at` (`DATETIME`).

### D. `recipe_ingredients`
- `id` (PK, `INTEGER`).
- `recipe_id` (FK -> `recipes.id`, `ON DELETE CASCADE`).
- `ingredient_id` (FK -> `ingredients.id`, `ON DELETE RESTRICT`).
- `quantity` (`FLOAT`, nullable for qualitative amounts), `unit` (`VARCHAR(64)`).
- `requirement_type` (`VARCHAR(32)`): `"required"` or `"optional"`.
- `preparation_note` (`VARCHAR(200)`, nullable).
- Unique constraint on `(recipe_id, ingredient_id)`.

### E. `recipe_dietary_attributes` & `recipe_allergens`
- Store verified dietary attributes (`vegetarian`, `vegan`, `gluten-free`, `dairy-free`, `nut-free`) and allergen declarations (`allergen`, `verification_status`, `source_reference`).

### F. `users`, `user_pantry_items`, `user_favourites`, `shopping_lists`, `shopping_list_items`
- Scoped by `user_id` (`FK -> users.id`, `ON DELETE CASCADE`) to isolate personal pantry items, saved favourites, and shopping lists per user workspace.

---
**Developed by Anil Biradar**

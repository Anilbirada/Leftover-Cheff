# Changelog — Leftover Chef

## [1.0.0] — 2026-10-13
### Added
- **Seed Catalogue (`data/seed/catalogue.json`)**: 30 canonical ingredients with explicit aliases and 12 structured, verified recipes preserving culinary and allergen distinctions.
- **Backend (`backend/`)**:
  - FastAPI application (`app/main.py`, `app/api/routes.py`) with 19 REST endpoints.
  - SQLAlchemy 2.0 relational database schema (`app/models/entities.py`) for ingredients, aliases, recipes, dietary tags, allergens, users, pantry items, favourites, and shopping lists.
  - Deterministic ingredient normalisation service (`app/services/normalizer.py`).
  - Transparent recipe-matching and ranking engine (`app/services/matcher.py`).
  - Serving size scaling and safe unit-combining service (`app/services/scaler.py`).
  - Seed validation and database seeding CLI (`scripts/seed_db.py`).
  - Automated backend test suite (`backend/tests/test_leftover_chef.py`) covering **TC-01 through TC-52** (52/52 passing).
- **Frontend (`frontend/`)**:
  - React 18 + TypeScript + Vite SPA with responsive olive/cream culinary design (`src/App.tsx`, `src/components/RecipeDetailModal.tsx`, `src/components/RecipeIllustration.tsx`).
  - Automated frontend test suite (`src/tests/App.test.tsx`) covering **TC-53 through TC-60** (8/8 passing).
  - Persistent production footer and About/Credits attribution: `Developed by Anil Biradar`.
- **Documentation (`docs/` & `README.md`)**: Complete 17-document engineering suite.

# System Design — Leftover Chef

## 1. Architectural Overview
Leftover Chef uses a clean, modular three-tier architecture:
1. **Presentation Layer (`frontend/`)**: React 18 + TypeScript SPA built with Vite. Communicates with the backend via typed REST calls (`frontend/src/services/api.ts`).
2. **Application & Domain Layer (`backend/app/`)**:
   - **API Routing (`app/api/routes.py`)**: Validates requests via Pydantic schemas (`app/schemas/api_schemas.py`), enforces user isolation (`app/core/security.py`), and delegates business logic to independent domain services.
   - **Normalisation Service (`app/services/normalizer.py`)**: Tokenises, cleans, deduplicates, and resolves raw user strings to canonical ingredient IDs.
   - **Matching & Ranking Service (`app/services/matcher.py`)**: Computes core required coverage scores, separates optional ingredients, applies filters, and ranks recipes.
   - **Quantity Scaling Service (`app/services/scaler.py`)**: Scales numeric recipe quantities and combines compatible shopping-list units while blocking unsafe mass-to-volume conversions.
   - **Catalogue Validator & Seeder (`app/services/seed_service.py`)**: Audits `data/seed/catalogue.json` before idempotently populating the relational database.
3. **Persistence Layer (`leftover_chef.db` / SQLAlchemy 2.0)**: Relational database with foreign-key enforcement.

## 2. End-to-End Request Flow
```
User enters "potato, onion, tomato, rice"
      |
      v
Frontend splits input into removable chips -> POST /api/v1/recipes/search-by-ingredients
      |
      v
normalizer.py cleans tokens & resolves canonical IDs (ing_potato, ing_onion, ing_tomato, ing_rice)
      |
      v
matcher.py compares against RecipeIngredient records, calculates required coverage %, and ranks
      |
      v
Frontend renders recipe cards with exact matched vs missing required ingredients
```

---
**Developed by Anil Biradar**

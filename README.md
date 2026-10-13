# LEFTOVER CHEF — Smart Recipe Discovery & Ingredient Matching Platform

**Leftover Chef** is a full-stack recipe discovery, ingredient normalisation, pantry management, and serving-scaling web application designed to help households cook practical meals using the ingredients they already have, reduce avoidable food waste, and maintain strict culinary and allergen transparency.

---

## 1. Main Features

- **Natural Ingredient Entry & Normalisation**: Enter single or comma-separated lists (e.g., `"potato, onion, tomato, rice"`), automatically converted into removable ingredient chips, deduplicated, and resolved against 30 canonical ingredients and approved aliases.
- **Preserved Culinary & Allergen Distinctions**: Explicitly distinguishes between `milk` vs `coconut milk`, `butter` vs `margarine`, `wheat flour` vs `rice flour`, `onion` vs `spring onion`, `fresh chilli` vs `chilli powder`, and `peanuts` vs `tree nuts`.
- **Transparent Recipe Matching & Ranking**: Computes deterministic core ingredient coverage (`(matched_required / total_required) * 100`), separates required vs optional ingredients, and highlights exact available and missing items.
- **Reliable Serving Size Scaling**: Scales numeric quantities dynamically (`adjusted = original * requested_servings / default_servings`), preserves qualitative measurements (`"to taste"`), never mutates stored recipe data, and forbids unsafe mass-to-volume conversions without density data.
- **My Kitchen Pantry**: Add, update, search, and remove household ingredients with quantities, units, reference dates, storage notes, and one-click recipe matching.
- **Smart Shopping List**: Export missing required ingredients directly from recipes, automatically combine compatible metric units (`g`/`kg`, `ml`/`litre`), keep incompatible units separate, and mark items as purchased.
- **Favourites & User Workspace Isolation**: Save favourite recipes and manage culinary preferences with strict server-side user isolation (`X-User-ID`).
- **Food-Safety & Allergen Integrity**: Clearly distinguishes verified base-recipe allergen audits from unverified components (`"Allergen information not verified"`), and warns that digital pantry records or best-before dates never prove food safety.

---

## 2. Technology Stack & Architecture

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite, Lucide Icons, Responsive CSS |
| **Backend** | Python 3.12, FastAPI, Pydantic v2, Modular Service Layer |
| **Database** | SQLite (`leftover_chef.db` for local execution) / PostgreSQL compatible via SQLAlchemy 2.0 ORM |
| **Testing** | `pytest` + FastAPI `TestClient` (52 backend tests: TC-01 to TC-52), `Vitest` + React Testing Library (8 frontend suites: TC-53 to TC-60) |

---

## 3. Recipe Catalogue, Sources & Licences

- **Dataset Location**: `data/seed/catalogue.json`
- **Source & Provenance**: Leftover Chef Verified Test Kitchen Catalogue v1.0 (12 complete, structured recipes and 30 canonical ingredients with explicit aliases).
- **Licence**: CC0-1.0 Public Domain Dedication. Original SVG dish illustrations (`frontend/src/components/RecipeIllustration.tsx`) are authored specifically for this project with zero unlicensed third-party media.

---

## 4. Prerequisites & Installation

### Prerequisites
- **Python**: 3.11+ (tested on Python 3.12.10)
- **Node.js & npm**: Node 20+ and npm 10+

### Environment Setup
1. Copy `.env.example` to `.env` if you wish to customise settings:
   ```bash
   cp .env.example .env
   ```
   *(The application works out-of-the-box locally using safe default SQLite settings without requiring any external API keys.)*

2. Install backend dependencies:
   ```bash
   python -m pip install -r backend/requirements.txt
   ```

3. Seed and validate the local SQLite database:
   ```bash
   python scripts/seed_db.py
   ```

4. Install frontend dependencies:
   ```bash
   cd frontend
   npm.cmd install
   ```

---

## 5. Starting the Application

### Start the Backend Server (Port 8000)
From the repository root:
```bash
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/api/v1/health`

### Start the Frontend Dev Server (Port 5173)
From the `frontend/` directory:
```bash
npm.cmd run dev
```
- Open `http://localhost:5173` in your browser. Vite automatically proxies `/api/v1/*` requests to `http://127.0.0.1:8000`.

---

## 6. Running Automated Tests

### Backend Test Suite (TC-01 through TC-52)
From the repository root:
```bash
python -m pytest backend/tests/test_leftover_chef.py -v
```

### Frontend Test Suite (TC-53 through TC-60) & Production Build
From the `frontend/` directory:
```bash
npm.cmd test
npm.cmd run build
```

---

## 7. How Ingredient Matching & Serving Adjustments Work

### Ingredient Matching Formula
$$\text{Core Coverage Score} = \text{round}\left(\frac{\text{Matched Required Ingredients}}{\text{Total Required Ingredients}} \times 100,\ 1\right)$$
- **Required Ingredients** (`requirement_type = "required"`): Included in the denominator. Required spices, oils, and seasonings are never hidden from the denominator.
- **Optional Ingredients** (`requirement_type = "optional"`): Excluded from the required coverage denominator and reported separately so optional garnishes do not distort core coverage.
- **Ranking Priority**: (1) Highest required coverage %, (2) Most matched required ingredients, (3) Fewest missing required ingredients, (4) Shortest total cooking time, (5) Alphabetical name.

### Serving Adjustments
$$\text{Adjusted Quantity} = \frac{\text{Original Quantity} \times \text{Requested Servings}}{\text{Original Servings}}$$
- Qualitative amounts (`"to taste"`) remain unchanged.
- Stored recipe records are never overwritten.
- Incompatible physical dimensions (e.g., mass `g` to volume `ml` or `cup`) are never converted without density data.

---

## 8. Optional AI Configuration, Privacy, Security & Food Safety

- **Optional AI**: Controlled via `ENABLE_OPTIONAL_AI` in `.env` (`false` by default). Core ingredient matching is 100% deterministic and never depends on an LLM. Any assistant notes are explicitly labelled as unverified suggestions.
- **Security & Privacy**: Parameterised SQLAlchemy queries prevent SQL injection; HTML escaping prevents XSS; user data is isolated by `X-User-ID`; no secrets are stored in code.
- **Food-Safety Limitations**: Digital pantry entries and best-before dates are for inventory convenience only and do not prove food is safe to eat. Always inspect food condition and commercial allergen labels before cooking.

---

## 9. Developer Credit

**Developed by Anil Biradar**

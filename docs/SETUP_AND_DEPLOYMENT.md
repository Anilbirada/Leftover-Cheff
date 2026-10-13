# Setup and Deployment Guide — Leftover Chef

## 1. Local Development Setup

### Step 1: Clone / Open Workspace & Configure Environment
```bash
cp .env.example .env
```

### Step 2: Install Backend Dependencies & Seed Database
```bash
python -m pip install -r backend/requirements.txt
python scripts/seed_db.py
```

### Step 3: Run Backend Automated Tests
```bash
python -m pytest backend/tests/test_leftover_chef.py -v
```

### Step 4: Start the FastAPI Backend
```bash
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

### Step 5: Install, Test & Start the React Frontend
```bash
cd frontend
npm.cmd install
npm.cmd test
npm.cmd run dev
```

## 2. Production Deployment Instructions

### Database Configuration
- For single-instance deployments, SQLite (`DATABASE_URL="sqlite:///./leftover_chef.db"`) works out of the box.
- For multi-worker or cloud deployments, set `DATABASE_URL="postgresql+psycopg://user:password@host:5432/leftover_chef"` in environment variables and run `python scripts/seed_db.py`.

### Security Environment Variables
- Set `APP_ENV="production"` and `DEBUG=false`.
- Generate a strong `SECRET_KEY`:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- Set `ALLOWED_ORIGINS` to your production frontend domain.

### Building Static Frontend Assets
```bash
cd frontend
npm.cmd run build
```
Serve `frontend/dist/` via Nginx, Caddy, Cloudflare Pages, Vercel, or FastAPI static file mounting.

---
**Developed by Anil Biradar**

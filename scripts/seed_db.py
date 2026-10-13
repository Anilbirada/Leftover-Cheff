"""Standalone CLI script to validate and seed the Leftover Chef SQLite/PostgreSQL database."""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import Base, SessionLocal, engine
from app.services.seed_service import seed_database_from_file


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        summary = seed_database_from_file(db)
        print("Leftover Chef database seeded successfully:", summary)


if __name__ == "__main__":
    main()

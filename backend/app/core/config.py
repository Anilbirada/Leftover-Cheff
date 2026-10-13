"""Application configuration loaded from environment variables with safe defaults."""
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_DB_PATH = BASE_DIR / "leftover_chef.db"
DEFAULT_SEED_PATH = BASE_DIR / "data" / "seed" / "catalogue.json"


class Settings(BaseSettings):
    app_name: str = "Leftover Chef"
    app_env: str = "development"
    app_version: str = "1.0.0"
    debug: bool = False
    developer_credit: str = "Developed by Anil Biradar"

    database_url: str = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
    seed_file_path: str = str(DEFAULT_SEED_PATH)

    secret_key: str = "leftover-chef-dev-only-secret-change-in-prod"
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
    rate_limit_per_minute: int = 120
    max_request_body_bytes: int = 65536
    max_ingredients_per_search: int = 50
    max_ingredient_input_chars: int = 1000

    enable_optional_ai: bool = False
    ai_provider_api_key: str = ""
    ai_request_timeout_seconds: int = 8

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()

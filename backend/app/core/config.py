"""
CarePath AI — Core Configuration
Centralized settings management using pydantic-settings.
All configuration is loaded from environment variables / .env file.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
import dotenv

dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))



class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    app_name: str = "CarePath AI"
    app_env: str = "development"
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    debug: bool = True
    api_prefix: str = "/api/v1"

    # ── Database ─────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://carepath:carepath_dev@localhost:5432/carepath_db"
    database_sync_url: str = "postgresql+psycopg2://carepath:carepath_dev@localhost:5432/carepath_db"

    # ── ML Model ─────────────────────────────────────────────
    wait_model_path: str = "../models/artifacts/wait_time_lgbm.txt"
    wait_model_version: str = "v001"
    feature_columns_path: str = "../models/artifacts/feature_columns.json"
    specialty_encoder_path: str = "../models/artifacts/specialty_encoder.json"
    specialty_params_path: str = "../models/artifacts/specialty_params.json"

    # ── Master Dataset ───────────────────────────────────────
    master_dataset_dir: str = "../Datasets/master"

    # ── Storage ──────────────────────────────────────────────
    storage_provider: str = "local"
    local_storage_path: str = "./storage"
    azure_storage_connection_string: Optional[str] = None

    # ── Authentication ───────────────────────────────────────
    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    # ── LLM ──────────────────────────────────────────────────
    llm_provider: str = "none"
    llm_model: Optional[str] = None
    llm_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None

    # ── Azure ────────────────────────────────────────────────
    azure_postgres_url: Optional[str] = None
    azure_blob_storage_url: Optional[str] = None
    azure_app_insights_key: Optional[str] = None

    # ── CORS ─────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # ── Rate Limiting ────────────────────────────────────────
    rate_limit_per_minute: int = 60

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    def resolve_path(self, relative_path: str) -> Path:
        """Resolve a path relative to the backend directory."""
        backend_dir = Path(__file__).resolve().parent.parent.parent
        resolved = (backend_dir / relative_path).resolve()
        return resolved


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()

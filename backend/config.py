"""
Backend application configuration settings.
Loads environment variables safely with Pydantic Settings.
"""

from __future__ import annotations

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    PROJECT_NAME: str = "Gold Research Terminal API"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = f"sqlite:///{(ROOT / 'database' / 'gold_research.db').as_posix()}"
    
    # Security
    TERMINAL_PASSWORD: str = "gold-terminal-secure"
    SECRET_KEY: str = "change-in-production-gold-secret-key-32chars"
    
    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8787",
        "http://127.0.0.1:8787",
        "http://localhost",
    ]

    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

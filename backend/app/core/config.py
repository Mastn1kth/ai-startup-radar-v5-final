import logging
import os
import secrets
from functools import lru_cache
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://radar:radar_secret_2026@localhost:5432/ai_startup_radar"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "startup_embeddings"
    
    # Ollama
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:14b"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHANNEL_ID: str = ""
    
    # Security
    SECRET_KEY: str = ""
    DEFAULT_ADMIN_EMAIL: str = "admin@radar.local"
    DEFAULT_ADMIN_PASSWORD: str = ""
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    # Scraping
    SCRAPE_INTERVAL_MINUTES: int = 120
    MAX_CONCURRENT_SCRAPERS: int = 4
    REQUEST_TIMEOUT: int = 30
    
    # Scoring
    MIN_STARTUP_SCORE_FOR_TELEGRAM: int = 70
    MIN_RUSSIA_SCORE_FOR_ALERT: int = 60
    
    # Sentry
    SENTRY_DSN: str = ""

    # Application
    APP_NAME: str = "AI Startup Radar"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    class Config:
        env_file = "../.env"
        case_sensitive = True
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    if not s.SECRET_KEY:
        s.SECRET_KEY = secrets.token_urlsafe(32)
        logger.warning("Generated random SECRET_KEY: %s. Set it in .env for persistence.", s.SECRET_KEY)
    if not s.DEFAULT_ADMIN_PASSWORD:
        s.DEFAULT_ADMIN_PASSWORD = secrets.token_urlsafe(12)
        logger.warning("Generated random admin password: %s. Set DEFAULT_ADMIN_PASSWORD in .env.", s.DEFAULT_ADMIN_PASSWORD)
    return s


settings = get_settings()
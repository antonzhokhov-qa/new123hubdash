"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "PSP Dashboard"
    debug: bool = False
    log_level: str = "INFO"
    timezone: str = "UTC"

    # Database
    database_url: str = "postgresql+asyncpg://psp_user:psp_password@localhost:5433/psp_dashboard"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Vima API
    vima_api_key: str = ""
    vima_base_url: str = "https://payment.woozuki.com/collector1/api/v1"
    vima_sync_interval_seconds: int = 30  # 30 seconds for real-time updates

    # PayShack API
    payshack_email: str = ""
    payshack_password: str = ""
    payshack_api_url: str = "https://api.payshack.in"
    payshack_sync_interval_seconds: int = 60  # 1 minute for near real-time
    payshack_metadata_sync_interval_seconds: int = 300  # 5 minutes for clients/balances

    # Sync settings
    sync_batch_size: int = 100
    sync_max_retries: int = 3

    # Historical sync settings (first run)
    initial_sync_days: int = 7  # Days to load on first run
    vima_max_batches: int = 100  # Max batches per sync (100 records each)
    payshack_max_pages: int = 500  # Max pages for PayShack sync

    # Cache TTL (seconds)
    cache_ttl_metrics: int = 15  # 15 seconds for fast dashboard
    cache_ttl_transactions: int = 5  # 5 seconds
    cache_ttl_sync_status: int = 3  # 3 seconds

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

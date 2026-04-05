"""Configuration settings for MCP Intelligence Server."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"

    # Backend Service URLs
    content_analysis_url: str = "http://content-analysis-v3:8117"
    entity_canon_url: str = "http://entity-canonicalization:8112"
    intelligence_url: str = "http://intelligence-service:8115"
    narrative_url: str = "http://narrative-service:8116"
    # NOTE: osint_url removed 2026-01-03 - osint-service was archived (placeholder only)

    # Circuit Breaker Settings
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60
    circuit_breaker_expected_exception: str = "httpx.HTTPStatusError"

    # Timeout Settings
    http_timeout: float = 30.0
    http_connect_timeout: float = 5.0

    # Retry Settings
    max_retries: int = 3
    retry_backoff_factor: float = 2.0

    # Redis Cache Settings
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 5
    redis_password: Optional[str] = None
    cache_ttl_short: int = 300      # 5 minutes
    cache_ttl_medium: int = 1800    # 30 minutes
    cache_ttl_long: int = 3600      # 1 hour

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

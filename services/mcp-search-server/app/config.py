"""Configuration settings for MCP Search Server."""

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
    search_url: str = "http://search-service:8106"
    feed_url: str = "http://feed-service:8101"
    research_url: str = "http://research-service:8103"

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

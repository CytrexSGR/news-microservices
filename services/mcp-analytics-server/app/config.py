"""Configuration settings for MCP Analytics Server."""

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
    analytics_url: str = "http://analytics-service:8107"
    prediction_url: str = "http://prediction-service:8116"
    execution_url: str = "http://execution-service:8120"

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
    redis_db: int = 6  # Different DB from search-server (was 5)
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

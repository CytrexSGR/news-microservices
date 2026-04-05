"""Configuration for MCP Integration Server."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server settings from environment variables."""

    # Server
    server_name: str = "mcp-integration-server"
    server_version: str = "1.0.0"
    log_level: str = "INFO"

    # Backend Services
    fmp_service_url: str = "http://localhost:8113"
    research_service_url: str = "http://localhost:8103"
    notification_service_url: str = "http://localhost:8105"

    # Redis Cache
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 3  # Different DB than other MCP servers
    redis_password: str = ""  # Optional, set via environment
    cache_ttl: int = 300  # 5 minutes

    # Circuit Breaker
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 30

    # Rate Limiting
    rate_limit_per_minute: int = 60

    class Config:
        env_prefix = "MCP_INTEGRATION_"
        case_sensitive = False


settings = Settings()

"""Configuration for MCP Core Server."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server settings from environment variables."""

    # Server
    server_name: str = "mcp-core-server"
    server_version: str = "1.0.0"
    log_level: str = "INFO"

    # Backend Services
    auth_service_url: str = "http://localhost:8100"
    analytics_service_url: str = "http://localhost:8107"

    # Redis Cache
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 8  # Different DB than other MCP servers
    redis_password: str = ""
    cache_ttl: int = 300  # 5 minutes

    # Circuit Breaker
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 30

    # Rate Limiting
    rate_limit_per_minute: int = 60

    class Config:
        env_prefix = "MCP_CORE_"
        case_sensitive = False


settings = Settings()

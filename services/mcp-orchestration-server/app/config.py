"""Configuration for MCP Orchestration Server."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server settings from environment variables."""

    # Server
    server_name: str = "mcp-orchestration-server"
    server_version: str = "1.0.0"
    log_level: str = "INFO"

    # Backend Services
    scheduler_service_url: str = "http://localhost:8108"
    mediastack_service_url: str = "http://localhost:8121"
    scraping_service_url: str = "http://localhost:8115"

    # Intelligence MCP Server (gateway to intelligence services)
    intelligence_service_url: str = "http://localhost:9001"

    # Redis Cache
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 10  # Different DB than other MCP servers
    redis_password: str = ""
    cache_ttl: int = 60  # 1 minute (scheduler data changes frequently)

    # Circuit Breaker
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 30

    # Rate Limiting
    rate_limit_per_minute: int = 60

    class Config:
        env_prefix = "MCP_ORCH_"
        case_sensitive = False


settings = Settings()

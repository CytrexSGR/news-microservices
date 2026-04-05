"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service Info
    service_name: str = "mcp-knowledge-graph-server"
    service_version: str = "1.0.0"
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 9004

    # Backend Service URLs
    knowledge_graph_url: str = "http://knowledge-graph-service:8111"

    # HTTP Client
    http_timeout: int = 30  # seconds
    max_connections: int = 100
    max_keepalive_connections: int = 20

    # Circuit Breaker
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60  # seconds

    # Redis Cache
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 7  # DB 7 for knowledge-graph-server
    redis_password: str = ""

    # Cache TTLs (seconds)
    cache_ttl_short: int = 60        # 1 minute - volatile data
    cache_ttl_medium: int = 300      # 5 minutes - semi-stable
    cache_ttl_long: int = 3600       # 1 hour - stable data

    # Cache by endpoint type
    cache_ttl_entity: int = 300      # Entity connections
    cache_ttl_stats: int = 60        # Statistics (frequent changes)
    cache_ttl_search: int = 300      # Search results
    cache_ttl_analytics: int = 600   # Analytics (10 min)
    cache_ttl_market: int = 60       # Market data (volatile)


settings = Settings()

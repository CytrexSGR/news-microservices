"""Configuration management for News MCP microservices."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "news-mcp"
    environment: str = Field(default="development", pattern="^(development|staging|production)$")
    debug: bool = False
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "news_user"
    postgres_password: str = Field(default="+t1koDEJO+ruZ3QnYlkVeU2u6Z+zCJtL6wFW+wfN5Yk=")
    postgres_db: str = "news_mcp"
    postgres_echo_sql: bool = False

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = "redis_secret_2024"
    redis_db: int = 0
    redis_decode_responses: bool = True

    # RabbitMQ
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "admin"
    rabbitmq_password: str = "rabbit_secret_2024"
    rabbitmq_vhost: str = "news_mcp"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "admin"
    minio_secret_key: str = "minio_secret_2024"
    minio_use_ssl: bool = False
    minio_bucket_prefix: str = "news"

    # JWT (Week 1 Security Fix - Load from environment)
    jwt_secret_key: str = Field(default="ef85d69e49bc971350142a18469c646d41addd16ac73d9b28392419b46000315")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    jwt_refresh_expiration_days: int = 30

    # Service Discovery
    service_registry_enabled: bool = True
    service_name: Optional[str] = None
    service_port: Optional[int] = None

    # Observability
    tracing_enabled: bool = True
    metrics_enabled: bool = True
    jaeger_host: str = "localhost"
    jaeger_port: int = 6831
    prometheus_port: int = 9090

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_requests_per_hour: int = 1000

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    cors_allow_headers: list[str] = ["*"]

    @property
    def postgres_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_sync_url(self) -> str:
        """Construct synchronous PostgreSQL connection URL."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL."""
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def rabbitmq_url(self) -> str:
        """Construct RabbitMQ connection URL."""
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}/{self.rabbitmq_vhost}"
        )

    @field_validator("environment")
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    def get_service_database(self, service_name: str) -> str:
        """Get database name for a specific service."""
        service_db_map = {
            "auth": "auth_service",
            "feed": "feed_service",
            "content-analysis": "content_analysis_service",
            "research": "research_service",
            "osint": "osint_service",
            "notification": "notification_service",
        }
        return service_db_map.get(service_name, self.postgres_db)

    def get_service_url(self, service_name: str, path: str = "") -> str:
        """Get URL for a specific service."""
        service_port_map = {
            "auth": 8000,
            "feed": 8001,
            "content-analysis": 8002,
            "research": 8003,
            "osint": 8004,
            "notification": 8005,
        }
        port = service_port_map.get(service_name, 8000)
        return f"http://localhost:{port}{path}"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
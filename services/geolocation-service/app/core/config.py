"""Configuration for geolocation-service."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Service settings from environment variables."""

    SERVICE_NAME: str = "geolocation-service"
    SERVICE_PORT: int = 8115
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database - use complete URL to avoid password encoding issues
    DATABASE_URL: str = "postgresql+asyncpg://news_user:your_db_password@postgres:5432/news_mcp"

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "redis_secret_2024"

    @property
    def REDIS_URL(self) -> str:
        """Build Redis URL from components."""
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # RabbitMQ
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"

    @property
    def RABBITMQ_URL(self) -> str:
        """Build RabbitMQ URL from components."""
        return (
            f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}"
            f"@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"
        )

    # Entity Canonicalization Service
    ENTITY_CANONICALIZATION_URL: str = "http://entity-canonicalization-service:8112"

    # Alias for location resolver
    @property
    def ENTITY_SERVICE_URL(self) -> str:
        """Alias for entity canonicalization URL."""
        return self.ENTITY_CANONICALIZATION_URL

    # CORS
    CORS_ORIGINS: str = '["http://localhost:3000", "http://localhost:5173"]'

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

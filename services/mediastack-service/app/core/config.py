"""Configuration for MediaStack Service."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Service
    SERVICE_NAME: str = "mediastack-service"
    SERVICE_PORT: int = 8121
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # MediaStack API
    MEDIASTACK_API_KEY: str = ""
    MEDIASTACK_BASE_URL: str = "http://api.mediastack.com/v1"

    # Rate Limiting (Free Plan: 10,000 calls/month)
    MEDIASTACK_MONTHLY_LIMIT: int = 10000
    MEDIASTACK_RATE_LIMIT_CALLS: int = 100  # Per hour safety limit
    MEDIASTACK_RATE_LIMIT_WINDOW: int = 3600  # 1 hour

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "redis_secret_2024"
    REDIS_URL: str = "redis://:redis_secret_2024@redis:6379/0"

    # RabbitMQ
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()

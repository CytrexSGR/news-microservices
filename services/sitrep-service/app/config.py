# services/sitrep-service/app/config.py
"""Configuration for SITREP service."""

import os
from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    # Service Info
    SERVICE_NAME: str = "sitrep-service"
    SERVICE_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@postgres:5432/news_intelligence"
    )

    # RabbitMQ
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_EXCHANGE: str = "news.events"
    RABBITMQ_CLUSTER_QUEUE: str = "sitrep_cluster_events"

    @property
    def RABBITMQ_URL(self) -> str:
        return (
            f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@"
            f"{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"
        )

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_TEMPERATURE: float = 0.3

    # SITREP Generation
    SITREP_TOP_STORIES_COUNT: int = 10
    SITREP_MIN_CLUSTER_SIZE: int = 3
    SITREP_GENERATION_HOUR: int = 6  # 6 AM UTC

    # Time Decay
    DEFAULT_DECAY_RATE: float = 0.05

    # JWT Auth
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "ef85d69e49bc971350142a18469c646d41addd16ac73d9b28392419b46000315")
    JWT_ALGORITHM: str = "HS256"

    # HITL Review Integration (feed-service)
    FEED_SERVICE_URL: str = os.getenv("FEED_SERVICE_URL", "http://feed-service:8101")
    REVIEW_ENABLED: bool = True
    REVIEW_TIMEOUT_SECONDS: float = 10.0


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

"""
Configuration management for Intelligence Service.
Loads settings from environment variables with sensible defaults.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Service Configuration
    SERVICE_NAME: str = "intelligence-service"
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8114"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://news_user:your_db_password@postgres:5432/news_mcp"
    )

    # RabbitMQ Configuration
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "rabbitmq")
    RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    RABBITMQ_USER: str = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "guest")
    RABBITMQ_VHOST: str = os.getenv("RABBITMQ_VHOST", "/")

    @property
    def rabbitmq_url(self) -> str:
        """Build RabbitMQ connection URL"""
        return (
            f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@"
            f"{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"
        )

    # Redis Configuration (for caching and rate limiting)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # Service Endpoints (for inter-service communication)
    FEED_SERVICE_URL: str = os.getenv("FEED_SERVICE_URL", "http://feed-service:8101")
    ANALYTICS_SERVICE_URL: str = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8107")
    RESEARCH_SERVICE_URL: str = os.getenv("RESEARCH_SERVICE_URL", "http://research-service:8103")
    OSINT_SERVICE_URL: str = os.getenv("OSINT_SERVICE_URL", "http://osint-service:8104")
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8100")

    # Circuit Breaker Configuration
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = int(
        os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5")
    )
    CIRCUIT_BREAKER_SUCCESS_THRESHOLD: int = int(
        os.getenv("CIRCUIT_BREAKER_SUCCESS_THRESHOLD", "2")
    )
    CIRCUIT_BREAKER_TIMEOUT: int = int(
        os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60")
    )

    # Retry Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    INITIAL_BACKOFF: float = float(os.getenv("INITIAL_BACKOFF", "1.0"))
    MAX_BACKOFF: float = float(os.getenv("MAX_BACKOFF", "32.0"))
    BACKOFF_MULTIPLIER: float = float(os.getenv("BACKOFF_MULTIPLIER", "2.0"))

    # HTTP Configuration
    HTTP_TIMEOUT: float = float(os.getenv("HTTP_TIMEOUT", "30.0"))
    HTTP_CONNECT_TIMEOUT: float = float(os.getenv("HTTP_CONNECT_TIMEOUT", "10.0"))

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

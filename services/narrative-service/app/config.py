"""
Configuration settings for Narrative Service.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    # Service Info
    SERVICE_NAME: str = "narrative-service"
    SERVICE_VERSION: str = "1.0.0"

    # Database (Week 1 Security Fix - Strong password)
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "news_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "+t1koDEJO+ruZ3QnYlkVeU2u6Z+zCJtL6wFW+wfN5Yk=")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "news_microservices")

    # JWT Authentication (Week 1 Security Fix)
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "ef85d69e49bc971350142a18469c646d41addd16ac73d9b28392419b46000315")
    JWT_ALGORITHM: str = "HS256"

    # Redis Cache
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")

    # RabbitMQ / Celery
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "rabbitmq")
    RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    RABBITMQ_USER: str = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "guest")

    @property
    def CELERY_BROKER_URL(self) -> str:
        """Celery broker URL (RabbitMQ)."""
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}//"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        """Celery result backend (Redis)."""
        return self.REDIS_URL

    # Performance Settings
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL_FRAME: int = int(os.getenv("CACHE_TTL_FRAME", "3600"))  # 1 hour
    CACHE_TTL_BIAS: int = int(os.getenv("CACHE_TTL_BIAS", "3600"))    # 1 hour
    CACHE_TTL_OVERVIEW: int = int(os.getenv("CACHE_TTL_OVERVIEW", "300"))  # 5 minutes

    @property
    def DATABASE_URL(self) -> str:
        """Async PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def REDIS_URL(self) -> str:
        """Redis connection URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # CORS (Security - Week 1 Fix)
    # Support both CORS_ORIGINS (JSON array) and CORS_ALLOWED_ORIGINS (comma-separated)
    CORS_ORIGINS_RAW: str = os.getenv(
        "CORS_ORIGINS",
        os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
    )

    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        """Parse CORS allowed origins from JSON array or comma-separated string."""
        import json
        if not self.CORS_ORIGINS_RAW:
            return []
        # Try parsing as JSON array first
        try:
            origins = json.loads(self.CORS_ORIGINS_RAW)
            if isinstance(origins, list):
                return origins
        except (json.JSONDecodeError, TypeError):
            pass
        # Fall back to comma-separated
        return [origin.strip() for origin in self.CORS_ORIGINS_RAW.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

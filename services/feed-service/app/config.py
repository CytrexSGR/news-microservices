"""
Configuration settings for the Feed Service
"""
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # Service Info
    SERVICE_NAME: str = "feed-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8001

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/news_feeds"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20  # Increased for Celery workers + FMP tasks
    DATABASE_MAX_OVERFLOW: int = 30  # Handle burst load (total 50 connections)

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour default

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    RABBITMQ_EXCHANGE: str = "news.events"

    # Auth Service
    AUTH_SERVICE_URL: str = "http://localhost:8000"
    JWT_SECRET_KEY: str = "ef85d69e49bc971350142a18469c646d41addd16ac73d9b28392419b46000315"
    JWT_ALGORITHM: str = "HS256"

    # Feed Processing
    DEFAULT_FETCH_INTERVAL_MINUTES: int = 60
    MAX_ITEMS_PER_FETCH: int = 50
    MAX_FETCH_RETRIES: int = 3
    FETCH_TIMEOUT_SECONDS: int = 30
    USER_AGENT: str = "NewsMicroservices-FeedService/1.0"

    # Feed Health
    HEALTH_CHECK_INTERVAL_SECONDS: int = 300  # 5 minutes
    CONSECUTIVE_FAILURES_FOR_ERROR: int = 5
    HEALTH_SCORE_THRESHOLD: int = 70

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_ALWAYS_EAGER: bool = False
    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1

    # Scheduler
    SCHEDULER_CHECK_INTERVAL_SECONDS: int = 60
    SCHEDULER_ENABLED: bool = False  # Disabled - using Celery Beat instead (single source)
    SCHEDULER_FETCH_TOLERANCE_SECONDS: int = 30  # Tolerance for fetch timing (30 seconds default)

    # Circuit Breaker
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_SUCCESS_THRESHOLD: int = 2
    CIRCUIT_BREAKER_TIMEOUT_SECONDS: int = 120

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # n8n Webhook for Review Alerts (Task 2.3.6)
    # When configured, sends notifications for high-risk review items (risk >= 0.7)
    N8N_REVIEW_WEBHOOK_URL: Optional[str] = None  # e.g., "http://n8n:5678/webhook/review-alert"
    N8N_WEBHOOK_TIMEOUT: float = 10.0  # Webhook request timeout in seconds

    # Nemesis MCP API
    NEMESIS_API_URL: str = "http://localhost:8765"
    NEMESIS_TASK_TIMEOUT: int = 10

    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

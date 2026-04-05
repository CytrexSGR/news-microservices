"""
Scheduler Service Configuration

Manages configuration from environment variables.
"""

import os

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Service Configuration
    SERVICE_NAME: str = "scheduler-service"
    SERVICE_PORT: int = 8008
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql://news_user:your_db_password@postgres:5432/news_mcp"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis Cache
    REDIS_URL: str = "redis://:redis_secret_2024@redis:6379/0"
    CACHE_ENABLED: bool = True

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"
    RABBITMQ_EXCHANGE: str = "news.events"
    RABBITMQ_ROUTING_KEY_PREFIX: str = "scheduler"

    # Service URLs
    FEED_SERVICE_URL: str = "http://feed-service:8000"  # Fixed: was 8001, correct is 8000
    ANALYSIS_SERVICE_URL: str = "http://content-analysis-service:8000"  # Fixed: was 8002, correct is 8000
    CONTENT_ANALYSIS_URL: str = "http://content-analysis-service:8000"  # Fixed: Alias for job processor
    AUTH_SERVICE_URL: str = "http://auth-service:8000"

    # JWT (for user endpoints)
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "ef85d69e49bc971350142a18469c646d41addd16ac73d9b28392419b46000315")
    JWT_ALGORITHM: str = "HS256"

    # Service-to-Service Authentication API Keys
    # These keys allow scheduler to authenticate with other services
    FEED_SERVICE_API_KEY: Optional[str] = None
    ANALYSIS_SERVICE_API_KEY: Optional[str] = None
    CONTENT_ANALYSIS_API_KEY: Optional[str] = None  # For job processor
    AUTH_SERVICE_API_KEY: Optional[str] = None

    # Scheduler's own API key (for receiving requests from other services)
    SCHEDULER_SERVICE_API_KEY: Optional[str] = None

    # Polling Configuration
    FEED_CHECK_INTERVAL: int = 60  # seconds
    MAX_CONCURRENT_ANALYSES: int = 10
    BATCH_SIZE: int = 50  # articles per batch

    # Job Processing Configuration
    JOB_PROCESS_INTERVAL: int = 30  # seconds between job processing cycles
    MAX_CONCURRENT_JOBS: int = 5  # max jobs to process per cycle
    JOB_PROCESSING_INTERVAL: int = 5  # seconds (legacy - for compatibility)
    JOB_RETRY_DELAY: int = 10  # seconds
    MAX_RETRIES: int = 3

    # Circuit Breaker
    CIRCUIT_BREAKER_THRESHOLD: int = 5  # consecutive failures
    CIRCUIT_BREAKER_TIMEOUT: int = 60  # seconds
    CIRCUIT_BREAKER_SUCCESS_THRESHOLD: int = 2  # successes to close

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_REQUESTS_PER_HOUR: int = 1000

    # Observability
    ENABLE_TRACING: bool = True
    JAEGER_ENDPOINT: Optional[str] = "http://localhost:14268/api/traces"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Service Configuration
    SERVICE_NAME: str = "analytics-service"
    SERVICE_VERSION: str = "0.1.0"
    PORT: int = 8007
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # RabbitMQ
    RABBITMQ_URL: str

    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # Authentication
    AUTH_SERVICE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    # Service Integration URLs
    FEED_SERVICE_URL: Optional[str] = "http://feed-service:8001"
    ANALYSIS_SERVICE_URL: Optional[str] = "http://content-analysis-service:8002"
    RESEARCH_SERVICE_URL: Optional[str] = "http://research-service:8003"
    OSINT_SERVICE_URL: Optional[str] = "http://osint-service:8004"
    NOTIFICATION_SERVICE_URL: Optional[str] = "http://notification-service:8005"
    SEARCH_SERVICE_URL: Optional[str] = "http://search-service:8006"

    # RAG Configuration (Ask Intelligence feature)
    OPENAI_API_KEY: str = ""  # From environment
    OPENAI_MODEL: str = "gpt-4o-mini"
    RAG_MAX_ARTICLES_BRIEF: int = 5
    RAG_MAX_ARTICLES_DETAILED: int = 15
    RAG_MIN_SIMILARITY: float = 0.6

    # Analytics Configuration
    METRICS_COLLECTION_INTERVAL: int = 60
    METRICS_RETENTION_DAYS: int = 90
    METRICS_AGGREGATION_RETENTION_DAYS: int = 365
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30

    # Report Generation
    REPORTS_STORAGE_PATH: str = "/tmp/analytics-reports"
    MAX_REPORT_SIZE_MB: int = 50
    REPORT_GENERATION_TIMEOUT: int = 300

    # Prometheus
    PROMETHEUS_PORT: int = 9090
    PROMETHEUS_METRICS_PATH: str = "/metrics"

    # Thresholds
    ALERT_ERROR_RATE_THRESHOLD: float = 0.05
    ALERT_LATENCY_THRESHOLD_MS: int = 1000
    ALERT_CPU_THRESHOLD_PERCENT: int = 80
    ALERT_MEMORY_THRESHOLD_PERCENT: int = 85

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

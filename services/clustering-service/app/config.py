# services/clustering-service/app/config.py
"""Configuration for Clustering Service."""

import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Service settings loaded from environment."""

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    # Service
    SERVICE_NAME: str = "clustering-service"
    DEBUG: bool = False

    # JWT Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "ef85d69e49bc971350142a18469c646d41addd16ac73d9b28392419b46000315")
    JWT_ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@postgres:5432/news_intelligence"
    )
    # Synchronous database URL for Celery workers (psycopg2)
    SYNC_DATABASE_URL: str = os.getenv(
        "SYNC_DATABASE_URL",
        "postgresql://postgres:postgres@postgres:5432/news_intelligence"
    )

    # RabbitMQ
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_EXCHANGE: str = "news.events"

    # Clustering parameters
    SIMILARITY_THRESHOLD: float = 0.75  # Cosine similarity threshold
    CLUSTER_MAX_AGE_HOURS: int = 72  # Archive clusters older than this
    BURST_DETECTION_WINDOW_MINUTES: int = 60
    BURST_ARTICLE_THRESHOLD: int = 5  # Articles in window to trigger burst

    # Enhanced Burst Detection (Epic 1.3)
    BURST_WINDOW_MINUTES: int = 15  # Velocity detection window (increased from 5)
    BURST_VELOCITY_LOW: int = 3  # Threshold for low severity
    BURST_VELOCITY_MEDIUM: int = 5  # Threshold for medium severity
    BURST_VELOCITY_HIGH: int = 10  # Threshold for high severity
    BURST_VELOCITY_CRITICAL: int = 20  # Threshold for critical severity
    BURST_COOLDOWN_MINUTES: int = 30  # Cooldown between alerts

    # Enhanced Burst Detection v2 (Multi-Signal Analysis)
    BURST_GROWTH_RATE_THRESHOLD: float = float(os.getenv("BURST_GROWTH_RATE_THRESHOLD", "2.0"))
    BURST_CONCENTRATION_THRESHOLD: float = float(os.getenv("BURST_CONCENTRATION_THRESHOLD", "0.5"))
    BURST_MIN_SOURCES: int = int(os.getenv("BURST_MIN_SOURCES", "2"))
    BURST_REQUIRE_MULTI_SIGNAL: bool = os.getenv("BURST_REQUIRE_MULTI_SIGNAL", "true").lower() == "true"
    USE_ENHANCED_BURST_DETECTION: bool = os.getenv("USE_ENHANCED_BURST_DETECTION", "true").lower() == "true"

    # Webhook Alert
    BURST_WEBHOOK_URL: str = os.getenv(
        "BURST_WEBHOOK_URL",
        "http://n8n:5678/webhook/burst-alert"
    )
    BURST_WEBHOOK_ENABLED: bool = os.getenv("BURST_WEBHOOK_ENABLED", "true").lower() == "true"

    # Batch Clustering (UMAP + HDBSCAN)
    # Periodic recomputation of high-quality topic clusters
    BATCH_CLUSTERING_INTERVAL_HOURS: int = int(os.getenv("BATCH_CLUSTERING_INTERVAL_HOURS", "2"))
    BATCH_MIN_CLUSTER_SIZE: int = int(os.getenv("BATCH_MIN_CLUSTER_SIZE", "15"))
    BATCH_UMAP_COMPONENTS: int = int(os.getenv("BATCH_UMAP_COMPONENTS", "10"))
    BATCH_UMAP_NEIGHBORS: int = int(os.getenv("BATCH_UMAP_NEIGHBORS", "15"))
    BATCH_UMAP_MIN_DIST: float = float(os.getenv("BATCH_UMAP_MIN_DIST", "0.1"))
    # Max articles to process in one batch (0 = no limit)
    # Set lower for memory-constrained environments
    BATCH_MAX_ARTICLES: int = int(os.getenv("BATCH_MAX_ARTICLES", "50000"))

    # Celery Configuration
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

    # OpenAI Embeddings for Semantic Topic Search
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_CACHE_SIZE: int = int(os.getenv("EMBEDDING_CACHE_SIZE", "10000"))

    # Feature Flags
    # Set to True to use article_clusters for profile matching instead of batch_clusters
    # article_clusters: Persistent, pgvector-based, no duplicates
    # batch_clusters: Temporary, recreated every 2h, may have duplicates
    USE_ARTICLE_CLUSTERS: bool = os.getenv("USE_ARTICLE_CLUSTERS", "false").lower() == "true"

    @property
    def RABBITMQ_URL(self) -> str:
        return (
            f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@"
            f"{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"
        )


settings = Settings()

"""
Configuration management for Search Service
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # Service Configuration
    SERVICE_NAME: str = "search-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8000
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/search_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis - parsed from REDIS_URL environment variable
    REDIS_URL: str = "redis://redis:6379/0"
    CACHE_TTL: int = 3600

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/7"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/7"

    # Service URLs (use Docker service names for inter-service communication)
    FEED_SERVICE_URL: str = "http://feed-service:8001"
    CONTENT_ANALYSIS_SERVICE_URL: str = "http://content-analysis-service:8002"
    AUTH_SERVICE_URL: str = "http://auth-service:8000"
    KNOWLEDGE_GRAPH_SERVICE_URL: str = "http://knowledge-graph-service:8111"

    # Knowledge Graph integration (Layer 2)
    KNOWLEDGE_GRAPH_REQUEST_TIMEOUT: float = 10.0
    KNOWLEDGE_GRAPH_CACHE_TTL: int = 300  # 5 minutes

    # RabbitMQ (Event Bus)
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"
    RABBITMQ_EXCHANGE: str = "news.events"

    # JWT Authentication (Week 1 Security Fix - Load from environment)
    JWT_SECRET_KEY: str = "105d52e9f4e75b3c6ddeef8e9abc5062fbcaa73d433efae4a95c198f4f464061"
    JWT_ALGORITHM: str = "HS256"

    # Search Configuration
    MAX_SEARCH_RESULTS: int = 100
    DEFAULT_PAGE_SIZE: int = 20
    ENABLE_FUZZY_SEARCH: bool = True
    # Optimized fuzzy similarity threshold (0.3 = balanced precision/recall)
    # Lower values (0.2): Higher recall, more results, lower precision
    # Higher values (0.4-0.5): Higher precision, fewer results, lower recall
    FUZZY_SIMILARITY_THRESHOLD: float = 0.3

    # Query result caching
    QUERY_RESULT_CACHE_ENABLED: bool = True
    QUERY_RESULT_CACHE_TTL: int = 300  # 5 minutes

    # Indexing Configuration
    INDEXING_ENABLED: bool = True
    INDEXING_INTERVAL: int = 300  # 5 minutes
    BATCH_SIZE: int = 100

    # Semantic Search (Layer 1)
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    EMBEDDING_CACHE_SIZE: int = 1000
    SEMANTIC_SEARCH_LIMIT: int = 50
    SEMANTIC_SIMILARITY_THRESHOLD: float = 0.5
    HDBSCAN_MIN_CLUSTER_SIZE: int = 3
    HDBSCAN_MIN_SAMPLES: int = 2

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:3000",
        "http://localhost:8106"
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )


settings = Settings()

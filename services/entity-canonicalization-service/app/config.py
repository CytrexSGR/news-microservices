"""Configuration for Entity Canonicalization Service."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Service configuration."""

    # Service
    SERVICE_NAME: str = "entity-canonicalization-service"
    SERVICE_PORT: int = 8112
    LOG_LEVEL: str = "INFO"

    # PostgreSQL
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "news_user"
    POSTGRES_PASSWORD: str = "your_db_password"
    POSTGRES_DB: str = "news_mcp"

    # Redis (Celery broker/backend)
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = "redis_secret_2024"

    # Wikidata
    WIKIDATA_API_URL: str = "https://www.wikidata.org/w/api.php"
    WIKIDATA_TIMEOUT: int = 10
    WIKIDATA_CACHE_TTL: int = 86400  # 24 hours
    WIKIDATA_ENABLED: bool = False  # 🔧 DISABLED until entity quality improves

    # Similarity Thresholds
    FUZZY_THRESHOLD: float = 0.95
    SEMANTIC_THRESHOLD: float = 0.85
    WIKIDATA_CONFIDENCE_THRESHOLD: float = 0.80

    # OpenAI Embeddings (Migration from sentence-transformers)
    OPENAI_API_KEY: str  # From .env
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    EMBEDDING_CACHE_SIZE: int = 10000  # LRU cache (10k entities, ~80% hit rate)

    # Batch Reprocessing
    MAX_DUPLICATE_PAIRS: int = 30000  # Bounded deque size (increased to prevent duplicate loss)

    # Memory Management (🔧 MEMORY FIX)
    CANDIDATE_LIMIT: int = 1000  # Max candidates for similarity matching (saves ~200 KB per call)
    BATCH_JOB_CACHE_SIZE: int = 100  # Max concurrent batch jobs (reduced from 1000, saves ~150 MB)
    BATCH_JOB_TTL: int = 1800  # Batch job TTL in seconds (30 minutes, reduced from 1 hour)

    # Monitoring
    METRICS_PORT: int = 9112

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        """Build PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()

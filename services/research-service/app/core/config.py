"""
Configuration management for Research Service.
"""

from typing import Optional, List, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """Service configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Service Info
    SERVICE_NAME: str = "research-service"
    SERVICE_VERSION: str = "0.1.0"
    SERVICE_PORT: int = Field(default=8003, env="PORT")
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")

    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = Field(default=["*"])
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)
    CORS_ALLOW_METHODS: List[str] = Field(default=["*"])
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"])

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://news_user:your_db_password@localhost:5432/news_mcp",
        env="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=10)
    DATABASE_MAX_OVERFLOW: int = Field(default=20)
    DATABASE_ECHO: bool = Field(default=False)

    # Redis
    REDIS_URL: str = Field(default="redis://:redis_secret_2024@localhost:6379/0", env="REDIS_URL")
    REDIS_CACHE_TTL: int = Field(default=604800)  # 7 days default
    CACHE_ENABLED: bool = Field(default=True)

    # RabbitMQ
    RABBITMQ_URL: str = Field(default="amqp://guest:guest@localhost:5672/", env="RABBITMQ_URL")
    RABBITMQ_EXCHANGE: str = Field(default="news.events")
    RABBITMQ_ROUTING_KEY_PREFIX: str = Field(default="research")

    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://:redis_secret_2024@localhost:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://:redis_secret_2024@localhost:6379/2", env="CELERY_RESULT_BACKEND")
    CELERY_TASK_ALWAYS_EAGER: bool = Field(default=False)
    CELERY_TASK_EAGER_PROPAGATES: bool = Field(default=False)

    # MinIO
    MINIO_ENDPOINT: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field(default="minioadmin", env="MINIO_SECRET_KEY")
    MINIO_BUCKET: str = Field(default="research-reports", env="MINIO_BUCKET")
    MINIO_USE_SSL: bool = Field(default=False)

    # Authentication (Integration with Auth Service)
    AUTH_SERVICE_URL: str = Field(default="http://localhost:8000", env="AUTH_SERVICE_URL")
    JWT_SECRET_KEY: str = Field(default="your-super-secret-jwt-key-change-in-production-must-be-32-chars-minimum", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # Feed Service Integration
    FEED_SERVICE_URL: str = Field(default="http://localhost:8001", env="FEED_SERVICE_URL")

    # Content Analysis Service Integration
    ANALYSIS_SERVICE_URL: str = Field(default="http://localhost:8002", env="ANALYSIS_SERVICE_URL")

    # Perplexity AI Configuration
    PERPLEXITY_API_KEY: Optional[str] = Field(default=None, env="PERPLEXITY_API_KEY")
    PERPLEXITY_BASE_URL: str = Field(default="https://api.perplexity.ai", env="PERPLEXITY_BASE_URL")
    PERPLEXITY_DEFAULT_MODEL: str = Field(
        default="sonar",
        pattern="^(sonar|sonar-pro|sonar-reasoning-pro)$",
        env="PERPLEXITY_DEFAULT_MODEL"
    )
    PERPLEXITY_TIMEOUT: int = Field(default=60)
    PERPLEXITY_MAX_RETRIES: int = Field(default=3)

    # Model Configuration
    PERPLEXITY_MODELS: dict = Field(default={
        "sonar": {
            "name": "sonar",
            "cost_per_1k_tokens": 0.005,
            "max_tokens": 4000,
            "description": "Fast, cost-effective model for general research"
        },
        "sonar-pro": {
            "name": "sonar-pro",
            "cost_per_1k_tokens": 0.015,
            "max_tokens": 8000,
            "description": "Advanced model with better reasoning"
        },
        "sonar-reasoning-pro": {
            "name": "sonar-reasoning-pro",
            "cost_per_1k_tokens": 0.025,
            "max_tokens": 16000,
            "description": "Highest quality model for complex research"
        }
    })

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=10)
    RATE_LIMIT_REQUESTS_PER_HOUR: int = Field(default=500)
    RATE_LIMIT_REQUESTS_PER_DAY: int = Field(default=5000)

    # Cost Tracking
    ENABLE_COST_TRACKING: bool = Field(default=True)
    MAX_COST_PER_REQUEST: float = Field(default=1.0)
    MAX_DAILY_COST: float = Field(default=50.0)
    MAX_MONTHLY_COST: float = Field(default=1000.0)
    COST_ALERT_THRESHOLD: float = Field(default=0.8)

    # Cost Optimization
    ENABLE_COST_OPTIMIZATION: bool = Field(default=True)
    DEFAULT_COST_TIER: str = Field(default="standard", pattern="^(quick|standard|deep)$")
    AUTO_DOWNGRADE_ON_BUDGET_LIMIT: bool = Field(default=True)
    CACHE_PREFERENCE_THRESHOLD: float = Field(default=0.6)  # 0.0-1.0

    # Research Configuration
    MAX_QUERY_LENGTH: int = Field(default=2000)
    DEFAULT_RESEARCH_DEPTH: str = Field(default="standard", pattern="^(quick|standard|deep)$")
    BATCH_SIZE: int = Field(default=5)
    RESEARCH_TIMEOUT: int = Field(default=300)

    # Template Configuration
    MAX_TEMPLATES_PER_USER: int = Field(default=50)
    TEMPLATE_VALIDATION_ENABLED: bool = Field(default=True)

    # Cache Configuration
    CACHE_RESEARCH_RESULTS_TTL: int = Field(default=604800)
    CACHE_TEMPLATE_RESULTS_TTL: int = Field(default=86400)

    # Observability
    ENABLE_TRACING: bool = Field(default=True)
    JAEGER_ENDPOINT: str = Field(default="http://localhost:14268/api/traces")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    LOG_FORMAT: str = Field(default="json", pattern="^(json|text)$")

    @validator("DATABASE_URL", pre=True)
    def build_database_url(cls, v: str, values: dict) -> str:
        """Ensure database URL is properly formatted."""
        if v and not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL URL")
        return v

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    def get_model_config(self, model_name: str) -> dict:
        """Get configuration for a specific Perplexity model."""
        return self.PERPLEXITY_MODELS.get(model_name, self.PERPLEXITY_MODELS["sonar"])

    def calculate_cost(self, tokens_used: int, model_name: str) -> float:
        """Calculate cost for a research query."""
        model_config = self.get_model_config(model_name)
        cost_per_1k = model_config["cost_per_1k_tokens"]
        return (tokens_used / 1000.0) * cost_per_1k


settings = Settings()

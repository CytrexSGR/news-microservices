"""
Content-Analysis-V3 Configuration
Based on: /home/cytrex/userdocs/content-analysis-v3/design/data-model.md
"""

from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """V3 Pipeline Configuration"""

    # Service
    SERVICE_NAME: str = "content-analysis-v3"
    VERSION: str = "v3.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8117  # V3 API port (docker-compose maps to 8117)

    # Database
    POSTGRES_USER: str = "news_user"
    POSTGRES_PASSWORD: str = "your_db_password"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "content_analysis_v3"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # RabbitMQ
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # Neo4j (Knowledge Graph)
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4j_password_2024"
    NEO4J_DATABASE: str = "neo4j"
    NEO4J_MAX_POOL_SIZE: int = 50
    NEO4J_CONNECTION_TIMEOUT: int = 30

    # LLM Provider API Keys
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Tier 0 Configuration
    V3_TIER0_PROVIDER: Literal["gemini", "openai"] = "gemini"
    V3_TIER0_MODEL: str = "gemini-2.0-flash-exp"
    V3_TIER0_MAX_TOKENS: int = 800
    V3_TIER0_MAX_COST: float = 0.001

    # Tier 1 Configuration
    V3_TIER1_PROVIDER: Literal["gemini", "openai"] = "gemini"
    V3_TIER1_MODEL: str = "gemini-2.0-flash-exp"
    V3_TIER1_MAX_TOKENS: int = 4000  # Increased from 2000 to prevent JSON truncation on large financial articles
    V3_TIER1_MAX_COST: float = 0.001

    # Tier 2 Configuration
    V3_TIER2_PROVIDER: Literal["gemini", "openai"] = "gemini"
    V3_TIER2_MODEL: str = "gemini-2.0-flash-exp"
    V3_TIER2_MAX_TOKENS: int = 8000  # Total budget across specialists
    V3_TIER2_MAX_COST: float = 0.005

    # Tier 3 Configuration
    V3_TIER3_PROVIDER: Literal["gemini", "openai"] = "openai"
    V3_TIER3_MODEL: str = "gpt-4o-mini"
    V3_TIER3_FALLBACK_PROVIDER: Literal["gemini", "openai"] | None = None
    V3_TIER3_FALLBACK_MODEL: str | None = None
    V3_TIER3_MAX_TOKENS: int = 3000
    V3_TIER3_MAX_COST: float = 0.002

    # Cost Monitoring
    V3_DAILY_BUDGET_USD: float = 5.0
    V3_COST_ALERT_THRESHOLD: float = 0.003  # Alert if cost > $0.003/article
    V3_COST_CIRCUIT_BREAKER: float = 0.005  # Stop if cost > $0.005/article

    # Feature Flags
    V3_ENABLED: bool = True
    V3_ROLLOUT_PERCENTAGE: int = 100  # 0-100%
    V3_FALLBACK_TO_V2: bool = False

    # Performance
    V3_MAX_WORKERS: int = 4
    V3_QUEUE_PREFETCH_COUNT: int = 10

    # JWT Authentication (shared with auth-service)
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production-must-be-32-chars-minimum"
    JWT_ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

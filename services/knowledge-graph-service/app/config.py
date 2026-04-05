"""
Knowledge Graph Service - Configuration

Loads settings from environment variables using Pydantic.
"""

from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Service Configuration
    SERVICE_NAME: str = "knowledge-graph-service"
    SERVICE_PORT: int = 8111
    LOG_LEVEL: str = "INFO"

    # Neo4j Configuration
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4j_password_2024"
    NEO4J_DATABASE: str = "neo4j"
    NEO4J_MAX_POOL_SIZE: int = 50
    NEO4J_CONNECTION_TIMEOUT: int = 30

    # RabbitMQ Configuration
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_EXCHANGE: str = "news.events"
    RABBITMQ_QUEUE: str = "knowledge_graph_relationships"
    RABBITMQ_ROUTING_KEY: str = "relationships.extracted.*"

    # API Configuration
    CORS_ORIGINS: str = '["http://localhost:3000", "http://localhost:3000"]'

    # PostgreSQL Configuration (for event logging and stats)
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "news_user"
    POSTGRES_PASSWORD: str = "your_db_password"
    POSTGRES_DB: str = "news_mcp"

    # External Services
    SCRAPING_SERVICE_URL: str = "http://news-scraping-service:8009"
    FMP_SERVICE_URL: str = "http://fmp-service:8113"

    # FMP Client Configuration
    FMP_TIMEOUT: int = 30
    FMP_MAX_RETRIES: int = 3
    FMP_CIRCUIT_BREAKER_THRESHOLD: int = 5
    FMP_CIRCUIT_BREAKER_TIMEOUT: int = 30

    # Query Limits
    MAX_QUERY_TIMEOUT_SECONDS: int = 30
    DEFAULT_RESULT_LIMIT: int = 100
    MAX_RESULT_LIMIT: int = 1000

    # Rate Limiting (requests per minute)
    RATE_LIMIT_DEFAULT: str = "100/minute"  # Default for most endpoints
    RATE_LIMIT_SEARCH: str = "60/minute"    # Search endpoints (heavier)
    RATE_LIMIT_WRITE: str = "30/minute"     # Write endpoints (heaviest)
    RATE_LIMIT_ADMIN: str = "10/minute"     # Admin endpoints (most restrictive)

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS from JSON string."""
        try:
            return json.loads(self.CORS_ORIGINS)
        except (json.JSONDecodeError, TypeError):
            return ["http://localhost:3000"]

    @property
    def rabbitmq_url(self) -> str:
        """Build RabbitMQ connection URL."""
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"

    @property
    def database_url(self) -> str:
        """Build PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

"""NEXUS Agent Service Configuration."""

from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """NEXUS Agent Service Configuration."""

    # Service
    SERVICE_NAME: str = "nexus-agent"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8120
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    DEBUG: bool = False

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 1000

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/news_db"

    # Perplexity
    PERPLEXITY_API_KEY: str = ""
    PERPLEXITY_BASE_URL: str = "https://api.perplexity.ai"
    PERPLEXITY_TIMEOUT: int = 30
    PERPLEXITY_MODEL: str = "sonar"

    # Redis (for later phases)
    REDIS_URL: str = "redis://redis:6379/1"

    # Auth
    AUTH_SERVICE_URL: str = "http://auth-service:8000"
    JWT_SECRET: str = "ef85d69e49bc971350142a18469c646d41addd16ac73d9b28392419b46000315"

    # Limits
    MAX_TOKENS_PER_REQUEST: int = 4000

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

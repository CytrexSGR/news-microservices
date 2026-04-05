"""
Configuration settings for LLM Orchestrator Service.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # Service
    SERVICE_NAME: str = "llm-orchestrator-service"
    PORT: int = 8109
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str

    # RabbitMQ
    RABBITMQ_URL: str
    RABBITMQ_VERIFICATION_EXCHANGE: str = "verification_exchange"
    RABBITMQ_VERIFICATION_QUEUE: str = "verification_queue"
    RABBITMQ_VERIFICATION_ROUTING_KEY: str = "verification.required.*"

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"

    # DIA Configuration
    DIA_STAGE1_TEMPERATURE: float = 0.3
    DIA_STAGE2_TEMPERATURE: float = 0.2
    DIA_MAX_RETRIES: int = 3

    # External Services (Phase 2 - Verifier)
    RESEARCH_SERVICE_URL: str = "http://research-service:8103"
    PERPLEXITY_API_KEY: Optional[str] = None  # Dedicated Perplexity API key
    ALPHA_VANTAGE_API_KEY: Optional[str] = None  # For financial data lookup
    FMP_API_KEY: Optional[str] = None  # Financial Modeling Prep (alternative)

    # Tool Configuration
    TOOL_TIMEOUT_SECONDS: int = 30
    TOOL_MAX_RETRIES: int = 2

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

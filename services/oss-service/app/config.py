"""
Configuration settings for OSS Service.
Loads from environment variables with sensible defaults.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Application
    APP_NAME: str = "OSS Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment name")

    # Server
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8110, description="Server port")

    # Neo4j Configuration
    NEO4J_URI: str = Field(default="bolt://neo4j:7687", description="Neo4j connection URI")
    NEO4J_USER: str = Field(default="neo4j", description="Neo4j username")
    NEO4J_PASSWORD: str = Field(default="news_graph_2024", description="Neo4j password")
    NEO4J_DATABASE: str = Field(default="neo4j", description="Neo4j database name")

    # Ontology Proposals API
    PROPOSALS_API_URL: str = Field(
        default="http://ontology-proposals-service:8109",
        description="Ontology Proposals Service URL"
    )

    # Analysis Configuration
    ANALYSIS_INTERVAL_SECONDS: int = Field(
        default=3600,
        description="Interval between analysis runs in seconds (default: 1 hour)"
    )
    MIN_PATTERN_OCCURRENCES: int = Field(
        default=10,
        description="Minimum occurrences to consider a pattern"
    )
    CONFIDENCE_THRESHOLD: float = Field(
        default=0.7,
        description="Minimum confidence to generate proposal"
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="text", description="Logging format (text or json)")

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

"""
Configuration settings for Ontology Proposals Service.
Loads from environment variables with sensible defaults.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Application
    APP_NAME: str = "Ontology Proposals Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment name")

    # Server
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8109, description="Server port")

    # Database
    DATABASE_URL: Optional[str] = Field(default=None, description="Complete database URL")
    POSTGRES_HOST: str = Field(default="postgres", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_USER: str = Field(default="news_user", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(default="your_db_password", description="PostgreSQL password")
    POSTGRES_DB: str = Field(default="news_mcp", description="PostgreSQL database")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins"
    )

    # Neo4j Configuration
    NEO4J_URI: str = Field(default="bolt://neo4j:7687", description="Neo4j connection URI")
    NEO4J_USER: str = Field(default="neo4j", description="Neo4j username")
    NEO4J_PASSWORD: str = Field(default="neo4j_password_2024", description="Neo4j password")
    NEO4J_DATABASE: str = Field(default="neo4j", description="Neo4j database name")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="text", description="Logging format (text or json)")

    @property
    def database_url(self) -> str:
        """Get database URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL

        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

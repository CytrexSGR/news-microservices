"""
Configuration settings for Auth Service.
Loads from environment variables with sensible defaults.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional
import secrets


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Application
    APP_NAME: str = "Auth Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment name")

    # Server
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")

    # Database (can be set via DATABASE_URL or individual variables)
    DATABASE_URL: Optional[str] = Field(default=None, description="Complete database URL")
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_USER: str = Field(default="news_user", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(default="+t1koDEJO+ruZ3QnYlkVeU2u6Z+zCJtL6wFW+wfN5Yk=", description="PostgreSQL password")
    POSTGRES_DB: str = Field(default="news_mcp", description="PostgreSQL database")

    # Redis (can be set via REDIS_URL or individual variables)
    REDIS_URL_OVERRIDE: Optional[str] = Field(default=None, alias="REDIS_URL", description="Complete Redis URL")
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_PASSWORD: str = Field(default="redis_secret_2024", description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database")
    REDIS_TOKEN_EXPIRY: int = Field(default=86400, description="Token blacklist expiry in seconds")

    # JWT (Week 1 Security Fix - Load from environment, fallback to generated)
    JWT_SECRET_KEY: str = Field(
        default="ef85d69e49bc971350142a18469c646d41addd16ac73d9b28392419b46000315",
        description="Secret key for JWT tokens"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    # Extended token lifetime for closed LAN environment (2026-01-06)
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, description="Access token expiry (24 hours)")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=90, description="Refresh token expiry (90 days)")

    # Secrets Manager Configuration
    SECRETS_PROVIDER: str = Field(
        default="local",
        description="Secrets provider type: 'aws', 'vault', or 'local' (dev only)"
    )
    AWS_REGION: str = Field(default="us-east-1", description="AWS region for Secrets Manager")
    VAULT_ADDR: Optional[str] = Field(default=None, description="Vault server address")
    VAULT_TOKEN: Optional[str] = Field(default=None, description="Vault authentication token")
    JWT_SECRET_NAME: str = Field(
        default="auth-service/jwt-secret",
        description="Name/path of JWT secret in secrets provider"
    )
    JWT_ROTATION_ENABLED: bool = Field(default=False, description="Enable automatic JWT key rotation")
    JWT_ROTATION_INTERVAL_DAYS: int = Field(default=30, description="JWT key rotation interval in days")

    # Security
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="Minimum password length")
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(default=True, description="Require uppercase in password")
    PASSWORD_REQUIRE_LOWERCASE: bool = Field(default=True, description="Require lowercase in password")
    PASSWORD_REQUIRE_DIGIT: bool = Field(default=True, description="Require digit in password")
    PASSWORD_REQUIRE_SPECIAL: bool = Field(default=True, description="Require special char in password")

    # API Keys
    API_KEY_LENGTH: int = Field(default=32, description="API key length")
    API_KEY_PREFIX: str = Field(default="nmc_", description="API key prefix")

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Requests per window")
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=3600, description="Rate limit window")

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format (json or text)")

    def get_database_url(self) -> str:
        """Get database URL (prefer DATABASE_URL env var, fallback to constructed)."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    def get_redis_url(self) -> str:
        """Get Redis URL (prefer REDIS_URL env var, fallback to constructed)."""
        if self.REDIS_URL_OVERRIDE:
            return self.REDIS_URL_OVERRIDE
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @validator("JWT_SECRET_KEY")
    def validate_jwt_secret(cls, v):
        """Ensure JWT secret is strong enough."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

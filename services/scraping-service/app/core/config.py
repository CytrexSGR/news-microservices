"""
Configuration for Scraping Service
"""
from pydantic_settings import BaseSettings
from typing import Optional
from urllib.parse import urlparse, quote_plus


class Settings(BaseSettings):
    """Service configuration from environment variables"""

    # Service
    SERVICE_NAME: str = "scraping-service"
    SERVICE_PORT: int = 8009
    LOG_LEVEL: str = "INFO"

    # Feed Service
    FEED_SERVICE_URL: str = "http://feed-service:8001"
    FEED_SERVICE_API_KEY: Optional[str] = None  # Optional: for service-to-service auth

    # RabbitMQ (can provide URL or individual parameters)
    RABBITMQ_URL: Optional[str] = None
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "admin"
    RABBITMQ_PASSWORD: str = ""
    RABBITMQ_VHOST: str = "news_mcp"
    RABBITMQ_QUEUE: str = "scraping_jobs"
    RABBITMQ_EXCHANGE: str = "news.events"  # Fixed: was news_events, should match feed-service
    RABBITMQ_ROUTING_KEY: str = "feed.item.created"

    # Redis (can provide URL or individual parameters)
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1
    REDIS_PASSWORD: Optional[str] = None

    # Scraping Configuration
    SCRAPING_USER_AGENT: str = "NewsMicroservices-ScrapingBot/1.0 (+https://github.com/news-microservices; scraping-service)"
    SCRAPING_TIMEOUT: int = 30
    SCRAPING_MAX_RETRIES: int = 3
    SCRAPING_FAILURE_THRESHOLD: int = 5  # Default fallback (feeds can override)
    SCRAPING_WORKER_CONCURRENCY: int = 3
    SCRAPING_MAX_CONCURRENT_JOBS: int = 5  # Maximum concurrent scraping jobs

    # Rate Limiting (per domain, per time window)
    SCRAPING_RATE_LIMIT_PER_DOMAIN: int = 10  # Max requests per domain per window
    SCRAPING_RATE_LIMIT_PER_FEED: int = 20    # Max requests per feed per window
    SCRAPING_RATE_LIMIT_GLOBAL: int = 50      # Max total requests per window
    SCRAPING_RATE_LIMIT_WINDOW: int = 60      # Time window in seconds

    # Wikipedia API Rate Limiting (polite bot: ~1 req/sec recommended)
    WIKIPEDIA_RATE_LIMIT: int = 10            # Max Wikipedia API requests per window
    WIKIPEDIA_RATE_LIMIT_WINDOW: int = 10     # Time window in seconds (~1 req/sec)

    # Newspaper4k Configuration
    NEWSPAPER4K_TIMEOUT: int = 15
    NEWSPAPER4K_MIN_WORD_COUNT: int = 50  # Minimum words for successful scrape

    # Playwright
    PLAYWRIGHT_HEADLESS: bool = True
    PLAYWRIGHT_TIMEOUT: int = 30000

    # Phase 1 Feature Flags (Enterprise Upgrade)
    ENABLE_UA_ROTATION: bool = True          # Use dynamic User-Agent pool
    ENABLE_JITTERED_BACKOFF: bool = True     # Use jittered exponential backoff
    ENABLE_TRAFILATURA_FALLBACK: bool = True # Fallback to trafilatura if newspaper4k fails

    # Phase 2 Feature Flags (Intelligence)
    ENABLE_SOURCE_REGISTRY: bool = True      # Track per-source scraping profiles
    ENABLE_AUTO_METHOD_SELECTION: bool = True # Intelligent method selection
    ENABLE_AUTO_PROFILING: bool = True       # Auto-profile new domains to find best method

    # Trafilatura Configuration
    TRAFILATURA_TIMEOUT: int = 30
    TRAFILATURA_MIN_WORD_COUNT: int = 50

    # Phase 6 Feature Flags (Scale)
    ENABLE_PROXY_ROTATION: bool = True           # Use proxy rotation for requests
    ENABLE_HTTP_CACHE: bool = True               # Cache successful scrape results
    ENABLE_PRIORITY_QUEUE: bool = True           # Use priority queue for jobs

    # HTTP Cache Configuration
    HTTP_CACHE_MAX_ENTRIES: int = 5000           # Maximum cached entries
    HTTP_CACHE_MAX_SIZE_MB: int = 500            # Maximum cache size in MB
    HTTP_CACHE_DEFAULT_TTL_SECONDS: int = 3600   # Default TTL (1 hour)
    HTTP_CACHE_NEWS_TTL_SECONDS: int = 1800      # TTL for news content (30 minutes)

    # Priority Queue Configuration
    PRIORITY_QUEUE_MAX_SIZE: int = 10000         # Maximum queue size
    PRIORITY_QUEUE_MAX_RETRIES: int = 3          # Default max retries per job

    # Proxy Configuration
    PROXY_ROTATION_ENABLED: bool = False         # Enable/disable rotation
    PROXY_MAX_CONSECUTIVE_FAILURES: int = 3      # Circuit breaker threshold
    PROXY_RECOVERY_TIMEOUT_SECONDS: int = 300    # Time before retry unhealthy proxy

    # Database (PostgreSQL) - can provide URL or individual parameters
    DATABASE_URL: Optional[str] = None
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "news_mcp"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Authentication (JWT validation)
    JWT_SECRET_KEY: str = "ef85d69e49bc971350142a18469c646d41addd16ac73d9b28392419b46000315"
    JWT_ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        case_sensitive = True

    def model_post_init(self, __context):
        """Parse URLs if provided"""
        # Parse RabbitMQ URL if provided
        if self.RABBITMQ_URL:
            parsed = urlparse(self.RABBITMQ_URL)
            if parsed.hostname:
                self.RABBITMQ_HOST = parsed.hostname
            if parsed.port:
                self.RABBITMQ_PORT = parsed.port
            if parsed.username:
                self.RABBITMQ_USER = parsed.username
            if parsed.password:
                self.RABBITMQ_PASSWORD = parsed.password
            if parsed.path and len(parsed.path) > 1:
                self.RABBITMQ_VHOST = parsed.path[1:]  # Remove leading /

        # Parse Redis URL if provided
        if self.REDIS_URL:
            parsed = urlparse(self.REDIS_URL)
            if parsed.hostname:
                self.REDIS_HOST = parsed.hostname
            if parsed.port:
                self.REDIS_PORT = parsed.port
            if parsed.password:
                self.REDIS_PASSWORD = parsed.password
            # Redis DB is in path like /0, /1, /2
            if parsed.path and len(parsed.path) > 1:
                try:
                    self.REDIS_DB = int(parsed.path[1:])
                except ValueError:
                    pass

        # Build DATABASE_URL if not provided
        if not self.DATABASE_URL:
            # URL-encode password to handle special characters
            encoded_password = quote_plus(self.POSTGRES_PASSWORD) if self.POSTGRES_PASSWORD else ""
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{encoded_password}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )


settings = Settings()

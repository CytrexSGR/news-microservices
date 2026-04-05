from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="news-mcp-common",
    version="0.1.0",
    author="News MCP Team",
    description="Shared library for News MCP microservices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/news-microservices",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        # Core dependencies
        "fastapi>=0.104.0",
        "pydantic>=2.8.0,<3.0.0",  # Constrained for ontology package compatibility
        "pydantic-settings>=2.0.0",

        # Database
        "sqlalchemy>=2.0.0",
        "asyncpg>=0.29.0",
        "alembic>=1.13.0",

        # Redis
        "redis>=5.0.0",
        "redis[hiredis]>=5.0.0",

        # RabbitMQ
        "aio-pika>=9.3.0",

        # Authentication
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-multipart>=0.0.6",

        # Observability
        "opentelemetry-api>=1.20.0",
        "opentelemetry-sdk>=1.20.0",
        "opentelemetry-instrumentation-fastapi>=0.41b0",
        "opentelemetry-instrumentation-sqlalchemy>=0.41b0",
        "opentelemetry-instrumentation-redis>=0.41b0",
        "opentelemetry-instrumentation-aio-pika>=0.41b0",
        "opentelemetry-exporter-jaeger>=1.20.0",
        "opentelemetry-exporter-prometheus>=0.41b0",
        "deprecated>=1.2.0",
        "prometheus-client>=0.19.0",

        # MinIO
        "minio>=7.2.0",

        # Utilities
        "httpx>=0.25.0",
        "python-dateutil>=2.8.2",
        "structlog>=23.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.5.0",
            "ruff>=0.1.0",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
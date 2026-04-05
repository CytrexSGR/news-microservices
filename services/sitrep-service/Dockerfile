# services/sitrep-service/Dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy shared libraries
COPY libs/news-intelligence-common /tmp/news-intelligence-common
COPY shared/news-mcp-common /tmp/news-mcp-common

# Copy requirements
COPY services/sitrep-service/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir /tmp/news-intelligence-common && \
    pip install --no-cache-dir /tmp/news-mcp-common && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./services/sitrep-service/app ./app
COPY ./services/sitrep-service/tests ./tests

# Expose port
EXPOSE 8123

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8123/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8123", "--reload"]

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared library first (ARCH-001 fix)
COPY shared/news-mcp-common /tmp/news-mcp-common

# Copy requirements
COPY services/entity-canonicalization-service/requirements.txt .

# Install news-mcp-common first, then other dependencies
RUN pip install --no-cache-dir /tmp/news-mcp-common && \
    grep -v 'news-mcp-common' requirements.txt > requirements-filtered.txt 2>/dev/null || cp requirements.txt requirements-filtered.txt && \
    pip install --no-cache-dir -r requirements-filtered.txt

# Copy application code
COPY services/entity-canonicalization-service/app/ /app/app/

# Expose ports
EXPOSE 8112

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8112/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8112", "--log-level", "info"]

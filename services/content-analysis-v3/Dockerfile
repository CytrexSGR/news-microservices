FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy shared library
COPY libs/news-intelligence-common /tmp/news-intelligence-common

# Copy requirements
COPY services/content-analysis-v3/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir /tmp/news-intelligence-common && \
    grep -v 'news-intelligence-common' requirements.txt > requirements-filtered.txt && \
    pip install --no-cache-dir -r requirements-filtered.txt

# Copy application code
COPY services/content-analysis-v3/app/ /app/app/
COPY services/content-analysis-v3/.env /app/.env

# Create directory for scripts (if needed)
RUN mkdir -p /app/scripts

# Expose port
EXPOSE 8117

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8117/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8117", "--log-level", "info"]

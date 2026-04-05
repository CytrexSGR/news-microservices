#!/bin/bash
# Optimize all service Dockerfiles with proper multi-stage builds
# Usage: ./scripts/optimize-all-dockerfiles.sh

set -e

echo "🚀 Optimizing all service Dockerfiles..."
echo ""

# Define services with their ports
declare -A SERVICES
SERVICES=(
    ["feed"]="8001"
    ["content-analysis"]="8002"
    ["notification"]="8005"
    ["search"]="8006"
    ["analytics"]="8007"
    ["scheduler"]="8008"
    ["research"]="8003"
    ["osint"]="8004"
)

# Scraping service is special (Playwright)
optimize_scraping() {
    echo "=== Optimizing scraping-service (special: Playwright) ==="

    cat > /home/cytrex/news-microservices/services/scraping-service/Dockerfile <<'EOF'
# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Skip browser download - using shared service
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Install to /root/.local
RUN pip install --user --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim

WORKDIR /app

# Runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Selective copy
COPY app/ app/

# Non-root user
RUN useradd -m -u 1000 scraper && chown -R scraper:scraper /app
USER scraper

# Expose port
EXPOSE 8109

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8109/health || exit 1

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8109"]
EOF

    echo "✓ scraping-service optimized"
}

# Generic service optimization
optimize_service() {
    local service=$1
    local port=$2
    local service_dir="/home/cytrex/news-microservices/services/${service}-service"

    echo "=== Optimizing ${service}-service (port: ${port}) ==="

    # Backup original
    if [ -f "$service_dir/Dockerfile" ]; then
        cp "$service_dir/Dockerfile" "$service_dir/Dockerfile.backup"
    fi

    # Check if service has alembic
    local has_alembic=""
    if [ -d "$service_dir/alembic" ]; then
        has_alembic="COPY alembic/ alembic/\nCOPY alembic.ini ."
    fi

    # Create optimized Dockerfile
    cat > "$service_dir/Dockerfile" <<EOF
# ============================================
# Stage 1: Builder (Build-time dependencies)
# ============================================
FROM python:3.11-slim as builder

WORKDIR /build

# Install ONLY build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install to /root/.local (user install - minimal)
RUN pip install --user --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Runtime (Minimal production image)
# ============================================
FROM python:3.11-slim

WORKDIR /app

# Install ONLY runtime dependencies (NO gcc!)
RUN apt-get update && apt-get install -y --no-install-recommends \\
    postgresql-client \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder (ONLY /root/.local)
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Selective copy - NO "COPY . ."
COPY app/ app/
$has_alembic

# Non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE ${port}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \\
    CMD curl -f http://localhost:${port}/health || exit 1

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${port}"]
EOF

    echo "✓ ${service}-service optimized"
}

# Optimize scraping service first (special case)
optimize_scraping

# Optimize all other services
for service in "${!SERVICES[@]}"; do
    optimize_service "$service" "${SERVICES[$service]}"
done

echo ""
echo "═══════════════════════════════════════"
echo "✅ All Dockerfiles optimized!"
echo "═══════════════════════════════════════"
echo ""
echo "Changes made:"
echo "  - True multi-stage builds (builder + runtime)"
echo "  - pip install --user (minimal /root/.local)"
echo "  - Selective COPY (no COPY . .)"
echo "  - Runtime: postgresql-client + curl only"
echo "  - Builder: gcc only (removed from runtime)"
echo "  - Playwright: SKIP_BROWSER_DOWNLOAD=1"
echo ""
echo "Next steps:"
echo "  1. Build base image: cd docker/base && docker build -t news-base:python3.11 ."
echo "  2. Test build: ./scripts/validate-docker-build.sh auth 400"
echo "  3. Rebuild all: docker-compose build"

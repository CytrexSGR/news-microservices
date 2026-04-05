#!/bin/bash
set -euo pipefail

# ============================================================================
# Fresh Database Deployment Script
# ============================================================================
# Orchestrates complete database rebuild with proper startup order
# Author: DevOps Engineer (Claude Flow Swarm)
# Last Updated: 2025-10-15
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_ROOT}/backups/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${PROJECT_ROOT}/logs/deploy-$(date +%Y%m%d_%H%M%S).log"

# Docker Compose command (supports both v1 and v2)
DOCKER_COMPOSE="docker-compose"
if command -v docker compose &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
fi

# Database configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-news_db}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"

# Timeouts (seconds)
SERVICE_STARTUP_TIMEOUT=60
HEALTH_CHECK_TIMEOUT=30
MIGRATION_TIMEOUT=300

# ============================================================================
# Logging Functions
# ============================================================================

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $*" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $*" | tee -a "$LOG_FILE"
}

# ============================================================================
# Pre-flight Checks
# ============================================================================

preflight_checks() {
    log "Running pre-flight checks..."

    # Check if Docker is running
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi

    # Check if docker-compose is available
    if ! command -v $DOCKER_COMPOSE &> /dev/null; then
        log_error "docker-compose not found. Please install Docker Compose."
        exit 1
    fi

    # Check if required files exist
    if [[ ! -f "${PROJECT_ROOT}/docker-compose.yml" ]]; then
        log_error "docker-compose.yml not found in ${PROJECT_ROOT}"
        exit 1
    fi

    # Create necessary directories
    mkdir -p "${PROJECT_ROOT}/logs"
    mkdir -p "${PROJECT_ROOT}/backups"
    mkdir -p "${PROJECT_ROOT}/database/migrations"

    log_success "Pre-flight checks passed"
}

# ============================================================================
# Backup Functions
# ============================================================================

backup_database() {
    log "Creating database backup..."

    # Check if database exists and is accessible
    if docker exec postgres psql -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        mkdir -p "$BACKUP_DIR"

        # Dump database
        docker exec postgres pg_dump -U "$DB_USER" "$DB_NAME" > "${BACKUP_DIR}/${DB_NAME}_backup.sql"

        if [[ -f "${BACKUP_DIR}/${DB_NAME}_backup.sql" ]]; then
            log_success "Database backed up to ${BACKUP_DIR}/${DB_NAME}_backup.sql"
            echo "$BACKUP_DIR" > "${PROJECT_ROOT}/.last_backup"
        else
            log_warning "Database backup failed, but continuing with deployment"
        fi
    else
        log_warning "Database ${DB_NAME} does not exist yet, skipping backup"
    fi
}

backup_volumes() {
    log "Backing up Docker volumes..."

    # Backup postgres data if volume exists
    if docker volume inspect postgres_data &> /dev/null; then
        docker run --rm \
            -v postgres_data:/data \
            -v "$BACKUP_DIR":/backup \
            alpine tar czf /backup/postgres_data.tar.gz -C /data .

        if [[ -f "${BACKUP_DIR}/postgres_data.tar.gz" ]]; then
            log_success "PostgreSQL volume backed up"
        fi
    fi
}

# ============================================================================
# Service Management
# ============================================================================

stop_all_services() {
    log "Stopping all services..."

    cd "$PROJECT_ROOT"
    $DOCKER_COMPOSE down --remove-orphans

    log_success "All services stopped"
}

start_infrastructure() {
    log "Starting infrastructure services (PostgreSQL, Redis, RabbitMQ)..."

    cd "$PROJECT_ROOT"
    $DOCKER_COMPOSE up -d postgres redis rabbitmq

    # Wait for PostgreSQL to be ready
    log "Waiting for PostgreSQL to be ready..."
    local attempts=0
    while ! docker exec postgres pg_isready -U "$DB_USER" &> /dev/null; do
        attempts=$((attempts + 1))
        if [[ $attempts -ge $SERVICE_STARTUP_TIMEOUT ]]; then
            log_error "PostgreSQL failed to start within ${SERVICE_STARTUP_TIMEOUT} seconds"
            return 1
        fi
        echo -n "."
        sleep 1
    done
    echo ""

    log_success "PostgreSQL is ready"

    # Wait for Redis
    log "Waiting for Redis to be ready..."
    attempts=0
    while ! docker exec redis redis-cli ping &> /dev/null; do
        attempts=$((attempts + 1))
        if [[ $attempts -ge $SERVICE_STARTUP_TIMEOUT ]]; then
            log_error "Redis failed to start within ${SERVICE_STARTUP_TIMEOUT} seconds"
            return 1
        fi
        echo -n "."
        sleep 1
    done
    echo ""

    log_success "Redis is ready"

    # Wait for RabbitMQ
    log "Waiting for RabbitMQ to be ready..."
    attempts=0
    while ! docker exec rabbitmq rabbitmqctl status &> /dev/null; do
        attempts=$((attempts + 1))
        if [[ $attempts -ge $SERVICE_STARTUP_TIMEOUT ]]; then
            log_error "RabbitMQ failed to start within ${SERVICE_STARTUP_TIMEOUT} seconds"
            return 1
        fi
        echo -n "."
        sleep 1
    done
    echo ""

    log_success "Infrastructure services are ready"
}

# ============================================================================
# Database Operations
# ============================================================================

recreate_database() {
    log "Dropping and recreating database..."

    # Drop database if exists
    docker exec postgres psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS ${DB_NAME};" 2>/dev/null || true

    # Create fresh database
    docker exec postgres psql -U "$DB_USER" -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

    # Create extensions
    docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
    docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS \"pg_trgm\";"

    log_success "Database ${DB_NAME} created successfully"
}

run_migrations() {
    log "Running Alembic migrations..."

    cd "$PROJECT_ROOT"

    # Check if alembic is installed
    if [[ -f "alembic.ini" ]]; then
        # Run migrations
        if command -v alembic &> /dev/null; then
            alembic upgrade head
        else
            # Try with Python
            python -m alembic upgrade head
        fi

        log_success "Migrations completed successfully"
    else
        log_warning "No alembic.ini found, skipping migrations"
    fi
}

seed_initial_data() {
    log "Seeding initial data..."

    # Check if seed script exists
    if [[ -f "${PROJECT_ROOT}/database/seed.py" ]]; then
        python "${PROJECT_ROOT}/database/seed.py"
        log_success "Initial data seeded"
    elif [[ -f "${PROJECT_ROOT}/scripts/seed-data.sh" ]]; then
        bash "${PROJECT_ROOT}/scripts/seed-data.sh"
        log_success "Initial data seeded"
    else
        log_warning "No seed script found, skipping data seeding"
    fi
}

# ============================================================================
# Application Services
# ============================================================================

start_application_services() {
    log "Starting application services..."

    cd "$PROJECT_ROOT"

    # Start services in order with dependencies
    local services=(
        "app"
        "worker"
        "scheduler"
        "api"
    )

    for service in "${services[@]}"; do
        if $DOCKER_COMPOSE config --services | grep -q "^${service}$"; then
            log "Starting ${service}..."
            $DOCKER_COMPOSE up -d "$service"
            sleep 5  # Give service time to initialize
        fi
    done

    log_success "Application services started"
}

# ============================================================================
# Health Checks
# ============================================================================

verify_deployment() {
    log "Verifying deployment..."

    if [[ -f "${SCRIPT_DIR}/verify-deployment.sh" ]]; then
        bash "${SCRIPT_DIR}/verify-deployment.sh"
    else
        log_warning "verify-deployment.sh not found, performing basic checks"
        basic_health_checks
    fi
}

basic_health_checks() {
    log "Running basic health checks..."

    # Check database connectivity
    if docker exec postgres psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &> /dev/null; then
        log_success "Database connectivity: OK"
    else
        log_error "Database connectivity: FAILED"
        return 1
    fi

    # Check running services
    local running_services
    running_services=$($DOCKER_COMPOSE ps --services --filter "status=running")

    log "Running services:"
    echo "$running_services" | while read -r service; do
        log_success "  - $service"
    done
}

# ============================================================================
# Cleanup and Finalization
# ============================================================================

cleanup() {
    log "Cleaning up temporary files..."

    # Remove old logs (keep last 30 days)
    find "${PROJECT_ROOT}/logs" -name "deploy-*.log" -mtime +30 -delete 2>/dev/null || true

    # Remove old backups (keep last 7 days)
    find "${PROJECT_ROOT}/backups" -mindepth 1 -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null || true

    log_success "Cleanup completed"
}

save_deployment_info() {
    log "Saving deployment information..."

    cat > "${PROJECT_ROOT}/.deployment_info" <<EOF
DEPLOYMENT_DATE=$(date -Iseconds)
BACKUP_LOCATION=$BACKUP_DIR
DATABASE_NAME=$DB_NAME
DATABASE_HOST=$DB_HOST
DATABASE_PORT=$DB_PORT
GIT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
EOF

    log_success "Deployment info saved"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    log "================================================"
    log "Fresh Database Deployment - Starting"
    log "================================================"
    log ""

    # Run all steps
    preflight_checks || exit 1

    # Backup existing data
    backup_database
    backup_volumes

    # Stop everything
    stop_all_services

    # Start infrastructure
    start_infrastructure || exit 1

    # Recreate database
    recreate_database || exit 1

    # Run migrations
    run_migrations || exit 1

    # Seed data
    seed_initial_data

    # Start application services
    start_application_services

    # Verify deployment
    sleep 10  # Give services time to fully start
    verify_deployment || log_warning "Some health checks failed"

    # Cleanup and finalize
    cleanup
    save_deployment_info

    log ""
    log "================================================"
    log_success "Fresh Database Deployment - COMPLETED"
    log "================================================"
    log ""
    log "Backup location: ${BACKUP_DIR}"
    log "Log file: ${LOG_FILE}"
    log ""
    log "To view logs: docker-compose logs -f"
    log "To rollback: bash ${SCRIPT_DIR}/rollback.sh"
    log ""
}

# Handle script interruption
trap 'log_error "Deployment interrupted"; exit 130' INT TERM

# Run main function
main "$@"

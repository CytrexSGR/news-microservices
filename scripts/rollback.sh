#!/bin/bash
set -euo pipefail

# ============================================================================
# Rollback Script
# ============================================================================
# Restores database and services to previous state
# Author: DevOps Engineer (Claude Flow Swarm)
# Last Updated: 2025-10-15
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR=""

# Docker Compose command
DOCKER_COMPOSE="docker-compose"
if command -v docker compose &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
fi

# Database configuration
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-news_db}"

# ============================================================================
# Logging Functions
# ============================================================================

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $*"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $*"
}

# ============================================================================
# Backup Selection
# ============================================================================

select_backup() {
    log "Available backups:"
    echo ""

    local backups=()
    local counter=1

    # Find all backup directories
    while IFS= read -r -d '' backup; do
        backups+=("$backup")
        local backup_date
        backup_date=$(basename "$backup")
        echo "  [$counter] $backup_date"
        counter=$((counter + 1))
    done < <(find "${PROJECT_ROOT}/backups" -mindepth 1 -maxdepth 1 -type d -print0 | sort -zr)

    if [[ ${#backups[@]} -eq 0 ]]; then
        log_error "No backups found in ${PROJECT_ROOT}/backups"
        exit 1
    fi

    # Check for last backup marker
    if [[ -f "${PROJECT_ROOT}/.last_backup" ]]; then
        local last_backup
        last_backup=$(cat "${PROJECT_ROOT}/.last_backup")
        log_warning "Last backup: $(basename "$last_backup")"
        echo ""
    fi

    # Prompt for backup selection
    echo ""
    read -p "Select backup to restore [1-${#backups[@]}]: " selection

    if [[ ! "$selection" =~ ^[0-9]+$ ]] || [[ "$selection" -lt 1 ]] || [[ "$selection" -gt ${#backups[@]} ]]; then
        log_error "Invalid selection"
        exit 1
    fi

    BACKUP_DIR="${backups[$((selection - 1))]}"
    log_success "Selected backup: $(basename "$BACKUP_DIR")"
}

# ============================================================================
# Confirmation
# ============================================================================

confirm_rollback() {
    log_warning "This will:"
    echo "  1. Stop all running services"
    echo "  2. Drop current database '$DB_NAME'"
    echo "  3. Restore database from backup"
    echo "  4. Restore Docker volumes from backup"
    echo "  5. Restart all services"
    echo ""
    echo -e "${RED}This action cannot be undone!${NC}"
    echo ""

    read -p "Are you sure you want to continue? (yes/no): " confirmation

    if [[ "$confirmation" != "yes" ]]; then
        log "Rollback cancelled"
        exit 0
    fi
}

# ============================================================================
# Rollback Operations
# ============================================================================

stop_services() {
    log "Stopping all services..."

    cd "$PROJECT_ROOT"
    $DOCKER_COMPOSE down

    log_success "Services stopped"
}

restore_database() {
    log "Restoring database from backup..."

    # Start only PostgreSQL
    cd "$PROJECT_ROOT"
    $DOCKER_COMPOSE up -d postgres

    # Wait for PostgreSQL
    log "Waiting for PostgreSQL..."
    local attempts=0
    while ! docker exec postgres pg_isready -U "$DB_USER" &> /dev/null; do
        attempts=$((attempts + 1))
        if [[ $attempts -ge 60 ]]; then
            log_error "PostgreSQL failed to start"
            return 1
        fi
        sleep 1
    done

    # Drop and recreate database
    log "Dropping existing database..."
    docker exec postgres psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS ${DB_NAME};" 2>/dev/null || true

    log "Creating fresh database..."
    docker exec postgres psql -U "$DB_USER" -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

    # Restore from backup
    if [[ -f "${BACKUP_DIR}/${DB_NAME}_backup.sql" ]]; then
        log "Restoring database from SQL dump..."
        docker exec -i postgres psql -U "$DB_USER" -d "$DB_NAME" < "${BACKUP_DIR}/${DB_NAME}_backup.sql"
        log_success "Database restored successfully"
    else
        log_error "Backup file not found: ${BACKUP_DIR}/${DB_NAME}_backup.sql"
        return 1
    fi
}

restore_volumes() {
    log "Restoring Docker volumes..."

    # Restore PostgreSQL volume if backup exists
    if [[ -f "${BACKUP_DIR}/postgres_data.tar.gz" ]]; then
        log "Stopping PostgreSQL to restore volume..."
        docker stop postgres 2>/dev/null || true

        log "Restoring postgres_data volume..."
        docker run --rm \
            -v postgres_data:/data \
            -v "${BACKUP_DIR}":/backup \
            alpine sh -c "cd /data && rm -rf ./* && tar xzf /backup/postgres_data.tar.gz"

        log_success "PostgreSQL volume restored"
    else
        log_warning "No volume backup found, skipping volume restore"
    fi
}

restart_services() {
    log "Restarting all services..."

    cd "$PROJECT_ROOT"
    $DOCKER_COMPOSE up -d

    log_success "Services restarted"
}

verify_rollback() {
    log "Verifying rollback..."

    sleep 10  # Give services time to start

    if [[ -f "${SCRIPT_DIR}/verify-deployment.sh" ]]; then
        bash "${SCRIPT_DIR}/verify-deployment.sh"
    else
        log_warning "verify-deployment.sh not found, skipping verification"
    fi
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    log "================================================"
    log "Database Rollback Utility"
    log "================================================"
    echo ""

    # Select backup
    select_backup

    # Confirm rollback
    confirm_rollback

    echo ""
    log "Starting rollback process..."
    echo ""

    # Execute rollback
    stop_services || exit 1
    restore_database || exit 1
    restore_volumes
    restart_services || exit 1

    # Verify
    verify_rollback

    echo ""
    log "================================================"
    log_success "Rollback Completed"
    log "================================================"
    echo ""
    log "Restored from: $(basename "$BACKUP_DIR")"
    log ""
    log "To view logs: docker-compose logs -f"
    echo ""
}

# Handle script interruption
trap 'log_error "Rollback interrupted"; exit 130' INT TERM

# Run main function
main "$@"

#!/bin/bash
set -euo pipefail

# ============================================================================
# Quick Start Script
# ============================================================================
# Rapid deployment for development environments
# ============================================================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[QuickStart]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[QuickStart] ✓${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[QuickStart] ⚠${NC} $*"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log "Starting Quick Deployment..."

# Check for .env
if [[ ! -f "${PROJECT_ROOT}/.env" ]]; then
    log_warning ".env file not found"
    if [[ -f "${PROJECT_ROOT}/.env.example" ]]; then
        log "Creating .env from .env.example..."
        cp "${PROJECT_ROOT}/.env.example" "${PROJECT_ROOT}/.env"
        log_warning "Please edit .env and add your API keys"
        exit 1
    fi
fi

# Run full deployment
log "Running full deployment pipeline..."
bash "${SCRIPT_DIR}/deploy-fresh-db.sh"

log_success "Quick start completed!"
log ""
log "Next steps:"
log "  1. View logs: docker-compose logs -f"
log "  2. Test API: curl http://localhost:8000/health"
log "  3. Access app: http://localhost:8000"
log ""

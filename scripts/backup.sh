#!/bin/bash
#
# Automated Backup Script for News Microservices
# Creates timestamped backup excluding build artifacts and dependencies
#
# Usage:
#   ./scripts/backup.sh              # Create backup with default settings
#   ./scripts/backup.sh --frontend   # Backup frontend only
#   ./scripts/backup.sh --full       # Include node_modules and venv (large!)
#
# Author: Auto-generated protection measure (2025-10-21)
# Incident: Frontend Total Loss - Never again.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/home/cytrex/news-microservices"
BACKUP_DIR="/home/cytrex/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="news-ms-${TIMESTAMP}"
FRONTEND_ONLY=false
FULL_BACKUP=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --frontend)
            FRONTEND_ONLY=true
            BACKUP_NAME="frontend-${TIMESTAMP}"
            shift
            ;;
        --full)
            FULL_BACKUP=true
            BACKUP_NAME="news-ms-full-${TIMESTAMP}"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --frontend    Backup frontend directory only"
            echo "  --full        Include node_modules and venv (WARNING: Large!)"
            echo "  --help, -h    Show this help message"
            echo ""
            echo "Default: Backup entire project excluding build artifacts and dependencies"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Function to print formatted messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check disk space
check_disk_space() {
    local required_mb=500  # Minimum 500MB required
    local available_mb=$(df -m "${BACKUP_DIR}" | awk 'NR==2 {print $4}')

    if [ "${available_mb}" -lt "${required_mb}" ]; then
        print_error "Insufficient disk space in ${BACKUP_DIR}"
        print_error "Required: ${required_mb}MB, Available: ${available_mb}MB"
        exit 1
    fi

    print_info "Disk space check passed (${available_mb}MB available)"
}

# Function to create backup
create_backup() {
    local backup_path="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

    print_info "Creating backup: ${BACKUP_NAME}.tar.gz"
    print_info "Backup directory: ${BACKUP_DIR}"

    # Build exclusion list
    local exclude_args=""

    if [ "${FULL_BACKUP}" = false ]; then
        exclude_args="--exclude=node_modules --exclude=venv --exclude=__pycache__ --exclude=.venv --exclude=ENV --exclude=env"
    fi

    # Always exclude these
    exclude_args="${exclude_args} --exclude=.git --exclude=dist --exclude=build --exclude=.vite --exclude=.cache"
    exclude_args="${exclude_args} --exclude=*.log --exclude=*.pyc --exclude=*.pyo --exclude=*.pyd --exclude=*.so"
    exclude_args="${exclude_args} --exclude=.pytest_cache --exclude=.coverage --exclude=htmlcov"
    exclude_args="${exclude_args} --exclude=postgres-data --exclude=redis-data --exclude=rabbitmq-data"
    exclude_args="${exclude_args} --exclude=*.swp --exclude=*.swo --exclude=*~ --exclude=.DS_Store"

    # Navigate to project parent directory
    cd "$(dirname "${PROJECT_ROOT}")"

    # Create backup
    if [ "${FRONTEND_ONLY}" = true ]; then
        print_info "Backup mode: Frontend only"
        tar -czf "${backup_path}" \
            ${exclude_args} \
            news-microservices/frontend/ 2>&1 | grep -v "Removing leading" || true
    else
        print_info "Backup mode: Full project"
        tar -czf "${backup_path}" \
            ${exclude_args} \
            news-microservices/ 2>&1 | grep -v "Removing leading" || true
    fi

    # Check if backup was created successfully
    if [ -f "${backup_path}" ]; then
        local size=$(du -h "${backup_path}" | cut -f1)
        print_success "Backup created successfully"
        print_success "Location: ${backup_path}"
        print_success "Size: ${size}"

        # Create verification checksum
        local checksum=$(sha256sum "${backup_path}" | cut -d' ' -f1)
        echo "${checksum}  ${BACKUP_NAME}.tar.gz" > "${backup_path}.sha256"
        print_info "Checksum: ${checksum}"

        # List backup contents (first 20 files)
        print_info "Backup contents (first 20 files):"
        tar -tzf "${backup_path}" | head -20

        # Show total file count
        local file_count=$(tar -tzf "${backup_path}" | wc -l)
        print_info "Total files in backup: ${file_count}"

        return 0
    else
        print_error "Backup failed to create"
        return 1
    fi
}

# Function to clean old backups
clean_old_backups() {
    print_info "Checking for old backups..."

    # Keep last 10 backups
    local backup_count=$(ls -1 "${BACKUP_DIR}"/news-ms-*.tar.gz 2>/dev/null | wc -l)

    if [ "${backup_count}" -gt 10 ]; then
        print_warning "Found ${backup_count} backups, keeping most recent 10"

        ls -1t "${BACKUP_DIR}"/news-ms-*.tar.gz | tail -n +11 | while read old_backup; do
            print_info "Removing old backup: $(basename "${old_backup}")"
            rm -f "${old_backup}" "${old_backup}.sha256"
        done

        print_success "Old backups cleaned"
    else
        print_info "Backup count: ${backup_count} (no cleanup needed)"
    fi
}

# Function to verify critical files exist
verify_critical_files() {
    print_info "Verifying critical files before backup..."

    local missing_files=()

    # Check frontend critical files
    [ -f "${PROJECT_ROOT}/frontend/package.json" ] || missing_files+=("frontend/package.json")
    [ -f "${PROJECT_ROOT}/frontend/package-lock.json" ] || missing_files+=("frontend/package-lock.json")
    [ -f "${PROJECT_ROOT}/frontend/FEATURES.md" ] || missing_files+=("frontend/FEATURES.md")
    [ -f "${PROJECT_ROOT}/frontend/ARCHITECTURE.md" ] || missing_files+=("frontend/ARCHITECTURE.md")
    [ -f "${PROJECT_ROOT}/frontend/SETUP.md" ] || missing_files+=("frontend/SETUP.md")

    # Check documentation
    [ -f "${PROJECT_ROOT}/docs/guides/FRONTEND-PROJECTS.md" ] || missing_files+=("docs/guides/FRONTEND-PROJECTS.md")
    [ -f "${PROJECT_ROOT}/CLAUDE.md" ] || missing_files+=("CLAUDE.md")

    # Check for nested .git (should NOT exist)
    if [ -d "${PROJECT_ROOT}/frontend/.git" ]; then
        print_error "CRITICAL: Nested .git directory found in frontend/"
        print_error "This should have been removed! Run: rm -rf ${PROJECT_ROOT}/frontend/.git"
        exit 1
    fi

    if [ ${#missing_files[@]} -gt 0 ]; then
        print_warning "Missing critical files:"
        for file in "${missing_files[@]}"; do
            print_warning "  - ${file}"
        done
        print_warning "Backup will proceed, but these files should be created"
    else
        print_success "All critical files present"
    fi
}

# Main execution
main() {
    print_info "========================================="
    print_info "News Microservices Backup Script"
    print_info "========================================="
    print_info "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    print_info ""

    # Verify we're in the right directory
    if [ ! -d "${PROJECT_ROOT}" ]; then
        print_error "Project root not found: ${PROJECT_ROOT}"
        exit 1
    fi

    # Run pre-backup checks
    check_disk_space
    verify_critical_files

    # Create backup
    if create_backup; then
        clean_old_backups

        print_info ""
        print_success "========================================="
        print_success "Backup completed successfully!"
        print_success "========================================="
        print_info ""
        print_info "To restore from this backup:"
        print_info "  cd /home/cytrex"
        print_info "  tar -xzf ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
        print_info ""
        print_info "To verify backup integrity:"
        print_info "  sha256sum -c ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz.sha256"
        print_info ""

        exit 0
    else
        print_error "========================================="
        print_error "Backup failed!"
        print_error "========================================="
        exit 1
    fi
}

# Run main function
main

#!/bin/bash

# Code Backup Script for News Microservices
# Excludes: venv, node_modules, __pycache__, .pyc, logs, old backups
# Date: 2025-10-22

set -e  # Exit on error

# Configuration
BACKUP_DIR="/home/cytrex/backups"
PROJECT_DIR="/home/cytrex/news-microservices"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="news-microservices-code-backup-${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== News Microservices Code Backup ===${NC}"
echo -e "Date: $(date)"
echo -e "Backup will be saved to: ${BACKUP_PATH}\n"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Change to project directory
cd "${PROJECT_DIR}"

echo -e "${YELLOW}Creating backup...${NC}"

# Create tar archive with exclusions
tar -czf "${BACKUP_PATH}" \
    --exclude='venv' \
    --exclude='*/venv' \
    --exclude='*/venv/*' \
    --exclude='__pycache__' \
    --exclude='*/__pycache__' \
    --exclude='*/__pycache__/*' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='*.pyd' \
    --exclude='node_modules' \
    --exclude='*/node_modules' \
    --exclude='*/node_modules/*' \
    --exclude='.git' \
    --exclude='*.log' \
    --exclude='logs' \
    --exclude='logs/*' \
    --exclude='frontend.backup' \
    --exclude='frontend.backup/*' \
    --exclude='frontend.backup.old-*' \
    --exclude='frontend.corrupted' \
    --exclude='frontend.corrupted/*' \
    --exclude='.swarm' \
    --exclude='.swarm/*' \
    --exclude='.claude' \
    --exclude='.claude/*' \
    --exclude='.claude-flow' \
    --exclude='.claude-flow/*' \
    --exclude='*.png' \
    --exclude='*.jpg' \
    --exclude='*.jpeg' \
    --exclude='.DS_Store' \
    --exclude='*.db' \
    --exclude='*.sqlite' \
    --exclude='*.sqlite3' \
    --exclude='.pytest_cache' \
    --exclude='*/.pytest_cache' \
    --exclude='.coverage' \
    --exclude='htmlcov' \
    --exclude='dist' \
    --exclude='build' \
    --exclude='*.egg-info' \
    .

# Check if backup was created successfully
if [ -f "${BACKUP_PATH}" ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_PATH}" | cut -f1)
    echo -e "\n${GREEN}✓ Backup created successfully!${NC}"
    echo -e "Location: ${BACKUP_PATH}"
    echo -e "Size: ${BACKUP_SIZE}"

    # List contents summary
    echo -e "\n${YELLOW}Backup contents:${NC}"
    tar -tzf "${BACKUP_PATH}" | head -20
    echo -e "... (showing first 20 files)"

    TOTAL_FILES=$(tar -tzf "${BACKUP_PATH}" | wc -l)
    echo -e "\nTotal files in backup: ${TOTAL_FILES}"

    # Create verification report
    REPORT_FILE="${BACKUP_DIR}/${BACKUP_NAME}-report.txt"
    echo "News Microservices Code Backup Report" > "${REPORT_FILE}"
    echo "======================================" >> "${REPORT_FILE}"
    echo "" >> "${REPORT_FILE}"
    echo "Date: $(date)" >> "${REPORT_FILE}"
    echo "Backup file: ${BACKUP_PATH}" >> "${REPORT_FILE}"
    echo "Size: ${BACKUP_SIZE}" >> "${REPORT_FILE}"
    echo "Total files: ${TOTAL_FILES}" >> "${REPORT_FILE}"
    echo "" >> "${REPORT_FILE}"
    echo "Included:" >> "${REPORT_FILE}"
    echo "  - services/ (all microservices code)" >> "${REPORT_FILE}"
    echo "  - frontend/ (React frontend, without node_modules)" >> "${REPORT_FILE}"
    echo "  - docs/ (all documentation)" >> "${REPORT_FILE}"
    echo "  - tests/ (test suites)" >> "${REPORT_FILE}"
    echo "  - scripts/ (utility scripts)" >> "${REPORT_FILE}"
    echo "  - shared/ (shared code)" >> "${REPORT_FILE}"
    echo "  - Configuration files (docker-compose.yml, .env.example, etc.)" >> "${REPORT_FILE}"
    echo "  - README.md, CLAUDE.md, POSTMORTEMS.md" >> "${REPORT_FILE}"
    echo "" >> "${REPORT_FILE}"
    echo "Excluded:" >> "${REPORT_FILE}"
    echo "  - venv/ (Python virtual environments)" >> "${REPORT_FILE}"
    echo "  - __pycache__/ (Python cache)" >> "${REPORT_FILE}"
    echo "  - *.pyc (compiled Python)" >> "${REPORT_FILE}"
    echo "  - node_modules/ (npm packages)" >> "${REPORT_FILE}"
    echo "  - .git/ (git repository)" >> "${REPORT_FILE}"
    echo "  - logs/ (log files)" >> "${REPORT_FILE}"
    echo "  - *.log (log files)" >> "${REPORT_FILE}"
    echo "  - old frontend backups" >> "${REPORT_FILE}"
    echo "  - .swarm/, .claude/, .claude-flow/ (temporary)" >> "${REPORT_FILE}"
    echo "  - images (*.png, *.jpg)" >> "${REPORT_FILE}"
    echo "  - databases (*.db, *.sqlite)" >> "${REPORT_FILE}"
    echo "" >> "${REPORT_FILE}"
    echo "Full file list:" >> "${REPORT_FILE}"
    tar -tzf "${BACKUP_PATH}" >> "${REPORT_FILE}"

    echo -e "\n${GREEN}✓ Verification report created: ${REPORT_FILE}${NC}"

    # Show older backups
    echo -e "\n${YELLOW}Existing backups in ${BACKUP_DIR}:${NC}"
    ls -lh "${BACKUP_DIR}"/news-microservices-code-backup-*.tar.gz 2>/dev/null || echo "No previous backups found"

else
    echo -e "\n${RED}✗ Backup failed!${NC}"
    exit 1
fi

echo -e "\n${GREEN}=== Backup Complete ===${NC}"

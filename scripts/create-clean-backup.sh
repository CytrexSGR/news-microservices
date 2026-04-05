#!/bin/bash
# VM Clean Backup Script - Exclusions für optimale Backup-Größe

set -e

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="news-ms-clean-backup-${BACKUP_DATE}"
BACKUP_DIR="/home/cytrex/backups"
SOURCE_DIR="/home/cytrex/news-microservices"

echo "🔍 Creating clean backup: ${BACKUP_NAME}"
echo "📁 Source: ${SOURCE_DIR}"
echo "💾 Destination: ${BACKUP_DIR}"

# Erstelle Backup mit Exclusions
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
  --exclude='venv' \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.pyo' \
  --exclude='.pytest_cache' \
  --exclude='.coverage' \
  --exclude='*.log' \
  --exclude='dist' \
  --exclude='build' \
  --exclude='.DS_Store' \
  --exclude='*.sqlite' \
  --exclude='*.db' \
  --exclude='.mypy_cache' \
  --exclude='.ruff_cache' \
  -C /home/cytrex news-microservices

# Backup-Statistiken
BACKUP_SIZE=$(du -sh "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)
echo ""
echo "✅ Backup completed successfully!"
echo "📦 File: ${BACKUP_NAME}.tar.gz"
echo "💾 Size: ${BACKUP_SIZE}"
echo ""

# Erstelle Backup-Report
cat > "${BACKUP_DIR}/${BACKUP_NAME}-report.txt" <<EOF
Backup Report
=============
Date: $(date)
Source: ${SOURCE_DIR}
Backup File: ${BACKUP_NAME}.tar.gz
Size: ${BACKUP_SIZE}

Contents (first 50 files):
--------------------------
$(tar -tzf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | head -50)
...

File Count:
-----------
$(tar -tzf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | wc -l) files

Exclusions:
-----------
- venv/
- node_modules/
- __pycache__/
- *.pyc, *.pyo
- .pytest_cache/
- .coverage
- *.log
- dist/, build/
- .DS_Store

Python Files Backed Up:
-----------------------
$(tar -tzf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | grep -c "\.py$" || echo "0") Python files
EOF

echo "📄 Backup report: ${BACKUP_NAME}-report.txt"
echo ""
echo "🔍 Backup verification:"
echo "$(tar -tzf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | grep -c "\.py$" || echo "0") Python files backed up"

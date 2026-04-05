# Backup Guide - News Microservices

**Last Updated:** 2025-10-22

## Quick Start

```bash
# Create a code backup (excludes venv, node_modules, etc.)
./scripts/backup-code.sh
```

Backup will be saved to: `/home/cytrex/backups/`

---

## What Gets Backed Up

### ✅ Included

- **services/** - All microservices source code (Python)
- **frontend/** - React frontend source code (TypeScript/TSX)
- **docs/** - All documentation (markdown, guides, ADRs)
- **tests/** - Test suites for all services
- **scripts/** - Utility and automation scripts
- **shared/** - Shared code and libraries
- **Configuration files:**
  - `docker-compose.yml`
  - `docker-compose.prod.yml`
  - `.env.example`
  - `Makefile`
  - `Tiltfile`
  - Service-specific configs
- **Documentation:**
  - `README.md`
  - `CLAUDE.md`
  - `POSTMORTEMS.md`
  - All markdown files

### ❌ Excluded

**Development artifacts (can be regenerated):**
- `venv/` - Python virtual environments
- `__pycache__/` - Python bytecode cache
- `*.pyc`, `*.pyo`, `*.pyd` - Compiled Python files
- `node_modules/` - NPM packages (regenerate with `npm install`)
- `.pytest_cache/` - Pytest cache
- `.coverage` - Coverage reports
- `htmlcov/` - HTML coverage reports
- `dist/`, `build/`, `*.egg-info` - Build artifacts

**Version control:**
- `.git/` - Git repository (separate backup strategy)

**Logs and temporary files:**
- `logs/` - Log directory
- `*.log` - Log files
- `.swarm/` - Swarm temporary files
- `.claude/` - Claude temporary files
- `.claude-flow/` - Claude Flow temporary files

**Old backups and corrupted files:**
- `frontend.backup/` - Old frontend backups
- `frontend.backup.old-*` - Older frontend backups
- `frontend.corrupted/` - Corrupted frontend files

**Media files:**
- `*.png`, `*.jpg`, `*.jpeg` - Images
- `*.db`, `*.sqlite`, `*.sqlite3` - Database files

**System files:**
- `.DS_Store` - macOS metadata

---

## Backup Contents Summary

**Latest backup: 2025-10-22**

| Category | Files | Size | Notes |
|----------|-------|------|-------|
| Services | 461 Python files | ~8.5M | All 11 microservices |
| Frontend | ~100 files | ~2.6M | Without node_modules |
| Docs | 208 files | ~2.8M | Complete documentation |
| Tests | Various | ~21M | Test suites |
| Scripts | ~50 files | ~368K | Automation scripts |
| **Total** | **1,469 files** | **~1.9M compressed** | Full codebase |

---

## Backup Locations

### Primary Backup

```
/home/cytrex/backups/news-microservices-code-backup-YYYYMMDD_HHMMSS.tar.gz
```

### Verification Report

Each backup includes a verification report:
```
/home/cytrex/backups/news-microservices-code-backup-YYYYMMDD_HHMMSS-report.txt
```

Contains:
- Backup date and size
- Total file count
- Complete file list
- Included/excluded items

---

## Restoring from Backup

### Full Restore

```bash
# Extract to temporary location
mkdir -p /tmp/restore
cd /tmp/restore
tar -xzf /home/cytrex/backups/news-microservices-code-backup-YYYYMMDD_HHMMSS.tar.gz

# Verify contents
ls -la

# Copy to target location (be careful!)
# Option 1: Fresh installation
sudo cp -r /tmp/restore/* /home/cytrex/news-microservices/

# Option 2: Selective restore
cp -r /tmp/restore/services/feed-service /home/cytrex/news-microservices/services/
```

### After Restore - Required Steps

**1. Reinstall Dependencies**

```bash
# Python dependencies (each service)
cd services/[service-name]
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
```

**2. Configure Environment**

```bash
# Copy environment example
cp .env.example .env

# Edit with actual values
nano .env
```

**3. Setup Database**

```bash
# Start infrastructure
docker compose up -d postgres redis rabbitmq

# Run migrations
docker compose exec auth-service alembic upgrade head
# Repeat for each service...
```

**4. Verify Services**

```bash
# Start all services
docker compose up -d

# Check health
docker compose ps
./scripts/health_report.py
```

---

## Backup Best Practices

### Frequency

| Environment | Backup Frequency | Retention |
|-------------|------------------|-----------|
| Development | Before major changes | Keep last 5 |
| Staging | Daily | Keep 30 days |
| Production | Daily + pre-deployment | Keep 90 days |

### Recommended Schedule

```bash
# Development: Before refactoring
./scripts/backup-code.sh

# Automated: Add to crontab
0 2 * * * /home/cytrex/news-microservices/scripts/backup-code.sh

# Pre-deployment: Manual backup
./scripts/backup-code.sh
# Then proceed with deployment
```

### Multiple Backup Locations

**Local:**
```bash
/home/cytrex/backups/
```

**Remote (recommended for production):**
```bash
# Copy to remote server
scp /home/cytrex/backups/news-microservices-*.tar.gz \
    user@backup-server:/backups/

# Or use rsync
rsync -avz /home/cytrex/backups/ \
    user@backup-server:/backups/news-microservices/
```

**Cloud Storage (recommended):**
```bash
# AWS S3 example
aws s3 cp /home/cytrex/backups/news-microservices-*.tar.gz \
    s3://your-backup-bucket/news-microservices/

# Google Cloud Storage example
gsutil cp /home/cytrex/backups/news-microservices-*.tar.gz \
    gs://your-backup-bucket/news-microservices/
```

---

## Backup Verification

### Verify Backup Integrity

```bash
# Check archive integrity
tar -tzf /home/cytrex/backups/news-microservices-code-backup-YYYYMMDD_HHMMSS.tar.gz > /dev/null
echo $?  # Should output 0 (success)

# List contents
tar -tzf /home/cytrex/backups/news-microservices-code-backup-YYYYMMDD_HHMMSS.tar.gz | less

# Extract single file to verify
tar -xzf backup.tar.gz ./services/auth-service/app/main.py -O | head -20
```

### Verify Critical Files Exist

```bash
BACKUP_FILE="/home/cytrex/backups/news-microservices-code-backup-YYYYMMDD_HHMMSS.tar.gz"

# Check for critical services
tar -tzf $BACKUP_FILE | grep "services/auth-service/app/main.py"
tar -tzf $BACKUP_FILE | grep "services/feed-service/app/main.py"
tar -tzf $BACKUP_FILE | grep "services/content-analysis-service/app/main.py"

# Check for documentation
tar -tzf $BACKUP_FILE | grep "CLAUDE.md"
tar -tzf $BACKUP_FILE | grep "README.md"
tar -tzf $BACKUP_FILE | grep "docs/refactoring/REFACTORING-ANALYSIS"

# Check for frontend
tar -tzf $BACKUP_FILE | grep "frontend/package.json"
tar -tzf $BACKUP_FILE | grep "frontend/src/App.tsx"
```

---

## Disaster Recovery Scenarios

### Scenario 1: Accidental File Deletion

**Problem:** Deleted important service file

**Solution:**
```bash
# Extract just the needed file
tar -xzf backup.tar.gz ./services/auth-service/app/services/user_service.py

# Move to correct location
mv services/auth-service/app/services/user_service.py \
   /home/cytrex/news-microservices/services/auth-service/app/services/
```

### Scenario 2: Failed Refactoring

**Problem:** Refactoring broke multiple services

**Solution:**
```bash
# Extract entire service
tar -xzf backup.tar.gz ./services/content-analysis-service

# Compare changes
diff -r services/content-analysis-service \
       /home/cytrex/news-microservices/services/content-analysis-service

# Restore if needed
rm -rf /home/cytrex/news-microservices/services/content-analysis-service
mv services/content-analysis-service \
   /home/cytrex/news-microservices/services/
```

### Scenario 3: Complete System Loss

**Problem:** Complete server failure or data loss

**Solution:**
1. Setup fresh server with Docker
2. Extract backup to new location
3. Follow "After Restore - Required Steps" above
4. Restore database from separate database backup
5. Verify all services operational

---

## Database Backups (Separate Strategy)

**Note:** Code backups do NOT include database data.

### Database Backup Script

```bash
# Backup PostgreSQL database
PGPASSWORD=your_db_password pg_dump \
    -h localhost \
    -p 5433 \
    -U news_user \
    -d news_mcp \
    --clean \
    --if-exists \
    -f /home/cytrex/backups/news_mcp_db_$(date +%Y%m%d_%H%M%S).sql

# Compress
gzip /home/cytrex/backups/news_mcp_db_*.sql
```

### Database Restore

```bash
# Drop and recreate database
PGPASSWORD=your_db_password psql -h localhost -p 5433 -U news_user \
    -c "DROP DATABASE IF EXISTS news_mcp;"
PGPASSWORD=your_db_password psql -h localhost -p 5433 -U news_user \
    -c "CREATE DATABASE news_mcp;"

# Restore from backup
gunzip -c /home/cytrex/backups/news_mcp_db_YYYYMMDD_HHMMSS.sql.gz | \
PGPASSWORD=your_db_password psql -h localhost -p 5433 -U news_user -d news_mcp
```

---

## Backup Size Estimates

### Without Exclusions (Original)

- services: 915M (includes venv, __pycache__)
- frontend: 277M (includes node_modules)
- venv: 202M
- **Total: ~1.4GB**

### With Exclusions (Backup)

- services: 8.5M (clean code only)
- frontend: 2.6M (without node_modules)
- docs: 2.8M
- tests: 21M
- Other: ~2M
- **Total: ~37M uncompressed → 1.9M compressed (95% compression!)**

---

## Automation

### Cron Job Setup

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /home/cytrex/news-microservices/scripts/backup-code.sh

# Add weekly backup cleanup (keep last 10)
0 3 * * 0 find /home/cytrex/backups -name "news-microservices-code-backup-*.tar.gz" -mtime +70 -delete
```

### Pre-Commit Hook (Optional)

```bash
# .githooks/pre-commit
#!/bin/bash

# Create backup before major commits
if git diff --cached --stat | grep -q "services/.*\.py"; then
    echo "Creating backup before commit..."
    ./scripts/backup-code.sh
fi
```

---

## Troubleshooting

### Issue: Backup Too Large

**Symptom:** Backup > 100M

**Cause:** Exclusions not working

**Solution:**
```bash
# Check for excluded directories
tar -tzf backup.tar.gz | grep -E "(node_modules|__pycache__|venv)"

# If found, verify exclusion patterns in script
```

### Issue: Missing Files

**Symptom:** Expected files not in backup

**Cause:** File permissions or patterns

**Solution:**
```bash
# Check file exists and is readable
ls -la services/auth-service/app/main.py

# Test tar manually
tar -czf test.tar.gz services/auth-service/app/main.py
tar -tzf test.tar.gz
```

### Issue: Corrupted Backup

**Symptom:** Cannot extract backup

**Solution:**
```bash
# Verify integrity
tar -tzf backup.tar.gz > /dev/null

# If corrupted, use previous backup
ls -lt /home/cytrex/backups/news-microservices-code-backup-*.tar.gz
```

---

## Related Documentation

- **Refactoring Analysis:** `docs/refactoring/REFACTORING-ANALYSIS-2025-10-22.md`
- **Development Guide:** `CLAUDE.md`
- **Deployment Guide:** `docs/guides/deployment-guide.md`
- **Docker Guide:** `docs/guides/docker-guide.md`

---

## Backup Script Location

**Script:** `/home/cytrex/news-microservices/scripts/backup-code.sh`

**Usage:**
```bash
# Run from anywhere
/home/cytrex/news-microservices/scripts/backup-code.sh

# Or from project root
./scripts/backup-code.sh
```

**Output:**
- Backup file: `/home/cytrex/backups/news-microservices-code-backup-YYYYMMDD_HHMMSS.tar.gz`
- Report: `/home/cytrex/backups/news-microservices-code-backup-YYYYMMDD_HHMMSS-report.txt`

---

## Summary

✅ **Quick backup:** `./scripts/backup-code.sh`

✅ **Location:** `/home/cytrex/backups/`

✅ **Size:** ~1.9M compressed (95% compression)

✅ **Contains:** All source code, docs, tests, configs

✅ **Excludes:** venv, node_modules, __pycache__, logs, images, databases

✅ **Restore:** Extract + reinstall dependencies + configure + verify

---

**For questions or issues, see CLAUDE.md or contact development team.**

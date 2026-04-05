# Scripts Directory

Utility scripts for system maintenance, diagnostics, and automation.

## Log Management

### `add_log_rotation.py`

**Purpose:** Automatically add Docker log rotation to all services in docker-compose.yml

**Usage:**
```bash
python3 scripts/add_log_rotation.py
```

**What it does:**
1. Reads `docker-compose.yml`
2. Checks if `x-logging` anchor exists
3. Scans all service definitions
4. Adds `logging: *default-logging` to services without it
5. Writes output to `docker-compose.yml.new`
6. Shows summary of changes

**Output:**
```
✅ Added logging to: auth-service
✅ Added logging to: feed-service
...
📊 Summary:
   Total services found: 45
   Log rotation added to: 45
```

**Requirements:**
- Python 3.6+
- `docker-compose.yml` must have `x-logging` anchor at top

**Created:** 2025-11-24 (Incident #24 - Disk Space Crisis)
**Commit:** `b82b832`

### `disk_analysis.sh`

**Purpose:** Comprehensive disk usage analysis and Docker diagnostics

**Usage:**
```bash
./scripts/disk_analysis.sh

# Or with sudo for full access
sudo ./scripts/disk_analysis.sh
```

**What it checks:**
1. **Disk Usage Overview** - Total disk space utilization
2. **Top 20 Largest Directories in Root** - Find space hogs
3. **Top 15 Largest Directories in /var** - Docker lives here
4. **Top 10 Largest Directories in /home** - User data
5. **Docker Disk Usage** - Images, containers, volumes, cache
6. **Docker Volumes** - Individual volume sizes
7. **Large Files (>1GB)** - Find massive files
8. **PostgreSQL Database Sizes** - Database space usage
9. **Systemd Journal Size** - System log space

**Sample Output:**
```
=== DISK USAGE OVERVIEW ===
/dev/mapper/ubuntu--vg-ubuntu--lv  495G  70G  405G  15% /

=== TOP 20 LARGEST DIRECTORIES IN ROOT ===
411G    /var
12G     /home
...

=== LARGE FILES (>1GB) ===
314G /var/lib/docker/containers/1e7370d80de0.../xxx-json.log  # ⚠️ Problem!
```

**Permissions:**
- Some commands require `sudo` (Docker inspections, /var access)
- Script handles missing permissions gracefully

**Created:** 2025-11-24 (Incident #24 - Disk Space Crisis)
**Commit:** `b82b832`

**Use Cases:**
- Regular disk space audits
- Troubleshooting disk space issues
- Identifying log file growth
- Finding orphaned Docker resources

## Migration Scripts

### `backfill_unified_analysis_table_v3.sql`

**Purpose:** Migrate content analysis data from legacy table to unified table

**Status:** ✅ Completed (2025-11-08)

**What it does:**
- Backfills missing articles from `content_analysis_v2` schema
- Migrates to unified `public.article_analysis` table
- Handles idempotency (safe to re-run)

**Usage:**
```bash
psql -U postgres -d news_db -f scripts/backfill_unified_analysis_table_v3.sql
```

**Created:** 2025-11-08 (Database unification)

## Health Checks

### `health_check.sh`

**Purpose:** Check health of all services

**Usage:**
```bash
./scripts/health_check.sh
```

**Output:**
- Service status (running/stopped/unhealthy)
- Health check results
- Container resource usage

## References

- [Docker Log Rotation Guide](../docs/guides/docker-log-rotation.md)
- [POSTMORTEMS.md - Incident #24](../POSTMORTEMS.md#incident-24-docker-log-overflow---346gb-disk-space-crisis-2025-11-24)
- [Docker Rebuild Procedure](../docs/guides/docker-rebuild-procedure.md)

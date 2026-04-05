# Monitoring Scripts Installation

**Created:** 2025-11-18
**Purpose:** Prevent disk space crises through automated monitoring and cleanup

---

## Scripts

### 1. Disk Usage Monitor (`check_disk_usage.sh`)
- **Purpose:** Alert when disk usage > 80%
- **Schedule:** Every 6 hours
- **Alert:** Console output + email (if configured)

### 2. Docker Cleanup (`docker_cleanup.sh`)
- **Purpose:** Remove old Docker resources weekly
- **Schedule:** Every Sunday 3 AM
- **Keeps:** Resources from last 7 days

---

## Installation

### Step 1: Test Scripts

```bash
# Test disk monitor
cd /home/cytrex/news-microservices/scripts/monitoring
./check_disk_usage.sh
# Expected: "✅ Disk usage OK: XX%"

# Test cleanup (dry-run mode)
./docker_cleanup.sh
# Expected: "✅ Docker cleanup completed"
```

### Step 2: Install to System

```bash
# Copy to system bin directory
sudo cp check_disk_usage.sh /usr/local/bin/
sudo cp docker_cleanup.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/check_disk_usage.sh
sudo chmod +x /usr/local/bin/docker_cleanup.sh
```

### Step 3: Add Cron Jobs

```bash
# Edit crontab
crontab -e

# Add these lines:
# Disk monitoring - every 6 hours
0 */6 * * * /usr/local/bin/check_disk_usage.sh >> /tmp/disk-monitor-cron.log 2>&1

# Docker cleanup - every Sunday 3 AM
0 3 * * 0 /usr/local/bin/docker_cleanup.sh >> /tmp/docker-cleanup-cron.log 2>&1
```

### Step 4: Verify Installation

```bash
# List cron jobs
crontab -l | grep -E "disk|docker"

# Check logs
tail -f /var/log/disk-monitor.log
tail -f /var/log/docker-cleanup.log
```

---

## Manual Usage

### Check Disk Now

```bash
/usr/local/bin/check_disk_usage.sh
```

### Cleanup Docker Now

```bash
/usr/local/bin/docker_cleanup.sh
```

---

## Logs

- **Disk Monitor:** `/var/log/disk-monitor.log`
- **Docker Cleanup:** `/var/log/docker-cleanup.log`
- **Cron Output:** `/tmp/disk-monitor-cron.log`, `/tmp/docker-cleanup-cron.log`

---

## Email Alerts (Optional)

To enable email alerts, install mailutils:

```bash
sudo apt-get update
sudo apt-get install mailutils
```

Configure SMTP or use system mail relay.

---

## Testing Schedule

After installation, verify scripts run as scheduled:

```bash
# After 6 hours, check disk monitor ran
ls -lh /var/log/disk-monitor.log

# After Sunday 3 AM, check cleanup ran
ls -lh /var/log/docker-cleanup.log
```

---

## Troubleshooting

### Script Not Running

```bash
# Check cron is running
sudo systemctl status cron

# Check cron logs
grep -i cron /var/log/syslog | tail -20
```

### Permission Errors

```bash
# Ensure scripts are executable
ls -l /usr/local/bin/check_disk_usage.sh
ls -l /usr/local/bin/docker_cleanup.sh

# Fix if needed
sudo chmod +x /usr/local/bin/*.sh
```

### No Logs

```bash
# Create log directory
sudo mkdir -p /var/log
sudo touch /var/log/disk-monitor.log
sudo touch /var/log/docker-cleanup.log
sudo chown cytrex:cytrex /var/log/disk-monitor.log
sudo chown cytrex:cytrex /var/log/docker-cleanup.log
```

---

**Next Steps:**
1. Test both scripts manually
2. Install to system (sudo)
3. Add cron jobs
4. Monitor logs for 1 week
5. Adjust thresholds if needed

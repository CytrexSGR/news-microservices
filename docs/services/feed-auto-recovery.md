# Feed Auto-Recovery System

## Overview

Automated system to recover feeds that failed due to temporary network outages.

**Problem Solved:** After internet outages, all feeds were marked as `ERROR` and stayed in that state permanently, requiring manual intervention.

**Solution:** Automatic recovery task that runs every 30 minutes to detect and recover feeds stuck in ERROR state.

## Implementation

### Task: `feed.auto_recover_failed_feeds`

**Location:** `services/feed-service/app/tasks/feed_tasks.py`

**Schedule:** Every 30 minutes (configurable in `app/celery_app.py`)

**Parameters:**
- `cooldown_minutes` (default: 60) - Minimum time a feed must be in ERROR state before recovery

### Recovery Strategy

1. **Find Stuck Feeds**
   - Query feeds with `status=ERROR` and `is_active=true`
   - Filter for feeds in ERROR state for > `cooldown_minutes`

2. **Verify Network Connectivity**
   - Check if other feeds had successful fetches in last 10 minutes
   - Skip recovery if network appears unavailable (prevents immediate re-failures)

3. **Reset Feeds**
   - Set `status` to `ACTIVE`
   - Reset `consecutive_failures` to 0
   - Reset `health_score` to 100
   - Clear `last_error_message` and `last_error_at`

4. **Publish Event**
   - Send `feed.auto_recovery_completed` event with recovery details

## Configuration

### Celery Beat Schedule

```python
# Every 30 minutes
"auto-recover-failed-feeds": {
    "task": "feed.auto_recover_failed_feeds",
    "schedule": 1800.0,  # 30 minutes
    "kwargs": {"cooldown_minutes": 60},  # Recover feeds in ERROR for >60 minutes
    "options": {"expires": 600},  # Expire after 10 minutes if not run
}
```

### Queue & Priority

- **Queue:** `maintenance`
- **Priority:** 2 (medium-low)

## Behavior Examples

### Scenario 1: Internet Outage Recovery

```
08:00 - Internet outage begins
08:05 - All 54 feeds marked as ERROR
08:30 - Internet restored
09:00 - Auto-recovery task runs (first check after internet restore)
09:00 - Network verified (recent successful fetches exist)
09:00 - All 54 feeds recovered to ACTIVE state
```

### Scenario 2: Network Still Down

```
08:00 - Internet outage begins
08:05 - All feeds marked as ERROR
09:00 - Auto-recovery task runs
09:00 - Network check fails (no recent successful fetches)
09:00 - Recovery skipped to avoid immediate re-failures
09:30 - Internet restored
10:00 - Auto-recovery task runs
10:00 - Network verified
10:00 - All feeds recovered
```

### Scenario 3: Individual Feed Issues

```
10:00 - Feed A fails (bad RSS URL)
10:05 - Feed A marked as ERROR
11:05 - Auto-recovery task runs (Feed A in ERROR for >60 min)
11:05 - Network verified
11:05 - Feed A recovered to ACTIVE
11:10 - Feed A fails again (URL still broken)
11:15 - Feed A marked as ERROR again
```

**Note:** Individual feed issues will cycle between ERROR and ACTIVE. This is intentional - the system gives feeds multiple chances before permanent deactivation.

## Monitoring

### Logs

Recovery operations are logged:

```
✅ Recovered feed: Reuters World News (was in ERROR for ~95 minutes)
✅ Recovered feed: BBC News (was in ERROR for ~92 minutes)
```

### Events

Subscribe to `feed.auto_recovery_completed` event for recovery notifications:

```json
{
  "feeds_recovered": 54,
  "recovered_feeds": [
    {
      "feed_id": "...",
      "feed_name": "Reuters",
      "error_duration_minutes": 95
    }
  ],
  "timestamp": "2025-11-18T09:00:00Z",
  "cooldown_minutes": 60
}
```

## Manual Recovery

If needed, feeds can still be recovered manually:

```sql
UPDATE feeds
SET status = 'ACTIVE',
    consecutive_failures = 0,
    health_score = 100,
    last_error_message = NULL,
    last_error_at = NULL
WHERE is_active = true AND status = 'ERROR';
```

## Tuning

### More Aggressive Recovery (Faster)

```python
# Run every 10 minutes, recover after 30 minutes in ERROR
"auto-recover-failed-feeds": {
    "schedule": 600.0,  # 10 minutes
    "kwargs": {"cooldown_minutes": 30},
}
```

### More Conservative Recovery (Slower)

```python
# Run every hour, recover after 120 minutes in ERROR
"auto-recover-failed-feeds": {
    "schedule": 3600.0,  # 60 minutes
    "kwargs": {"cooldown_minutes": 120},
}
```

## Implementation Date

- **Created:** 2025-11-18
- **Reason:** Internet outage caused all feeds to permanently fail
- **Status:** Active, running every 30 minutes

## Related

- **Task File:** `services/feed-service/app/tasks/feed_tasks.py`
- **Schedule:** `services/feed-service/app/celery_app.py`
- **Incident:** See POSTMORTEMS.md for original outage details

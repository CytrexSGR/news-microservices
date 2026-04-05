# Content Analysis V2 - Monitoring API

**Service:** Content Analysis V2
**Base URL:** `http://localhost:8114/api/v1/monitoring`
**Version:** 1.0.0
**Added:** 2025-10-30

---

## Overview

The Monitoring API provides endpoints for tracking pipeline health, detecting unprocessed articles, and performing backfill operations.

### Key Features

- ✅ **Unprocessed Article Detection** - Identifies articles with events but no pipeline execution
- ✅ **Feed-Level Health Metrics** - Processing rates per feed
- ✅ **Processing Gap Analysis** - Detects time periods with low processing rates
- ✅ **Backfill Operations** - Republish events for reprocessing
- ✅ **Hourly Statistics** - Breakdown of processing performance
- ✅ **Automated Logging** - Background task logs unprocessed articles every hour

---

## Endpoints

### 1. Get Unprocessed Articles

Retrieves articles that have published `article.created` events but no corresponding pipeline execution.

**Endpoint:** `GET /api/v1/monitoring/unprocessed-articles`

**Parameters:**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `hours` | int | 7 | 1-168 | Lookback period in hours |
| `limit` | int | 100 | 1-1000 | Maximum articles to return |

**Example Request:**
```bash
curl "http://localhost:8114/api/v1/monitoring/unprocessed-articles?hours=7&limit=100"
```

**Response:**
```json
{
  "total_unprocessed": 5,
  "time_range": {
    "from": "2025-10-29T22:59:14.141373",
    "to": "2025-10-30T05:59:14.150860",
    "hours": 7
  },
  "articles": [
    {
      "event_id": "466bbc51-5580-4f28-b4ac-4bbdc0843e1d",
      "article_id": "a1cc0cd4-5ef5-4b77-9a32-a3280f83453d",
      "title": "Example Article",
      "feed_id": "0e0840d8-2526-4ba9-a926-f568331f2616",
      "feed_name": "ABC News Australia",
      "feed_url": "https://www.abc.net.au/news/feed/51120/rss.xml",
      "event_created": "2025-10-30T05:58:05.282005+00:00",
      "event_published": "2025-10-30T05:58:07.052215+00:00",
      "age_hours": "0.02"
    }
  ],
  "hourly_statistics": [
    {
      "hour": "2025-10-30T05:00:00+00:00",
      "total_events": 56,
      "processed_events": 37,
      "unprocessed_events": 19,
      "processing_rate": 66.07
    }
  ]
}
```

**Use Cases:**
- Daily monitoring of pipeline health
- Detecting worker failures
- Identifying message routing issues
- Capacity planning

---

### 2. Get Feed Health

Analyzes processing health per feed, sorted by lowest processing rates.

**Endpoint:** `GET /api/v1/monitoring/feed-health`

**Parameters:**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `hours` | int | 24 | 1-168 | Lookback period in hours |

**Example Request:**
```bash
curl "http://localhost:8114/api/v1/monitoring/feed-health?hours=24"
```

**Response:**
```json
{
  "total_feeds": 5,
  "time_range": {
    "from": "2025-10-29T22:59:14.141373",
    "to": "2025-10-30T05:59:14.150860"
  },
  "feeds": [
    {
      "feed_id": "0e0840d8-2526-4ba9-a926-f568331f2616",
      "feed_name": "ABC News Australia",
      "feed_url": "https://www.abc.net.au/news/feed/51120/rss.xml",
      "enable_analysis_v2": true,
      "total_events": 100,
      "processed_events": 85,
      "unprocessed_events": 15,
      "processing_rate": 85.0,
      "health": "good"
    }
  ]
}
```

**Health Status:**
- `good`: Processing rate ≥ 70%
- `warning`: Processing rate 50-70%
- `critical`: Processing rate < 50%

**Use Cases:**
- Identify problematic feeds
- Feed-level troubleshooting
- Quality monitoring

---

### 3. Get Processing Gaps

Identifies hourly time periods with processing rates below 70%.

**Endpoint:** `GET /api/v1/monitoring/processing-gaps`

**Parameters:**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `hours` | int | 24 | 1-168 | Lookback period in hours |

**Example Request:**
```bash
curl "http://localhost:8114/api/v1/monitoring/processing-gaps?hours=24"
```

**Response:**
```json
{
  "gaps_found": 2,
  "threshold_percentage": 70,
  "time_range": {
    "from": "2025-10-29T22:59:14.141373",
    "to": "2025-10-30T05:59:14.150860"
  },
  "gaps": [
    {
      "hour": "2025-10-29T23:00:00+00:00",
      "total_events": 45,
      "processed_events": 25,
      "processing_rate": 55.56,
      "severity": "warning"
    }
  ]
}
```

**Severity Levels:**
- `critical`: Processing rate < 50%
- `warning`: Processing rate 50-70%

**Use Cases:**
- Incident detection
- Performance degradation analysis
- Capacity planning

---

### 4. Trigger Backfill

Republishes events for unprocessed articles to RabbitMQ for reprocessing.

**Endpoint:** `POST /api/v1/monitoring/backfill`

**Parameters:**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `hours` | int | 7 | 1-168 | Lookback period in hours |
| `dry_run` | bool | true | - | Dry run mode (no actual republishing) |
| `limit` | int | 100 | 1-1000 | Maximum articles to backfill |

**Example Request (Dry Run):**
```bash
curl -X POST "http://localhost:8114/api/v1/monitoring/backfill?hours=7&dry_run=true&limit=100"
```

**Response (Dry Run):**
```json
{
  "dry_run": true,
  "total_articles": 5,
  "would_backfill": [
    "a1cc0cd4-5ef5-4b77-9a32-a3280f83453d",
    "ac626c54-123b-44ef-87b1-1a1ae7011270"
  ],
  "message": "Would republish 5 events (dry run mode)"
}
```

**Example Request (Actual Backfill):**
```bash
curl -X POST "http://localhost:8114/api/v1/monitoring/backfill?hours=7&dry_run=false&limit=100"
```

**Response (Actual Backfill):**
```json
{
  "dry_run": false,
  "total_articles": 5,
  "success": 5,
  "failed": 0,
  "message": "Backfilled 5 articles, 0 failed"
}
```

**⚠️ Important:**
- Always test with `dry_run=true` first
- Limit backfill to 100-500 articles at a time
- Monitor DLQ after backfill operations
- Perform backfills during low-traffic periods

**Use Cases:**
- Recovery from worker outages
- Reprocessing after bug fixes
- Manual intervention for stuck articles

---

## Database Schema

### Tables Used

#### event_outbox
Published events from the feed service.

```sql
CREATE TABLE event_outbox (
    id UUID PRIMARY KEY,
    event_type VARCHAR NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL,
    published_at TIMESTAMP
);
```

#### content_analysis_v2.pipeline_executions
Completed pipeline executions.

```sql
CREATE TABLE content_analysis_v2.pipeline_executions (
    id UUID PRIMARY KEY,
    article_id UUID NOT NULL,
    status VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP
);
```

#### feeds
Feed metadata.

```sql
CREATE TABLE feeds (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    url VARCHAR NOT NULL,
    enable_analysis_v2 BOOLEAN DEFAULT false
);
```

### Key Query Logic

**Finding Unprocessed Articles:**
```sql
SELECT *
FROM event_outbox eo
LEFT JOIN content_analysis_v2.pipeline_executions pe
  ON (eo.payload->>'item_id')::uuid = pe.article_id
WHERE eo.event_type = 'article.created'
  AND eo.published_at IS NOT NULL
  AND pe.id IS NULL  -- No pipeline execution found
  AND eo.created_at >= NOW() - INTERVAL '7 hours'
```

**Calculating Hourly Statistics:**
```sql
SELECT
    DATE_TRUNC('hour', eo.created_at) as hour,
    COUNT(eo.id) as total_events,
    COUNT(pe.id) as processed_events,
    ROUND(100.0 * COUNT(pe.id) / NULLIF(COUNT(eo.id), 0), 2) as processing_rate
FROM event_outbox eo
LEFT JOIN content_analysis_v2.pipeline_executions pe
  ON (eo.payload->>'item_id')::uuid = pe.article_id
WHERE eo.created_at >= NOW() - INTERVAL '7 hours'
  AND eo.event_type = 'article.created'
  AND eo.published_at IS NOT NULL
GROUP BY DATE_TRUNC('hour', eo.created_at)
ORDER BY hour DESC
```

---

## Frontend Integration

### Admin Dashboard

**URL:** `http://localhost:3000/admin/services/content-analysis`

**Tab:** "Monitoring"

**Components:**

1. **MonitoringPage** (`frontend/src/features/admin/content-analysis-v2/pages/MonitoringPage.tsx`)
   - Processing health overview
   - Unprocessed articles table
   - Feed health metrics
   - Processing gaps
   - Backfill controls

2. **API Client** (`frontend/src/lib/api/contentAnalysisV2Admin.ts`)
   - Type-safe API client methods
   - React Query integration
   - Auto-refresh configuration

**Auto-Refresh:**
- Interval: 30 seconds
- Configurable lookback period: 1h, 7h, 24h, 7d

---

## Automated Monitoring

### Background Logger

**File:** `app/tasks/monitoring_logger.py`

**Schedule:** Every 1 hour

**Configuration:**
```python
monitoring_logger = MonitoringLogger(
    interval_hours=1,  # Check frequency
    lookback_hours=7   # Analysis period
)
```

**Log Output:**
```
⚠️  5 UNPROCESSED ARTICLES in last 7h
📊 Breakdown by feed:
  • ABC News Australia: 2 unprocessed
  • DW English: 2 unprocessed
📈 Processing statistics:
  • Total events: 311
  • Processed: 306 (98.4%)
  • Unprocessed: 5 (1.6%)
⏰ Oldest unprocessed articles:
  • [0.09h old] Centrists and far-right level in tight Dutch election
📋 Unprocessed article IDs: ['a1cc0cd4-...', ...]
```

**Startup:**
```python
# In app/api/main.py
@app.on_event("startup")
async def startup_event():
    monitoring_logger = get_monitoring_logger()
    await monitoring_logger.start()

@app.on_event("shutdown")
async def shutdown_event():
    monitoring_logger = get_monitoring_logger()
    await monitoring_logger.stop()
```

---

## Error Handling

### Common Errors

**500 Internal Server Error**
```json
{
  "detail": "Failed to get unprocessed articles: connection timeout"
}
```

**Causes:**
- Database connection issues
- Invalid SQL queries
- Timeout errors

**Solution:**
- Check database connectivity
- Review query parameters
- Check service logs

---

## Monitoring Best Practices

### 1. Regular Checks
- Review monitoring dashboard daily
- Check automated logs hourly
- Investigate processing rates < 70%

### 2. Backfill Strategy
- **Always** use Dry Run first
- Perform during low-traffic periods
- Limit to 100-500 articles per operation
- Monitor DLQ after backfilling
- Check worker logs for errors

### 3. Alert Thresholds
- **Critical:** Processing rate < 50%
- **Warning:** Processing rate 50-70%
- **Good:** Processing rate ≥ 70%

### 4. Troubleshooting Steps

**High unprocessed count:**
1. Check worker container status
2. Review RabbitMQ queue depth
3. Check database connections
4. Review worker capacity
5. Check for errors in logs

**Specific feed issues:**
1. Check feed configuration
2. Review feed content format
3. Check for parsing errors
4. Verify `enable_analysis_v2` flag

**Processing gaps:**
1. Identify time period
2. Check worker logs for that period
3. Review system metrics (CPU, memory)
4. Check for deployments or restarts

---

## Performance Considerations

### Query Performance

**Indexes Required:**
```sql
-- event_outbox
CREATE INDEX idx_event_outbox_created_at ON event_outbox(created_at);
CREATE INDEX idx_event_outbox_event_type ON event_outbox(event_type);
CREATE INDEX idx_event_outbox_published_at ON event_outbox(published_at);
CREATE INDEX idx_event_outbox_payload_item_id ON event_outbox USING GIN ((payload->'item_id'));

-- pipeline_executions
CREATE INDEX idx_pipeline_executions_article_id ON content_analysis_v2.pipeline_executions(article_id);
CREATE INDEX idx_pipeline_executions_created_at ON content_analysis_v2.pipeline_executions(created_at);
```

### Rate Limiting

The API has no built-in rate limiting. Recommended usage:
- Frontend: Auto-refresh every 30 seconds
- Automated monitoring: Check every 1 hour
- Manual queries: As needed

### Response Size

- Unprocessed articles: Limited by `limit` parameter (default 100, max 1000)
- Feed health: Limited to 20 feeds
- Processing gaps: All gaps in time range (typically < 50 entries)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-30 | Initial release with 4 endpoints, frontend dashboard, and automated logging |

---

## See Also

- [Content Analysis V2 Service Documentation](../services/content-analysis-v2.md)
- [Pipeline Logic Documentation](../services/content-analysis-v2-pipeline-logic.md)
- [Frontend Admin Dashboard](../services/content-analysis-admin-dashboard.md)

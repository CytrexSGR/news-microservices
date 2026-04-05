# OSINT Service API

**Base URL:** `http://localhost:8104`

**Authentication:** Required - Bearer token (JWT) via `/api/v1/auth/login`

**API Prefix:** `/api/v1`

## Overview

Open Source Intelligence (OSINT) monitoring API providing 50+ pre-built intelligence templates, automated scheduling with APScheduler, z-score anomaly detection, and multi-level alerting for comprehensive threat intelligence collection and monitoring.

**Key Features:**
- 50+ YAML-based OSINT templates (social media, domain analysis, threat intel)
- APScheduler integration for automated periodic execution
- Statistical anomaly detection using z-score analysis
- Multi-level alerting system (info, warning, critical, emergency)
- Template validation and hot-reload capabilities

---

## Template Management

### GET /api/v1/templates/

List all available OSINT templates.

**Authentication:** Required

**Query Parameters:**
- `category` (string, optional): Filter by category (e.g., "social_media", "domain_analysis")
- `search` (string, optional): Search templates by name or description

**Response:** `200 OK`
```json
{
  "templates": [
    {
      "name": "twitter_monitoring",
      "category": "social_media",
      "description": "Monitor Twitter accounts and hashtags",
      "parameters": {
        "account": {"type": "string", "required": true},
        "keywords": {"type": "array", "required": false}
      },
      "schedule": {
        "type": "interval",
        "interval": "15m"
      },
      "metrics": ["follower_count", "tweet_count", "engagement_rate"],
      "alert_rules": [
        {
          "metric": "follower_count",
          "condition": "change_percent > 50",
          "level": "warning"
        }
      ]
    }
  ],
  "count": 52
}
```

**With Search:**
```json
{
  "templates": [...],
  "count": 5,
  "query": "twitter"
}
```

**With Category:**
```json
{
  "templates": [...],
  "category": "social_media",
  "count": 12
}
```

**Usage:**
```bash
# List all templates
curl http://localhost:8104/api/v1/templates/ \
  -H "Authorization: Bearer $TOKEN"

# Filter by category
curl "http://localhost:8104/api/v1/templates/?category=social_media" \
  -H "Authorization: Bearer $TOKEN"

# Search templates
curl "http://localhost:8104/api/v1/templates/?search=twitter" \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /api/v1/templates/categories

List all template categories.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "categories": [
    "social_media",
    "domain_analysis",
    "threat_intelligence",
    "dark_web",
    "cryptocurrency",
    "data_breach",
    "network_monitoring",
    "credential_monitoring",
    "brand_protection"
  ],
  "count": 9
}
```

**Usage:**
```bash
curl http://localhost:8104/api/v1/templates/categories \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /api/v1/templates/{template_name}

Get a specific template by name.

**Authentication:** Required

**Path Parameters:**
- `template_name` (string): Template identifier (e.g., "twitter_monitoring")

**Response:** `200 OK`
```json
{
  "name": "whois_monitoring",
  "category": "domain_analysis",
  "description": "Monitor WHOIS records for domain changes",
  "version": "1.0",
  "author": "OSINT Team",
  "parameters": {
    "domain": {
      "type": "string",
      "required": true,
      "description": "Domain name to monitor"
    },
    "notify_on_change": {
      "type": "boolean",
      "required": false,
      "default": true
    }
  },
  "schedule": {
    "type": "interval",
    "interval": "24h"
  },
  "metrics": [
    "registrar",
    "expiration_date",
    "name_servers",
    "registrant_email"
  ],
  "alert_rules": [
    {
      "metric": "registrar",
      "condition": "changed",
      "level": "critical",
      "message": "Domain registrar changed"
    }
  ],
  "execution": {
    "timeout": 60,
    "max_retries": 3
  }
}
```

**Error Responses:**
- `404 Not Found` - Template does not exist

**Usage:**
```bash
curl http://localhost:8104/api/v1/templates/whois_monitoring \
  -H "Authorization: Bearer $TOKEN"
```

---

### POST /api/v1/templates/reload

Reload all templates from disk.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "message": "Templates reloaded",
  "count": 52
}
```

**Usage:**
```bash
curl -X POST http://localhost:8104/api/v1/templates/reload \
  -H "Authorization: Bearer $TOKEN"
```

**Use Case:** After modifying template YAML files, reload them without restarting the service.

---

### POST /api/v1/templates/validate

Validate a template configuration.

**Authentication:** Required

**Request Body:**
```json
{
  "name": "custom_monitoring",
  "category": "custom",
  "description": "Custom OSINT template",
  "parameters": {
    "target": {
      "type": "string",
      "required": true
    }
  },
  "metrics": ["metric1", "metric2"],
  "alert_rules": [
    {
      "metric": "metric1",
      "condition": "value > 100",
      "level": "warning"
    }
  ]
}
```

**Response:** `200 OK`
```json
{
  "valid": true,
  "errors": []
}
```

**Validation Failed:**
```json
{
  "valid": false,
  "errors": [
    "Missing required field: name",
    "Invalid alert level: must be one of info, warning, critical, emergency",
    "Metric 'unknown_metric' not defined in template"
  ]
}
```

**Usage:**
```bash
curl -X POST http://localhost:8104/api/v1/templates/validate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"test","category":"custom","metrics":[]}'
```

---

## Schedule Management

### POST /api/v1/schedules/

Schedule a template for periodic execution.

**Authentication:** Required

**Request Body:**
```json
{
  "template_name": "twitter_monitoring",
  "parameters": {
    "account": "@example",
    "keywords": ["security", "breach"]
  },
  "trigger_type": "interval",
  "interval": "15m"
}
```

**Trigger Types:**

**Interval Trigger:**
```json
{
  "template_name": "domain_monitoring",
  "parameters": {"domain": "example.com"},
  "trigger_type": "interval",
  "interval": "1h"
}
```

**Interval Formats:**
- `"5m"` - 5 minutes
- `"1h"` - 1 hour
- `"24h"` - 24 hours

**Cron Trigger:**
```json
{
  "template_name": "daily_report",
  "parameters": {...},
  "trigger_type": "cron",
  "cron_minute": "0",
  "cron_hour": "9",
  "cron_day": "*",
  "cron_month": "*",
  "cron_day_of_week": "1-5"
}
```

**Cron Fields:**
- `cron_minute` - Minute (0-59)
- `cron_hour` - Hour (0-23)
- `cron_day` - Day of month (1-31)
- `cron_month` - Month (1-12)
- `cron_day_of_week` - Day of week (0-6, Monday=0)

**Response:** `200 OK`
```json
{
  "message": "Template scheduled successfully",
  "job_id": "twitter_monitoring_scheduled",
  "job_info": {
    "id": "twitter_monitoring_scheduled",
    "trigger": "interval[0:15:00]",
    "next_run_time": "2025-01-19T10:15:00Z",
    "executor": "default"
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid parameters or missing interval/cron fields
- `404 Not Found` - Template not found

**Usage:**
```bash
# Interval schedule
curl -X POST http://localhost:8104/api/v1/schedules/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "whois_monitoring",
    "parameters": {"domain": "example.com"},
    "trigger_type": "interval",
    "interval": "24h"
  }'

# Cron schedule (daily at 9 AM on weekdays)
curl -X POST http://localhost:8104/api/v1/schedules/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "security_report",
    "parameters": {},
    "trigger_type": "cron",
    "cron_minute": "0",
    "cron_hour": "9",
    "cron_day_of_week": "1-5"
  }'
```

---

### GET /api/v1/schedules/

List all scheduled jobs.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "schedules": [
    {
      "id": "twitter_monitoring_scheduled",
      "name": "twitter_monitoring",
      "trigger": "interval[0:15:00]",
      "next_run_time": "2025-01-19T10:15:00Z",
      "executor": "default",
      "pending": false
    },
    {
      "id": "whois_monitoring_scheduled",
      "name": "whois_monitoring",
      "trigger": "interval[1 day, 0:00:00]",
      "next_run_time": "2025-01-20T08:00:00Z",
      "executor": "default",
      "pending": false
    }
  ],
  "count": 2
}
```

**Usage:**
```bash
curl http://localhost:8104/api/v1/schedules/ \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /api/v1/schedules/{job_id}

Get information about a scheduled job.

**Authentication:** Required

**Path Parameters:**
- `job_id` (string): Job identifier

**Response:** `200 OK`
```json
{
  "id": "twitter_monitoring_scheduled",
  "name": "twitter_monitoring",
  "trigger": "interval[0:15:00]",
  "next_run_time": "2025-01-19T10:15:00Z",
  "executor": "default",
  "pending": false,
  "misfire_grace_time": 60,
  "max_instances": 1,
  "coalesce": true
}
```

**Error Responses:**
- `404 Not Found` - Job not found

**Usage:**
```bash
curl http://localhost:8104/api/v1/schedules/twitter_monitoring_scheduled \
  -H "Authorization: Bearer $TOKEN"
```

---

### DELETE /api/v1/schedules/{job_id}

Delete a scheduled job.

**Authentication:** Required

**Path Parameters:**
- `job_id` (string): Job identifier

**Response:** `200 OK`
```json
{
  "message": "Schedule deleted successfully",
  "job_id": "twitter_monitoring_scheduled"
}
```

**Error Responses:**
- `404 Not Found` - Job not found

**Usage:**
```bash
curl -X DELETE http://localhost:8104/api/v1/schedules/twitter_monitoring_scheduled \
  -H "Authorization: Bearer $TOKEN"
```

---

### POST /api/v1/schedules/{job_id}/pause

Pause a scheduled job.

**Authentication:** Required

**Path Parameters:**
- `job_id` (string): Job identifier

**Response:** `200 OK`
```json
{
  "message": "Schedule paused",
  "job_id": "twitter_monitoring_scheduled"
}
```

**Error Responses:**
- `404 Not Found` - Job not found

**Usage:**
```bash
curl -X POST http://localhost:8104/api/v1/schedules/twitter_monitoring_scheduled/pause \
  -H "Authorization: Bearer $TOKEN"
```

---

### POST /api/v1/schedules/{job_id}/resume

Resume a paused job.

**Authentication:** Required

**Path Parameters:**
- `job_id` (string): Job identifier

**Response:** `200 OK`
```json
{
  "message": "Schedule resumed",
  "job_id": "twitter_monitoring_scheduled"
}
```

**Error Responses:**
- `404 Not Found` - Job not found

**Usage:**
```bash
curl -X POST http://localhost:8104/api/v1/schedules/twitter_monitoring_scheduled/resume \
  -H "Authorization: Bearer $TOKEN"
```

---

## Anomaly Detection

### GET /api/v1/anomalies/baselines

Get baseline statistics for anomaly detection.

**Authentication:** Required

**Query Parameters:**
- `template_name` (string, optional): Filter by specific template

**Response (All Templates):** `200 OK`
```json
{
  "templates": [
    {
      "template_name": "twitter_monitoring",
      "metrics": [
        {
          "metric_name": "follower_count",
          "baseline": {
            "mean": 15234.5,
            "std_dev": 523.2,
            "min": 14200,
            "max": 16800,
            "sample_count": 120,
            "last_updated": "2025-01-19T10:00:00Z"
          }
        }
      ]
    }
  ],
  "count": 8
}
```

**Response (Specific Template):** `200 OK`
```json
{
  "template_name": "twitter_monitoring",
  "baselines": [
    {
      "metric_name": "follower_count",
      "mean": 15234.5,
      "std_dev": 523.2,
      "min": 14200,
      "max": 16800,
      "sample_count": 120,
      "z_score_threshold": 3.0,
      "last_updated": "2025-01-19T10:00:00Z"
    },
    {
      "metric_name": "engagement_rate",
      "mean": 0.045,
      "std_dev": 0.008,
      "min": 0.028,
      "max": 0.067,
      "sample_count": 120,
      "z_score_threshold": 3.0,
      "last_updated": "2025-01-19T10:00:00Z"
    }
  ]
}
```

**Error Responses:**
- `404 Not Found` - No baseline data found for template

**Usage:**
```bash
# List all baselines
curl http://localhost:8104/api/v1/anomalies/baselines \
  -H "Authorization: Bearer $TOKEN"

# Get template baselines
curl "http://localhost:8104/api/v1/anomalies/baselines?template_name=twitter_monitoring" \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /api/v1/anomalies/baselines/{template_name}/{metric_name}

Get baseline statistics for a specific metric.

**Authentication:** Required

**Path Parameters:**
- `template_name` (string): Template identifier
- `metric_name` (string): Metric identifier

**Response:** `200 OK`
```json
{
  "template_name": "twitter_monitoring",
  "metric_name": "follower_count",
  "mean": 15234.5,
  "std_dev": 523.2,
  "min": 14200,
  "max": 16800,
  "sample_count": 120,
  "z_score_threshold": 3.0,
  "confidence_level": 0.997,
  "last_updated": "2025-01-19T10:00:00Z",
  "calculation_window": "30d"
}
```

**Error Responses:**
- `404 Not Found` - Baseline not found

**Usage:**
```bash
curl http://localhost:8104/api/v1/anomalies/baselines/twitter_monitoring/follower_count \
  -H "Authorization: Bearer $TOKEN"
```

---

### DELETE /api/v1/anomalies/baselines/{template_name}

Reset baseline data for a template or specific metric.

**Authentication:** Required

**Path Parameters:**
- `template_name` (string): Template identifier

**Query Parameters:**
- `metric_name` (string, optional): Specific metric to reset (if omitted, resets all metrics)

**Response:** `200 OK`
```json
{
  "message": "Baseline reset successfully",
  "template_name": "twitter_monitoring",
  "metric_name": null
}
```

**Usage:**
```bash
# Reset all metrics for template
curl -X DELETE http://localhost:8104/api/v1/anomalies/baselines/twitter_monitoring \
  -H "Authorization: Bearer $TOKEN"

# Reset specific metric
curl -X DELETE "http://localhost:8104/api/v1/anomalies/baselines/twitter_monitoring?metric_name=follower_count" \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /api/v1/anomalies/tracked

Get list of all tracked metrics.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "tracked_metrics": [
    {
      "template_name": "twitter_monitoring",
      "metrics": ["follower_count", "tweet_count", "engagement_rate"]
    },
    {
      "template_name": "whois_monitoring",
      "metrics": ["registrar", "name_servers"]
    }
  ],
  "template_count": 2
}
```

**Usage:**
```bash
curl http://localhost:8104/api/v1/anomalies/tracked \
  -H "Authorization: Bearer $TOKEN"
```

---

## Alert Management

### GET /api/v1/alerts/

List alerts with optional filters.

**Authentication:** Required

**Query Parameters:**
- `level` (string, optional): Filter by alert level (info, warning, critical, emergency)
- `acknowledged` (boolean, optional): Filter by acknowledgement status
- `limit` (int, optional): Maximum alerts to return (1-1000, default: 100)

**Response:** `200 OK`
```json
{
  "alerts": [
    {
      "id": "alert_12345",
      "template_name": "twitter_monitoring",
      "level": "warning",
      "title": "Follower count spike detected",
      "message": "Follower count increased by 78% (z-score: 3.5)",
      "metric": "follower_count",
      "current_value": 27120,
      "baseline_mean": 15234.5,
      "z_score": 3.5,
      "acknowledged": false,
      "created_at": "2025-01-19T09:45:00Z",
      "acknowledged_at": null,
      "acknowledged_by": null
    },
    {
      "id": "alert_12344",
      "template_name": "whois_monitoring",
      "level": "critical",
      "title": "Domain registrar changed",
      "message": "Registrar changed from GoDaddy to Namecheap",
      "metric": "registrar",
      "current_value": "Namecheap",
      "previous_value": "GoDaddy",
      "acknowledged": true,
      "created_at": "2025-01-19T08:30:00Z",
      "acknowledged_at": "2025-01-19T08:45:00Z",
      "acknowledged_by": "user_uuid"
    }
  ],
  "count": 2
}
```

**Alert Levels:**
- `info` - Informational, no action required
- `warning` - Potential issue, review recommended
- `critical` - Significant issue, immediate attention required
- `emergency` - Severe issue, urgent action required

**Usage:**
```bash
# List all alerts
curl http://localhost:8104/api/v1/alerts/ \
  -H "Authorization: Bearer $TOKEN"

# Critical alerts only
curl "http://localhost:8104/api/v1/alerts/?level=critical" \
  -H "Authorization: Bearer $TOKEN"

# Unacknowledged alerts
curl "http://localhost:8104/api/v1/alerts/?acknowledged=false&limit=50" \
  -H "Authorization: Bearer $TOKEN"
```

**Error Responses:**
- `400 Bad Request` - Invalid alert level

---

### GET /api/v1/alerts/stats

Get alert statistics.

**Authentication:** Required

**Response:** `200 OK`
```json
{
  "total_alerts": 156,
  "by_level": {
    "info": 45,
    "warning": 78,
    "critical": 28,
    "emergency": 5
  },
  "acknowledged": 120,
  "unacknowledged": 36,
  "last_24h": 23,
  "last_7d": 67,
  "most_active_templates": [
    {
      "template_name": "twitter_monitoring",
      "alert_count": 34
    },
    {
      "template_name": "domain_monitoring",
      "alert_count": 28
    }
  ]
}
```

**Usage:**
```bash
curl http://localhost:8104/api/v1/alerts/stats \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /api/v1/alerts/{alert_id}

Get a specific alert by ID.

**Authentication:** Required

**Path Parameters:**
- `alert_id` (string): Alert identifier

**Response:** `200 OK`
```json
{
  "id": "alert_12345",
  "template_name": "twitter_monitoring",
  "execution_id": "exec_uuid",
  "level": "warning",
  "title": "Follower count spike detected",
  "message": "Follower count increased by 78% (z-score: 3.5)",
  "metric": "follower_count",
  "current_value": 27120,
  "baseline_mean": 15234.5,
  "baseline_std_dev": 523.2,
  "z_score": 3.5,
  "threshold": 3.0,
  "acknowledged": false,
  "created_at": "2025-01-19T09:45:00Z",
  "acknowledged_at": null,
  "acknowledged_by": null,
  "metadata": {
    "account": "@example",
    "change_percent": 78.0,
    "previous_check": "2025-01-19T09:30:00Z"
  }
}
```

**Error Responses:**
- `404 Not Found` - Alert not found

**Usage:**
```bash
curl http://localhost:8104/api/v1/alerts/alert_12345 \
  -H "Authorization: Bearer $TOKEN"
```

---

### POST /api/v1/alerts/{alert_id}/acknowledge

Acknowledge an alert.

**Authentication:** Required

**Path Parameters:**
- `alert_id` (string): Alert identifier

**Response:** `200 OK`
```json
{
  "message": "Alert acknowledged",
  "alert_id": "alert_12345"
}
```

**Error Responses:**
- `404 Not Found` - Alert not found

**Usage:**
```bash
curl -X POST http://localhost:8104/api/v1/alerts/alert_12345/acknowledge \
  -H "Authorization: Bearer $TOKEN"
```

---

## Health & Status

### GET /health

Basic health check.

**Authentication:** Not required

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "osint-service",
  "timestamp": "2025-01-19T10:00:00Z"
}
```

**Usage:**
```bash
curl http://localhost:8104/health
```

---

### GET /health/ready

Service readiness check.

**Authentication:** Not required

**Response:** `200 OK`
```json
{
  "ready": true,
  "checks": {
    "templates_loaded": true,
    "template_count": 52,
    "scheduler_running": true
  },
  "timestamp": "2025-01-19T10:00:00Z"
}
```

**Not Ready:**
```json
{
  "ready": false,
  "checks": {
    "templates_loaded": false,
    "template_count": 0,
    "scheduler_running": false
  },
  "timestamp": "2025-01-19T10:00:00Z"
}
```

**Usage:**
```bash
curl http://localhost:8104/health/ready
```

---

## Error Handling

All endpoints return standard HTTP status codes and error responses:

**400 Bad Request:**
```json
{
  "detail": "Interval required for interval trigger"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Invalid or expired token"
}
```

**404 Not Found:**
```json
{
  "detail": "Template not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Failed to schedule job: APScheduler error"
}
```

---

## Configuration

**Z-Score Threshold:** Configurable via `ANOMALY_Z_SCORE_THRESHOLD` (default: 3.0)
- Higher values = fewer anomalies detected
- Lower values = more sensitive detection

**Minimum Samples:** Configurable via `ANOMALY_MIN_SAMPLES` (default: 30)
- Minimum data points required before baseline calculation

**Baseline Window:** Configurable via `BASELINE_CALCULATION_WINDOW` (default: 30d)
- Time window for statistical baseline calculation

**Scheduler Max Instances:** Configurable via `SCHEDULER_MAX_INSTANCES` (default: 50)
- Maximum concurrent scheduled jobs

---

## Related Documentation

- [Service Documentation](../services/osint-service.md)
- [Configuration Reference](./osint-service-config.md)
- [Deployment Guide](../guides/DEPLOYMENT_GUIDE.md)

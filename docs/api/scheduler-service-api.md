# Scheduler Service API

Base path: `/api/v1/scheduler`  
Default port: `8108`

Authentication:
- Endpoints labeled **Service Auth** require `X-Service-Key` and `X-Service-Name` headers.
- Public endpoints only require standard JWT/user context if front-end features are added (current implementation uses service-level access).

---

## GET /api/v1/scheduler/status
**Description:** Returns component status for feed monitor, job processor, cron scheduler, and queue counts.

### Response
| Field | Type | Description |
| --- | --- | --- |
| `feed_monitor.is_running` | boolean | Feed monitor scheduler state |
| `feed_monitor.check_interval_seconds` | integer | Polling interval in seconds |
| `job_processor.is_running` | boolean | Job processor scheduler state |
| `job_processor.process_interval_seconds` | integer | Job polling interval |
| `job_processor.max_concurrent_jobs` | integer | Jobs processed per cycle |
| `cron_scheduler.is_running` | boolean | Cron scheduler state |
| `cron_scheduler.total_jobs` | integer | Registered cron jobs |
| `cron_scheduler.running_jobs` | integer | Active APScheduler jobs |
| `queue.pending_jobs` | integer | Count of pending jobs |
| `queue.processing_jobs` | integer | Count of processing jobs |

#### Example
```json
{
  "feed_monitor": {"is_running": true, "check_interval_seconds": 60},
  "job_processor": {"is_running": true, "process_interval_seconds": 30, "max_concurrent_jobs": 5},
  "cron_scheduler": {"is_running": true, "total_jobs": 2, "running_jobs": 2},
  "queue": {"pending_jobs": 48, "processing_jobs": 3}
}
```

---

## GET /api/v1/scheduler/jobs/stats
**Description:** Returns aggregate job metrics.

### Response
| Field | Type | Description |
| --- | --- | --- |
| `total_pending` | integer | Jobs waiting to run |
| `total_processing` | integer | Jobs in progress |
| `total_completed` | integer | Completed job count |
| `total_failed` | integer | Failed job count |
| `by_type` | object | Map of `job_type` → count |

---

## GET /api/v1/scheduler/jobs
**Description:** Paginated job listing with optional status filter.

### Query Parameters
| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `status` | string | No | `pending`, `processing`, `completed`, or `failed` |
| `limit` | integer | No | Maximum jobs to return (default 50) |
| `offset` | integer | No | Records to skip |

### Response
| Field | Type | Description |
| --- | --- | --- |
| `total` | integer | Total matching jobs |
| `limit` | integer | Limit used |
| `offset` | integer | Offset used |
| `jobs[]` | array | Ordered job list |

#### `jobs[]` item
| Field | Type | Description |
| --- | --- | --- |
| `id` | string (uuid) | Job identifier |
| `article_id` | string (uuid) | Article associated with job |
| `job_type` | string | Job type (`categorization`, `finance_sentiment`, `geopolitical_sentiment`, `standard_sentiment`, `osint_analysis`) |
| `status` | string | Job status |
| `priority` | integer | Priority score (1–10) |
| `retry_count` | integer | Retries attempted |
| `created_at` | string (ISO 8601) | Creation timestamp |
| `started_at` | string (ISO 8601 \| null) | Processing start timestamp |
| `completed_at` | string (ISO 8601 \| null) | Completion timestamp |
| `error_message` | string \| null | Last failure reason |

---

## POST /api/v1/scheduler/jobs/{job_id}/retry
**Description:** Reset a failed job back to `pending`.  
**Authentication:** **Service Auth**

### Path Parameters
| Name | Type | Description |
| --- | --- | --- |
| `job_id` | string (uuid) | Job to retry |

### Responses
| Status | Description |
| --- | --- |
| 200 | Job reset for retry |
| 400 | Job is not in failed status |
| 401 | Missing or invalid service API key |
| 404 | Job not found |

#### Example
```json
{
  "status": "success",
  "message": "Job 7f7c... reset for retry",
  "job": {"id": "7f7c...", "status": "pending"}
}
```

---

## POST /api/v1/scheduler/jobs/{job_id}/cancel
**Description:** Cancel a pending or processing job. Marks the job as failed with cancellation metadata.  
**Authentication:** **Service Auth**

### Path Parameters
| Name | Type | Description |
| --- | --- | --- |
| `job_id` | string (uuid) | Job to cancel |

### Responses
| Status | Description |
| --- | --- |
| 200 | Job cancelled |
| 400 | Job not cancellable |
| 401 | Missing or invalid service API key |
| 404 | Job not found |

---

## POST /api/v1/scheduler/feeds/{feed_id}/check
**Description:** Schedule an immediate feed check for a feed UUID.  
**Authentication:** **Service Auth**

### Path Parameters
| Name | Type | Description |
| --- | --- | --- |
| `feed_id` | string (uuid) | Feed identifier |

### Responses
| Status | Description |
| --- | --- |
| 200 | Feed check scheduled |
| 401 | Missing or invalid service API key |

#### Example
```json
{
  "status": "triggered",
  "feed_id": "5a7b...",
  "message": "Feed check scheduled"
}
```

---

## GET /api/v1/scheduler/cron/jobs
**Description:** List cron and interval jobs registered with APScheduler.

### Response
| Field | Type | Description |
| --- | --- | --- |
| `total` | integer | Number of registered cron jobs |
| `jobs[]` | array | Job metadata |

#### `jobs[]` item
| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Job identifier |
| `name` | string | Job name |
| `next_run_time` | string \| null | Next scheduled run (ISO 8601) |
| `trigger` | string | APScheduler trigger description |
| `pending` | boolean | Whether job is pending execution |

---

## POST /api/v1/scheduler/internal/health/service
**Description:** Service-to-service health probe returning authentication result.  
**Authentication:** **Service Auth**

### Response
| Field | Type | Description |
| --- | --- | --- |
| `status` | string | Always `"healthy"` |
| `authenticated_service` | string | Service resolved from API key |
| `internal_api` | string | Always `"operational"` |

---

## Error Reference

| Status | Meaning | Typical Causes |
| --- | --- | --- |
| 400 | Bad Request | Invalid job status, cancelling completed job |
| 401 | Unauthorized | Missing or incorrect `X-Service-Key` header |
| 404 | Not Found | Unknown job ID |
| 500 | Internal Error | Downstream Content Analysis request failed |

---

**Generated:** 2025-01-19  
**Maintainer:** Scheduler Platform Team

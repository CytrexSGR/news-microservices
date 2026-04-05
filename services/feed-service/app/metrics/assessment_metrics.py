"""
Prometheus metrics for feed assessment operations.

Tracks:
- Assessment request counts (total, success, failure)
- Assessment duration
- Response time from research service
- Validation errors
"""

from prometheus_client import Counter, Histogram, Gauge

# Assessment request counters
assessment_requests_total = Counter(
    'feed_assessment_requests_total',
    'Total number of feed assessment requests',
    ['status']  # labels: success, failed, timeout, validation_error
)

assessment_duration_seconds = Histogram(
    'feed_assessment_duration_seconds',
    'Time taken to complete feed assessment',
    buckets=[1, 2, 5, 10, 30, 60, 120, 300]  # seconds
)

research_service_response_time_seconds = Histogram(
    'feed_assessment_research_service_response_seconds',
    'Time taken for research service to complete analysis',
    buckets=[0.5, 1, 2, 5, 10, 30, 60]  # seconds
)

# Validation error counter
validation_errors_total = Counter(
    'feed_assessment_validation_errors_total',
    'Total number of validation errors during assessment',
    ['error_type']  # labels: none_task_result, invalid_type, missing_fields, invalid_status
)

# Active assessments gauge
active_assessments = Gauge(
    'feed_assessment_active_assessments',
    'Number of currently running assessments'
)

# Polling metrics
polling_iterations_total = Histogram(
    'feed_assessment_polling_iterations',
    'Number of polling iterations until task completion',
    buckets=[1, 2, 3, 5, 10, 15, 20, 30]
)

polling_wait_time_seconds = Histogram(
    'feed_assessment_polling_wait_time_seconds',
    'Total time spent polling for task completion',
    buckets=[1, 2, 3, 5, 10, 15, 20, 30]
)

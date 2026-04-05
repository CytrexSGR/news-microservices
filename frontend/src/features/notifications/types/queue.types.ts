/**
 * Queue Types
 *
 * Types for notification queue management including statistics,
 * dead letter queue, and admin operations.
 */

/**
 * Overall queue statistics
 */
export interface QueueStatistics {
  pending: QueueChannelStats;
  retrying: QueueChannelStats;
  dlq: DLQStats;
  processing_rate: ProcessingRate;
  last_updated: string;
}

/**
 * Statistics per channel
 */
export interface QueueChannelStats {
  total: number;
  by_channel: {
    email: number;
    webhook: number;
    push: number;
    rabbitmq: number;
  };
  oldest_item_age_seconds?: number;
}

/**
 * Dead Letter Queue statistics
 */
export interface DLQStats {
  total: number;
  by_error_type: Record<string, number>;
  oldest_item_age_seconds?: number;
}

/**
 * Processing rate metrics
 */
export interface ProcessingRate {
  last_hour: number;
  last_24h: number;
  success_rate_percent: number;
  average_processing_time_ms: number;
}

/**
 * Dead Letter Queue item
 */
export interface DLQItem {
  notification_id: number;
  user_id: string;
  channel: string;
  subject?: string;
  content: string;
  error_message: string;
  error_type: string;
  attempt_count: number;
  first_attempt_at: string;
  last_attempt_at: string;
  metadata?: Record<string, unknown>;
}

/**
 * DLQ list response
 */
export interface DLQListResponse {
  status: string;
  count: number;
  dlq_items: DLQItem[];
}

/**
 * Queue stats response from API
 */
export interface QueueStatsResponse {
  status: string;
  queue_stats: QueueStatistics;
}

/**
 * Retry DLQ item response
 */
export interface RetryDLQResponse {
  status: string;
  message: string;
  retry_info: {
    notification_id: number;
    requeued_at: string;
    new_status: string;
  };
}

/**
 * Rate limit information for a user
 */
export interface UserRateLimits {
  user_id: string;
  rate_limits: {
    email: RateLimitInfo;
    webhook: RateLimitInfo;
    push: RateLimitInfo;
  };
}

/**
 * Rate limit details per channel
 */
export interface RateLimitInfo {
  current_count: number;
  limit: number;
  reset_at: string;
  window_seconds: number;
  is_limited: boolean;
}

/**
 * Queue trend data point for charts
 */
export interface QueueTrendDataPoint {
  timestamp: string;
  pending: number;
  sent: number;
  failed: number;
  retrying: number;
}

/**
 * Queue health status
 */
export interface QueueHealthStatus {
  status: 'healthy' | 'degraded' | 'critical';
  issues: QueueHealthIssue[];
  recommendations: string[];
}

/**
 * Queue health issue
 */
export interface QueueHealthIssue {
  type: 'high_dlq' | 'slow_processing' | 'backlog' | 'high_failure_rate';
  severity: 'warning' | 'error';
  message: string;
  metric_value: number;
  threshold: number;
}

/**
 * Detailed health response (admin)
 */
export interface DetailedHealthResponse {
  status: string;
  service: string;
  version: string;
  jwt_rotation: {
    last_rotation: string;
    next_rotation: string;
    key_age_seconds: number;
  };
  delivery_queue: QueueStatistics;
  features: {
    jwt_rotation: boolean;
    rate_limiting: boolean;
    input_validation: boolean;
    delivery_retry: boolean;
    dead_letter_queue: boolean;
  };
}

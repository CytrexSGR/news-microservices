/**
 * Monitoring Feature Types
 *
 * TypeScript interfaces for comprehensive system monitoring.
 * Covers services, queues, databases, caches, and error logs.
 */

// =============================================================================
// Enums and Base Types
// =============================================================================

/**
 * Health status for services and infrastructure components
 */
export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';

/**
 * Type of service in the system
 */
export type ServiceType = 'api' | 'worker' | 'database' | 'queue' | 'cache';

/**
 * Log levels for error logs
 */
export type LogLevel = 'error' | 'warning' | 'critical';

/**
 * Database types supported
 */
export type DatabaseType = 'postgresql' | 'neo4j';

// =============================================================================
// System Health
// =============================================================================

/**
 * Overall system health status
 */
export interface SystemHealth {
  /** Current system health status */
  status: HealthStatus;
  /** Number of healthy services */
  services_healthy: number;
  /** Total number of services */
  services_total: number;
  /** System uptime in seconds */
  uptime_seconds: number;
  /** Last health check timestamp (ISO 8601) */
  last_check: string;
  /** List of current issues */
  issues: HealthIssue[];
}

/**
 * A health issue detected in the system
 */
export interface HealthIssue {
  /** Service name where issue occurred */
  service: string;
  /** Severity level */
  severity: 'warning' | 'critical';
  /** Human-readable message */
  message: string;
  /** When the issue started (ISO 8601) */
  since: string;
}

// =============================================================================
// Service Status
// =============================================================================

/**
 * Individual service status
 */
export interface ServiceStatus {
  /** Service name */
  name: string;
  /** Type of service */
  type: ServiceType;
  /** Current health status */
  status: HealthStatus;
  /** Service port number */
  port?: number;
  /** Service version */
  version?: string;
  /** Uptime in seconds */
  uptime_seconds?: number;
  /** Last health check timestamp (ISO 8601) */
  last_check: string;
  /** Optional metrics for the service */
  metrics?: ServiceMetrics;
  /** Service description */
  description?: string;
  /** Service endpoint URL */
  endpoint?: string;
  /** Docker container name */
  container_name?: string;
}

/**
 * Metrics for a service
 */
export interface ServiceMetrics {
  /** Requests per minute */
  requests_per_minute: number;
  /** Average response time in milliseconds */
  avg_response_time_ms: number;
  /** Error rate as percentage (0-100) */
  error_rate_percent: number;
  /** Memory usage in MB */
  memory_mb: number;
  /** CPU usage as percentage (0-100) */
  cpu_percent: number;
}

/**
 * Detailed metrics for a service (extended)
 */
export interface DetailedServiceMetrics extends ServiceMetrics {
  /** Total requests in last hour */
  requests_last_hour: number;
  /** Total errors in last hour */
  errors_last_hour: number;
  /** P50 latency in milliseconds */
  p50_latency_ms: number;
  /** P95 latency in milliseconds */
  p95_latency_ms: number;
  /** P99 latency in milliseconds */
  p99_latency_ms: number;
  /** Latency histogram data points */
  latency_histogram?: LatencyHistogramPoint[];
  /** Requests over time (last 24h) */
  requests_over_time?: TimeSeriesPoint[];
  /** Errors over time (last 24h) */
  errors_over_time?: TimeSeriesPoint[];
}

/**
 * Time series data point
 */
export interface TimeSeriesPoint {
  /** Timestamp (ISO 8601) */
  timestamp: string;
  /** Value at this timestamp */
  value: number;
}

/**
 * Latency histogram data point
 */
export interface LatencyHistogramPoint {
  /** Bucket range (e.g., "0-10ms") */
  bucket: string;
  /** Count of requests in this bucket */
  count: number;
}

// =============================================================================
// Error Logs
// =============================================================================

/**
 * Error log entry
 */
export interface ErrorLog {
  /** Unique log ID */
  id: string;
  /** Service that produced the error */
  service: string;
  /** Log level */
  level: LogLevel;
  /** Error message */
  message: string;
  /** Stack trace (if available) */
  stack_trace?: string;
  /** Timestamp of the error (ISO 8601) */
  timestamp: string;
  /** Number of occurrences of this error */
  count: number;
  /** First occurrence timestamp */
  first_seen?: string;
  /** Last occurrence timestamp */
  last_seen?: string;
  /** Additional context */
  context?: Record<string, unknown>;
}

/**
 * Error log filter options
 */
export interface ErrorLogFilters {
  /** Filter by service name */
  service?: string;
  /** Filter by log level */
  level?: LogLevel;
  /** Start time for filtering */
  start_time?: string;
  /** End time for filtering */
  end_time?: string;
  /** Limit number of results */
  limit?: number;
  /** Offset for pagination */
  offset?: number;
}

// =============================================================================
// Performance Metrics
// =============================================================================

/**
 * System-wide performance metrics
 */
export interface PerformanceMetrics {
  /** Overall system latency (avg) in ms */
  avg_latency_ms: number;
  /** Total requests per second across all services */
  total_rps: number;
  /** Total error rate as percentage */
  total_error_rate_percent: number;
  /** Total memory usage in MB */
  total_memory_mb: number;
  /** Total CPU usage as percentage */
  total_cpu_percent: number;
  /** Performance by service */
  services: ServicePerformance[];
  /** Performance trends */
  trends: PerformanceTrends;
  /** Last updated timestamp */
  last_updated: string;
}

/**
 * Performance data for a single service
 */
export interface ServicePerformance {
  /** Service name */
  name: string;
  /** Average latency in ms */
  avg_latency_ms: number;
  /** Requests per second */
  rps: number;
  /** Error rate percentage */
  error_rate_percent: number;
  /** Status indicator */
  status: HealthStatus;
}

/**
 * Performance trends over time
 */
export interface PerformanceTrends {
  /** Latency trend (positive = increasing, negative = decreasing) */
  latency_trend: number;
  /** RPS trend */
  rps_trend: number;
  /** Error rate trend */
  error_rate_trend: number;
  /** Time period for trend calculation */
  period: string;
}

// =============================================================================
// Queue Health (RabbitMQ)
// =============================================================================

/**
 * RabbitMQ queue health information
 */
export interface QueueHealth {
  /** Queue name */
  name: string;
  /** Messages ready for delivery */
  messages_ready: number;
  /** Messages unacknowledged */
  messages_unacked: number;
  /** Number of consumers */
  consumers: number;
  /** Memory usage in MB */
  memory_mb: number;
  /** Queue health status */
  status: HealthStatus;
  /** Messages per second (publish rate) */
  publish_rate?: number;
  /** Messages per second (delivery rate) */
  deliver_rate?: number;
  /** Total messages in queue */
  total_messages?: number;
  /** Virtual host */
  vhost?: string;
}

/**
 * Overall queue system health
 */
export interface QueueSystemHealth {
  /** Overall status */
  status: HealthStatus;
  /** Total queues */
  total_queues: number;
  /** Healthy queues */
  healthy_queues: number;
  /** Total messages across all queues */
  total_messages: number;
  /** Total consumers */
  total_consumers: number;
  /** Total memory usage in MB */
  total_memory_mb: number;
  /** Individual queue health */
  queues: QueueHealth[];
  /** RabbitMQ version */
  version?: string;
  /** Uptime in seconds */
  uptime_seconds?: number;
  /** Last updated timestamp */
  last_updated: string;
}

// =============================================================================
// Database Stats
// =============================================================================

/**
 * Database statistics
 */
export interface DatabaseStats {
  /** Database type */
  type: DatabaseType;
  /** Display name */
  name: string;
  /** Active connections */
  connections_active: number;
  /** Maximum connections allowed */
  connections_max: number;
  /** Database size in GB */
  size_gb: number;
  /** Average query time in ms */
  query_avg_ms: number;
  /** Current health status */
  status: HealthStatus;
  /** Database version */
  version?: string;
  /** Uptime in seconds */
  uptime_seconds?: number;
  /** Connection pool utilization percentage */
  pool_utilization_percent?: number;
  /** Slow queries count (last hour) */
  slow_queries_count?: number;
  /** Last updated timestamp */
  last_updated: string;
}

/**
 * Overall database system health
 */
export interface DatabaseSystemHealth {
  /** Overall status */
  status: HealthStatus;
  /** PostgreSQL stats */
  postgresql: DatabaseStats | null;
  /** Neo4j stats */
  neo4j: DatabaseStats | null;
  /** Last updated timestamp */
  last_updated: string;
}

// =============================================================================
// Cache Stats (Redis)
// =============================================================================

/**
 * Redis cache statistics
 */
export interface CacheStats {
  /** Memory used in MB */
  memory_used_mb: number;
  /** Maximum memory in MB */
  memory_max_mb: number;
  /** Cache hit rate as percentage (0-100) */
  hit_rate_percent: number;
  /** Total number of keys */
  keys_count: number;
  /** Operations per second */
  operations_per_sec: number;
  /** Current health status */
  status: HealthStatus;
  /** Connected clients */
  connected_clients?: number;
  /** Total hits */
  total_hits?: number;
  /** Total misses */
  total_misses?: number;
  /** Memory fragmentation ratio */
  fragmentation_ratio?: number;
  /** Redis version */
  version?: string;
  /** Uptime in seconds */
  uptime_seconds?: number;
  /** Expired keys (last hour) */
  expired_keys?: number;
  /** Evicted keys (last hour) */
  evicted_keys?: number;
  /** Last updated timestamp */
  last_updated: string;
}

// =============================================================================
// API Response Types
// =============================================================================

/**
 * Generic API response wrapper
 */
export interface MonitoringApiResponse<T> {
  data?: T;
  error?: string;
}

/**
 * Paginated response for logs
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

// =============================================================================
// Component Props Types
// =============================================================================

/**
 * Props for SystemHealthCard component
 */
export interface SystemHealthCardProps {
  health: SystemHealth | null;
  isLoading: boolean;
  onRefresh?: () => void;
}

/**
 * Props for ServiceStatusCard component
 */
export interface ServiceStatusCardProps {
  service: ServiceStatus;
  onClick?: () => void;
}

/**
 * Props for ServicesGrid component
 */
export interface ServicesGridProps {
  services: ServiceStatus[];
  isLoading: boolean;
  onServiceClick?: (serviceName: string) => void;
}

/**
 * Props for ErrorLogsTable component
 */
export interface ErrorLogsTableProps {
  logs: ErrorLog[];
  isLoading: boolean;
  onLogClick?: (logId: string) => void;
}

/**
 * Props for PerformanceChart component
 */
export interface PerformanceChartProps {
  data: TimeSeriesPoint[];
  title: string;
  color?: string;
  unit?: string;
  isLoading?: boolean;
}

/**
 * Props for QueueHealthPanel component
 */
export interface QueueHealthPanelProps {
  queueHealth: QueueSystemHealth | null;
  isLoading: boolean;
}

/**
 * Props for DatabaseStatsPanel component
 */
export interface DatabaseStatsPanelProps {
  databaseStats: DatabaseSystemHealth | null;
  isLoading: boolean;
}

/**
 * Props for CacheStatsPanel component
 */
export interface CacheStatsPanelProps {
  cacheStats: CacheStats | null;
  isLoading: boolean;
}

/**
 * Props for HealthBadge component
 */
export interface HealthBadgeProps {
  status: HealthStatus;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

/**
 * Props for MetricsSparkline component
 */
export interface MetricsSparklineProps {
  data: number[];
  color?: string;
  height?: number;
  width?: number;
}

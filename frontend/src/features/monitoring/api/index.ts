/**
 * Monitoring API Hooks Export
 */

// System health
export { useSystemHealth, SYSTEM_HEALTH_QUERY_KEY } from './useSystemHealth';

// Services
export { useServiceStatus, SERVICE_STATUS_QUERY_KEY_PREFIX } from './useServiceStatus';
export { useServicesList, SERVICES_LIST_QUERY_KEY } from './useServicesList';
export { useServiceMetrics, SERVICE_METRICS_QUERY_KEY_PREFIX } from './useServiceMetrics';

// Error logs
export { useErrorLogs, ERROR_LOGS_QUERY_KEY_PREFIX } from './useErrorLogs';

// Performance
export { usePerformanceMetrics, PERFORMANCE_METRICS_QUERY_KEY } from './usePerformanceMetrics';

// Infrastructure
export { useQueueHealth, QUEUE_HEALTH_QUERY_KEY } from './useQueueHealth';
export { useDatabaseStats, DATABASE_STATS_QUERY_KEY } from './useDatabaseStats';
export { useCacheStats, CACHE_STATS_QUERY_KEY } from './useCacheStats';

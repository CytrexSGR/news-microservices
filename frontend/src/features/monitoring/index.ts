/**
 * Monitoring Feature
 *
 * System monitoring and health dashboards for administrators.
 * Provides real-time visibility into services, queues, databases, and cache.
 *
 * @module features/monitoring
 *
 * @example Routes integration:
 * ```tsx
 * import { monitoringRoutes } from '@/features/monitoring';
 *
 * const adminRoutes = {
 *   path: 'admin',
 *   children: [
 *     monitoringRoutes,
 *     // ... other admin routes
 *   ]
 * };
 * ```
 *
 * @example Using hooks directly:
 * ```tsx
 * import { useSystemHealth, useServicesList } from '@/features/monitoring';
 *
 * function MyComponent() {
 *   const { data: health } = useSystemHealth();
 *   const { services } = useServicesList();
 *   // ...
 * }
 * ```
 */

// Routes
export { monitoringRoutes, MONITORING_ROUTES } from './routes';

// Layout
export { MonitoringLayout } from './MonitoringLayout';

// Pages
export {
  MonitoringDashboard,
  ServicesPage,
  ServiceDetailPage,
  ErrorLogsPage,
  PerformancePage,
  InfrastructurePage,
} from './pages';

// API Hooks
export {
  useSystemHealth,
  useServiceStatus,
  useServicesList,
  useServiceMetrics,
  useErrorLogs,
  usePerformanceMetrics,
  useQueueHealth,
  useDatabaseStats,
  useCacheStats,
} from './api';

// Components
export {
  HealthBadge,
  MetricsSparkline,
  SystemHealthCard,
  ServiceStatusCard,
  ServicesGrid,
  ErrorLogsTable,
  PerformanceChart,
  QueueHealthPanel,
  DatabaseStatsPanel,
  CacheStatsPanel,
} from './components';

// Types
export type {
  // Base types
  HealthStatus,
  ServiceType,
  LogLevel,
  DatabaseType,
  // System health
  SystemHealth,
  HealthIssue,
  // Services
  ServiceStatus,
  ServiceMetrics,
  DetailedServiceMetrics,
  TimeSeriesPoint,
  LatencyHistogramPoint,
  // Error logs
  ErrorLog,
  ErrorLogFilters,
  // Performance
  PerformanceMetrics,
  ServicePerformance,
  PerformanceTrends,
  // Queue
  QueueHealth,
  QueueSystemHealth,
  // Database
  DatabaseStats,
  DatabaseSystemHealth,
  // Cache
  CacheStats,
  // Response types
  MonitoringApiResponse,
  PaginatedResponse,
  // Component props
  SystemHealthCardProps,
  ServiceStatusCardProps,
  ServicesGridProps,
  ErrorLogsTableProps,
  PerformanceChartProps,
  QueueHealthPanelProps,
  DatabaseStatsPanelProps,
  CacheStatsPanelProps,
  HealthBadgeProps,
  MetricsSparklineProps,
} from './types';

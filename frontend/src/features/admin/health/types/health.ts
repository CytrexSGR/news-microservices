/**
 * System Health Types
 *
 * TypeScript interfaces for the System Health Dashboard feature.
 * Based on analytics-service (port 8107) health monitoring endpoints.
 */

/**
 * Health status values for services and containers
 */
export type HealthStatus = 'healthy' | 'unhealthy' | 'degraded' | null;

/**
 * Container status from Docker
 */
export type ContainerStatus = 'running' | 'stopped' | 'exited' | 'paused';

/**
 * Alert severity levels
 */
export type AlertSeverity = 'CRITICAL' | 'WARNING' | 'INFO';

/**
 * Container health information from Docker
 */
export interface ContainerHealth {
  name: string;
  status: ContainerStatus;
  health: HealthStatus;
  cpu_percent: number;
  memory_percent: number;
  memory_usage: string;
  pids: number;
  timestamp: string;
}

/**
 * System health summary statistics
 */
export interface HealthSummary {
  total_containers: number;
  healthy: number;
  unhealthy: number;
  no_healthcheck: number;
  running: number;
  stopped: number;
  avg_cpu_percent: number;
  avg_memory_percent: number;
  total_pids: number;
  recent_critical_alerts: number;
  recent_warning_alerts: number;
  timestamp: string;
}

/**
 * Health alert notification
 */
export interface HealthAlert {
  timestamp: string;
  severity: AlertSeverity;
  service: string;
  message: string;
  id?: string;
}

/**
 * Service health status (individual microservice)
 */
export interface ServiceHealth {
  name: string;
  port: number;
  status: HealthStatus;
  latency_ms: number;
  last_check: string;
  endpoint: string;
  error?: string;
}

/**
 * Aggregated system health data
 */
export interface SystemHealthData {
  summary: HealthSummary | null;
  containers: ContainerHealth[];
  alerts: HealthAlert[];
  services: ServiceHealth[];
  lastUpdated: Date | null;
}

/**
 * Health percentage calculation result
 */
export interface HealthPercentage {
  value: number;
  label: string;
  status: 'good' | 'warning' | 'critical';
}

/**
 * Props for health components
 */
export interface HealthSummaryCardProps {
  summary: HealthSummary | null;
  isLoading: boolean;
}

export interface ServiceHealthGridProps {
  containers: ContainerHealth[];
  isLoading: boolean;
}

export interface ContainerStatusListProps {
  containers: ContainerHealth[];
  isLoading: boolean;
  showDetails?: boolean;
}

export interface HealthAlertsListProps {
  alerts: HealthAlert[];
  isLoading: boolean;
  limit?: number;
}

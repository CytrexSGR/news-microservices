/**
 * FMP Service Types for Admin Frontend
 *
 * Matches backend responses from fmp-service admin endpoints
 */

/**
 * System Health Response
 */
export interface SystemHealth {
  timestamp: string; // ISO 8601 timestamp
  status: 'healthy' | 'degraded' | 'unhealthy';
  database_connected: boolean;
  fmp_api_reachable: boolean;
  scheduler_running: boolean;
  circuit_breaker?: {
    state: 'closed' | 'open' | 'half_open';
    failure_count: number;
  };
}

/**
 * Worker Status
 */
export interface WorkerStatus {
  worker_id: string;
  tier: 1 | 2 | 3;
  status: 'running' | 'stopped' | 'error';
  last_heartbeat: string | null; // ISO 8601 timestamp
  symbols_count: number;
  update_interval_seconds: number;
}

/**
 * API Quota Status
 */
export interface ApiQuota {
  daily_calls: number;
  daily_limit: number;
  daily_remaining: number;
  percentage_used: number;
  reset_time: string; // ISO 8601 timestamp
  note?: string;
}

/**
 * Error Log Entry
 */
export interface ErrorLog {
  id: number;
  timestamp: string; // ISO 8601 timestamp
  worker_id: string;
  symbol?: string;
  error_message: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
}

/**
 * API Call Metrics
 */
export interface Metrics {
  timestamp: string; // ISO 8601 timestamp
  count: number;
  endpoint?: string;
  status_code?: number;
}

/**
 * API Response Wrapper
 */
export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

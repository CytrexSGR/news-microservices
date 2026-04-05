/**
 * System Health Types for Finance Terminal
 */

export type SystemHealthStatus = 'healthy' | 'degraded' | 'down';

export type WorkerStatus = 'running' | 'paused' | 'error';

export interface WorkerInfo {
  name: string;
  status: WorkerStatus;
  symbols_synced: number;
  total_symbols: number;
  last_sync: string;
  duration_ms?: number;
}

export interface SystemHealth {
  overall_status: SystemHealthStatus;
  timestamp: string;
  fmp_api: {
    status: SystemHealthStatus;
    uptime_percent?: number;
  };
  database: {
    status: SystemHealthStatus;
    avg_query_ms?: number;
  };
  rate_limiter: {
    current: number;
    max: number;
  };
  workers: WorkerInfo[];
}

export interface ErrorLogEntry {
  id: number;
  timestamp: string;
  worker_id: string;
  symbol?: string;
  error_message: string;
}

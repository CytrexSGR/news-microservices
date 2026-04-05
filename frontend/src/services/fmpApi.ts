/**
 * FMP Service API Client
 *
 * Admin-focused API calls for FMP Service health monitoring and management.
 * Handles communication with FMP service for:
 * - System health monitoring
 * - Worker status tracking
 * - API quota management
 * - Error log retrieval
 * - Performance metrics
 */

import type {
  SystemHealth,
  WorkerStatus,
  ApiQuota,
  ErrorLog,
  Metrics,
  ApiResponse,
} from '@/types/fmp';

// Use relative URL to leverage Vite proxy (configured in vite.config.ts)
// Proxy routes /api/v1 → http://news-fmp-service:8113 inside Docker network
const FMP_SERVICE_URL = import.meta.env.VITE_FMP_SERVICE_URL || '';

/**
 * Fetch helper with error handling
 */
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
  try {
    const url = `${FMP_SERVICE_URL}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      return { error: `HTTP ${response.status}: ${errorText}` };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    return { error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

/**
 * Get system health metrics
 */
export async function getSystemHealth(): Promise<ApiResponse<SystemHealth>> {
  return fetchApi<SystemHealth>('/api/v1/system/health');
}

/**
 * Get worker status for all background workers
 */
export async function getWorkerStatus(): Promise<ApiResponse<WorkerStatus[]>> {
  return fetchApi<WorkerStatus[]>('/api/v1/system/workers');
}

/**
 * Get API quota information
 */
export async function getApiQuota(): Promise<ApiResponse<ApiQuota>> {
  return fetchApi<ApiQuota>('/api/v1/system/quota');
}

/**
 * Get recent error logs
 */
export async function getErrorLogs(limit = 50): Promise<ApiResponse<ErrorLog[]>> {
  return fetchApi<ErrorLog[]>(`/api/v1/system/errors?limit=${limit}`);
}

/**
 * Get API call statistics
 */
export async function getApiCallStats(
  timeframe: '24h' | '7d' | '30d' = '24h'
): Promise<ApiResponse<Metrics[]>> {
  return fetchApi<Metrics[]>(`/api/v1/system/metrics/api-calls?timeframe=${timeframe}`);
}

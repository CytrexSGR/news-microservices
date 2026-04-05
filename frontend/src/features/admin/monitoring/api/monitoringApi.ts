/**
 * API client for Monitoring endpoints
 *
 * Communicates with analytics-service (port 8107)
 */

import { analyticsApi } from '@/api/axios'

// getCircuitBreakers removed - use Grafana dashboard (2025-12-28)

/**
 * Get query performance statistics
 */
export interface QueryPerformanceResponse {
  total_queries: number
  unique_patterns: number
  top_queries: Array<{
    query_pattern: string
    avg_time_ms: number
    call_count: number
    max_time_ms: number
    min_time_ms: number
  }>
  slow_queries: Array<{
    query_pattern: string
    avg_time_ms: number
    call_count: number
  }>
  index_recommendations: string[]
}

export const getQueryPerformance = async (): Promise<QueryPerformanceResponse> => {
  const { data } = await analyticsApi.get<QueryPerformanceResponse>(
    '/monitoring/query-performance'
  )
  return data
}

/**
 * Reset query performance statistics
 */
export const resetQueryStatistics = async (): Promise<{ message: string }> => {
  const { data } = await analyticsApi.post<{ message: string }>(
    '/monitoring/query-performance/reset'
  )
  return data
}

/**
 * Get WebSocket connection statistics
 */
export interface WebSocketStats {
  total_connections: number
  connections: Array<{
    user_id: string
    subscriptions: string[]
    connected_at: string
    uptime_seconds: number
  }>
}

export const getWebSocketStats = async (): Promise<WebSocketStats> => {
  const { data } = await analyticsApi.get<WebSocketStats>('/monitoring/websocket')
  return data
}

/**
 * Get comprehensive system health
 */
export interface SystemHealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy'
  issues: string[]
  metrics: {
    circuit_breakers: {
      total: number
      open: number
      closed: number
    }
    database: {
      total_queries: number
      unique_patterns: number
      slow_queries: number
    }
    websocket: {
      total_connections: number
    }
  }
}

export const getSystemHealth = async (): Promise<SystemHealthResponse> => {
  const { data } = await analyticsApi.get<SystemHealthResponse>('/monitoring/health')
  return data
}

/**
 * usePerformanceMetrics Hook
 *
 * Fetches system-wide performance metrics with auto-refresh.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { PerformanceMetrics } from '../types';

const QUERY_KEY = ['monitoring', 'performance-metrics'];

/**
 * Fetch performance metrics from MCP orchestration server
 */
async function fetchPerformanceMetrics(): Promise<PerformanceMetrics> {
  return mcpClient.callTool<PerformanceMetrics>('get_performance_metrics');
}

export interface UsePerformanceMetricsOptions {
  /** Enable auto-refresh */
  autoRefresh?: boolean;
  /** Refresh interval in milliseconds (default: 30000) */
  refetchInterval?: number;
  /** Enable the query */
  enabled?: boolean;
}

/**
 * Hook to fetch system-wide performance metrics
 *
 * @example
 * ```tsx
 * const { data: metrics, isLoading } = usePerformanceMetrics({
 *   autoRefresh: true,
 *   refetchInterval: 15000
 * });
 * ```
 */
export function usePerformanceMetrics({
  autoRefresh = true,
  refetchInterval = 30000,
  enabled = true,
}: UsePerformanceMetricsOptions = {}) {
  const queryClient = useQueryClient();

  const query = useQuery<PerformanceMetrics>({
    queryKey: QUERY_KEY,
    queryFn: fetchPerformanceMetrics,
    refetchInterval: autoRefresh ? refetchInterval : false,
    staleTime: 10000, // 10 seconds
    enabled,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: QUERY_KEY });
  };

  return {
    ...query,
    invalidate,
  };
}

export { QUERY_KEY as PERFORMANCE_METRICS_QUERY_KEY };

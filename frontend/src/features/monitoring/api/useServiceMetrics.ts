/**
 * useServiceMetrics Hook
 *
 * Fetches detailed metrics for a specific service.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { DetailedServiceMetrics } from '../types';

const QUERY_KEY_PREFIX = ['monitoring', 'service-metrics'];

/**
 * Fetch service metrics from MCP orchestration server
 */
async function fetchServiceMetrics(serviceName: string): Promise<DetailedServiceMetrics> {
  return mcpClient.callTool<DetailedServiceMetrics>('get_service_metrics', {
    service_name: serviceName,
  });
}

export interface UseServiceMetricsOptions {
  /** Service name to fetch metrics for */
  serviceName: string;
  /** Enable auto-refresh */
  autoRefresh?: boolean;
  /** Refresh interval in milliseconds (default: 30000) */
  refetchInterval?: number;
  /** Enable the query */
  enabled?: boolean;
}

/**
 * Hook to fetch detailed metrics for a service
 *
 * @example
 * ```tsx
 * const { data: metrics, isLoading } = useServiceMetrics({
 *   serviceName: 'feed-service',
 *   autoRefresh: true
 * });
 * ```
 */
export function useServiceMetrics({
  serviceName,
  autoRefresh = true,
  refetchInterval = 30000,
  enabled = true,
}: UseServiceMetricsOptions) {
  const queryClient = useQueryClient();
  const queryKey = [...QUERY_KEY_PREFIX, serviceName];

  const query = useQuery<DetailedServiceMetrics>({
    queryKey,
    queryFn: () => fetchServiceMetrics(serviceName),
    refetchInterval: autoRefresh ? refetchInterval : false,
    staleTime: 10000, // 10 seconds
    enabled: enabled && !!serviceName,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey });
  };

  return {
    ...query,
    invalidate,
  };
}

export { QUERY_KEY_PREFIX as SERVICE_METRICS_QUERY_KEY_PREFIX };

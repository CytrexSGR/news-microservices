/**
 * useSystemHealth Hook
 *
 * Fetches overall system health status with auto-refresh capability.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { SystemHealth } from '../types';

const QUERY_KEY = ['monitoring', 'system-health'];

/**
 * Fetch system health from MCP orchestration server
 */
async function fetchSystemHealth(): Promise<SystemHealth> {
  return mcpClient.callTool<SystemHealth>('get_system_health');
}

export interface UseSystemHealthOptions {
  /** Enable auto-refresh */
  autoRefresh?: boolean;
  /** Refresh interval in milliseconds (default: 30000) */
  refetchInterval?: number;
  /** Enable the query */
  enabled?: boolean;
}

/**
 * Hook to fetch overall system health
 *
 * @example
 * ```tsx
 * const { data, isLoading, refetch } = useSystemHealth({
 *   autoRefresh: true,
 *   refetchInterval: 30000
 * });
 * ```
 */
export function useSystemHealth({
  autoRefresh = true,
  refetchInterval = 30000,
  enabled = true,
}: UseSystemHealthOptions = {}) {
  const queryClient = useQueryClient();

  const query = useQuery<SystemHealth>({
    queryKey: QUERY_KEY,
    queryFn: fetchSystemHealth,
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

export { QUERY_KEY as SYSTEM_HEALTH_QUERY_KEY };

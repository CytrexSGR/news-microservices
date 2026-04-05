/**
 * useServicesList Hook
 *
 * Fetches list of all services with their status.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { ServiceStatus } from '../types';

const QUERY_KEY = ['monitoring', 'services-list'];

/**
 * Fetch services list from MCP orchestration server
 */
async function fetchServicesList(): Promise<ServiceStatus[]> {
  return mcpClient.callTool<ServiceStatus[]>('list_services');
}

export interface UseServicesListOptions {
  /** Enable auto-refresh */
  autoRefresh?: boolean;
  /** Refresh interval in milliseconds (default: 30000) */
  refetchInterval?: number;
  /** Enable the query */
  enabled?: boolean;
}

/**
 * Hook to fetch list of all services
 *
 * @example
 * ```tsx
 * const { data: services, isLoading } = useServicesList({
 *   autoRefresh: true,
 *   refetchInterval: 30000
 * });
 * ```
 */
export function useServicesList({
  autoRefresh = true,
  refetchInterval = 30000,
  enabled = true,
}: UseServicesListOptions = {}) {
  const queryClient = useQueryClient();

  const query = useQuery<ServiceStatus[]>({
    queryKey: QUERY_KEY,
    queryFn: fetchServicesList,
    refetchInterval: autoRefresh ? refetchInterval : false,
    staleTime: 10000, // 10 seconds
    enabled,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: QUERY_KEY });
  };

  // Derived data
  const healthyCount = query.data?.filter((s) => s.status === 'healthy').length ?? 0;
  const unhealthyCount = query.data?.filter((s) => s.status === 'unhealthy').length ?? 0;
  const degradedCount = query.data?.filter((s) => s.status === 'degraded').length ?? 0;
  const totalCount = query.data?.length ?? 0;

  return {
    ...query,
    services: query.data ?? [],
    healthyCount,
    unhealthyCount,
    degradedCount,
    totalCount,
    invalidate,
  };
}

export { QUERY_KEY as SERVICES_LIST_QUERY_KEY };

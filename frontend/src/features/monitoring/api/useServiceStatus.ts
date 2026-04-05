/**
 * useServiceStatus Hook
 *
 * Fetches status for a single service with auto-refresh capability.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { ServiceStatus } from '../types';

const QUERY_KEY_PREFIX = ['monitoring', 'service-status'];

/**
 * Fetch service status from MCP orchestration server
 */
async function fetchServiceStatus(serviceName: string): Promise<ServiceStatus> {
  return mcpClient.callTool<ServiceStatus>('get_service_status', {
    service_name: serviceName,
  });
}

export interface UseServiceStatusOptions {
  /** Service name to fetch status for */
  serviceName: string;
  /** Enable auto-refresh */
  autoRefresh?: boolean;
  /** Refresh interval in milliseconds (default: 30000) */
  refetchInterval?: number;
  /** Enable the query */
  enabled?: boolean;
}

/**
 * Hook to fetch status for a single service
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useServiceStatus({
 *   serviceName: 'feed-service',
 *   autoRefresh: true
 * });
 * ```
 */
export function useServiceStatus({
  serviceName,
  autoRefresh = true,
  refetchInterval = 30000,
  enabled = true,
}: UseServiceStatusOptions) {
  const queryClient = useQueryClient();
  const queryKey = [...QUERY_KEY_PREFIX, serviceName];

  const query = useQuery<ServiceStatus>({
    queryKey,
    queryFn: () => fetchServiceStatus(serviceName),
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

export { QUERY_KEY_PREFIX as SERVICE_STATUS_QUERY_KEY_PREFIX };

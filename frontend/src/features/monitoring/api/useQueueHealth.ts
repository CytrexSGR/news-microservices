/**
 * useQueueHealth Hook
 *
 * Fetches RabbitMQ queue health status with auto-refresh.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { QueueSystemHealth } from '../types';

const QUERY_KEY = ['monitoring', 'queue-health'];

/**
 * Fetch queue health from MCP orchestration server
 */
async function fetchQueueHealth(): Promise<QueueSystemHealth> {
  return mcpClient.callTool<QueueSystemHealth>('get_queue_health');
}

export interface UseQueueHealthOptions {
  /** Enable auto-refresh */
  autoRefresh?: boolean;
  /** Refresh interval in milliseconds (default: 30000) */
  refetchInterval?: number;
  /** Enable the query */
  enabled?: boolean;
}

/**
 * Hook to fetch RabbitMQ queue health
 *
 * @example
 * ```tsx
 * const { data: queueHealth, isLoading } = useQueueHealth({
 *   autoRefresh: true,
 *   refetchInterval: 30000
 * });
 * ```
 */
export function useQueueHealth({
  autoRefresh = true,
  refetchInterval = 30000,
  enabled = true,
}: UseQueueHealthOptions = {}) {
  const queryClient = useQueryClient();

  const query = useQuery<QueueSystemHealth>({
    queryKey: QUERY_KEY,
    queryFn: fetchQueueHealth,
    refetchInterval: autoRefresh ? refetchInterval : false,
    staleTime: 10000, // 10 seconds
    enabled,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: QUERY_KEY });
  };

  // Derived data
  const queues = query.data?.queues ?? [];
  const totalMessages = query.data?.total_messages ?? 0;
  const totalConsumers = query.data?.total_consumers ?? 0;
  const healthyQueues = query.data?.healthy_queues ?? 0;
  const totalQueues = query.data?.total_queues ?? 0;

  return {
    ...query,
    queues,
    totalMessages,
    totalConsumers,
    healthyQueues,
    totalQueues,
    invalidate,
  };
}

export { QUERY_KEY as QUEUE_HEALTH_QUERY_KEY };

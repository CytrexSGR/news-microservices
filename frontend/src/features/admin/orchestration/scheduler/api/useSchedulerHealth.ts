import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { SchedulerHealth } from '../types/scheduler.types';

/**
 * Query key for scheduler health
 */
export const schedulerHealthQueryKey = ['scheduler', 'health'] as const;

/**
 * Fetch scheduler health using MCP tool
 */
async function fetchSchedulerHealth(): Promise<SchedulerHealth> {
  return mcpClient.callTool<SchedulerHealth>('scheduler_health');
}

/**
 * Hook to fetch scheduler health status
 *
 * @param options - React Query options
 * @returns Query result with scheduler health
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useSchedulerHealth();
 *
 * if (data?.status === 'healthy') {
 *   // All good
 * }
 * ```
 */
export function useSchedulerHealth(
  options?: Omit<UseQueryOptions<SchedulerHealth>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: schedulerHealthQueryKey,
    queryFn: fetchSchedulerHealth,
    staleTime: 5000, // 5 seconds
    refetchInterval: 10000, // Auto-refresh every 10 seconds
    ...options,
  });
}

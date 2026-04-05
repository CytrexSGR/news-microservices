import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { SchedulerStatus } from '../types/scheduler.types';

/**
 * Query key for scheduler status
 */
export const schedulerStatusQueryKey = ['scheduler', 'status'] as const;

/**
 * Fetch scheduler status using MCP tool
 */
async function fetchSchedulerStatus(): Promise<SchedulerStatus> {
  return mcpClient.callTool<SchedulerStatus>('scheduler_status');
}

/**
 * Hook to fetch scheduler status
 *
 * @param options - React Query options
 * @returns Query result with scheduler status
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useSchedulerStatus();
 * ```
 */
export function useSchedulerStatus(
  options?: Omit<UseQueryOptions<SchedulerStatus>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: schedulerStatusQueryKey,
    queryFn: fetchSchedulerStatus,
    staleTime: 3000, // 3 seconds
    refetchInterval: 5000, // Auto-refresh every 5 seconds
    ...options,
  });
}

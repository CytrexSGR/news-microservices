import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { JobsStats } from '../types/scheduler.types';

/**
 * Query key for jobs statistics
 */
export const jobsStatsQueryKey = ['scheduler', 'jobs', 'stats'] as const;

/**
 * Fetch jobs statistics using MCP tool
 */
async function fetchJobsStats(): Promise<JobsStats> {
  return mcpClient.callTool<JobsStats>('jobs_stats');
}

/**
 * Hook to fetch jobs statistics
 *
 * @param options - React Query options
 * @returns Query result with jobs stats
 *
 * @example
 * ```tsx
 * const { data } = useJobsStats();
 *
 * console.log(`Success rate: ${data?.success_rate}%`);
 * ```
 */
export function useJobsStats(
  options?: Omit<UseQueryOptions<JobsStats>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: jobsStatsQueryKey,
    queryFn: fetchJobsStats,
    staleTime: 5000,
    refetchInterval: 10000, // Auto-refresh every 10 seconds
    ...options,
  });
}

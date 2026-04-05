import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { CronJobsListResponse } from '../types/scheduler.types';

/**
 * Query key for cron jobs list
 */
export const cronJobsListQueryKey = ['scheduler', 'cron'] as const;

/**
 * Fetch cron jobs list using MCP tool
 */
async function fetchCronJobsList(): Promise<CronJobsListResponse> {
  return mcpClient.callTool<CronJobsListResponse>('cron_list');
}

/**
 * Hook to fetch cron jobs list
 *
 * @param options - React Query options
 * @returns Query result with cron jobs list
 *
 * @example
 * ```tsx
 * const { data } = useCronJobsList();
 *
 * data?.cron_jobs.forEach(job => {
 *   console.log(`${job.name}: ${job.schedule}`);
 * });
 * ```
 */
export function useCronJobsList(
  options?: Omit<UseQueryOptions<CronJobsListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: cronJobsListQueryKey,
    queryFn: fetchCronJobsList,
    staleTime: 30000, // 30 seconds - cron jobs don't change often
    ...options,
  });
}

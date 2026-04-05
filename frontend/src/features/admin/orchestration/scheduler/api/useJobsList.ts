import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { JobsListResponse, JobsListParams } from '../types/scheduler.types';

/**
 * Create query key for jobs list
 */
export function jobsListQueryKey(params: JobsListParams = {}) {
  return ['scheduler', 'jobs', params] as const;
}

/**
 * Fetch jobs list using MCP tool
 */
async function fetchJobsList(params: JobsListParams): Promise<JobsListResponse> {
  return mcpClient.callTool<JobsListResponse>('jobs_list', params);
}

/**
 * Hook to fetch jobs list with filtering and pagination
 *
 * @param params - Filter and pagination parameters
 * @param options - React Query options
 * @returns Query result with jobs list
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useJobsList({
 *   status: 'running',
 *   limit: 20,
 * });
 * ```
 */
export function useJobsList(
  params: JobsListParams = {},
  options?: Omit<UseQueryOptions<JobsListResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: jobsListQueryKey(params),
    queryFn: () => fetchJobsList(params),
    staleTime: 5000,
    keepPreviousData: true, // For pagination
    ...options,
  });
}

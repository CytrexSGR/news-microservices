import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { MediaStackUsage } from '../types/mediastack.types';

/**
 * Query key for MediaStack usage
 */
export const mediaStackUsageQueryKey = ['mediastack', 'usage'] as const;

/**
 * Fetch MediaStack API usage statistics
 */
async function fetchMediaStackUsage(): Promise<MediaStackUsage> {
  return mcpClient.callTool<MediaStackUsage>('mediastack_usage');
}

/**
 * Hook to fetch MediaStack API usage statistics
 *
 * @param options - React Query options
 * @returns Query result with API usage data
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useMediaStackUsage();
 *
 * if (data) {
 *   console.log(`${data.calls_remaining} calls remaining`);
 * }
 * ```
 */
export function useMediaStackUsage(
  options?: Omit<UseQueryOptions<MediaStackUsage>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: mediaStackUsageQueryKey,
    queryFn: fetchMediaStackUsage,
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Auto-refresh every 5 minutes
    ...options,
  });
}

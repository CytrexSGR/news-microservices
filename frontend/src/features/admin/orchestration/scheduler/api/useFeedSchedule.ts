import { useQuery } from '@tanstack/react-query';
import type { UseQueryOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { FeedSchedule } from '../types/scheduler.types';

/**
 * Create query key for feed schedule
 */
export function feedScheduleQueryKey(feedId: number) {
  return ['scheduler', 'feeds', feedId, 'schedule'] as const;
}

/**
 * Fetch feed schedule using MCP tool
 */
async function fetchFeedSchedule(feedId: number): Promise<FeedSchedule> {
  return mcpClient.callTool<FeedSchedule>('feed_schedule_check', { feed_id: feedId });
}

/**
 * Hook to fetch schedule for a specific feed
 *
 * @param feedId - The feed ID to check schedule for
 * @param options - React Query options
 * @returns Query result with feed schedule
 *
 * @example
 * ```tsx
 * const { data } = useFeedSchedule(123);
 *
 * console.log(`Next run: ${data?.next_run}`);
 * console.log(`Interval: ${data?.interval_minutes} minutes`);
 * ```
 */
export function useFeedSchedule(
  feedId: number,
  options?: Omit<UseQueryOptions<FeedSchedule>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: feedScheduleQueryKey(feedId),
    queryFn: () => fetchFeedSchedule(feedId),
    staleTime: 30000, // 30 seconds
    enabled: feedId > 0, // Only fetch if feedId is valid
    ...options,
  });
}

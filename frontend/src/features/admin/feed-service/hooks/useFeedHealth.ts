import { useQuery } from '@tanstack/react-query'
import { getFeedHealth } from '@/lib/api/feedServiceAdmin'
import type { FeedHealthResponse } from '@/types/feedServiceAdmin'

/**
 * Hook to fetch health status for a specific feed
 * @param feedId - Feed ID
 * @param enabled - Whether the query should run (default: true)
 */
export const useFeedHealth = (feedId: string, enabled: boolean = true) => {
  return useQuery<FeedHealthResponse>({
    queryKey: ['feed-service', 'feeds', feedId, 'health'],
    queryFn: () => getFeedHealth(feedId),
    enabled: enabled && !!feedId,
  })
}

import { useQuery } from '@tanstack/react-query'
import { getFeedStats } from '@/lib/api/feedServiceAdmin'
import type { FeedStats } from '@/types/feedServiceAdmin'

/**
 * Hook to fetch feed statistics for dashboard
 * @param refetchInterval - Auto-refresh interval in milliseconds (default: no auto-refresh)
 */
export const useFeedStats = (refetchInterval?: number) => {
  return useQuery<FeedStats>({
    queryKey: ['feed-service', 'stats'],
    queryFn: getFeedStats,
    refetchInterval,
    staleTime: refetchInterval ? refetchInterval * 0.8 : undefined,
  })
}

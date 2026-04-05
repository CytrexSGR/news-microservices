import { useQuery } from '@tanstack/react-query'
import { getFeedList } from '@/lib/api/feedServiceAdmin'
import type { FeedListResponse, FeedListFilters } from '@/types/feedServiceAdmin'

/**
 * Hook to fetch feed list with filters
 * @param filters - Optional filters for feed list
 * @param refetchInterval - Auto-refresh interval in milliseconds (default: no auto-refresh)
 */
export const useFeedList = (filters?: FeedListFilters, refetchInterval?: number) => {
  return useQuery<FeedListResponse>({
    queryKey: ['feed-service', 'feeds', 'list', filters],
    queryFn: () => getFeedList(filters),
    refetchInterval,
    staleTime: refetchInterval ? refetchInterval * 0.8 : undefined,
  })
}

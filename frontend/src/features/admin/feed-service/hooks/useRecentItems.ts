import { useQuery } from '@tanstack/react-query'
import { getRecentItems } from '@/lib/api/feedServiceAdmin'
import type { RecentItemsResponse } from '@/types/feedServiceAdmin'

/**
 * Hook to fetch recent feed items
 * @param limit - Number of items to fetch (default: 20)
 * @param refetchInterval - Auto-refresh interval in milliseconds (default: no auto-refresh)
 */
export const useRecentItems = (limit: number = 20, refetchInterval?: number) => {
  return useQuery<RecentItemsResponse>({
    queryKey: ['feed-service', 'items', 'recent', limit],
    queryFn: () => getRecentItems(limit),
    refetchInterval,
    staleTime: refetchInterval ? refetchInterval * 0.8 : undefined,
  })
}

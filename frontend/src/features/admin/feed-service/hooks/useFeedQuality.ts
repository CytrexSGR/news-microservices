import { useQuery } from '@tanstack/react-query'
import { getFeedQuality } from '@/lib/api/feedServiceAdmin'
import type { FeedQualityResponse } from '@/types/feedServiceAdmin'

/**
 * Hook to fetch quality metrics for a specific feed
 * @param feedId - Feed ID
 * @param enabled - Whether the query should run (default: true)
 */
export const useFeedQuality = (feedId: string, enabled: boolean = true) => {
  return useQuery<FeedQualityResponse>({
    queryKey: ['feed-service', 'feeds', feedId, 'quality'],
    queryFn: () => getFeedQuality(feedId),
    enabled: enabled && !!feedId,
    staleTime: 5 * 60 * 1000, // Quality metrics are expensive to compute, cache for 5 minutes
  })
}

import { useQuery } from '@tanstack/react-query'
import { getFeedQualityOverview } from '@/lib/api/feedServiceAdmin'
import type { FeedQualityOverview } from '@/types/feedServiceAdmin'

/**
 * Hook to fetch Quality V2 overview for all active feeds
 *
 * Returns a list of feeds with key quality metrics:
 * - Feed name and ID
 * - Quality score and Admiralty code
 * - Total articles and last 24h count
 * - Confidence level and trend
 *
 * Optimized for table display with sortable columns.
 */
export const useFeedQualityOverview = () => {
  return useQuery<FeedQualityOverview[]>({
    queryKey: ['feed-service', 'feeds', 'quality-v2-overview'],
    queryFn: () => getFeedQualityOverview(),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes (expensive query)
    retry: 2,
  })
}

import { useQuery } from '@tanstack/react-query'
import { getFeedQualityV2 } from '@/lib/api/feedServiceAdmin'
import type { FeedQualityV2Response } from '@/types/feedServiceAdmin'

/**
 * Hook to fetch comprehensive Quality V2 metrics for a specific feed
 *
 * Quality V2 provides:
 * - Weighted quality score (0-100) based on 4 components
 * - Admiralty Code (A-F) reliability rating
 * - Confidence level (low/medium/high) based on data volume
 * - Trend analysis (improving/stable/declining)
 * - Component breakdown (Article Quality 50%, Source Credibility 20%, Operational 20%, Freshness 10%)
 * - Actionable recommendations
 *
 * @param feedId - Feed UUID
 * @param days - Number of days to analyze (default: 30)
 * @param enabled - Whether the query should run (default: true)
 */
export const useFeedQualityV2 = (
  feedId: string,
  days: number = 30,
  enabled: boolean = true
) => {
  return useQuery<FeedQualityV2Response>({
    queryKey: ['feed-service', 'feeds', feedId, 'quality-v2', days],
    queryFn: () => getFeedQualityV2(feedId, days),
    enabled: enabled && !!feedId,
    staleTime: 5 * 60 * 1000, // Quality metrics are expensive to compute, cache for 5 minutes
    retry: 2, // Retry failed requests twice
  })
}

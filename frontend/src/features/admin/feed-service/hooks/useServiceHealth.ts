import { useQuery } from '@tanstack/react-query'
import { getServiceHealth } from '@/lib/api/feedServiceAdmin'
import type { FeedServiceHealth } from '@/types/feedServiceAdmin'

/**
 * Hook to fetch feed service health status
 * @param refetchInterval - Auto-refresh interval in milliseconds (default: no auto-refresh)
 */
export const useServiceHealth = (refetchInterval?: number) => {
  return useQuery<FeedServiceHealth>({
    queryKey: ['feed-service', 'health'],
    queryFn: getServiceHealth,
    refetchInterval,
    staleTime: refetchInterval ? refetchInterval * 0.8 : undefined,
  })
}

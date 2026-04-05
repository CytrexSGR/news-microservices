import { useQuery } from '@tanstack/react-query'
import { getCacheStats } from '@/lib/api/searchServiceAdmin'
import type { CacheStatistics } from '@/types/searchServiceAdmin'

/**
 * Hook to fetch search service cache statistics
 * @param refetchInterval - Auto-refresh interval in milliseconds (default: no auto-refresh)
 */
export const useCacheStats = (refetchInterval?: number) => {
  return useQuery<CacheStatistics>({
    queryKey: ['search-service', 'cache-stats'],
    queryFn: getCacheStats,
    refetchInterval,
    staleTime: refetchInterval ? refetchInterval * 0.8 : undefined,
  })
}

import { useQuery } from '@tanstack/react-query'
import { getIndexStats } from '@/lib/api/searchServiceAdmin'
import type { IndexStatistics } from '@/types/searchServiceAdmin'

/**
 * Hook to fetch search service index statistics
 * @param refetchInterval - Auto-refresh interval in milliseconds (default: no auto-refresh)
 */
export const useIndexStats = (refetchInterval?: number) => {
  return useQuery<IndexStatistics>({
    queryKey: ['search-service', 'index-stats'],
    queryFn: getIndexStats,
    refetchInterval,
    staleTime: refetchInterval ? refetchInterval * 0.8 : undefined,
  })
}

import { useQuery } from '@tanstack/react-query'
import { getQueryStats } from '@/lib/api/searchServiceAdmin'
import type { QueryStatistics } from '@/types/searchServiceAdmin'

/**
 * Hook to fetch search service query statistics
 * @param refetchInterval - Auto-refresh interval in milliseconds (default: no auto-refresh)
 */
export const useQueryStats = (refetchInterval?: number) => {
  return useQuery<QueryStatistics>({
    queryKey: ['search-service', 'query-stats'],
    queryFn: getQueryStats,
    refetchInterval,
    staleTime: refetchInterval ? refetchInterval * 0.8 : undefined,
  })
}

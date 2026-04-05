import { useQuery } from '@tanstack/react-query'
import { getPerformanceStats } from '@/lib/api/searchServiceAdmin'
import type { PerformanceStatistics } from '@/types/searchServiceAdmin'

/**
 * Hook to fetch search service performance statistics
 * @param refetchInterval - Auto-refresh interval in milliseconds (default: no auto-refresh)
 */
export const usePerformanceStats = (refetchInterval?: number) => {
  return useQuery<PerformanceStatistics>({
    queryKey: ['search-service', 'performance-stats'],
    queryFn: getPerformanceStats,
    refetchInterval,
    staleTime: refetchInterval ? refetchInterval * 0.8 : undefined,
  })
}

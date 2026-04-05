import { useQuery } from '@tanstack/react-query'
import { getCeleryStats } from '@/lib/api/searchServiceAdmin'
import type { CeleryStatistics } from '@/types/searchServiceAdmin'

/**
 * Hook to fetch search service Celery worker statistics
 * @param refetchInterval - Auto-refresh interval in milliseconds (default: no auto-refresh)
 */
export const useCeleryStats = (refetchInterval?: number) => {
  return useQuery<CeleryStatistics>({
    queryKey: ['search-service', 'celery-stats'],
    queryFn: getCeleryStats,
    refetchInterval,
    staleTime: refetchInterval ? refetchInterval * 0.8 : undefined,
  })
}

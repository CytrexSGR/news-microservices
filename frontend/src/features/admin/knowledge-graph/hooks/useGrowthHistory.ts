import { useQuery } from '@tanstack/react-query'
import { getGrowthHistory } from '@/lib/api/knowledgeGraphAdmin'

export function useGrowthHistory(days: number = 30, refetchInterval?: number) {
  return useQuery({
    queryKey: ['knowledge-graph', 'growth-history', days],
    queryFn: () => getGrowthHistory(days),
    refetchInterval, // Optional auto-refresh
    staleTime: 60000, // Consider data stale after 60 seconds
  })
}

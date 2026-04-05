import { useQuery } from '@tanstack/react-query'
import { getGraphStats } from '@/lib/api/knowledgeGraphAdmin'

export function useGraphStats(refetchInterval: number = 30000) {
  return useQuery({
    queryKey: ['knowledge-graph', 'graph-stats'],
    queryFn: getGraphStats,
    refetchInterval, // Auto-refresh every 30 seconds (stats change slowly)
    staleTime: 15000,
  })
}

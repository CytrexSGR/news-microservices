import { useQuery } from '@tanstack/react-query'
import { getRelationshipStats } from '@/lib/api/knowledgeGraphAdmin'

export function useRelationshipStats(refetchInterval?: number) {
  return useQuery({
    queryKey: ['knowledge-graph', 'relationship-stats'],
    queryFn: getRelationshipStats,
    refetchInterval, // Optional auto-refresh
    staleTime: 30000, // Consider data stale after 30 seconds
  })
}

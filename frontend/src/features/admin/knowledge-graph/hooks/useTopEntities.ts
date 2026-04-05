import { useQuery } from '@tanstack/react-query'
import { getTopEntities } from '@/lib/api/knowledgeGraphAdmin'

export function useTopEntities(limit: number = 10, entityType?: string, refetchInterval?: number) {
  return useQuery({
    queryKey: ['knowledge-graph', 'top-entities', limit, entityType],
    queryFn: () => getTopEntities(limit, entityType),
    refetchInterval, // Optional auto-refresh
    staleTime: 30000, // Consider data stale after 30 seconds
  })
}

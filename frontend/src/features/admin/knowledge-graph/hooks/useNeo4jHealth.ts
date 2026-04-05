import { useQuery } from '@tanstack/react-query'
import { getNeo4jHealth } from '@/lib/api/knowledgeGraphAdmin'

export function useNeo4jHealth(refetchInterval: number = 10000) {
  return useQuery({
    queryKey: ['knowledge-graph', 'neo4j-health'],
    queryFn: getNeo4jHealth,
    refetchInterval, // Auto-refresh every 10 seconds
    staleTime: 5000,
  })
}

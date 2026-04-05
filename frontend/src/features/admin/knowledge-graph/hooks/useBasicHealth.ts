import { useQuery } from '@tanstack/react-query'
import { getBasicHealth } from '@/lib/api/knowledgeGraphAdmin'

export function useBasicHealth(refetchInterval: number = 10000) {
  return useQuery({
    queryKey: ['knowledge-graph', 'basic-health'],
    queryFn: getBasicHealth,
    refetchInterval, // Auto-refresh every 10 seconds
    staleTime: 5000,
  })
}

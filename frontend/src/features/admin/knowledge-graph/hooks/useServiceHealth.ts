import { useQuery } from '@tanstack/react-query'
import { getServiceHealth } from '@/lib/api/knowledgeGraphAdmin'

export function useServiceHealth(refetchInterval: number = 10000) {
  return useQuery({
    queryKey: ['knowledge-graph', 'service-health'],
    queryFn: getServiceHealth,
    refetchInterval, // Auto-refresh every 10 seconds
    staleTime: 5000,
  })
}

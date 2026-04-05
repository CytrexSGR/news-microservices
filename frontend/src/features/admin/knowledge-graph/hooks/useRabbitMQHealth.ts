import { useQuery } from '@tanstack/react-query'
import { getRabbitMQHealth } from '@/lib/api/knowledgeGraphAdmin'

export function useRabbitMQHealth(refetchInterval: number = 10000) {
  return useQuery({
    queryKey: ['knowledge-graph', 'rabbitmq-health'],
    queryFn: getRabbitMQHealth,
    refetchInterval, // Auto-refresh every 10 seconds
    staleTime: 5000,
  })
}

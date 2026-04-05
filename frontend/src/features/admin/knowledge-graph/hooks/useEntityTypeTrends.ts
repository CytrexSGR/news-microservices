import { useQuery } from '@tanstack/react-query'
import { getEntityTypeTrends } from '@/lib/api/canonicalizationAdmin'

export function useEntityTypeTrends(days: number = 30, enabled: boolean = true) {
  return useQuery({
    queryKey: ['canonicalization', 'entity-type-trends', days],
    queryFn: () => getEntityTypeTrends(days),
    enabled,
    refetchInterval: 60000, // Refetch every 60 seconds
    staleTime: 30000, // Consider data stale after 30 seconds
  })
}

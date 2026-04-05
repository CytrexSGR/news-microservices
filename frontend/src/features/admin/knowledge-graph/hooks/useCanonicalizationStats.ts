import { useQuery } from '@tanstack/react-query'
import { getCanonicalizationStats } from '@/lib/api/canonicalizationAdmin'

export function useCanonicalizationStats(refetchInterval: number = 60000) {
  return useQuery({
    queryKey: ['canonicalization', 'detailed-stats'],
    queryFn: getCanonicalizationStats,
    refetchInterval, // Auto-refresh every 60 seconds (stats change slowly)
    staleTime: 30000,
  })
}

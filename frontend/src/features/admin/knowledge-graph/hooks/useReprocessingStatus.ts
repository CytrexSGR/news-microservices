import { useQuery } from '@tanstack/react-query'
import { getReprocessingStatus } from '@/lib/api/canonicalizationAdmin'

export function useReprocessingStatus(enabled: boolean = true, forcedInterval?: number) {
  return useQuery({
    queryKey: ['canonicalization', 'reprocessing-status'],
    queryFn: getReprocessingStatus,
    enabled, // Only fetch when enabled
    refetchInterval: (query) => {
      const data = query.state.data

      // If forced polling is active, use that interval
      if (forcedInterval) {
        return forcedInterval
      }

      // Poll every 2 seconds if running, otherwise disable polling
      if (data?.status === 'running') {
        return 2000
      }

      return false
    },
    staleTime: 1000, // Consider data stale after 1 second
  })
}

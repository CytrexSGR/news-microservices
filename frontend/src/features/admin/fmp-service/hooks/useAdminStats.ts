/**
 * useAdminStats Hooks
 *
 * Fetches FMP Service admin statistics with React Query
 * - Job Performance (execution times, success rates)
 * - Data Quality (completeness, freshness)
 * - Data Growth (trends over time)
 */

import { useQuery } from '@tanstack/react-query'
import { getJobPerformance, getDataQuality, getDataGrowth } from '@/lib/api/fmpAdmin'

/**
 * Hook to fetch job performance metrics
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useJobPerformance({ refetchInterval: 10000 })
 * ```
 */
export function useJobPerformance({
  refetchInterval = 30000, // Default: 30 seconds
  enabled = true,
}: {
  refetchInterval?: number
  enabled?: boolean
} = {}) {
  return useQuery({
    queryKey: ['fmp-job-performance'],
    queryFn: () => getJobPerformance().then(res => res.data),
    enabled,
    refetchInterval,
    staleTime: 1000 * 20, // 20 seconds
  })
}

/**
 * Hook to fetch data quality metrics
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useDataQuality({ refetchInterval: 60000 })
 * ```
 */
export function useDataQuality({
  refetchInterval = 60000, // Default: 1 minute
  enabled = true,
}: {
  refetchInterval?: number
  enabled?: boolean
} = {}) {
  return useQuery({
    queryKey: ['fmp-data-quality'],
    queryFn: () => getDataQuality().then(res => res.data),
    enabled,
    refetchInterval,
    staleTime: 1000 * 30, // 30 seconds
  })
}

/**
 * Hook to fetch data growth metrics
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useDataGrowth({
 *   days: 30,
 *   refetchInterval: 300000
 * })
 * ```
 */
export function useDataGrowth({
  days = 30,
  refetchInterval = 300000, // Default: 5 minutes
  enabled = true,
}: {
  days?: number
  refetchInterval?: number
  enabled?: boolean
} = {}) {
  return useQuery({
    queryKey: ['fmp-data-growth', days],
    queryFn: () => getDataGrowth(days).then(res => res.data),
    enabled,
    refetchInterval,
    staleTime: 1000 * 60 * 2, // 2 minutes
  })
}

/**
 * Hook to fetch all admin statistics at once
 *
 * @example
 * ```tsx
 * const { jobPerformance, dataQuality, dataGrowth, isLoading } = useAllAdminStats()
 * ```
 */
export function useAllAdminStats({
  days = 30,
  enabled = true,
}: {
  days?: number
  enabled?: boolean
} = {}) {
  const jobPerformance = useJobPerformance({ enabled })
  const dataQuality = useDataQuality({ enabled })
  const dataGrowth = useDataGrowth({ days, enabled })

  return {
    jobPerformance: jobPerformance.data,
    dataQuality: dataQuality.data,
    dataGrowth: dataGrowth.data,
    isLoading: jobPerformance.isLoading || dataQuality.isLoading || dataGrowth.isLoading,
    error: jobPerformance.error || dataQuality.error || dataGrowth.error,
    refetch: () => {
      jobPerformance.refetch()
      dataQuality.refetch()
      dataGrowth.refetch()
    },
  }
}

/**
 * useMacroIndicators Hook
 *
 * Fetches macroeconomic indicators (GDP, CPI, unemployment, etc.)
 * Supports both latest values and historical trends
 */

import { useQuery } from '@tanstack/react-query'
import { getEconomicCalendar } from '@/lib/api/fmpMarket'
import axios from 'axios'

const FMP_API_URL = import.meta.env.VITE_FMP_API_URL || 'http://localhost:8113/api/v1'

const api = axios.create({
  baseURL: `${FMP_API_URL}/macro`,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Hook to fetch all available macro indicators (latest values)
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useLatestMacroIndicators()
 * ```
 */
export function useLatestMacroIndicators({
  refetchInterval = 300000, // 5 minutes
  enabled = true,
}: {
  refetchInterval?: number
  enabled?: boolean
} = {}) {
  return useQuery({
    queryKey: ['macro-indicators-latest'],
    queryFn: getEconomicCalendar,
    enabled,
    refetchInterval,
    staleTime: 1000 * 60 * 2, // 2 minutes
    gcTime: 1000 * 60 * 30,   // 30 minutes
  })
}

/**
 * Hook to fetch list of available macro indicators
 *
 * Backend endpoint: GET /macro/indicators
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useMacroIndicatorsList()
 * ```
 */
export function useMacroIndicatorsList({
  enabled = true,
}: {
  enabled?: boolean
} = {}) {
  return useQuery({
    queryKey: ['macro-indicators-list'],
    queryFn: () => api.get('/indicators').then(res => res.data),
    enabled,
    staleTime: 1000 * 60 * 60, // 1 hour - list rarely changes
    gcTime: 1000 * 60 * 60 * 2, // 2 hours
  })
}

/**
 * Hook to fetch historical data for a specific macro indicator
 *
 * Backend endpoint: GET /macro/indicators/{indicator_name}
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useMacroIndicatorDetail({
 *   indicatorName: 'GDP',
 *   fromDate: '2020-01-01',
 *   toDate: '2024-12-31'
 * })
 * ```
 */
export function useMacroIndicatorDetail({
  indicatorName,
  fromDate,
  toDate,
  enabled = true,
}: {
  indicatorName: string
  fromDate?: string  // YYYY-MM-DD
  toDate?: string    // YYYY-MM-DD
  enabled?: boolean
}) {
  return useQuery({
    queryKey: ['macro-indicator-detail', indicatorName, fromDate, toDate],
    queryFn: () =>
      api
        .get(`/indicators/${indicatorName}`, {
          params: {
            from_date: fromDate,
            to_date: toDate,
          },
        })
        .then(res => res.data),
    enabled: enabled && !!indicatorName,
    staleTime: 1000 * 60 * 30, // 30 minutes
    gcTime: 1000 * 60 * 60,    // 1 hour
  })
}

/**
 * Hook to fetch multiple macro indicators at once
 *
 * @example
 * ```tsx
 * const queries = useMacroIndicatorsBatch({
 *   indicators: ['GDP', 'CPI', 'UNEMPLOYMENT'],
 *   fromDate: '2020-01-01',
 *   toDate: '2024-12-31'
 * })
 * ```
 */
export function useMacroIndicatorsBatch({
  indicators,
  fromDate,
  toDate,
  enabled = true,
}: {
  indicators: string[]
  fromDate?: string
  toDate?: string
  enabled?: boolean
}) {
  return indicators.map(indicator =>
    useQuery({
      queryKey: ['macro-indicator-detail', indicator, fromDate, toDate],
      queryFn: () =>
        api
          .get(`/indicators/${indicator}`, {
            params: {
              from_date: fromDate,
              to_date: toDate,
            },
          })
          .then(res => res.data),
      enabled: enabled && !!indicator,
      staleTime: 1000 * 60 * 30,
      gcTime: 1000 * 60 * 60,
    })
  )
}

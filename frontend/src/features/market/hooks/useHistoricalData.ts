/**
 * useHistoricalData Hook
 *
 * Fetches historical price data for market assets (indices, forex, commodities, crypto)
 * with React Query caching and automatic refetching
 */

import { useQuery } from '@tanstack/react-query'
import { getHistoricalData, type HistoricalParams } from '@/lib/api/fmpMarket'

export interface UseHistoricalDataOptions {
  assetType: 'indices' | 'forex' | 'commodities' | 'crypto'
  symbol: string
  fromDate: string // YYYY-MM-DD
  toDate: string   // YYYY-MM-DD
  enabled?: boolean // Optional: disable query
}

/**
 * Hook to fetch historical data for a specific asset
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useHistoricalData({
 *   assetType: 'indices',
 *   symbol: '^GSPC',
 *   fromDate: '2024-01-01',
 *   toDate: '2024-12-31'
 * })
 * ```
 */
export function useHistoricalData({
  assetType,
  symbol,
  fromDate,
  toDate,
  enabled = true,
}: UseHistoricalDataOptions) {
  const params: HistoricalParams = {
    from_date: fromDate,
    to_date: toDate,
  }

  return useQuery({
    queryKey: ['historical-data', assetType, symbol, fromDate, toDate],
    queryFn: () => getHistoricalData(assetType, symbol, params),
    enabled: enabled && !!symbol && !!fromDate && !!toDate,
    staleTime: 1000 * 60 * 30, // 30 minutes - historical data doesn't change
    gcTime: 1000 * 60 * 60,    // 1 hour - keep in cache longer
  })
}

/**
 * Hook to fetch historical data for multiple symbols
 *
 * @example
 * ```tsx
 * const queries = useHistoricalDataBatch({
 *   assetType: 'indices',
 *   symbols: ['^GSPC', '^DJI', '^IXIC'],
 *   fromDate: '2024-01-01',
 *   toDate: '2024-12-31'
 * })
 * ```
 */
export function useHistoricalDataBatch({
  assetType,
  symbols,
  fromDate,
  toDate,
  enabled = true,
}: {
  assetType: 'indices' | 'forex' | 'commodities' | 'crypto'
  symbols: string[]
  fromDate: string
  toDate: string
  enabled?: boolean
}) {
  // Create array of query options for useQueries
  const params: HistoricalParams = {
    from_date: fromDate,
    to_date: toDate,
  }

  return symbols.map(symbol =>
    useQuery({
      queryKey: ['historical-data', assetType, symbol, fromDate, toDate],
      queryFn: () => getHistoricalData(assetType, symbol, params),
      enabled: enabled && !!symbol && !!fromDate && !!toDate,
      staleTime: 1000 * 60 * 30,
      gcTime: 1000 * 60 * 60,
    })
  )
}

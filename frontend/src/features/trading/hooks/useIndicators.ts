/**
 * React Query Hooks for Technical Indicators
 *
 * Provides real-time indicator data with automatic caching and polling
 */

import { useQuery } from '@tanstack/react-query'
import type { UseQueryOptions } from '@tanstack/react-query'
import { predictionService } from '@/lib/api/prediction-service'
import type { IndicatorsSnapshot, HistoricalIndicator } from '@/types/indicators'

/**
 * Query key factory for indicators
 */
export const indicatorKeys = {
  all: ['indicators'] as const,
  symbols: () => [...indicatorKeys.all, 'symbols'] as const,
  current: (symbol: string) => [...indicatorKeys.all, 'current', symbol] as const,
  historical: (symbol: string) => [...indicatorKeys.all, 'historical', symbol] as const,
}

/**
 * Hook to fetch current indicators for a symbol
 *
 * Features:
 * - Auto-refresh every 60 seconds
 * - Cache for 30 seconds
 * - Stale-while-revalidate pattern
 *
 * @param symbol Trading symbol (e.g., "BTCUSDT")
 * @param options Query options
 * @returns Current indicators snapshot
 */
export function useIndicators(
  symbol: string,
  options?: Omit<
    UseQueryOptions<IndicatorsSnapshot, Error>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<IndicatorsSnapshot, Error>({
    queryKey: indicatorKeys.current(symbol),
    queryFn: () => predictionService.getIndicators(symbol),
    // Refresh every 60 seconds (matches backend cache TTL)
    refetchInterval: 60_000,
    // Consider data fresh for 30 seconds
    staleTime: 30_000,
    // Retry on failure
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    ...options,
  })
}

/**
 * Hook to fetch historical indicators (24h)
 *
 * @param symbol Trading symbol (e.g., "BTCUSDT")
 * @param options Query options
 * @returns Historical indicator data
 */
export function useHistoricalIndicators(
  symbol: string,
  options?: Omit<
    UseQueryOptions<HistoricalIndicator[], Error>,
    'queryKey' | 'queryFn'
  >
) {
  return useQuery<HistoricalIndicator[], Error>({
    queryKey: indicatorKeys.historical(symbol),
    queryFn: () => predictionService.getHistoricalIndicators(symbol),
    // Less frequent refresh for historical data
    refetchInterval: 300_000, // 5 minutes
    staleTime: 120_000, // 2 minutes
    retry: 3,
    ...options,
  })
}

/**
 * Hook to fetch available symbols
 *
 * @param options Query options
 * @returns Available Bybit symbols
 */
export function useAvailableSymbols(
  options?: Omit<UseQueryOptions<string[], Error>, 'queryKey' | 'queryFn'>
) {
  return useQuery<string[], Error>({
    queryKey: indicatorKeys.symbols(),
    queryFn: () => predictionService.getAvailableSymbols(),
    // Symbols rarely change, cache for 1 hour
    staleTime: 3600_000,
    // Cache indefinitely
    cacheTime: Infinity,
    retry: 3,
    ...options,
  })
}

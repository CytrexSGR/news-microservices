/**
 * Hook for Market News & Events
 */

import { useQuery } from '@tanstack/react-query'
import * as fmpMarket from '@/lib/api/fmpMarket'
import type { NewsParams, CalendarParams } from '@/lib/api/fmpMarket'

/**
 * Hook to fetch general financial news
 * Endpoint: GET /news?page={page}&limit={limit}&symbol={symbol}
 */
export function useGeneralNews(params?: NewsParams) {
  return useQuery({
    queryKey: ['market', 'news', 'general', params],
    queryFn: () => fmpMarket.getGeneralNews(params),
    refetchInterval: 300000, // 5 minutes
    staleTime: 120000, // 2 minutes
  })
}

/**
 * Hook to fetch stock-specific news
 * Endpoint: GET /news/stock?page={page}&limit={limit}
 */
export function useStockNews(params?: NewsParams) {
  return useQuery({
    queryKey: ['market', 'news', 'stock', params],
    queryFn: () => fmpMarket.getStockNews(params),
    refetchInterval: 300000,
    staleTime: 120000,
  })
}

/**
 * Hook to fetch news by symbol (stocks, forex, crypto)
 * Endpoint: GET /news/by-symbol/{symbol}?days={days}&limit={limit}
 */
export function useNewsBySymbol(symbol: string, days: number = 7, limit: number = 50) {
  return useQuery({
    queryKey: ['market', 'news', 'by-symbol', symbol, days, limit],
    queryFn: () => fmpMarket.getNewsBySymbol(symbol, days, limit),
    enabled: Boolean(symbol), // Only fetch if symbol provided
    refetchInterval: 300000,
    staleTime: 120000,
  })
}

/**
 * Hook to fetch forex news (using live news endpoint)
 * Endpoint: GET /news/live/forex?page={page}&limit={limit}
 */
export function useForexNews(page: number = 0, limit: number = 50) {
  return useQuery({
    queryKey: ['market', 'news', 'forex', page, limit],
    queryFn: () => fmpMarket.getLiveForexNews(page, limit),
    refetchInterval: 300000,
    staleTime: 120000,
  })
}

/**
 * Hook to fetch crypto news (using live news endpoint)
 * Endpoint: GET /news/live/crypto?page={page}&limit={limit}
 */
export function useCryptoNews(page: number = 0, limit: number = 50) {
  return useQuery({
    queryKey: ['market', 'news', 'crypto', page, limit],
    queryFn: () => fmpMarket.getLiveCryptoNews(page, limit),
    refetchInterval: 300000,
    staleTime: 120000,
  })
}

// ==================== Live News Hooks (Real-time from FMP) ====================

/**
 * Hook to fetch live general financial news (real-time)
 * Endpoint: GET /news/live/general?page={page}&limit={limit}
 */
export function useLiveGeneralNews(page: number = 0, limit: number = 20) {
  return useQuery({
    queryKey: ['market', 'news', 'live', 'general', page, limit],
    queryFn: () => fmpMarket.getLiveGeneralNews(page, limit),
    refetchInterval: 60000, // 1 minute (more frequent for live data)
    staleTime: 30000, // 30 seconds
  })
}

/**
 * Hook to fetch live stock market news (real-time)
 * Endpoint: GET /news/live/stock?page={page}&limit={limit}
 */
export function useLiveStockNews(page: number = 0, limit: number = 20) {
  return useQuery({
    queryKey: ['market', 'news', 'live', 'stock', page, limit],
    queryFn: () => fmpMarket.getLiveStockNews(page, limit),
    refetchInterval: 60000, // 1 minute
    staleTime: 30000, // 30 seconds
  })
}

/**
 * Hook to fetch live forex news (real-time)
 * Endpoint: GET /news/live/forex?page={page}&limit={limit}
 */
export function useLiveForexNews(page: number = 0, limit: number = 20) {
  return useQuery({
    queryKey: ['market', 'news', 'live', 'forex', page, limit],
    queryFn: () => fmpMarket.getLiveForexNews(page, limit),
    refetchInterval: 60000, // 1 minute
    staleTime: 30000, // 30 seconds
  })
}

/**
 * Hook to fetch live crypto news (real-time)
 * Endpoint: GET /news/live/crypto?page={page}&limit={limit}
 */
export function useLiveCryptoNews(page: number = 0, limit: number = 20) {
  return useQuery({
    queryKey: ['market', 'news', 'live', 'crypto', page, limit],
    queryFn: () => fmpMarket.getLiveCryptoNews(page, limit),
    refetchInterval: 60000, // 1 minute
    staleTime: 30000, // 30 seconds
  })
}

/**
 * Hook to fetch live mergers & acquisitions news (real-time)
 * Endpoint: GET /news/live/mergers-acquisitions?page={page}&limit={limit}
 */
export function useLiveMergersAcquisitions(page: number = 0, limit: number = 20) {
  return useQuery({
    queryKey: ['market', 'news', 'live', 'mergers-acquisitions', page, limit],
    queryFn: () => fmpMarket.getLiveMergersAcquisitions(page, limit),
    refetchInterval: 60000, // 1 minute
    staleTime: 30000, // 30 seconds
  })
}

/**
 * Hook to fetch latest macroeconomic indicators
 * Endpoint: GET /macro/latest
 */
export function useEconomicCalendar() {
  return useQuery({
    queryKey: ['market', 'macro', 'latest'],
    queryFn: () => fmpMarket.getEconomicCalendar(),
    refetchInterval: 3600000, // 1 hour
    staleTime: 1800000, // 30 minutes
  })
}

/**
 * Hook to fetch earnings calendar events
 * Endpoint: GET /earnings/calendar?from_date={from}&to_date={to}&symbol={symbol}&limit={limit}
 */
export function useEarningsCalendar(params?: CalendarParams) {
  return useQuery({
    queryKey: ['market', 'calendar', 'earnings', params],
    queryFn: () => fmpMarket.getEarningsCalendar(params),
    refetchInterval: 3600000, // 1 hour
    staleTime: 1800000, // 30 minutes
  })
}

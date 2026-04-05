/**
 * FMP Service Market Data API Client
 * Real-time quotes, news, and calendar events
 */

import axios from 'axios'
import type {
  FMPNews,
  EarningsEvent,
  MacroIndicator,
} from '@/features/market/types/market.types'

const FMP_API_URL = import.meta.env.VITE_FMP_API_URL || 'http://localhost:8113/api/v1'

const api = axios.create({
  baseURL: FMP_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ==================== Quote Endpoints (Phase 6 Unified) ====================

export type AssetType = 'indices' | 'forex' | 'commodities' | 'crypto'

export interface UnifiedQuote {
  symbol: string
  asset_type: AssetType
  timestamp: string
  price: number
  change?: number
  change_percent?: number
  volume?: number
  bid?: number
  ask?: number
  day_open?: number
  day_high?: number
  day_low?: number
  prev_close?: number
  name?: string
  market_cap?: number
}

export interface QuotesListResponse {
  asset_type: AssetType
  quotes: UnifiedQuote[]
  count: number
  timestamp: string
}

/**
 * [PHASE 6] Get real-time quotes for any asset type
 * Unified endpoint replacing asset-specific endpoints
 * Updates: Every 1 minute
 *
 * @param assetType - indices | forex | commodities | crypto
 * @returns List of quotes for the specified asset type
 *
 * Backend: GET /market/quotes?asset_type={type}
 */
export const getQuotesByAssetType = (assetType: AssetType) =>
  api.get<QuotesListResponse>(`/market/quotes?asset_type=${assetType}`)
    .then(res => res.data.quotes)

/**
 * [PHASE 6] Get quote for a specific symbol
 * Works for any asset type (auto-detected)
 *
 * @param symbol - Asset symbol (e.g., ^GSPC, EURUSD, GCUSD, BTCUSD)
 * @returns Single quote
 *
 * Backend: GET /market/quotes/{symbol}
 */
export const getQuoteBySymbol = (symbol: string) =>
  api.get<UnifiedQuote>(`/market/quotes/${symbol}`)
    .then(res => res.data)

/**
 * Get real-time index quotes (S&P 500, Dow Jones, etc.)
 * Updates: Every 1 minute
 *
 * Uses Phase 6 unified endpoint under the hood
 */
export const getIndices = () =>
  getQuotesByAssetType('indices').then(quotes =>
    quotes.map(quote => ({
      ...quote,
      category: 'index' as const,
      price: parseFloat(String(quote.price)),
      change: quote.change ? parseFloat(String(quote.change)) : undefined,
      change_percent: quote.change_percent ? parseFloat(String(quote.change_percent)) : undefined,
      volume: quote.volume ? parseInt(String(quote.volume)) : undefined,
    }))
  )

/**
 * Get real-time forex quotes (currency pairs)
 * Updates: Every 1 minute
 *
 * Uses Phase 6 unified endpoint under the hood
 */
export const getForex = () =>
  getQuotesByAssetType('forex').then(quotes =>
    quotes.map(quote => ({
      ...quote,
      category: 'forex' as const,
      pair: quote.symbol,
      price: parseFloat(String(quote.price)),
      change: quote.change ? parseFloat(String(quote.change)) : undefined,
      change_percent: quote.change_percent ? parseFloat(String(quote.change_percent)) : undefined,
      bid: quote.bid ? parseFloat(String(quote.bid)) : undefined,
      ask: quote.ask ? parseFloat(String(quote.ask)) : undefined,
      volume: quote.volume ? parseInt(String(quote.volume)) : undefined,
    }))
  )

/**
 * Get real-time commodity quotes (gold, oil, etc.)
 * Updates: Every 5 minutes
 *
 * Uses Phase 6 unified endpoint under the hood
 */
export const getCommodities = () =>
  getQuotesByAssetType('commodities').then(quotes =>
    quotes.map(quote => ({
      ...quote,
      category: 'commodity' as const,
      price: parseFloat(String(quote.price)),
      change: quote.change ? parseFloat(String(quote.change)) : undefined,
      change_percent: quote.change_percent ? parseFloat(String(quote.change_percent)) : undefined,
      volume: quote.volume ? parseInt(String(quote.volume)) : undefined,
      open_price: quote.day_open ? parseFloat(String(quote.day_open)) : undefined,
      day_high: quote.day_high ? parseFloat(String(quote.day_high)) : undefined,
      day_low: quote.day_low ? parseFloat(String(quote.day_low)) : undefined,
    }))
  )

/**
 * Get real-time crypto quotes (bitcoin, ethereum, etc.)
 * Updates: Every 1 minute
 *
 * Uses Phase 6 unified endpoint under the hood
 */
export const getCrypto = () =>
  getQuotesByAssetType('crypto').then(quotes =>
    quotes.map(quote => {
      // Parse market_cap safely - it may be null/undefined
      const parsedMarketCap = quote.market_cap ? parseInt(String(quote.market_cap)) : undefined
      const marketCap = parsedMarketCap && !isNaN(parsedMarketCap) ? parsedMarketCap : undefined

      return {
        ...quote,
        category: 'crypto' as const,
        price: parseFloat(String(quote.price)),
        change: quote.change ? parseFloat(String(quote.change)) : undefined,
        change_percent: quote.change_percent ? parseFloat(String(quote.change_percent)) : undefined,
        volume: quote.volume ? parseInt(String(quote.volume)) : undefined,
        market_cap: marketCap,
        open_price: quote.day_open ? parseFloat(String(quote.day_open)) : undefined,
        day_high: quote.day_high ? parseFloat(String(quote.day_high)) : undefined,
        day_low: quote.day_low ? parseFloat(String(quote.day_low)) : undefined,
      }
    })
  )

// ==================== News Endpoints ====================

export interface NewsParams {
  page?: number
  size?: number
  symbol?: string
}

// ==================== Database News Endpoints (Stored News) ====================

/**
 * Get general financial news from database
 * Backend endpoint: GET /news?page={page}&limit={limit}&symbol={symbol}
 */
export const getGeneralNews = (params?: NewsParams) =>
  api.get<FMPNews[]>('/news', { params }).then(res => res.data)

/**
 * Get stock-specific news from database
 * Backend endpoint: GET /news/stock?page={page}&limit={limit}
 */
export const getStockNews = (params?: NewsParams) =>
  api.get<FMPNews[]>('/news/stock', { params }).then(res => res.data)

/**
 * Get news by symbol (can be used for stocks, forex, crypto)
 * Backend endpoint: GET /news/by-symbol/{symbol}?days={days}&limit={limit}
 */
export const getNewsBySymbol = (symbol: string, days: number = 7, limit: number = 50) =>
  api.get<FMPNews[]>(`/news/by-symbol/${symbol}`, {
    params: { days, limit }
  }).then(res => res.data)

// ==================== Live News Endpoints (Direct from FMP API) ====================

/**
 * Get live general financial news (real-time from FMP)
 * Backend endpoint: GET /news/live/general?page={page}&limit={limit}
 */
export const getLiveGeneralNews = (page: number = 0, limit: number = 20) =>
  api.get<FMPNews[]>('/news/live/general', {
    params: { page, limit }
  }).then(res => res.data)

/**
 * Get live stock market news (real-time from FMP)
 * Backend endpoint: GET /news/live/stock?page={page}&limit={limit}
 */
export const getLiveStockNews = (page: number = 0, limit: number = 20) =>
  api.get<FMPNews[]>('/news/live/stock', {
    params: { page, limit }
  }).then(res => res.data)

/**
 * Get live forex news (real-time from FMP)
 * Backend endpoint: GET /news/live/forex?page={page}&limit={limit}
 */
export const getLiveForexNews = (page: number = 0, limit: number = 20) =>
  api.get<FMPNews[]>('/news/live/forex', {
    params: { page, limit }
  }).then(res => res.data)

/**
 * Get live crypto news (real-time from FMP)
 * Backend endpoint: GET /news/live/crypto?page={page}&limit={limit}
 */
export const getLiveCryptoNews = (page: number = 0, limit: number = 20) =>
  api.get<FMPNews[]>('/news/live/crypto', {
    params: { page, limit }
  }).then(res => res.data)

/**
 * Get live mergers & acquisitions news (real-time from FMP)
 * Backend endpoint: GET /news/live/mergers-acquisitions?page={page}&limit={limit}
 */
export const getLiveMergersAcquisitions = (page: number = 0, limit: number = 20) =>
  api.get<FMPNews[]>('/news/live/mergers-acquisitions', {
    params: { page, limit }
  }).then(res => res.data)

// ==================== Calendar Endpoints ====================

export interface CalendarParams {
  from_date?: string // YYYY-MM-DD
  to_date?: string   // YYYY-MM-DD
  symbol?: string
  limit?: number
}

/**
 * Get latest macroeconomic indicators (GDP, CPI, unemployment, etc.)
 * Backend endpoint: GET /macro/latest
 */
export const getEconomicCalendar = () =>
  api.get<MacroIndicator[]>('/macro/latest').then(res => res.data)

/**
 * Get earnings calendar events
 * Backend endpoint: GET /earnings/calendar?from_date={from}&to_date={to}&symbol={symbol}&limit={limit}
 */
export const getEarningsCalendar = (params?: CalendarParams) =>
  api.get<EarningsEvent[]>('/earnings/calendar', { params }).then(res => res.data)

// ==================== Historical Data ====================

export interface HistoricalParams {
  from_date: string // YYYY-MM-DD
  to_date: string   // YYYY-MM-DD
}

/**
 * Get historical data for a symbol
 * @param assetType - indices | forex | commodities | crypto
 * @param symbol - Asset symbol
 * @param params - Date range
 *
 * Backend Routes:
 * - indices:     GET /quotes/history/{symbol}
 * - forex:       GET /forex/history/{pair}
 * - commodities: GET /commodities/history/{symbol}
 * - crypto:      GET /crypto/history/{symbol}
 */
export const getHistoricalData = (
  assetType: 'indices' | 'forex' | 'commodities' | 'crypto',
  symbol: string,
  params: HistoricalParams
) => {
  // Map asset type to correct backend route
  const routes = {
    indices: `/quotes/history/${symbol}`,
    forex: `/forex/history/${symbol}`,
    commodities: `/commodities/history/${symbol}`,
    crypto: `/crypto/history/${symbol}`
  }

  return api.get(routes[assetType], { params }).then(res => res.data)
}

// ==================== Tier Management API ====================

export type TierLevel = 'tier1' | 'tier2' | 'tier3'

export interface TierStatistics {
  tier1_configured: number
  tier1_actual: number
  tier1_synced: boolean
  tier1_interval: string
  tier1_data_type: string

  tier2_configured: number
  tier2_actual: number
  tier2_synced: boolean
  tier2_interval: string
  tier2_data_type: string

  tier3_configured: number
  tier3_actual: number
  tier3_synced: boolean
  tier3_interval: string
  tier3_data_type: string

  total_configured: number
  total_actual: number
  rate_limit_utilization: number
  reserve_capacity: number
  timestamp: string
}

export interface SymbolTierInfo {
  symbol: string
  tier: TierLevel
  asset_type: AssetType
  in_database: boolean
  last_update: string | null
  interval: string
  data_type: string
}

export interface SymbolListResponse {
  symbols: SymbolTierInfo[]
  total: number
  limit: number
  offset: number
  timestamp: string
}

export interface SymbolCreateRequest {
  symbol: string
  tier: TierLevel
  asset_type: AssetType
  subsection?: string
}

export interface SymbolUpdateRequest {
  new_tier: TierLevel
  new_asset_type?: AssetType
  subsection?: string
}

export interface SymbolResponse {
  success: boolean
  message: string
  symbol: string
  tier: TierLevel
  asset_type: AssetType
  note: string
  timestamp: string
}

export interface SymbolDeleteResponse extends SymbolResponse {
  data_deleted: boolean
}

/**
 * Get tier statistics (configured vs actual symbol counts)
 *
 * Backend: GET /admin/tiers/statistics
 */
export const getTierStatistics = () =>
  api.get<TierStatistics>('/admin/tiers/statistics')
    .then(res => res.data)

/**
 * List symbols with tier assignments
 *
 * @param params - Filter parameters
 *
 * Backend: GET /admin/tiers/symbols
 */
export const listSymbols = (params?: {
  tier?: TierLevel
  asset_type?: AssetType
  search?: string
  limit?: number
  offset?: number
}) =>
  api.get<SymbolListResponse>('/admin/tiers/symbols', { params })
    .then(res => res.data)

/**
 * Reload tier configuration from JSON file
 *
 * Backend: POST /admin/tiers/reload
 */
export const reloadTierConfig = () =>
  api.post<{ success: boolean; message: string; version: string }>('/admin/tiers/reload')
    .then(res => res.data)

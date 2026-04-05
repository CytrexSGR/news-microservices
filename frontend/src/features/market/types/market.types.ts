/**
 * Unified Market Data Types for FMP Service Integration
 * Consolidates: Indices, Forex, Commodities, Crypto, News, Events
 */

// ==================== Quote Types ====================

export type MarketCategory = 'index' | 'forex' | 'commodity' | 'crypto'

/**
 * Unified Quote Interface - Base structure for all market quotes
 */
export interface UnifiedQuote {
  symbol: string
  name: string
  price: number
  change: number
  change_percent: number
  volume?: number
  timestamp: string
  category: MarketCategory
}

/**
 * Index Quote (S&P 500, Dow Jones, etc.)
 */
export interface IndexQuote extends UnifiedQuote {
  category: 'index'
  volume: number
}

/**
 * Forex Quote (Currency Pairs)
 */
export interface ForexQuote extends UnifiedQuote {
  category: 'forex'
  bid: number
  ask: number
}

/**
 * Commodity Quote (Gold, Oil, etc.)
 */
export interface CommodityQuote extends UnifiedQuote {
  category: 'commodity'
  volume: number
  open_price: number
  day_high: number
  day_low: number
}

/**
 * Crypto Quote (Bitcoin, Ethereum, etc.)
 */
export interface CryptoQuote extends UnifiedQuote {
  category: 'crypto'
  volume: number
  market_cap: number
  open_price: number
  day_high: number
  day_low: number
}

// ==================== Market Summary ====================

export interface MarketSummary {
  totalAssets: number
  gainers: number
  losers: number
  unchanged: number
  topGainers: UnifiedQuote[]
  topLosers: UnifiedQuote[]
  lastUpdate: string
}

export interface CategorySummary {
  category: MarketCategory
  totalAssets: number
  avgChange: number
  gainers: number
  losers: number
}

// ==================== News & Events ====================

export interface FMPNews {
  title: string
  content: string
  url: string
  publishedAt: string
  source: string
  symbols: string[]
  sentiment?: 'positive' | 'negative' | 'neutral'
  imageUrl?: string
}

export interface EarningsEvent {
  symbol: string
  companyName: string
  fiscalDate: string
  reportDate: string
  epsActual?: number
  epsEstimate?: number
  revenueActual?: number
  revenueEstimate?: number
  time: 'bmo' | 'amc' // Before Market Open / After Market Close
}

export interface MacroIndicator {
  indicatorName: string
  value: number
  period: string
  releaseDate: string
}

// ==================== Filters & Sorting ====================

export interface QuoteFilters {
  categories: MarketCategory[]
  changeDirection?: 'up' | 'down' | 'all'
  minChange?: number
  maxChange?: number
  search?: string
}

export type SortField = 'symbol' | 'name' | 'price' | 'change' | 'change_percent' | 'volume'
export type SortDirection = 'asc' | 'desc'

export interface SortConfig {
  field: SortField
  direction: SortDirection
}

// ==================== Historical Data ====================

export interface HistoricalDataPoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume?: number
}

// ==================== Response Types ====================

export interface MarketDataResponse {
  indices: IndexQuote[]
  forex: ForexQuote[]
  commodities: CommodityQuote[]
  crypto: CryptoQuote[]
  lastUpdate: string
}

export interface NewsResponse {
  articles: FMPNews[]
  total: number
  page: number
  pageSize: number
}

export interface CalendarResponse {
  earnings: EarningsEvent[]
  macroEvents: MacroIndicator[]
}

/**
 * Market Data Utility Functions
 * Formatting, calculations, and helpers for market data display
 */

import type { MarketCategory } from '@/features/market/types/market.types'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Bitcoin,
  BarChart3,
  Coins,
  type LucideIcon,
} from 'lucide-react'

/**
 * Format price with appropriate decimal places
 */
export function formatPrice(price: number | undefined | null, decimals: number = 2): string {
  if (price === null || price === undefined || isNaN(price)) {
    return 'N/A'
  }
  if (price >= 1000) {
    return price.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })
  }
  // For prices < 1, show more decimals
  if (price < 1) {
    decimals = Math.max(4, decimals)
  }
  return price.toFixed(decimals)
}

/**
 * Format change value with sign and color
 */
export function formatChange(change: number | undefined | null, decimals: number = 2): string {
  if (change === null || change === undefined || isNaN(change)) {
    return 'N/A'
  }
  const sign = change > 0 ? '+' : ''
  return `${sign}${formatPrice(change, decimals)}`
}

/**
 * Format percentage change with sign
 */
export function formatChangePercent(changePercent: number | undefined | null): string {
  if (changePercent === null || changePercent === undefined || isNaN(changePercent)) {
    return 'N/A'
  }
  const sign = changePercent > 0 ? '+' : ''
  return `${sign}${changePercent.toFixed(2)}%`
}

/**
 * Format volume (compact format for large numbers)
 */
export function formatVolume(volume: number | undefined | null): string {
  if (volume === null || volume === undefined || isNaN(volume)) {
    return 'N/A'
  }
  if (volume >= 1_000_000_000) {
    return `${(volume / 1_000_000_000).toFixed(2)}B`
  }
  if (volume >= 1_000_000) {
    return `${(volume / 1_000_000).toFixed(2)}M`
  }
  if (volume >= 1_000) {
    return `${(volume / 1_000).toFixed(2)}K`
  }
  return volume.toLocaleString()
}

/**
 * Format market cap (compact format)
 */
export function formatMarketCap(marketCap: number | undefined | null): string {
  if (!marketCap || isNaN(marketCap)) {
    return 'N/A'
  }
  if (marketCap >= 1_000_000_000_000) {
    return `$${(marketCap / 1_000_000_000_000).toFixed(2)}T`
  }
  if (marketCap >= 1_000_000_000) {
    return `$${(marketCap / 1_000_000_000).toFixed(2)}B`
  }
  if (marketCap >= 1_000_000) {
    return `$${(marketCap / 1_000_000).toFixed(2)}M`
  }
  return `$${marketCap.toLocaleString()}`
}

/**
 * Get color class based on change value
 */
export function getChangeColor(change: number): string {
  if (change > 0) return 'text-green-600 dark:text-green-400'
  if (change < 0) return 'text-red-600 dark:text-red-400'
  return 'text-muted-foreground'
}

/**
 * Get background color class based on change value
 */
export function getChangeBgColor(change: number): string {
  if (change > 0) return 'bg-green-500/10 border-green-500/20 text-green-600 dark:text-green-400'
  if (change < 0) return 'bg-red-500/10 border-red-500/20 text-red-600 dark:text-red-400'
  return 'bg-muted/50 border-border text-muted-foreground'
}

/**
 * Get icon for market category
 */
export function getCategoryIcon(category: MarketCategory): LucideIcon {
  const icons: Record<MarketCategory, LucideIcon> = {
    index: BarChart3,
    forex: DollarSign,
    commodity: Coins,
    crypto: Bitcoin,
  }
  return icons[category]
}

/**
 * Get category display name
 */
export function getCategoryName(category: MarketCategory): string {
  const names: Record<MarketCategory, string> = {
    index: 'Indices',
    forex: 'Forex',
    commodity: 'Commodities',
    crypto: 'Crypto',
  }
  return names[category]
}

/**
 * Get trend icon based on change
 */
export function getTrendIcon(change: number): LucideIcon {
  return change >= 0 ? TrendingUp : TrendingDown
}

/**
 * Check if market is currently open (simplified - for display purposes)
 * Note: Actual market hours depend on specific market and timezone
 */
export function getMarketStatus(category: MarketCategory): {
  isOpen: boolean
  status: string
} {
  const now = new Date()
  const day = now.getDay() // 0 = Sunday, 6 = Saturday
  const hour = now.getHours()

  // Crypto: Always open (24/7)
  if (category === 'crypto') {
    return { isOpen: true, status: 'Open 24/7' }
  }

  // Forex: Closed on weekends
  if (category === 'forex') {
    if (day === 0 || day === 6) {
      return { isOpen: false, status: 'Closed (Weekend)' }
    }
    return { isOpen: true, status: 'Open' }
  }

  // Indices & Commodities: Weekdays only, typical trading hours
  if (day === 0 || day === 6) {
    return { isOpen: false, status: 'Closed (Weekend)' }
  }

  // Simplified: 9:30 AM - 4:00 PM ET (14:30 - 21:00 UTC)
  // Note: This is approximation, actual hours vary
  if (hour >= 9 && hour < 16) {
    return { isOpen: true, status: 'Open' }
  }

  return { isOpen: false, status: 'Closed' }
}

/**
 * Calculate total change for an array of quotes
 */
export function calculateTotalChange(changes: number[]): number {
  if (changes.length === 0) return 0
  return changes.reduce((sum, change) => sum + change, 0) / changes.length
}

/**
 * Get top gainers/losers from quotes
 */
export function getTopMovers<T extends { change: number }>(
  quotes: T[],
  count: number = 5,
  type: 'gainers' | 'losers' = 'gainers'
): T[] {
  const sorted = [...quotes].sort((a, b) =>
    type === 'gainers' ? b.change - a.change : a.change - b.change
  )
  return sorted.slice(0, count)
}

/**
 * Format timestamp to relative time
 */
export function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`

  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`

  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}

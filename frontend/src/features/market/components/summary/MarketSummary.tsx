/**
 * MarketSummary Component - Overview tab showing market highlights
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { TrendingUp, TrendingDown, Activity } from 'lucide-react'
import { QuoteCard } from '../quotes/QuoteCard'
import type { UnifiedQuote } from '@/features/market/types/market.types'
import {
  formatChangePercent,
  getTopMovers,
  getCategoryIcon,
  getCategoryName,
} from '@/lib/utils/marketUtils'

interface MarketSummaryProps {
  allQuotes: UnifiedQuote[]
  onQuoteClick?: (quote: UnifiedQuote) => void
}

export function MarketSummary({ allQuotes, onQuoteClick }: MarketSummaryProps) {
  // Calculate market metrics
  const totalAssets = allQuotes.length
  const gainers = allQuotes.filter((q) => q.change > 0).length
  const losers = allQuotes.filter((q) => q.change < 0).length
  const unchanged = allQuotes.filter((q) => q.change === 0).length

  // Get top movers
  const topGainers = getTopMovers(allQuotes, 5, 'gainers')
  const topLosers = getTopMovers(allQuotes, 5, 'losers')

  // Category summaries
  const categories = ['index', 'forex', 'commodity', 'crypto'] as const
  const categorySummaries = categories.map((category) => {
    const quotes = allQuotes.filter((q) => q.category === category)
    const categoryGainers = quotes.filter((q) => q.change > 0).length
    const categoryLosers = quotes.filter((q) => q.change < 0).length
    const avgChange =
      quotes.length > 0
        ? quotes.reduce((sum, q) => sum + q.change_percent, 0) / quotes.length
        : 0

    const Icon = getCategoryIcon(category)

    return {
      category,
      name: getCategoryName(category),
      icon: Icon,
      total: quotes.length,
      gainers: categoryGainers,
      losers: categoryLosers,
      avgChange,
    }
  })

  return (
    <div className="space-y-6">
      {/* Market Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Assets</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalAssets}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Tracked across 4 categories
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Gainers</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{gainers}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {totalAssets > 0 ? ((gainers / totalAssets) * 100).toFixed(1) : '0.0'}% of market
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Losers</CardTitle>
            <TrendingDown className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{losers}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {totalAssets > 0 ? ((losers / totalAssets) * 100).toFixed(1) : '0.0'}% of market
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Unchanged</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{unchanged}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {totalAssets > 0 ? ((unchanged / totalAssets) * 100).toFixed(1) : '0.0'}% of market
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Category Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Category Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {categorySummaries.map((cat) => (
              <div
                key={cat.category}
                className="p-4 rounded-lg border border-border hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-2 mb-3">
                  <cat.icon className="h-5 w-5 text-primary" />
                  <span className="font-semibold">{cat.name}</span>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total</span>
                    <span className="font-medium">{cat.total}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Avg Change</span>
                    <span
                      className={`font-medium ${
                        cat.avgChange > 0
                          ? 'text-green-600'
                          : cat.avgChange < 0
                          ? 'text-red-600'
                          : ''
                      }`}
                    >
                      {formatChangePercent(cat.avgChange)}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-green-600">↑ {cat.gainers}</span>
                    <span className="text-red-600">↓ {cat.losers}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Top Movers */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Top Gainers */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-600" />
              Top Gainers
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {topGainers.map((quote) => (
              <QuoteCard
                key={`${quote.category}-${quote.symbol}`}
                quote={quote}
                compact
                onClick={() => onQuoteClick?.(quote)}
              />
            ))}
          </CardContent>
        </Card>

        {/* Top Losers */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingDown className="h-5 w-5 text-red-600" />
              Top Losers
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {topLosers.map((quote) => (
              <QuoteCard
                key={`${quote.category}-${quote.symbol}`}
                quote={quote}
                compact
                onClick={() => onQuoteClick?.(quote)}
              />
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

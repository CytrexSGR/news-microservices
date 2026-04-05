/**
 * Reusable Quote Card Component
 * Displays individual market quote with key metrics
 */

import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import type { UnifiedQuote, ForexQuote, CommodityQuote, CryptoQuote } from '@/features/market/types/market.types'
import {
  formatPrice,
  formatChange,
  formatChangePercent,
  formatVolume,
  formatMarketCap,
  formatTimestamp,
  getChangeColor,
  getChangeBgColor,
  getTrendIcon,
} from '@/lib/utils/marketUtils'

interface QuoteCardProps {
  quote: UnifiedQuote
  onClick?: () => void
  compact?: boolean
  showDetails?: boolean
}

export function QuoteCard({ quote, onClick, compact = false, showDetails = true }: QuoteCardProps) {
  const TrendIcon = getTrendIcon(quote.change)
  const changeColor = getChangeColor(quote.change)
  const changeBg = getChangeBgColor(quote.change)

  // Type guards for extended quote types
  const isForex = quote.category === 'forex'
  const isCommodity = quote.category === 'commodity'
  const isCrypto = quote.category === 'crypto'

  const forexQuote = isForex ? (quote as ForexQuote) : null
  const commodityQuote = isCommodity ? (quote as CommodityQuote) : null
  const cryptoQuote = isCrypto ? (quote as CryptoQuote) : null

  if (compact) {
    return (
      <Card
        className="p-4 hover:shadow-md transition-shadow cursor-pointer"
        onClick={onClick}
      >
        <div className="flex items-center justify-between">
          <div>
            <div className="font-semibold text-sm">{quote.symbol}</div>
            <div className="text-xs text-muted-foreground">{quote.name}</div>
          </div>
          <div className="text-right">
            <div className="font-bold">${formatPrice(quote.price)}</div>
            <div className={`text-xs ${changeColor} flex items-center gap-1 justify-end`}>
              <TrendIcon className="h-3 w-3" />
              {formatChangePercent(quote.change_percent)}
            </div>
          </div>
        </div>
      </Card>
    )
  }

  return (
    <Card
      className="p-6 hover:shadow-md transition-shadow cursor-pointer"
      onClick={onClick}
    >
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold">{quote.symbol}</h3>
              <Badge variant="outline" className="text-xs">
                {quote.category}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground mt-1">{quote.name}</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">${formatPrice(quote.price)}</div>
            <div className="text-xs text-muted-foreground mt-1">
              {formatTimestamp(quote.timestamp)}
            </div>
          </div>
        </div>

        {/* Change Metrics */}
        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-1 px-3 py-1.5 rounded-full border ${changeBg}`}>
            <TrendIcon className="h-4 w-4" />
            <span className="font-semibold">{formatChange(quote.change)}</span>
          </div>
          <div className={`px-3 py-1.5 rounded-full border ${changeBg}`}>
            <span className="font-semibold">{formatChangePercent(quote.change_percent)}</span>
          </div>
        </div>

        {/* Extended Details */}
        {showDetails && (
          <div className="grid grid-cols-2 gap-3 pt-3 border-t border-border text-sm">
            {/* Forex-specific */}
            {forexQuote && (
              <>
                <div>
                  <div className="text-muted-foreground">Bid</div>
                  <div className="font-medium">${formatPrice(forexQuote.bid, 5)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Ask</div>
                  <div className="font-medium">${formatPrice(forexQuote.ask, 5)}</div>
                </div>
              </>
            )}

            {/* Commodity-specific */}
            {commodityQuote && (
              <>
                <div>
                  <div className="text-muted-foreground">Open</div>
                  <div className="font-medium">${formatPrice(commodityQuote.open_price)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Volume</div>
                  <div className="font-medium">{formatVolume(commodityQuote.volume)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Day High</div>
                  <div className="font-medium text-green-600">${formatPrice(commodityQuote.day_high)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Day Low</div>
                  <div className="font-medium text-red-600">${formatPrice(commodityQuote.day_low)}</div>
                </div>
              </>
            )}

            {/* Crypto-specific */}
            {cryptoQuote && (
              <>
                <div>
                  <div className="text-muted-foreground">Market Cap</div>
                  <div className="font-medium">{formatMarketCap(cryptoQuote.market_cap)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Volume 24h</div>
                  <div className="font-medium">{formatVolume(cryptoQuote.volume)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Day High</div>
                  <div className="font-medium text-green-600">${formatPrice(cryptoQuote.day_high)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Day Low</div>
                  <div className="font-medium text-red-600">${formatPrice(cryptoQuote.day_low)}</div>
                </div>
              </>
            )}

            {/* Standard volume for indices */}
            {!isForex && !isCommodity && !isCrypto && quote.volume && (
              <div className="col-span-2">
                <div className="text-muted-foreground">Volume</div>
                <div className="font-medium">{formatVolume(quote.volume)}</div>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  )
}

/**
 * CommoditiesTab - Display commodity quotes grouped by category
 */

import { QuoteCard } from './QuoteCard'
import { QuoteTable } from './QuoteTable'
import { Button } from '@/components/ui/Button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { LayoutGrid, List } from 'lucide-react'
import { useState, useMemo } from 'react'
import type { CommodityQuote } from '@/features/market/types/market.types'

interface CommoditiesTabProps {
  commodities: CommodityQuote[]
  isLoading: boolean
  onQuoteClick?: (quote: CommodityQuote) => void
}

// Categorize commodities
const COMMODITY_GROUPS = {
  'Precious Metals': ['GCUSD', 'SIUSD', 'PLUSD', 'PAUSD'],
  'Energy': ['CLUSD', 'NGUSD', 'HOUSD'],
  'Agriculture': ['ZCUSD', 'ZSUSD', 'WTUSD', 'KCUSD', 'CCUSD'],
}

export function CommoditiesTab({ commodities, isLoading, onQuoteClick }: CommoditiesTabProps) {
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid')

  // Group commodities by category
  const groupedCommodities = useMemo(() => {
    return Object.entries(COMMODITY_GROUPS).map(([category, symbols]) => ({
      category,
      items: commodities.filter((c) => symbols.includes(c.symbol)),
    }))
  }, [commodities])

  if (isLoading) {
    return (
      <div className="space-y-6">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="space-y-4">
            <div className="h-6 w-32 bg-muted animate-pulse rounded"></div>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {Array.from({ length: 4 }).map((_, j) => (
                <div key={j} className="h-48 bg-muted animate-pulse rounded-lg"></div>
              ))}
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (!commodities || commodities.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        No commodity data available
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* View Mode Toggle */}
      <div className="flex justify-end gap-2">
        <Button
          variant={viewMode === 'grid' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setViewMode('grid')}
        >
          <LayoutGrid className="h-4 w-4 mr-2" />
          Grid
        </Button>
        <Button
          variant={viewMode === 'table' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setViewMode('table')}
        >
          <List className="h-4 w-4 mr-2" />
          Table
        </Button>
      </div>

      {/* Content */}
      {viewMode === 'grid' ? (
        <div className="space-y-6">
          {groupedCommodities.map((group) => (
            <Card key={group.category}>
              <CardHeader>
                <CardTitle className="text-lg">{group.category}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                  {group.items.map((quote) => (
                    <QuoteCard
                      key={quote.symbol}
                      quote={quote}
                      onClick={() => onQuoteClick?.(quote)}
                    />
                  ))}
                </div>
                {group.items.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    No data available for this category
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <QuoteTable
          quotes={commodities}
          onRowClick={onQuoteClick ? (quote) => onQuoteClick(quote as CommodityQuote) : undefined}
        />
      )}
    </div>
  )
}

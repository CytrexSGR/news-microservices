/**
 * ForexTab - Display forex currency pairs
 */

import { QuoteCard } from './QuoteCard'
import { QuoteTable } from './QuoteTable'
import { Button } from '@/components/ui/Button'
import { LayoutGrid, List } from 'lucide-react'
import { useState } from 'react'
import type { ForexQuote } from '@/features/market/types/market.types'

interface ForexTabProps {
  forex: ForexQuote[]
  isLoading: boolean
  onQuoteClick?: (quote: ForexQuote) => void
}

export function ForexTab({ forex, isLoading, onQuoteClick }: ForexTabProps) {
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid')

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} className="h-48 bg-muted animate-pulse rounded-lg"></div>
        ))}
      </div>
    )
  }

  if (!forex || forex.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        No forex data available
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
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {forex.map((quote) => (
            <QuoteCard
              key={quote.symbol}
              quote={quote}
              onClick={() => onQuoteClick?.(quote)}
            />
          ))}
        </div>
      ) : (
        <QuoteTable
          quotes={forex}
          onRowClick={onQuoteClick ? (quote) => onQuoteClick(quote as ForexQuote) : undefined}
        />
      )}
    </div>
  )
}

/**
 * IndicesTab - Display stock market indices
 */

import { QuoteCard } from './QuoteCard'
import { QuoteTable } from './QuoteTable'
import { Button } from '@/components/ui/Button'
import { LayoutGrid, List } from 'lucide-react'
import { useState } from 'react'
import type { IndexQuote } from '@/features/market/types/market.types'

interface IndicesTabProps {
  indices: IndexQuote[]
  isLoading: boolean
  onQuoteClick?: (quote: IndexQuote) => void
}

export function IndicesTab({ indices, isLoading, onQuoteClick }: IndicesTabProps) {
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid')

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-48 bg-muted animate-pulse rounded-lg"></div>
        ))}
      </div>
    )
  }

  if (!indices || indices.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        No index data available
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
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {indices.map((quote) => (
            <QuoteCard
              key={quote.symbol}
              quote={quote}
              onClick={() => onQuoteClick?.(quote)}
            />
          ))}
        </div>
      ) : (
        <QuoteTable
          quotes={indices}
          onRowClick={onQuoteClick ? (quote) => onQuoteClick(quote as IndexQuote) : undefined}
        />
      )}
    </div>
  )
}

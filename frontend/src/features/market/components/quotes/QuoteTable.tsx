/**
 * QuoteTable Component - Table view for market quotes
 */

import { useState, useMemo } from 'react'
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import type { UnifiedQuote, SortField, SortDirection } from '@/features/market/types/market.types'
import {
  formatPrice,
  formatChange,
  formatChangePercent,
  formatVolume,
  getChangeColor,
  getTrendIcon,
} from '@/lib/utils/marketUtils'

interface QuoteTableProps {
  quotes: UnifiedQuote[]
  onRowClick?: (quote: UnifiedQuote) => void
}

export function QuoteTable({ quotes, onRowClick }: QuoteTableProps) {
  const [sortField, setSortField] = useState<SortField>('symbol')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')

  // Sort quotes
  const sortedQuotes = useMemo(() => {
    const sorted = [...quotes].sort((a, b) => {
      const aVal = a[sortField]
      const bVal = b[sortField]

      // Handle undefined values
      if (aVal === undefined) return 1
      if (bVal === undefined) return -1

      // String comparison for symbol/name
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortDirection === 'asc'
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal)
      }

      // Numeric comparison
      const numA = Number(aVal)
      const numB = Number(bVal)

      return sortDirection === 'asc' ? numA - numB : numB - numA
    })

    return sorted
  }, [quotes, sortField, sortDirection])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-4 w-4 ml-1" />
    }
    return sortDirection === 'asc' ? (
      <ArrowUp className="h-4 w-4 ml-1" />
    ) : (
      <ArrowDown className="h-4 w-4 ml-1" />
    )
  }

  return (
    <div className="rounded-md border border-border overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-muted/50 border-b border-border">
            <tr>
              <th className="text-left p-3">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSort('symbol')}
                  className="font-semibold"
                >
                  Symbol
                  <SortIcon field="symbol" />
                </Button>
              </th>
              <th className="text-left p-3">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSort('name')}
                  className="font-semibold"
                >
                  Name
                  <SortIcon field="name" />
                </Button>
              </th>
              <th className="text-right p-3">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSort('price')}
                  className="font-semibold"
                >
                  Price
                  <SortIcon field="price" />
                </Button>
              </th>
              <th className="text-right p-3">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSort('change')}
                  className="font-semibold"
                >
                  Change
                  <SortIcon field="change" />
                </Button>
              </th>
              <th className="text-right p-3">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSort('change_percent')}
                  className="font-semibold"
                >
                  Change %
                  <SortIcon field="change_percent" />
                </Button>
              </th>
              <th className="text-right p-3">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleSort('volume')}
                  className="font-semibold"
                >
                  Volume
                  <SortIcon field="volume" />
                </Button>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedQuotes.map((quote) => {
              const TrendIcon = getTrendIcon(quote.change)
              const changeColor = getChangeColor(quote.change)

              return (
                <tr
                  key={`${quote.category}-${quote.symbol}`}
                  onClick={() => onRowClick?.(quote)}
                  className="border-b border-border hover:bg-muted/30 cursor-pointer transition-colors"
                >
                  <td className="p-3">
                    <div className="font-semibold">{quote.symbol}</div>
                  </td>
                  <td className="p-3">
                    <div className="text-sm text-muted-foreground">{quote.name}</div>
                  </td>
                  <td className="p-3 text-right">
                    <div className="font-medium">${formatPrice(quote.price)}</div>
                  </td>
                  <td className="p-3 text-right">
                    <div className={`flex items-center justify-end gap-1 ${changeColor}`}>
                      <TrendIcon className="h-4 w-4" />
                      <span className="font-medium">{formatChange(quote.change)}</span>
                    </div>
                  </td>
                  <td className="p-3 text-right">
                    <div className={`font-medium ${changeColor}`}>
                      {formatChangePercent(quote.change_percent)}
                    </div>
                  </td>
                  <td className="p-3 text-right">
                    <div className="text-sm text-muted-foreground">
                      {quote.volume ? formatVolume(quote.volume) : '-'}
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {sortedQuotes.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          No quotes available
        </div>
      )}
    </div>
  )
}

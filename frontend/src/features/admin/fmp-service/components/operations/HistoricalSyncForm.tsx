/**
 * HistoricalSyncForm Component
 *
 * Form to manually trigger historical data synchronization:
 * - Asset type selection (indices, forex, commodities, crypto)
 * - Symbol input
 * - Date range picker
 * - Submit with loading state and feedback
 */

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/badge'
import { Calendar, Download, Loader2 } from 'lucide-react'
import { syncHistoricalData, type HistoricalSyncParams } from '@/lib/api/fmpAdmin'
import toast from 'react-hot-toast'

export interface HistoricalSyncFormProps {
  className?: string
}

/**
 * Historical data synchronization form
 *
 * @example
 * ```tsx
 * <HistoricalSyncForm />
 * ```
 */
export function HistoricalSyncForm({ className = '' }: HistoricalSyncFormProps) {
  const queryClient = useQueryClient()

  // Form state
  const [assetType, setAssetType] = useState<'indices' | 'forex' | 'commodities' | 'crypto'>(
    'indices'
  )
  const [symbol, setSymbol] = useState('')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')

  // Mutation for sync
  const syncMutation = useMutation({
    mutationFn: (params: HistoricalSyncParams) => syncHistoricalData(params),
    onSuccess: () => {
      toast.success('Historical sync triggered successfully!')
      // Reset form
      setSymbol('')
      setFromDate('')
      setToDate('')
      // Invalidate database stats to show updated counts
      queryClient.invalidateQueries({ queryKey: ['fmp-database-stats'] })
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to trigger historical sync')
    },
  })

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Validation
    if (!symbol.trim()) {
      toast.error('Please enter a symbol')
      return
    }
    if (!fromDate || !toDate) {
      toast.error('Please select both from and to dates')
      return
    }
    if (new Date(fromDate) > new Date(toDate)) {
      toast.error('From date must be before to date')
      return
    }

    // Submit
    syncMutation.mutate({
      asset_type: assetType,
      symbol: symbol.trim().toUpperCase(),
      from_date: fromDate,
      to_date: toDate,
    })
  }

  // Preset common symbols by asset type
  const commonSymbols = {
    indices: ['^GSPC', '^DJI', '^IXIC', '^RUT'],
    forex: ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD'],
    commodities: ['GCUSD', 'CLUSD', 'NGUSD', 'SIUSD'],
    crypto: ['BTCUSD', 'ETHUSD', 'BNBUSD', 'SOLUSD'],
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Download className="h-5 w-5" />
          Historical Data Sync
        </CardTitle>
        <CardDescription>
          Manually backfill historical data for specific symbols and date ranges
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Asset Type Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Asset Type</label>
            <div className="flex flex-wrap gap-2">
              {(['indices', 'forex', 'commodities', 'crypto'] as const).map((type) => (
                <Button
                  key={type}
                  type="button"
                  variant={assetType === type ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setAssetType(type)}
                  disabled={syncMutation.isPending}
                >
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </Button>
              ))}
            </div>
          </div>

          {/* Symbol Input */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Symbol</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder={`e.g., ${commonSymbols[assetType][0]}`}
              className="w-full px-3 py-2 border rounded-md text-sm uppercase"
              disabled={syncMutation.isPending}
            />
            {/* Common Symbols Quick Select */}
            <div className="flex flex-wrap gap-1">
              <span className="text-xs text-muted-foreground mr-2">Quick select:</span>
              {commonSymbols[assetType].map((sym) => (
                <Badge
                  key={sym}
                  variant="outline"
                  className="cursor-pointer hover:bg-accent"
                  onClick={() => setSymbol(sym)}
                >
                  {sym}
                </Badge>
              ))}
            </div>
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                From Date
              </label>
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                max={toDate || new Date().toISOString().split('T')[0]}
                className="w-full px-3 py-2 border rounded-md text-sm"
                disabled={syncMutation.isPending}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                To Date
              </label>
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                min={fromDate}
                max={new Date().toISOString().split('T')[0]}
                className="w-full px-3 py-2 border rounded-md text-sm"
                disabled={syncMutation.isPending}
              />
            </div>
          </div>

          {/* Preset Date Ranges */}
          <div className="flex flex-wrap gap-2">
            <span className="text-xs text-muted-foreground mr-2">Quick ranges:</span>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                const today = new Date()
                const oneYearAgo = new Date(today)
                oneYearAgo.setFullYear(today.getFullYear() - 1)
                setFromDate(oneYearAgo.toISOString().split('T')[0])
                setToDate(today.toISOString().split('T')[0])
              }}
              disabled={syncMutation.isPending}
              className="h-7 text-xs"
            >
              Last Year
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                const today = new Date()
                const ytd = new Date(today.getFullYear(), 0, 1)
                setFromDate(ytd.toISOString().split('T')[0])
                setToDate(today.toISOString().split('T')[0])
              }}
              disabled={syncMutation.isPending}
              className="h-7 text-xs"
            >
              YTD
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                const today = new Date()
                const fiveYearsAgo = new Date(today)
                fiveYearsAgo.setFullYear(today.getFullYear() - 5)
                setFromDate(fiveYearsAgo.toISOString().split('T')[0])
                setToDate(today.toISOString().split('T')[0])
              }}
              disabled={syncMutation.isPending}
              className="h-7 text-xs"
            >
              5 Years
            </Button>
          </div>

          {/* Submit Button */}
          <div className="flex gap-3 pt-2">
            <Button
              type="submit"
              disabled={syncMutation.isPending || !symbol || !fromDate || !toDate}
              className="flex-1"
            >
              {syncMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Syncing...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Trigger Sync
                </>
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setSymbol('')
                setFromDate('')
                setToDate('')
              }}
              disabled={syncMutation.isPending}
            >
              Clear
            </Button>
          </div>

          {/* Info Notice */}
          <div className="text-xs text-muted-foreground p-3 bg-muted/50 rounded-md">
            <strong>Note:</strong> Historical sync is asynchronous. Data will be fetched in the
            background and stored in the database. Check Database Stats to see progress.
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

/**
 * HistoricalChart Component
 *
 * Interactive historical price chart using Recharts
 * Supports line/area charts, tooltips, zoom, and responsive design
 */

import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { TrendingUp, TrendingDown } from 'lucide-react'

export interface HistoricalDataPoint {
  date: string
  price: number
  volume?: number
  open?: number
  high?: number
  low?: number
  close?: number
}

export interface HistoricalChartProps {
  data: HistoricalDataPoint[]
  symbol: string
  title?: string
  description?: string
  chartType?: 'line' | 'area'
  showVolume?: boolean
  isLoading?: boolean
  error?: Error | null
  height?: number
  className?: string
}

/**
 * Historical price chart with Recharts
 *
 * @example
 * ```tsx
 * <HistoricalChart
 *   data={historicalData}
 *   symbol="^GSPC"
 *   title="S&P 500 Historical Data"
 *   chartType="area"
 *   showVolume
 * />
 * ```
 */
export function HistoricalChart({
  data,
  symbol,
  title,
  description,
  chartType = 'line',
  showVolume = false,
  isLoading = false,
  error = null,
  height = 400,
  className = '',
}: HistoricalChartProps) {
  // Calculate price change statistics
  const stats = data.length > 0 ? calculateStats(data) : null

  // Loading state
  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-32 mt-2" />
        </CardHeader>
        <CardContent>
          <Skeleton className="w-full" style={{ height }} />
        </CardContent>
      </Card>
    )
  }

  // Error state
  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>{title || `${symbol} Historical Data`}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-12 text-destructive">
            <p>Error loading chart data: {error.message}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Empty state
  if (!data || data.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>{title || `${symbol} Historical Data`}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-12 text-muted-foreground">
            <p>No historical data available for the selected period</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle>{title || `${symbol} Historical Data`}</CardTitle>
            {description && <CardDescription>{description}</CardDescription>}
          </div>
          {stats && (
            <div className="text-right">
              <div className="text-2xl font-bold">${stats.latestPrice.toFixed(2)}</div>
              <div
                className={`flex items-center gap-1 text-sm ${
                  stats.change >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {stats.change >= 0 ? (
                  <TrendingUp className="h-4 w-4" />
                ) : (
                  <TrendingDown className="h-4 w-4" />
                )}
                <span>
                  {stats.change >= 0 ? '+' : ''}
                  {stats.change.toFixed(2)} ({stats.changePercent >= 0 ? '+' : ''}
                  {stats.changePercent.toFixed(2)}%)
                </span>
              </div>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          {chartType === 'area' ? (
            <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="date"
                className="text-xs"
                tickFormatter={(value) => formatDate(value)}
              />
              <YAxis
                className="text-xs"
                domain={['auto', 'auto']}
                tickFormatter={(value) => `$${value.toFixed(2)}`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Area
                type="monotone"
                dataKey="close"
                stroke="hsl(var(--primary))"
                fillOpacity={1}
                fill="url(#colorPrice)"
                name="Price"
              />
            </AreaChart>
          ) : (
            <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="date"
                className="text-xs"
                tickFormatter={(value) => formatDate(value)}
              />
              <YAxis
                className="text-xs"
                domain={['auto', 'auto']}
                tickFormatter={(value) => `$${value.toFixed(2)}`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Line
                type="monotone"
                dataKey="close"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                dot={false}
                name="Price"
              />
            </LineChart>
          )}
        </ResponsiveContainer>

        {/* Summary Stats */}
        {stats && (
          <div className="grid grid-cols-4 gap-4 mt-6 pt-4 border-t">
            <div>
              <div className="text-xs text-muted-foreground">High</div>
              <div className="text-sm font-semibold">${stats.high.toFixed(2)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Low</div>
              <div className="text-sm font-semibold">${stats.low.toFixed(2)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Avg</div>
              <div className="text-sm font-semibold">${stats.average.toFixed(2)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Data Points</div>
              <div className="text-sm font-semibold">{data.length}</div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

/**
 * Custom tooltip for the chart
 */
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload || !payload.length) {
    return null
  }

  const data = payload[0].payload

  return (
    <div className="bg-background border border-border rounded-lg p-3 shadow-lg">
      <p className="text-sm font-medium mb-2">{formatDate(label, true)}</p>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between gap-4">
          <span className="text-muted-foreground">Price:</span>
          <span className="font-semibold">${Number(data.close || data.price || 0).toFixed(2)}</span>
        </div>
        {data.volume !== undefined && (
          <div className="flex justify-between gap-4">
            <span className="text-muted-foreground">Volume:</span>
            <span className="font-semibold">{formatVolume(Number(data.volume))}</span>
          </div>
        )}
        {data.open !== undefined && (
          <>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Open:</span>
              <span className="font-semibold">${Number(data.open).toFixed(2)}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">High:</span>
              <span className="font-semibold">${Number(data.high).toFixed(2)}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Low:</span>
              <span className="font-semibold">${Number(data.low).toFixed(2)}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Close:</span>
              <span className="font-semibold">${Number(data.close).toFixed(2)}</span>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

/**
 * Calculate statistics from historical data
 */
function calculateStats(data: HistoricalDataPoint[]) {
  // Use 'close' price for calculations (standard for OHLC data)
  // Convert to number as API returns strings
  const prices = data.map((d) => Number(d.close || d.price || 0))
  const firstPrice = prices[0]
  const latestPrice = prices[prices.length - 1]

  return {
    high: Math.max(...prices),
    low: Math.min(...prices),
    average: prices.reduce((sum, p) => sum + p, 0) / prices.length,
    latestPrice,
    change: latestPrice - firstPrice,
    changePercent: ((latestPrice - firstPrice) / firstPrice) * 100,
  }
}

/**
 * Format date for display
 */
function formatDate(dateStr: string, long = false): string {
  const date = new Date(dateStr)
  if (long) {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

/**
 * Format volume with K/M/B suffixes
 */
function formatVolume(volume: number): string {
  if (volume >= 1e9) return `${(volume / 1e9).toFixed(2)}B`
  if (volume >= 1e6) return `${(volume / 1e6).toFixed(2)}M`
  if (volume >= 1e3) return `${(volume / 1e3).toFixed(2)}K`
  return volume.toString()
}

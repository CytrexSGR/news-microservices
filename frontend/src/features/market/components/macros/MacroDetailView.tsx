/**
 * MacroDetailView Component
 *
 * Detailed view of a single macroeconomic indicator with:
 * - Historical trend chart
 * - Statistical summary
 * - Time range controls
 * - Related indicators (optional)
 */

import { useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { TrendingUp, TrendingDown, Calendar, BarChart3 } from 'lucide-react'
import { ChartControls } from '../historical/ChartControls'
import { calculateDateRange, TIME_RANGES } from '../historical/TimeRangePicker'
import type { TimeRange } from '../historical/TimeRangePicker'

export interface MacroDataPoint {
  date: string
  value: number
}

export interface MacroDetailViewProps {
  indicatorName: string
  data: MacroDataPoint[]
  unit?: string
  description?: string
  isLoading?: boolean
  error?: Error | null
  onTimeRangeChange?: (fromDate: string, toDate: string) => void
  className?: string
}

/**
 * Detailed macro indicator view with historical chart
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useMacroIndicatorDetail({
 *   indicatorName: 'GDP',
 *   fromDate: '2020-01-01',
 *   toDate: '2024-12-31'
 * })
 * <MacroDetailView
 *   indicatorName="GDP"
 *   data={data}
 *   unit="Billions USD"
 *   isLoading={isLoading}
 *   error={error}
 * />
 * ```
 */
export function MacroDetailView({
  indicatorName,
  data,
  unit,
  description,
  isLoading = false,
  error = null,
  onTimeRangeChange,
  className = '',
}: MacroDetailViewProps) {
  const [selectedRange, setSelectedRange] = useState('1y')

  const handleRangeChange = (range: TimeRange) => {
    setSelectedRange(range.value)
    if (onTimeRangeChange) {
      const { fromDate, toDate } = calculateDateRange(range)
      onTimeRangeChange(fromDate, toDate)
    }
  }

  const handleCustomDateRange = (range: { fromDate: string; toDate: string }) => {
    setSelectedRange('custom')
    if (onTimeRangeChange) {
      onTimeRangeChange(range.fromDate, range.toDate)
    }
  }

  // Loading state
  if (isLoading) {
    return (
      <div className={`space-y-4 ${className}`}>
        <Card>
          <CardHeader>
            <Skeleton className="h-7 w-48" />
            <Skeleton className="h-4 w-32 mt-2" />
          </CardHeader>
          <CardContent>
            <Skeleton className="w-full h-[400px]" />
          </CardContent>
        </Card>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>{formatIndicatorName(indicatorName)}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-destructive">
            <p>Error loading indicator data: {error.message}</p>
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
          <CardTitle>{formatIndicatorName(indicatorName)}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-muted-foreground">
            <p>No historical data available for this indicator</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Calculate statistics
  const stats = calculateStats(data)

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header Card */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                {formatIndicatorName(indicatorName)}
              </CardTitle>
              {description && <CardDescription className="mt-2">{description}</CardDescription>}
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold">{stats.latest.toFixed(2)}</div>
              {unit && <div className="text-sm text-muted-foreground mt-1">{unit}</div>}
              <div
                className={`flex items-center justify-end gap-1 mt-2 text-sm ${
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
          </div>
        </CardHeader>
      </Card>

      {/* Chart Controls */}
      <ChartControls
        selectedRange={selectedRange}
        onRangeChange={handleRangeChange}
        onCustomDateRange={handleCustomDateRange}
        showCustomDatePicker
      />

      {/* Historical Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Historical Trend</CardTitle>
          <CardDescription>
            {data.length} data points • Last updated: {formatDate(stats.latestDate)}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
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
                tickFormatter={(value) => value.toFixed(2)}
              />
              <Tooltip content={<CustomTooltip unit={unit} />} />
              <Line
                type="monotone"
                dataKey="value"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                dot={false}
                name={formatIndicatorName(indicatorName)}
              />
            </LineChart>
          </ResponsiveContainer>

          {/* Statistics Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-4 border-t">
            <div>
              <div className="text-xs text-muted-foreground mb-1">High</div>
              <div className="text-lg font-semibold">{stats.high.toFixed(2)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Low</div>
              <div className="text-lg font-semibold">{stats.low.toFixed(2)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Average</div>
              <div className="text-lg font-semibold">{stats.average.toFixed(2)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Volatility</div>
              <div className="text-lg font-semibold">{stats.volatility.toFixed(2)}%</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

/**
 * Custom tooltip for the chart
 */
function CustomTooltip({ active, payload, label, unit }: any) {
  if (!active || !payload || !payload.length) {
    return null
  }

  const value = payload[0].value

  return (
    <div className="bg-background border border-border rounded-lg p-3 shadow-lg">
      <p className="text-sm font-medium mb-2">{formatDate(label, true)}</p>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between gap-4">
          <span className="text-muted-foreground">Value:</span>
          <span className="font-semibold">
            {value.toFixed(2)}
            {unit && ` ${unit}`}
          </span>
        </div>
      </div>
    </div>
  )
}

/**
 * Calculate statistics from data
 */
function calculateStats(data: MacroDataPoint[]) {
  const values = data.map((d) => d.value)
  const firstValue = values[0]
  const lastValue = values[values.length - 1]
  const change = lastValue - firstValue
  const changePercent = (change / firstValue) * 100

  // Calculate volatility (standard deviation)
  const avg = values.reduce((sum, v) => sum + v, 0) / values.length
  const variance = values.reduce((sum, v) => sum + Math.pow(v - avg, 2), 0) / values.length
  const stdDev = Math.sqrt(variance)
  const volatility = (stdDev / avg) * 100

  return {
    latest: lastValue,
    latestDate: data[data.length - 1].date,
    high: Math.max(...values),
    low: Math.min(...values),
    average: avg,
    change,
    changePercent,
    volatility,
  }
}

/**
 * Format indicator name for display
 */
function formatIndicatorName(name: string): string {
  return name
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}

/**
 * Format date for display
 */
function formatDate(dateStr: string, long = false): string {
  const date = new Date(dateStr)
  if (long) {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
}

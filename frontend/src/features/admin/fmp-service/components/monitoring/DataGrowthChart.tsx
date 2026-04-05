/**
 * DataGrowthChart Component
 *
 * Displays data growth trends over time:
 * - Daily record growth per category
 * - Cumulative growth visualization
 * - Growth rate analysis
 */

import {
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
import { TrendingUp, Database } from 'lucide-react'

export interface DataGrowthPoint {
  date: string // YYYY-MM-DD
  indices_count: number
  forex_count: number
  commodities_count: number
  crypto_count: number
  total_count: number
}

export interface DataGrowthChartProps {
  data: DataGrowthPoint[] | undefined
  isLoading: boolean
  error: Error | null
  days?: number
  className?: string
}

/**
 * Data growth chart with stacked area visualization
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useDataGrowth({ days: 30 })
 * <DataGrowthChart data={data} isLoading={isLoading} error={error} days={30} />
 * ```
 */
export function DataGrowthChart({
  data,
  isLoading,
  error,
  days = 30,
  className = '',
}: DataGrowthChartProps) {
  // Loading state
  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-4 w-32 mt-2" />
        </CardHeader>
        <CardContent>
          <Skeleton className="w-full h-[300px]" />
        </CardContent>
      </Card>
    )
  }

  // Error state
  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Data Growth Trends
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-destructive">
            Error loading data growth: {error.message}
          </div>
        </CardContent>
      </Card>
    )
  }

  // Ensure data is an array
  const growthArray = Array.isArray(data) ? data : []

  // Empty state
  if (growthArray.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Data Growth Trends
          </CardTitle>
          <CardDescription>Last {days} days data ingestion trends</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground py-12 text-center">
            No growth data available for the selected period
          </div>
        </CardContent>
      </Card>
    )
  }

  // Calculate growth statistics
  const firstDay = growthArray[0]
  const lastDay = growthArray[growthArray.length - 1]
  const totalGrowth = lastDay.total_count - firstDay.total_count
  const avgDailyGrowth = totalGrowth / growthArray.length
  const growthRate = firstDay.total_count > 0 ? (totalGrowth / firstDay.total_count) * 100 : 0

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Data Growth Trends
            </CardTitle>
            <CardDescription>Last {days} days data ingestion by category</CardDescription>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">+{totalGrowth.toLocaleString()}</div>
            <div className="text-sm text-muted-foreground">
              {growthRate >= 0 ? '+' : ''}
              {growthRate.toFixed(1)}% growth
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Growth Statistics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-3 rounded-lg bg-blue-50 dark:bg-blue-950">
            <div className="text-xs text-muted-foreground mb-1">Indices</div>
            <div className="text-lg font-semibold">
              +{(lastDay.indices_count - firstDay.indices_count).toLocaleString()}
            </div>
          </div>
          <div className="text-center p-3 rounded-lg bg-green-50 dark:bg-green-950">
            <div className="text-xs text-muted-foreground mb-1">Forex</div>
            <div className="text-lg font-semibold">
              +{(lastDay.forex_count - firstDay.forex_count).toLocaleString()}
            </div>
          </div>
          <div className="text-center p-3 rounded-lg bg-yellow-50 dark:bg-yellow-950">
            <div className="text-xs text-muted-foreground mb-1">Commodities</div>
            <div className="text-lg font-semibold">
              +{(lastDay.commodities_count - firstDay.commodities_count).toLocaleString()}
            </div>
          </div>
          <div className="text-center p-3 rounded-lg bg-purple-50 dark:bg-purple-950">
            <div className="text-xs text-muted-foreground mb-1">Crypto</div>
            <div className="text-lg font-semibold">
              +{(lastDay.crypto_count - firstDay.crypto_count).toLocaleString()}
            </div>
          </div>
        </div>

        {/* Stacked Area Chart */}
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={growthArray} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorIndices" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.2} />
              </linearGradient>
              <linearGradient id="colorForex" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.2} />
              </linearGradient>
              <linearGradient id="colorCommodities" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.2} />
              </linearGradient>
              <linearGradient id="colorCrypto" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.2} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="date"
              className="text-xs"
              tickFormatter={(value) => {
                const date = new Date(value)
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
              }}
            />
            <YAxis className="text-xs" tickFormatter={(value) => value.toLocaleString()} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Area
              type="monotone"
              dataKey="indices_count"
              stackId="1"
              stroke="#3b82f6"
              fill="url(#colorIndices)"
              name="Indices"
            />
            <Area
              type="monotone"
              dataKey="forex_count"
              stackId="1"
              stroke="#10b981"
              fill="url(#colorForex)"
              name="Forex"
            />
            <Area
              type="monotone"
              dataKey="commodities_count"
              stackId="1"
              stroke="#f59e0b"
              fill="url(#colorCommodities)"
              name="Commodities"
            />
            <Area
              type="monotone"
              dataKey="crypto_count"
              stackId="1"
              stroke="#8b5cf6"
              fill="url(#colorCrypto)"
              name="Crypto"
            />
          </AreaChart>
        </ResponsiveContainer>

        {/* Summary Footer */}
        <div className="mt-6 pt-4 border-t grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-xs text-muted-foreground mb-1 flex items-center justify-center gap-1">
              <Database className="h-3 w-3" />
              Total Records
            </div>
            <div className="text-lg font-semibold">{lastDay.total_count.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Avg Daily Growth</div>
            <div className="text-lg font-semibold">+{avgDailyGrowth.toFixed(0)}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Growth Rate</div>
            <div className="text-lg font-semibold text-green-600">
              {growthRate >= 0 ? '+' : ''}
              {growthRate.toFixed(2)}%
            </div>
          </div>
        </div>
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

  const date = new Date(label)
  const formattedDate = date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  return (
    <div className="bg-background border border-border rounded-lg p-3 shadow-lg">
      <p className="text-sm font-medium mb-2">{formattedDate}</p>
      <div className="space-y-1 text-xs">
        {payload.reverse().map((entry: any) => (
          <div key={entry.dataKey} className="flex justify-between gap-4">
            <span className="flex items-center gap-1">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              {entry.name}:
            </span>
            <span className="font-semibold">{entry.value.toLocaleString()}</span>
          </div>
        ))}
        <div className="pt-1 mt-1 border-t flex justify-between gap-4 font-semibold">
          <span>Total:</span>
          <span>
            {payload.reduce((sum: number, entry: any) => sum + entry.value, 0).toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  )
}

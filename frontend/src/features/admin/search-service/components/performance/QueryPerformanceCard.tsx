import { Card } from '@/components/ui/Card'
import { TrendingUp } from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { PerformanceStatistics } from '@/types/searchServiceAdmin'

interface QueryPerformanceCardProps {
  stats: PerformanceStatistics
}

export function QueryPerformanceCard({ stats }: QueryPerformanceCardProps) {
  const hasData =
    stats?.result_distribution && stats.result_distribution.length > 0

  // Map result distribution to chart data with colors
  const chartData = hasData
    ? (stats?.result_distribution ?? []).map((item) => ({
        range: item.range,
        count: item.count,
        fill: item.range === '0 results' ? '#ef4444' : '#3b82f6', // red-500 : blue-500
      }))
    : []

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-muted-foreground" />
          <h3 className="text-lg font-semibold">Query Performance</h3>
        </div>
      </div>

      {/* Average Execution Time */}
      <div className="mb-6">
        <div className="text-sm text-muted-foreground mb-1">
          Average Execution Time
        </div>
        <div className="flex items-baseline gap-1">
          <span className="text-4xl font-bold">
            {(stats?.avg_execution_time_ms ?? 0).toFixed(1)}
          </span>
          <span className="text-lg text-muted-foreground">ms</span>
        </div>
      </div>

      {/* Result Distribution Chart */}
      <div>
        <h4 className="text-sm font-medium mb-3">Result Distribution</h4>
        {!hasData ? (
          <div className="h-64 flex items-center justify-center border rounded-md bg-muted/20">
            <p className="text-sm text-muted-foreground">No data yet</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="range"
                tick={{ fontSize: 12 }}
                className="text-muted-foreground"
              />
              <YAxis
                tick={{ fontSize: 12 }}
                className="text-muted-foreground"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--background))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '0.5rem',
                }}
                labelStyle={{ color: 'hsl(var(--foreground))' }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </Card>
  )
}

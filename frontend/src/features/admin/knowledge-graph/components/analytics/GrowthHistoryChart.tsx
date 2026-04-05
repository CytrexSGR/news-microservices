import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { LineChart, TrendingUp, Calendar } from 'lucide-react'
import {
  ResponsiveContainer,
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'
import type { GrowthDataPoint } from '@/types/knowledgeGraph'

interface GrowthHistoryChartProps {
  data: GrowthDataPoint[] | null
  isLoading: boolean
  days: number
}

export function GrowthHistoryChart({ data, isLoading, days }: GrowthHistoryChartProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <LineChart className="h-5 w-5" />
            Growth History ({days} days)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            Loading growth history...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <LineChart className="h-5 w-5" />
            Growth History ({days} days)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <Calendar className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No growth data available for the selected period</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Format date for display (e.g., "2025-10-24" -> "Oct 24")
  const formattedData = data.map((point) => {
    const date = new Date(point.date)
    const formatted = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    return {
      ...point,
      displayDate: formatted,
    }
  })

  // Calculate totals for summary
  const totalNewNodes = data.reduce((sum, point) => sum + point.new_nodes, 0)
  const totalNewRelationships = data.reduce((sum, point) => sum + point.new_relationships, 0)
  const latestPoint = data[data.length - 1]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <LineChart className="h-5 w-5" />
          Growth History ({days} days)
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-4 pb-4 border-b">
          <div>
            <div className="text-xs text-muted-foreground">New Nodes</div>
            <div className="text-lg font-bold">{totalNewNodes.toLocaleString()}</div>
            <div className="text-xs text-muted-foreground">in {days} days</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">New Relationships</div>
            <div className="text-lg font-bold">{totalNewRelationships.toLocaleString()}</div>
            <div className="text-xs text-muted-foreground">in {days} days</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Total Size</div>
            <div className="text-lg font-bold">{latestPoint.total_nodes.toLocaleString()}</div>
            <div className="text-xs text-muted-foreground">nodes</div>
          </div>
        </div>

        {/* Chart */}
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RechartsLineChart
              data={formattedData}
              margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="displayDate"
                className="text-xs"
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis className="text-xs" tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px',
                }}
                labelStyle={{ color: 'hsl(var(--foreground))' }}
              />
              <Legend
                wrapperStyle={{ fontSize: '12px' }}
                iconType="line"
              />
              <Line
                type="monotone"
                dataKey="new_nodes"
                name="New Nodes"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
              <Line
                type="monotone"
                dataKey="new_relationships"
                name="New Relationships"
                stroke="hsl(var(--chart-2))"
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            </RechartsLineChart>
          </ResponsiveContainer>
        </div>

        {/* Growth Rate Indicator */}
        {data.length > 1 && (
          <div className="pt-2 border-t text-xs text-muted-foreground flex items-center gap-1">
            <TrendingUp className="h-3 w-3" />
            <span>
              Daily Average: {Math.round(totalNewNodes / days)} nodes, {Math.round(totalNewRelationships / days)} relationships
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

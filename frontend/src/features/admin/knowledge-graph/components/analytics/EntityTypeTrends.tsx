import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { TrendingUp, Info } from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
} from 'recharts'
import { useEntityTypeTrends } from '../../hooks/useEntityTypeTrends'

interface EntityTypeTrendsProps {
  days?: number
}

// Colors for each entity type
const entityTypeColors = {
  PERSON: '#3b82f6', // blue
  ORGANIZATION: '#8b5cf6', // purple
  LOCATION: '#10b981', // green
  EVENT: '#f59e0b', // amber
  PRODUCT: '#ef4444', // red
  OTHER: '#6b7280', // gray
}

export function EntityTypeTrends({ days = 30 }: EntityTypeTrendsProps) {
  // Fetch real data from API
  const { data, isLoading } = useEntityTypeTrends(days)

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Entity Type Trends
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
            <p className="text-sm">Loading trends...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // No data available
  if (!data || data.trends.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Entity Type Trends
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <p className="text-sm">No trend data available</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const displayData = data.trends

  // Calculate totals and growth
  const firstDay = displayData[0]
  const lastDay = displayData[displayData.length - 1]
  const entityTypes = Object.keys(entityTypeColors) as Array<keyof typeof entityTypeColors>

  const growth = entityTypes.map((type) => {
    const first = firstDay[type]
    const last = lastDay[type]
    const growthPercent = ((last - first) / first) * 100
    return { type, first, last, growthPercent }
  }).sort((a, b) => b.last - a.last)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Entity Type Trends
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-4 w-4 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p className="text-sm">
                  Shows how different entity types grow over time. Useful for
                  understanding content focus and coverage patterns.
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Growth Summary */}
        <div className="grid grid-cols-3 gap-3">
          {growth.slice(0, 6).map((item) => (
            <div
              key={item.type}
              className="p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center justify-between mb-1">
                <Badge
                  variant="outline"
                  className="text-xs"
                  style={{ borderColor: entityTypeColors[item.type] }}
                >
                  {item.type}
                </Badge>
                <span
                  className={`text-xs font-bold ${
                    item.growthPercent > 0
                      ? 'text-green-600'
                      : item.growthPercent < 0
                      ? 'text-red-600'
                      : 'text-gray-600'
                  }`}
                >
                  {item.growthPercent > 0 ? '+' : ''}
                  {item.growthPercent.toFixed(0)}%
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold">{item.last}</span>
                <span className="text-xs text-muted-foreground">entities</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                from {item.first} ({days} days ago)
              </p>
            </div>
          ))}
        </div>

        {/* Trend Chart */}
        <div className="w-full h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={displayData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="date"
                className="text-xs"
                tick={{ fill: 'currentColor' }}
                tickFormatter={(value) => {
                  const date = new Date(value)
                  return `${date.getMonth() + 1}/${date.getDate()}`
                }}
              />
              <YAxis className="text-xs" tick={{ fill: 'currentColor' }} />
              <RechartsTooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--background))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px',
                }}
                labelFormatter={(value) => {
                  const date = new Date(value)
                  return date.toLocaleDateString()
                }}
              />
              <Legend />
              {entityTypes.map((type) => (
                <Line
                  key={type}
                  type="monotone"
                  dataKey={type}
                  stroke={entityTypeColors[type]}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Summary */}
        <div className="pt-3 border-t text-center text-xs text-muted-foreground">
          Showing {days}-day entity type growth trends
        </div>
      </CardContent>
    </Card>
  )
}

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { BarChart3, CheckCircle2, AlertTriangle, XCircle, Info, TrendingUp, TrendingDown } from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { useRelationshipQualityTrends } from '../../hooks/useRelationshipQualityTrends'

/**
 * RelationshipQualityBreakdown Component
 *
 * Displays comprehensive relationship quality breakdown with:
 * - Current distribution (Pie Chart)
 * - Quality trends over time (Stacked Area Chart)
 * - Statistics summary
 * - Quality insights and recommendations
 */
export function RelationshipQualityBreakdown() {
  const { data, isLoading, error } = useRelationshipQualityTrends(30, {
    refetchInterval: 5 * 60 * 1000 // Auto-refresh every 5 minutes
  })

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Relationship Quality Breakdown (30 days)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
            <p className="text-sm">Loading quality breakdown...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Relationship Quality Breakdown (30 days)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert className="bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800">
            <XCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-sm text-red-900 dark:text-red-100">
              Failed to load quality breakdown. Please try again later.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Relationship Quality Breakdown (30 days)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <BarChart3 className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No quality data available yet</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Current data (latest day)
  const current = data[data.length - 1]
  const previous = data[0]

  // Calculate trends
  const highTrend = current.high_confidence_percentage - previous.high_confidence_percentage
  const mediumTrend = current.medium_confidence_percentage - previous.medium_confidence_percentage
  const lowTrend = current.low_confidence_percentage - previous.low_confidence_percentage

  // Calculate averages
  const avgHigh = data.reduce((sum, d) => sum + d.high_confidence_percentage, 0) / data.length
  const avgMedium = data.reduce((sum, d) => sum + d.medium_confidence_percentage, 0) / data.length
  const avgLow = data.reduce((sum, d) => sum + d.low_confidence_percentage, 0) / data.length

  // Pie chart data (current distribution)
  const pieData = [
    { name: 'High Confidence', value: current.high_confidence_percentage, color: '#10b981' },
    { name: 'Medium Confidence', value: current.medium_confidence_percentage, color: '#3b82f6' },
    { name: 'Low Confidence', value: current.low_confidence_percentage, color: '#f59e0b' },
  ].filter(d => d.value > 0)

  // Area chart data (trends over time)
  const areaChartData = data.map(d => ({
    date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    high: parseFloat(d.high_confidence_percentage.toFixed(2)),
    medium: parseFloat(d.medium_confidence_percentage.toFixed(2)),
    low: parseFloat(d.low_confidence_percentage.toFixed(2)),
  }))

  // Quality status
  const getQualityStatus = (highPercentage: number) => {
    if (highPercentage >= 95) return { label: 'Excellent', color: 'text-green-600', bgColor: 'bg-green-100 dark:bg-green-900', icon: CheckCircle2 }
    if (highPercentage >= 85) return { label: 'Good', color: 'text-blue-600', bgColor: 'bg-blue-100 dark:bg-blue-900', icon: CheckCircle2 }
    if (highPercentage >= 70) return { label: 'Fair', color: 'text-yellow-600', bgColor: 'bg-yellow-100 dark:bg-yellow-900', icon: AlertTriangle }
    return { label: 'Needs Review', color: 'text-red-600', bgColor: 'bg-red-100 dark:bg-red-900', icon: XCircle }
  }

  const qualityStatus = getQualityStatus(current.high_confidence_percentage)
  const QualityIcon = qualityStatus.icon

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Relationship Quality Breakdown (30 days)
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-4 w-4 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p className="text-sm">
                  Tracks relationship confidence levels over time. High confidence (&gt;0.8) indicates
                  strong entity relationships. Goal: maximize high confidence ratio.
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current Status Summary */}
        <div className="flex items-center justify-between pb-4 border-b">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm text-muted-foreground">Overall Quality</span>
              <Badge className={`${qualityStatus.bgColor} ${qualityStatus.color} border-none text-xs`}>
                {qualityStatus.label}
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <QualityIcon className={`h-5 w-5 ${qualityStatus.color}`} />
              <span className="text-3xl font-bold">{current.high_confidence_percentage.toFixed(1)}%</span>
              <span className="text-sm text-muted-foreground">High Confidence</span>
            </div>
          </div>

          <div className="text-right space-y-1">
            <div className="text-xs text-muted-foreground">Total Relationships</div>
            <div className="text-2xl font-bold">{current.total_relationships.toLocaleString()}</div>
          </div>
        </div>

        {/* Two Column Layout: Pie Chart + Stats */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Current Distribution (Pie Chart) */}
          <div>
            <h3 className="text-sm font-medium mb-4 text-center">Current Distribution</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                  labelLine={false}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip
                  formatter={(value: number) => `${value.toFixed(2)}%`}
                  contentStyle={{
                    backgroundColor: 'hsl(var(--background))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '6px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Statistics Summary */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium mb-4">Statistics</h3>

            {/* High Confidence */}
            <div className="flex items-center justify-between p-2 rounded bg-green-50 dark:bg-green-950">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span className="text-sm font-medium">High (&gt;0.8)</span>
              </div>
              <div className="text-right">
                <div className="text-sm font-bold">{current.high_confidence_percentage.toFixed(2)}%</div>
                <div className="text-xs text-muted-foreground">
                  {highTrend > 0 ? '+' : ''}{highTrend.toFixed(2)}%
                  {highTrend > 0 ? <TrendingUp className="inline h-3 w-3 ml-1 text-green-600" /> :
                   highTrend < 0 ? <TrendingDown className="inline h-3 w-3 ml-1 text-red-600" /> : null}
                </div>
              </div>
            </div>

            {/* Medium Confidence */}
            <div className="flex items-center justify-between p-2 rounded bg-blue-50 dark:bg-blue-950">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium">Medium (0.5-0.8)</span>
              </div>
              <div className="text-right">
                <div className="text-sm font-bold">{current.medium_confidence_percentage.toFixed(2)}%</div>
                <div className="text-xs text-muted-foreground">
                  {mediumTrend > 0 ? '+' : ''}{mediumTrend.toFixed(2)}%
                  {mediumTrend > 0 ? <TrendingUp className="inline h-3 w-3 ml-1" /> :
                   mediumTrend < 0 ? <TrendingDown className="inline h-3 w-3 ml-1" /> : null}
                </div>
              </div>
            </div>

            {/* Low Confidence */}
            {current.low_confidence_percentage > 0 && (
              <div className="flex items-center justify-between p-2 rounded bg-orange-50 dark:bg-orange-950">
                <div className="flex items-center gap-2">
                  <XCircle className="h-4 w-4 text-orange-600" />
                  <span className="text-sm font-medium">Low (&lt;0.5)</span>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold">{current.low_confidence_percentage.toFixed(2)}%</div>
                  <div className="text-xs text-muted-foreground">
                    {lowTrend > 0 ? '+' : ''}{lowTrend.toFixed(2)}%
                  </div>
                </div>
              </div>
            )}

            {/* Averages */}
            <div className="pt-2 border-t space-y-1 text-xs text-muted-foreground">
              <div className="flex justify-between">
                <span>30-day avg (High):</span>
                <span className="font-medium">{avgHigh.toFixed(2)}%</span>
              </div>
              <div className="flex justify-between">
                <span>30-day avg (Medium):</span>
                <span className="font-medium">{avgMedium.toFixed(2)}%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Trend Chart (Stacked Area) */}
        <div className="pt-4 border-t">
          <h3 className="text-sm font-medium mb-4">Quality Trends (30 days)</h3>
          <div className="w-full h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={areaChartData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12 }}
                  className="text-muted-foreground"
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  className="text-muted-foreground"
                  label={{ value: 'Confidence %', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
                />
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--background))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '6px',
                  }}
                  formatter={(value: number) => `${value}%`}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="high"
                  stackId="1"
                  name="High Confidence"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.6}
                />
                <Area
                  type="monotone"
                  dataKey="medium"
                  stackId="1"
                  name="Medium Confidence"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.6}
                />
                {avgLow > 0 && (
                  <Area
                    type="monotone"
                    dataKey="low"
                    stackId="1"
                    name="Low Confidence"
                    stroke="#f59e0b"
                    fill="#f59e0b"
                    fillOpacity={0.6}
                  />
                )}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Quality Insights */}
        <div className="space-y-2 pt-4 border-t">
          {current.high_confidence_percentage >= 95 && (
            <Alert className="bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-sm text-green-900 dark:text-green-100">
                <strong>Excellent quality!</strong> {current.high_confidence_percentage.toFixed(1)}% of relationships
                have high confidence. Continue monitoring to maintain this standard.
              </AlertDescription>
            </Alert>
          )}

          {highTrend > 1 && (
            <Alert className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
              <TrendingUp className="h-4 w-4 text-blue-600" />
              <AlertDescription className="text-sm text-blue-900 dark:text-blue-100">
                <strong>Positive trend!</strong> High confidence relationships increased by {highTrend.toFixed(1)}%
                over the past 30 days.
              </AlertDescription>
            </Alert>
          )}

          {current.medium_confidence_percentage > 20 && (
            <Alert className="bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <AlertDescription className="text-sm text-yellow-900 dark:text-yellow-100">
                <strong>Review recommended:</strong> {current.medium_confidence_percentage.toFixed(1)}% of
                relationships have medium confidence. Consider reviewing relationship extraction logic.
              </AlertDescription>
            </Alert>
          )}

          {current.low_confidence_percentage > 5 && (
            <Alert className="bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800">
              <XCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-sm text-red-900 dark:text-red-100">
                <strong>Action required:</strong> {current.low_confidence_percentage.toFixed(1)}% low confidence
                relationships detected. Investigate extraction quality and consider reprocessing.
              </AlertDescription>
            </Alert>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

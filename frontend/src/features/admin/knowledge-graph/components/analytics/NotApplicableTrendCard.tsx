import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { TrendingDown, TrendingUp, AlertTriangle, CheckCircle2, XCircle, Info, Minus } from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  ResponsiveContainer,
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
} from 'recharts'
import { useNotApplicableTrends } from '../../hooks/useNotApplicableTrends'

/**
 * NotApplicableTrendCard Component
 *
 * Displays NOT_APPLICABLE relationship trends over time to track data quality improvements.
 * Shows percentage trend line with quality indicators.
 */
export function NotApplicableTrendCard() {
  const { data, isLoading, error } = useNotApplicableTrends(30, {
    refetchInterval: 5 * 60 * 1000 // Auto-refresh every 5 minutes
  })

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            NOT_APPLICABLE Trend (30 days)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
            <p className="text-sm">Loading trend data...</p>
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
            <AlertTriangle className="h-5 w-5" />
            NOT_APPLICABLE Trend (30 days)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert className="bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800">
            <XCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-sm text-red-900 dark:text-red-100">
              Failed to load trend data. Please try again later.
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
            <AlertTriangle className="h-5 w-5" />
            NOT_APPLICABLE Trend (30 days)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <AlertTriangle className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No trend data available yet</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Calculate trend statistics
  const currentValue = data[data.length - 1]?.not_applicable_percentage || 0
  const firstValue = data[0]?.not_applicable_percentage || 0
  const averageValue = data.reduce((sum, d) => sum + d.not_applicable_percentage, 0) / data.length
  const peakValue = Math.max(...data.map(d => d.not_applicable_percentage))

  // Calculate trend direction
  const trendChange = currentValue - firstValue
  const trendDirection = trendChange > 0.5 ? 'up' : trendChange < -0.5 ? 'down' : 'stable'

  // Quality status
  const getQualityStatus = (percentage: number) => {
    if (percentage < 5) return { label: 'Excellent', color: 'text-green-600', bgColor: 'bg-green-100 dark:bg-green-900', icon: CheckCircle2 }
    if (percentage < 15) return { label: 'Good', color: 'text-blue-600', bgColor: 'bg-blue-100 dark:bg-blue-900', icon: CheckCircle2 }
    if (percentage < 25) return { label: 'Fair', color: 'text-yellow-600', bgColor: 'bg-yellow-100 dark:bg-yellow-900', icon: AlertTriangle }
    return { label: 'Needs Review', color: 'text-red-600', bgColor: 'bg-red-100 dark:bg-red-900', icon: XCircle }
  }

  const qualityStatus = getQualityStatus(currentValue)
  const QualityIcon = qualityStatus.icon

  // Format chart data
  const chartData = data.map(d => ({
    date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    percentage: parseFloat(d.not_applicable_percentage.toFixed(2))
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" />
          NOT_APPLICABLE Trend (30 days)
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <Info className="h-4 w-4 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p className="text-sm">
                  Tracks the percentage of NOT_APPLICABLE relationships over time.
                  Lower values indicate better entity extraction quality.
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current Status Summary */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm text-muted-foreground">Current</span>
              <Badge className={`${qualityStatus.bgColor} ${qualityStatus.color} border-none text-xs`}>
                {qualityStatus.label}
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-3xl font-bold">{currentValue.toFixed(2)}%</span>
              {trendDirection === 'up' && (
                <TrendingUp className="h-5 w-5 text-red-600" />
              )}
              {trendDirection === 'down' && (
                <TrendingDown className="h-5 w-5 text-green-600" />
              )}
              {trendDirection === 'stable' && (
                <Minus className="h-5 w-5 text-gray-600" />
              )}
            </div>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Average:</span>
              <span className="font-medium">{averageValue.toFixed(2)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Peak:</span>
              <span className="font-medium">{peakValue.toFixed(2)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Change:</span>
              <span className={`font-medium ${trendChange > 0 ? 'text-red-600' : trendChange < 0 ? 'text-green-600' : 'text-gray-600'}`}>
                {trendChange > 0 ? '+' : ''}{trendChange.toFixed(2)}%
              </span>
            </div>
          </div>
        </div>

        {/* Trend Chart */}
        <div className="w-full h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RechartsLineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                className="text-muted-foreground"
              />
              <YAxis
                tick={{ fontSize: 12 }}
                className="text-muted-foreground"
                label={{ value: 'NOT_APPLICABLE %', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
              />
              <RechartsTooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--background))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px',
                }}
                labelStyle={{ color: 'hsl(var(--foreground))' }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="percentage"
                name="NOT_APPLICABLE %"
                stroke="#ef4444"
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            </RechartsLineChart>
          </ResponsiveContainer>
        </div>

        {/* Quality Insights */}
        {currentValue > 15 && (
          <Alert className="bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="text-sm text-yellow-900 dark:text-yellow-100">
              <strong>High NOT_APPLICABLE ratio detected.</strong> Consider reviewing entity extraction quality
              and relationship classification logic.
            </AlertDescription>
          </Alert>
        )}

        {trendDirection === 'down' && (
          <Alert className="bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-sm text-green-900 dark:text-green-100">
              <strong>Positive trend!</strong> NOT_APPLICABLE relationships are decreasing, indicating improved
              data quality.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  )
}

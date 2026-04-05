/**
 * DataQualityCard Component
 *
 * Displays data quality metrics:
 * - Data completeness (% of expected fields populated)
 * - Data freshness (time since last update)
 * - Data accuracy/validation status
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { CheckCircle2, AlertTriangle, Clock, Database } from 'lucide-react'

export interface DataQualityMetric {
  category: string // e.g., "Indices", "Forex", "Commodities"
  total_records: number
  complete_records: number
  completeness_percent: number
  last_updated: string // ISO timestamp
  freshness_minutes: number
  validation_status: 'healthy' | 'warning' | 'critical'
  missing_fields?: string[] // Optional: which fields are commonly missing
}

export interface DataQualityCardProps {
  data: DataQualityMetric[] | undefined
  isLoading: boolean
  error: Error | null
  className?: string
}

/**
 * Data quality metrics card
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useDataQuality()
 * <DataQualityCard data={data} isLoading={isLoading} error={error} />
 * ```
 */
export function DataQualityCard({
  data,
  isLoading,
  error,
  className = '',
}: DataQualityCardProps) {
  // Loading state
  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-4 w-32 mt-2" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-20 w-full" />
            ))}
          </div>
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
            <Database className="h-5 w-5" />
            Data Quality
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-destructive">
            Error loading data quality: {error.message}
          </div>
        </CardContent>
      </Card>
    )
  }

  // Ensure data is an array
  const metricsArray = Array.isArray(data) ? data : []

  // Empty state
  if (metricsArray.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Data Quality
          </CardTitle>
          <CardDescription>Completeness, freshness, and validation metrics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground py-4 text-center">
            No data quality metrics available
          </div>
        </CardContent>
      </Card>
    )
  }

  // Calculate overall metrics
  const totalRecords = metricsArray.reduce((sum, m) => sum + m.total_records, 0)
  const totalComplete = metricsArray.reduce((sum, m) => sum + m.complete_records, 0)
  const overallCompleteness = totalRecords > 0 ? (totalComplete / totalRecords) * 100 : 0
  const avgFreshness = metricsArray.reduce((sum, m) => sum + m.freshness_minutes, 0) / metricsArray.length
  const healthyCount = metricsArray.filter((m) => m.validation_status === 'healthy').length
  const warningCount = metricsArray.filter((m) => m.validation_status === 'warning').length
  const criticalCount = metricsArray.filter((m) => m.validation_status === 'critical').length

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Database className="h-5 w-5" />
          Data Quality
        </CardTitle>
        <CardDescription>
          {metricsArray.length} categories • {overallCompleteness.toFixed(1)}% complete •{' '}
          {formatFreshness(avgFreshness)} avg freshness
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Overall Health Status */}
        <div className="grid grid-cols-3 gap-4 mb-4 pb-4 border-b">
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span className="text-xs text-muted-foreground">Healthy</span>
            </div>
            <div className="text-2xl font-semibold text-green-600">{healthyCount}</div>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
              <span className="text-xs text-muted-foreground">Warning</span>
            </div>
            <div className="text-2xl font-semibold text-yellow-600">{warningCount}</div>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              <span className="text-xs text-muted-foreground">Critical</span>
            </div>
            <div className="text-2xl font-semibold text-red-600">{criticalCount}</div>
          </div>
        </div>

        {/* Category Details */}
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {metricsArray.map((metric) => (
            <div
              key={metric.category}
              className={`p-4 rounded-lg border transition-colors ${
                metric.validation_status === 'critical'
                  ? 'border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950'
                  : metric.validation_status === 'warning'
                  ? 'border-yellow-200 bg-yellow-50 dark:border-yellow-900 dark:bg-yellow-950'
                  : 'border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <h4 className="font-medium text-sm">{metric.category}</h4>
                  <Badge
                    variant={
                      metric.validation_status === 'healthy'
                        ? 'default'
                        : metric.validation_status === 'warning'
                        ? 'secondary'
                        : 'destructive'
                    }
                  >
                    {metric.validation_status}
                  </Badge>
                </div>
                <div className="text-right">
                  <div className="text-lg font-semibold">
                    {metric.completeness_percent.toFixed(1)}%
                  </div>
                  <div className="text-xs text-muted-foreground">complete</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <div className="text-muted-foreground mb-1">Records</div>
                  <div className="font-medium">
                    {metric.complete_records.toLocaleString()} /{' '}
                    {metric.total_records.toLocaleString()}
                  </div>
                </div>
                <div>
                  <div className="text-muted-foreground mb-1 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    Freshness
                  </div>
                  <div className="font-medium">{formatFreshness(metric.freshness_minutes)}</div>
                </div>
              </div>

              {/* Missing Fields Warning */}
              {metric.missing_fields && metric.missing_fields.length > 0 && (
                <div className="mt-2 pt-2 border-t">
                  <div className="text-xs text-muted-foreground mb-1">Common missing fields:</div>
                  <div className="flex flex-wrap gap-1">
                    {metric.missing_fields.map((field) => (
                      <Badge key={field} variant="outline" className="text-xs">
                        {field}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Format freshness in human-readable form
 */
function formatFreshness(minutes: number): string {
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${Math.floor(minutes)}m ago`
  if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`
  return `${Math.floor(minutes / 1440)}d ago`
}

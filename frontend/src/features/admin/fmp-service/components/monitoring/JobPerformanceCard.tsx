/**
 * JobPerformanceCard Component
 *
 * Displays job execution performance metrics:
 * - Average execution time per job
 * - Success/failure rates
 * - Last execution status
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { Activity, Clock, CheckCircle2, XCircle } from 'lucide-react'

export interface JobPerformance {
  job_id: string
  job_name: string
  total_executions: number
  successful_executions: number
  failed_executions: number
  avg_execution_time_ms: number
  last_execution_time: string // ISO timestamp
  last_execution_status: 'success' | 'failed' | 'running'
}

export interface JobPerformanceCardProps {
  data: JobPerformance[] | undefined
  isLoading: boolean
  error: Error | null
  className?: string
}

/**
 * Job performance metrics card
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useJobPerformance()
 * <JobPerformanceCard data={data} isLoading={isLoading} error={error} />
 * ```
 */
export function JobPerformanceCard({
  data,
  isLoading,
  error,
  className = '',
}: JobPerformanceCardProps) {
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
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
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
            <Activity className="h-5 w-5" />
            Job Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-destructive">
            Error loading job performance: {error.message}
          </div>
        </CardContent>
      </Card>
    )
  }

  // Ensure data is an array
  const jobsArray = Array.isArray(data) ? data : []

  // Empty state
  if (jobsArray.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Job Performance
          </CardTitle>
          <CardDescription>Execution metrics for scheduled jobs</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground py-4 text-center">
            No job performance data available
          </div>
        </CardContent>
      </Card>
    )
  }

  // Calculate overall statistics
  const totalExecutions = jobsArray.reduce((sum, job) => sum + job.total_executions, 0)
  const totalSuccess = jobsArray.reduce((sum, job) => sum + job.successful_executions, 0)
  const totalFailed = jobsArray.reduce((sum, job) => sum + job.failed_executions, 0)
  const successRate = totalExecutions > 0 ? (totalSuccess / totalExecutions) * 100 : 0
  const avgExecutionTime = jobsArray.reduce((sum, job) => sum + job.avg_execution_time_ms, 0) / jobsArray.length

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Job Performance
        </CardTitle>
        <CardDescription>
          {jobsArray.length} jobs • {totalExecutions} executions • {successRate.toFixed(1)}% success rate
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Overall Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 pb-4 border-b">
          <div>
            <div className="text-xs text-muted-foreground mb-1">Total Executions</div>
            <div className="text-xl font-semibold">{totalExecutions}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Success Rate</div>
            <div className="text-xl font-semibold text-green-600">
              {successRate.toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Failures</div>
            <div className="text-xl font-semibold text-red-600">{totalFailed}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-1">Avg Time</div>
            <div className="text-xl font-semibold">{avgExecutionTime.toFixed(0)}ms</div>
          </div>
        </div>

        {/* Individual Jobs */}
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {jobsArray.map((job) => {
            const jobSuccessRate =
              job.total_executions > 0
                ? (job.successful_executions / job.total_executions) * 100
                : 0

            return (
              <div
                key={job.job_id}
                className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="font-medium text-sm truncate">{job.job_name}</div>
                    <Badge
                      variant={
                        job.last_execution_status === 'success'
                          ? 'default'
                          : job.last_execution_status === 'failed'
                          ? 'destructive'
                          : 'secondary'
                      }
                      className="shrink-0"
                    >
                      {job.last_execution_status === 'success' && (
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                      )}
                      {job.last_execution_status === 'failed' && (
                        <XCircle className="h-3 w-3 mr-1" />
                      )}
                      {job.last_execution_status}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {job.avg_execution_time_ms.toFixed(0)}ms avg
                    </span>
                    <span>
                      {job.successful_executions}/{job.total_executions} success
                    </span>
                    <span className="text-xs">
                      ({jobSuccessRate.toFixed(1)}%)
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

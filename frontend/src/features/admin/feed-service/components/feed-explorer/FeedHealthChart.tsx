import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Activity } from 'lucide-react'
import type { FeedResponse } from '@/types/feedServiceAdmin'

interface FeedHealthChartProps {
  feeds: FeedResponse[]
}

export function FeedHealthChart({ feeds }: FeedHealthChartProps) {
  // Calculate distribution
  const distribution = {
    healthy: feeds.filter((f) => f.health_score >= 80).length,
    warning: feeds.filter((f) => f.health_score >= 50 && f.health_score < 80).length,
    critical: feeds.filter((f) => f.health_score < 50).length,
  }

  const total = feeds.length
  const healthyPercent = total > 0 ? (distribution.healthy / total) * 100 : 0
  const warningPercent = total > 0 ? (distribution.warning / total) * 100 : 0
  const criticalPercent = total > 0 ? (distribution.critical / total) * 100 : 0

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Activity className="h-5 w-5" />
        Health Score Distribution
      </h3>

      {/* Visual Distribution Bar */}
      <div className="mb-6">
        <div className="flex h-8 rounded-lg overflow-hidden">
          {healthyPercent > 0 && (
            <div
              className="bg-green-500 flex items-center justify-center text-white text-xs font-medium"
              style={{ width: `${healthyPercent}%` }}
            >
              {healthyPercent >= 10 && `${healthyPercent.toFixed(0)}%`}
            </div>
          )}
          {warningPercent > 0 && (
            <div
              className="bg-yellow-500 flex items-center justify-center text-white text-xs font-medium"
              style={{ width: `${warningPercent}%` }}
            >
              {warningPercent >= 10 && `${warningPercent.toFixed(0)}%`}
            </div>
          )}
          {criticalPercent > 0 && (
            <div
              className="bg-red-500 flex items-center justify-center text-white text-xs font-medium"
              style={{ width: `${criticalPercent}%` }}
            >
              {criticalPercent >= 10 && `${criticalPercent.toFixed(0)}%`}
            </div>
          )}
        </div>
      </div>

      {/* Legend & Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="p-3 rounded-lg border bg-green-50 dark:bg-green-950/20">
          <div className="flex items-center gap-2 mb-1">
            <div className="h-3 w-3 rounded-full bg-green-500" />
            <span className="text-sm font-medium">Healthy</span>
          </div>
          <div className="text-2xl font-bold">{distribution.healthy}</div>
          <div className="text-xs text-muted-foreground">80-100 score</div>
        </div>

        <div className="p-3 rounded-lg border bg-yellow-50 dark:bg-yellow-950/20">
          <div className="flex items-center gap-2 mb-1">
            <div className="h-3 w-3 rounded-full bg-yellow-500" />
            <span className="text-sm font-medium">Warning</span>
          </div>
          <div className="text-2xl font-bold">{distribution.warning}</div>
          <div className="text-xs text-muted-foreground">50-79 score</div>
        </div>

        <div className="p-3 rounded-lg border bg-red-50 dark:bg-red-950/20">
          <div className="flex items-center gap-2 mb-1">
            <div className="h-3 w-3 rounded-full bg-red-500" />
            <span className="text-sm font-medium">Critical</span>
          </div>
          <div className="text-2xl font-bold">{distribution.critical}</div>
          <div className="text-xs text-muted-foreground">0-49 score</div>
        </div>
      </div>

      {/* Error Rate */}
      <div className="mt-4 p-3 rounded-lg border">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Feeds with Consecutive Failures</span>
          <Badge variant="destructive">
            {feeds.filter((f) => f.consecutive_failures > 0).length}
          </Badge>
        </div>
      </div>
    </Card>
  )
}

import { Card } from '@/components/ui/Card'
import { Progress } from '@/components/ui/progress'
import { Zap } from 'lucide-react'
import type { CacheStatistics } from '@/types/searchServiceAdmin'

interface CacheStatsCardProps {
  stats: CacheStatistics
}

export function CacheStatsCard({ stats }: CacheStatsCardProps) {
  const hitRate = stats?.hit_rate_percent ?? 0

  // Color coding based on hit rate
  const getHitRateColor = (): string => {
    if (hitRate >= 70) return 'text-green-600'
    if (hitRate >= 40) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getProgressColor = (): string => {
    if (hitRate >= 70) return 'bg-green-500'
    if (hitRate >= 40) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const totalHits = stats?.total_hits ?? 0
  const totalMisses = stats?.total_misses ?? 0
  const totalRequests = totalHits + totalMisses
  const hitRatio = totalRequests > 0
    ? `${totalHits.toLocaleString()} / ${totalRequests.toLocaleString()}`
    : '0 / 0'

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Zap className="h-5 w-5" />
        Cache Performance
      </h3>

      <div className="space-y-4">
        {/* Hit Rate - Prominent Display */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-sm font-medium">Hit Rate</div>
            <div className={`text-2xl font-bold ${getHitRateColor()}`}>
              {hitRate.toFixed(1)}%
            </div>
          </div>
          <Progress
            value={hitRate}
            className="h-3"
            indicatorClassName={getProgressColor()}
          />
          <div className="text-xs text-muted-foreground text-center">
            {hitRate >= 70 && '✓ Excellent performance'}
            {hitRate >= 40 && hitRate < 70 && '⚠ Moderate performance'}
            {hitRate < 40 && '✗ Poor performance - consider cache tuning'}
          </div>
        </div>

        {/* Memory Usage */}
        <div className="flex items-center justify-between p-3 rounded-lg border">
          <div className="flex items-center gap-3">
            <Zap className="h-4 w-4 text-muted-foreground" />
            <div>
              <div className="font-medium">Memory Used</div>
              <div className="text-sm text-muted-foreground">
                {(stats?.total_keys ?? 0).toLocaleString()} keys
              </div>
            </div>
          </div>
          <div className="text-sm font-mono font-semibold">{stats?.memory_used ?? 'Unknown'}</div>
        </div>

        {/* Hits/Misses Ratio */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-lg border bg-green-50 dark:bg-green-950/20">
            <div className="text-sm text-muted-foreground">Hits</div>
            <div className="text-lg font-bold text-green-600">
              {totalHits.toLocaleString()}
            </div>
          </div>
          <div className="p-3 rounded-lg border bg-red-50 dark:bg-red-950/20">
            <div className="text-sm text-muted-foreground">Misses</div>
            <div className="text-lg font-bold text-red-600">
              {totalMisses.toLocaleString()}
            </div>
          </div>
        </div>

        {/* Hit Ratio */}
        <div className="flex items-center justify-between p-3 rounded-lg border">
          <div className="font-medium">Hit Ratio</div>
          <div className="text-sm font-mono">{hitRatio}</div>
        </div>

        {/* Evicted and Expired Keys */}
        <div className="pt-3 border-t">
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Evicted:</span>
              <span className="font-medium">{(stats?.evicted_keys ?? 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Expired:</span>
              <span className="font-medium">{(stats?.expired_keys ?? 0).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}

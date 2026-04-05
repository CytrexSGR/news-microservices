import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Cpu, Users } from 'lucide-react'
import type { CeleryStatistics } from '@/types/searchServiceAdmin'

interface CeleryStatsCardProps {
  stats: CeleryStatistics
}

export function CeleryStatsCard({ stats }: CeleryStatsCardProps) {
  const isHealthy = stats?.status === 'healthy'
  const hasNoWorkers = (stats?.active_workers ?? 0) === 0

  const getStatusVariant = (): 'default' | 'destructive' => {
    return isHealthy ? 'default' : 'destructive'
  }

  const getStatusLabel = (): string => {
    if (hasNoWorkers) return 'No Workers'
    return stats?.status ?? 'unknown'
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Cpu className="h-5 w-5" />
        Celery Workers
      </h3>

      <div className="space-y-4">
        {/* Active Workers - Prominent Display */}
        <div className="flex items-center justify-between p-4 rounded-lg border-2 border-primary/20 bg-primary/5">
          <div>
            <div className="text-2xl font-bold">{stats?.active_workers ?? 0}</div>
            <div className="text-sm text-muted-foreground">Active Workers</div>
          </div>
          <Cpu className="h-8 w-8 text-primary" />
        </div>

        {/* Status Badge */}
        <div className="flex items-center justify-between p-3 rounded-lg border">
          <div className="flex items-center gap-3">
            <Users className="h-4 w-4 text-muted-foreground" />
            <div className="font-medium">Status</div>
          </div>
          <Badge variant={getStatusVariant()}>
            {getStatusLabel()}
          </Badge>
        </div>

        {/* Task Metrics */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-lg border">
            <div className="text-sm text-muted-foreground">Registered Tasks</div>
            <div className="text-lg font-bold">{stats?.registered_tasks ?? 0}</div>
          </div>
          <div className="p-3 rounded-lg border">
            <div className="text-sm text-muted-foreground">Reserved Tasks</div>
            <div className="text-lg font-bold">{stats?.reserved_tasks ?? 0}</div>
          </div>
        </div>

        {/* Worker Details */}
        {stats.worker_stats && stats.worker_stats.length > 0 && (
          <div className="pt-3 border-t">
            <div className="text-sm font-medium mb-3">Worker Details</div>
            <div className="space-y-2">
              {stats.worker_stats.map((worker, index) => (
                <div key={index} className="flex items-center justify-between p-3 rounded-lg border bg-secondary/10">
                  <div className="flex items-center gap-3">
                    <Cpu className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <div className="text-sm font-medium truncate max-w-[200px]" title={worker.worker}>
                        {worker.worker}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Pool size: {worker.pool}
                      </div>
                    </div>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {Object.keys(worker.total_tasks || {}).length} tasks
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* No Workers Warning */}
        {hasNoWorkers && (
          <div className="p-3 rounded-lg border border-destructive bg-destructive/10">
            <div className="text-sm font-medium text-destructive">
              ⚠ No active workers detected
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Background tasks will not be processed
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

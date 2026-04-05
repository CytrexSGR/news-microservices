import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Activity, Server, Clock } from 'lucide-react'
import type { FeedServiceHealth } from '@/types/feedServiceAdmin'

interface ServiceHealthCardProps {
  health: FeedServiceHealth
}

export function ServiceHealthCard({ health }: ServiceHealthCardProps) {
  const isHealthy = health.status === 'UP' || health.status === 'healthy'
  const isSchedulerRunning = health.scheduler?.is_running ?? false

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Activity className="h-5 w-5" />
        Service Health
      </h3>

      <div className="space-y-4">
        {/* Overall Status */}
        <div className="flex items-center justify-between p-3 rounded-lg border">
          <div className="flex items-center gap-3">
            <Server className="h-4 w-4 text-muted-foreground" />
            <div>
              <div className="font-medium">Service Status</div>
              <div className="text-sm text-muted-foreground">
                {health.service} - {health.environment}
              </div>
            </div>
          </div>
          <Badge variant={isHealthy ? 'default' : 'destructive'}>
            {health.status}
          </Badge>
        </div>

        {/* Scheduler Status */}
        {health.scheduler && (
          <div className="flex items-center justify-between p-3 rounded-lg border">
            <div className="flex items-center gap-3">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <div>
                <div className="font-medium">Scheduler</div>
                <div className="text-sm text-muted-foreground">
                  Check interval: {health.scheduler.check_interval_seconds}s
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <Badge variant={isSchedulerRunning ? 'default' : 'secondary'}>
                {isSchedulerRunning ? 'Running' : 'Stopped'}
              </Badge>
              {health.scheduler.fetcher_active && (
                <Badge variant="outline">Fetcher Active</Badge>
              )}
            </div>
          </div>
        )}

        {/* Version */}
        <div className="pt-3 border-t text-sm">
          <span className="text-muted-foreground">Version:</span>{' '}
          <span className="font-medium">{health.version}</span>
        </div>
      </div>
    </Card>
  )
}

import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Clock, PlayCircle, Timer } from 'lucide-react'
import type { FeedServiceHealth } from '@/types/feedServiceAdmin'

interface SchedulerStatusCardProps {
  health: FeedServiceHealth
}

export function SchedulerStatusCard({ health }: SchedulerStatusCardProps) {
  const schedulerData = health.scheduler_status

  if (!health.scheduler_enabled) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Scheduler Status
        </h3>
        <div className="text-center py-8 text-muted-foreground">
          <Clock className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p>Scheduler is disabled</p>
          <p className="text-sm mt-1">Enable in service configuration to automate feed fetching</p>
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Clock className="h-5 w-5" />
        Scheduler Status
      </h3>

      <div className="space-y-4">
        {/* Active Jobs */}
        <div className="flex items-center justify-between p-3 rounded-lg border">
          <div className="flex items-center gap-3">
            <PlayCircle className="h-4 w-4 text-muted-foreground" />
            <div>
              <div className="font-medium">Active Jobs</div>
              <div className="text-sm text-muted-foreground">
                Currently running fetch operations
              </div>
            </div>
          </div>
          <Badge variant="outline" className="text-lg font-semibold">
            {schedulerData?.active_jobs || 0}
          </Badge>
        </div>

        {/* Next Scheduled Fetch */}
        {schedulerData?.next_scheduled_fetch && (
          <div className="p-3 rounded-lg border">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <div className="font-medium">Next Scheduled Fetch</div>
            </div>
            <div className="text-sm text-muted-foreground ml-6">
              {new Date(schedulerData.next_scheduled_fetch).toLocaleString()}
            </div>
          </div>
        )}

        {/* Average Fetch Duration */}
        {schedulerData?.average_fetch_duration_seconds !== undefined && (
          <div className="flex items-center justify-between p-3 rounded-lg border">
            <div className="flex items-center gap-3">
              <Timer className="h-4 w-4 text-muted-foreground" />
              <div>
                <div className="font-medium">Average Fetch Time</div>
                <div className="text-sm text-muted-foreground">
                  Per feed operation
                </div>
              </div>
            </div>
            <Badge variant="outline" className="text-lg font-semibold">
              {schedulerData.average_fetch_duration_seconds.toFixed(1)}s
            </Badge>
          </div>
        )}
      </div>
    </Card>
  )
}

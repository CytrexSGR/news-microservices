/**
 * SchedulerStatusCard Component
 *
 * Displays scheduler operational status including:
 * - Feed monitor status
 * - Job processor status
 * - Cron scheduler status
 * - Queue statistics
 */

import { Activity, Clock, Cog, Layers } from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import type { SchedulerStatus } from '../types';

interface SchedulerStatusCardProps {
  status: SchedulerStatus;
}

export function SchedulerStatusCard({ status }: SchedulerStatusCardProps) {
  const allRunning =
    status.feed_monitor.is_running &&
    status.job_processor.is_running &&
    status.cron_scheduler.is_running;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              <Cog className="h-5 w-5" />
              Scheduler Status
            </CardTitle>
            <CardDescription>Service components and workers</CardDescription>
          </div>
          <Badge
            variant={allRunning ? 'default' : 'destructive'}
            className={allRunning ? 'bg-green-500' : ''}
          >
            {allRunning ? 'All Running' : 'Degraded'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Feed Monitor */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
            <div className="flex items-center gap-3">
              <Activity
                className={`h-4 w-4 ${status.feed_monitor.is_running ? 'text-green-500' : 'text-red-500'}`}
              />
              <div>
                <div className="font-medium text-sm">Feed Monitor</div>
                <div className="text-xs text-muted-foreground">
                  Interval: {status.feed_monitor.check_interval_seconds}s
                </div>
              </div>
            </div>
            <Badge variant={status.feed_monitor.is_running ? 'outline' : 'destructive'}>
              {status.feed_monitor.is_running ? 'Running' : 'Stopped'}
            </Badge>
          </div>

          {/* Job Processor */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
            <div className="flex items-center gap-3">
              <Layers
                className={`h-4 w-4 ${status.job_processor.is_running ? 'text-green-500' : 'text-red-500'}`}
              />
              <div>
                <div className="font-medium text-sm">Job Processor</div>
                <div className="text-xs text-muted-foreground">
                  Interval: {status.job_processor.process_interval_seconds}s |
                  Max concurrent: {status.job_processor.max_concurrent_jobs}
                </div>
              </div>
            </div>
            <Badge variant={status.job_processor.is_running ? 'outline' : 'destructive'}>
              {status.job_processor.is_running ? 'Running' : 'Stopped'}
            </Badge>
          </div>

          {/* Cron Scheduler */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
            <div className="flex items-center gap-3">
              <Clock
                className={`h-4 w-4 ${status.cron_scheduler.is_running ? 'text-green-500' : 'text-red-500'}`}
              />
              <div>
                <div className="font-medium text-sm">Cron Scheduler</div>
                <div className="text-xs text-muted-foreground">
                  Total jobs: {status.cron_scheduler.total_jobs} | Running:{' '}
                  {status.cron_scheduler.running_jobs}
                </div>
              </div>
            </div>
            <Badge variant={status.cron_scheduler.is_running ? 'outline' : 'destructive'}>
              {status.cron_scheduler.is_running ? 'Running' : 'Stopped'}
            </Badge>
          </div>

          {/* Queue Stats */}
          <div className="mt-4 pt-4 border-t">
            <div className="text-sm font-medium mb-2">Queue Status</div>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 rounded-lg bg-yellow-500/10">
                <div className="text-2xl font-bold text-yellow-500">
                  {status.queue.pending_jobs}
                </div>
                <div className="text-xs text-muted-foreground">Pending</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-blue-500/10">
                <div className="text-2xl font-bold text-blue-500">
                  {status.queue.processing_jobs}
                </div>
                <div className="text-xs text-muted-foreground">Processing</div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * JobDetailPanel Component
 *
 * Shows detailed job information including:
 * - Job configuration
 * - Execution history
 * - Performance metrics
 */

import { X, Clock, Calendar, Activity, AlertTriangle, CheckCircle } from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { JobHistoryChart } from './JobHistoryChart';
import type { CronJob } from '../types';
import { cronToHumanReadable } from '../types';

interface JobDetailPanelProps {
  job: CronJob;
  onClose: () => void;
}

export function JobDetailPanel({ job, onClose }: JobDetailPanelProps) {
  const formatNextRun = (nextRunTime: string | null): string => {
    if (!nextRunTime) return 'Not scheduled';

    const date = new Date(nextRunTime);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);

    if (diffMins < 0) return 'Overdue';
    if (diffMins < 60) return `In ${diffMins} minutes`;
    if (diffHours < 24) return `In ${diffHours} hours ${diffMins % 60} min`;
    return `${Math.floor(diffHours / 24)} days ${diffHours % 24} hours`;
  };

  // Mock history data - in real implementation this would come from the API
  const mockHistory = [
    { timestamp: new Date(Date.now() - 3600000).toISOString(), duration: 1200, success: true },
    { timestamp: new Date(Date.now() - 7200000).toISOString(), duration: 1350, success: true },
    { timestamp: new Date(Date.now() - 10800000).toISOString(), duration: 980, success: true },
    { timestamp: new Date(Date.now() - 14400000).toISOString(), duration: 2100, success: false },
    { timestamp: new Date(Date.now() - 18000000).toISOString(), duration: 1100, success: true },
    { timestamp: new Date(Date.now() - 21600000).toISOString(), duration: 1250, success: true },
    { timestamp: new Date(Date.now() - 25200000).toISOString(), duration: 1050, success: true },
    { timestamp: new Date(Date.now() - 28800000).toISOString(), duration: 1400, success: true },
  ];

  const avgDuration =
    mockHistory.reduce((sum, h) => sum + h.duration, 0) / mockHistory.length;
  const successRate =
    (mockHistory.filter((h) => h.success).length / mockHistory.length) * 100;

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{job.name}</CardTitle>
            <CardDescription className="font-mono text-xs">{job.id}</CardDescription>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Status */}
        <div className="flex items-center gap-2">
          {job.pending ? (
            <Badge className="bg-blue-500/10 text-blue-500">Pending Execution</Badge>
          ) : job.next_run_time ? (
            <Badge className="bg-green-500/10 text-green-500">Active</Badge>
          ) : (
            <Badge className="bg-gray-500/10 text-gray-500">Paused</Badge>
          )}
        </div>

        {/* Schedule Info */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Schedule
          </h4>
          <div className="pl-6 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Pattern:</span>
              <span className="font-medium">{cronToHumanReadable(job.trigger)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Raw trigger:</span>
              <span className="font-mono text-xs">{job.trigger}</span>
            </div>
          </div>
        </div>

        <Separator />

        {/* Next Run */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Next Execution
          </h4>
          <div className="pl-6 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Time until:</span>
              <span className="font-medium">{formatNextRun(job.next_run_time)}</span>
            </div>
            {job.next_run_time && (
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Scheduled at:</span>
                <span>{new Date(job.next_run_time).toLocaleString()}</span>
              </div>
            )}
          </div>
        </div>

        <Separator />

        {/* Performance Metrics */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Performance (Last 24h)
          </h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 rounded-lg bg-muted/50 text-center">
              <div className="text-2xl font-bold">{(avgDuration / 1000).toFixed(1)}s</div>
              <div className="text-xs text-muted-foreground">Avg Duration</div>
            </div>
            <div className="p-3 rounded-lg bg-muted/50 text-center">
              <div className={`text-2xl font-bold ${successRate >= 95 ? 'text-green-500' : successRate >= 80 ? 'text-yellow-500' : 'text-red-500'}`}>
                {successRate.toFixed(0)}%
              </div>
              <div className="text-xs text-muted-foreground">Success Rate</div>
            </div>
          </div>
        </div>

        <Separator />

        {/* Execution History Chart */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium">Execution History</h4>
          <JobHistoryChart
            history={mockHistory.map((h) => ({
              timestamp: h.timestamp,
              duration: h.duration,
              success: h.success,
            }))}
          />
        </div>

        <Separator />

        {/* Recent Executions */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium">Recent Runs</h4>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {mockHistory.slice(0, 5).map((execution, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2 rounded-lg bg-muted/50"
              >
                <div className="flex items-center gap-2">
                  {execution.success ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : (
                    <AlertTriangle className="h-4 w-4 text-red-500" />
                  )}
                  <div>
                    <div className="text-xs text-muted-foreground">
                      {new Date(execution.timestamp).toLocaleString()}
                    </div>
                  </div>
                </div>
                <div className="text-sm font-mono">
                  {(execution.duration / 1000).toFixed(2)}s
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

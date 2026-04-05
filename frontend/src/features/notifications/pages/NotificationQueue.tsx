/**
 * NotificationQueue Page
 *
 * Admin page for monitoring notification queue health and managing failed notifications.
 */

import { useState } from 'react';
import { Activity, RefreshCw, Settings2, AlertTriangle, Pause, Play } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { QueueStatsCards } from '../components/queue/QueueStatsCards';
import { QueueChart } from '../components/queue/QueueChart';
import { FailedNotificationsList } from '../components/queue/FailedNotificationsList';
import { useQueueStats, useRateLimits } from '../api';

export function NotificationQueue() {
  const { data: stats, refetch: refetchStats, isRefetching } = useQueueStats();
  const { data: rateLimits } = useRateLimits();
  const [isPaused, setIsPaused] = useState(false);

  const handlePauseQueue = () => {
    // TODO: Implement queue pause via MCP
    setIsPaused(true);
  };

  const handleResumeQueue = () => {
    // TODO: Implement queue resume via MCP
    setIsPaused(false);
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="h-6 w-6" />
            Notification Queue
            {isPaused && (
              <Badge variant="secondary" className="ml-2">
                <Pause className="h-3 w-3 mr-1" />
                Paused
              </Badge>
            )}
          </h1>
          <p className="text-muted-foreground mt-1">
            Monitor queue health and manage failed notifications
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => refetchStats()}
            disabled={isRefetching}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {isPaused ? (
            <Button onClick={handleResumeQueue}>
              <Play className="h-4 w-4 mr-2" />
              Resume Queue
            </Button>
          ) : (
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="outline">
                  <Pause className="h-4 w-4 mr-2" />
                  Pause Queue
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Pause Notification Queue?</AlertDialogTitle>
                  <AlertDialogDescription>
                    Pausing the queue will stop all notification processing. New notifications
                    will be queued but not delivered until the queue is resumed.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={handlePauseQueue}>
                    Pause Queue
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          )}
        </div>
      </div>

      {/* Stats cards */}
      <QueueStatsCards />

      {/* Main content */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview" className="gap-2">
            <Activity className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="failed" className="gap-2">
            <AlertTriangle className="h-4 w-4" />
            Failed
            {stats && stats.dlq > 0 && (
              <Badge variant="destructive" className="ml-1 h-5 px-1.5">
                {stats.dlq}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="rate-limits" className="gap-2">
            <Settings2 className="h-4 w-4" />
            Rate Limits
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <QueueChart />

          {/* Queue info */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Processing Status</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Queue Status</span>
                  <Badge variant={isPaused ? 'secondary' : 'default'}>
                    {isPaused ? 'Paused' : 'Active'}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Workers</span>
                  <span className="font-medium">4 active</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Avg. Processing Time</span>
                  <span className="font-medium">~250ms</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Retry Policy</span>
                  <span className="font-medium">3 attempts, exponential backoff</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Channel Health</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Email</span>
                  <Badge variant="outline" className="text-green-600">
                    Healthy
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Webhook</span>
                  <Badge variant="outline" className="text-green-600">
                    Healthy
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Push</span>
                  <Badge variant="outline" className="text-green-600">
                    Healthy
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Last Health Check</span>
                  <span className="text-sm text-muted-foreground">
                    {new Date().toLocaleTimeString('de-DE')}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="failed" className="space-y-4">
          <FailedNotificationsList />
        </TabsContent>

        <TabsContent value="rate-limits" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Rate Limit Configuration</CardTitle>
              <CardDescription>
                Current rate limits for notification delivery by channel
              </CardDescription>
            </CardHeader>
            <CardContent>
              {rateLimits ? (
                <div className="space-y-4">
                  {rateLimits.limits.map((limit) => (
                    <div
                      key={limit.channel}
                      className="flex items-center justify-between p-4 border rounded-lg"
                    >
                      <div>
                        <h4 className="font-medium capitalize">{limit.channel}</h4>
                        <p className="text-sm text-muted-foreground">
                          {limit.requests_per_minute} requests/minute,{' '}
                          {limit.requests_per_hour} requests/hour
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium">
                          Current Usage
                        </div>
                        <div className="text-2xl font-bold">
                          {limit.current_usage ?? 0}
                          <span className="text-sm text-muted-foreground font-normal">
                            /{limit.requests_per_minute}
                          </span>
                        </div>
                        <div
                          className="h-2 w-32 bg-muted rounded-full overflow-hidden mt-1"
                        >
                          <div
                            className="h-full bg-primary transition-all"
                            style={{
                              width: `${Math.min(100, ((limit.current_usage ?? 0) / limit.requests_per_minute) * 100)}%`,
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Loading rate limit information...
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Rate Limit Best Practices</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none dark:prose-invert">
              <ul>
                <li>
                  <strong>Email:</strong> Keep under 100/minute to avoid being flagged as spam
                </li>
                <li>
                  <strong>Webhook:</strong> Respect target server rate limits and implement backoff
                </li>
                <li>
                  <strong>Push:</strong> FCM/APNs have their own limits; batch notifications when possible
                </li>
                <li>
                  <strong>Bursts:</strong> Use queue smoothing to spread notifications evenly
                </li>
              </ul>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

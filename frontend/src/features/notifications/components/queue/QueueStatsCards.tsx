/**
 * QueueStatsCards Component
 *
 * Metric cards showing pending, retrying, and DLQ notification counts.
 */

import { Clock, RefreshCw, AlertTriangle, CheckCircle, Activity, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { cn } from '@/lib/utils';
import { useQueueStats } from '../../api';

interface QueueStatsCardsProps {
  className?: string;
}

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  description?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  variant?: 'default' | 'warning' | 'danger' | 'success';
}

function StatCard({ title, value, icon, description, trend, variant = 'default' }: StatCardProps) {
  const variantStyles = {
    default: 'border-border',
    warning: 'border-yellow-500/50 bg-yellow-50/50 dark:bg-yellow-950/20',
    danger: 'border-red-500/50 bg-red-50/50 dark:bg-red-950/20',
    success: 'border-green-500/50 bg-green-50/50 dark:bg-green-950/20',
  };

  const iconStyles = {
    default: 'text-muted-foreground',
    warning: 'text-yellow-600 dark:text-yellow-400',
    danger: 'text-red-600 dark:text-red-400',
    success: 'text-green-600 dark:text-green-400',
  };

  return (
    <Card className={cn('transition-all', variantStyles[variant])}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div className={cn('h-5 w-5', iconStyles[variant])}>{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value.toLocaleString()}</div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
        {trend && (
          <div
            className={cn(
              'flex items-center text-xs mt-1',
              trend.isPositive ? 'text-green-600' : 'text-red-600'
            )}
          >
            {trend.isPositive ? '+' : '-'}
            {Math.abs(trend.value)}% from last hour
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function LoadingCards() {
  return (
    <>
      {[1, 2, 3, 4, 5].map((i) => (
        <Card key={i}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-5 w-5 rounded" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-8 w-16 mb-1" />
            <Skeleton className="h-3 w-24" />
          </CardContent>
        </Card>
      ))}
    </>
  );
}

export function QueueStatsCards({ className }: QueueStatsCardsProps) {
  const { data, isLoading, error } = useQueueStats();

  if (error) {
    return (
      <div className={cn('grid gap-4 md:grid-cols-2 lg:grid-cols-5', className)}>
        <Card className="col-span-full border-destructive">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-4 w-4" />
              <span>Failed to load queue statistics</span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isLoading || !data) {
    return (
      <div className={cn('grid gap-4 md:grid-cols-2 lg:grid-cols-5', className)}>
        <LoadingCards />
      </div>
    );
  }

  const { pending, retrying, dlq, processed_last_hour, success_rate } = data;

  // Determine variants based on values
  const pendingVariant = pending > 1000 ? 'warning' : pending > 5000 ? 'danger' : 'default';
  const retryingVariant = retrying > 100 ? 'warning' : retrying > 500 ? 'danger' : 'default';
  const dlqVariant = dlq > 0 ? 'danger' : 'default';
  const successVariant = success_rate >= 99 ? 'success' : success_rate >= 95 ? 'default' : 'warning';

  return (
    <div className={cn('grid gap-4 md:grid-cols-2 lg:grid-cols-5', className)}>
      <StatCard
        title="Pending"
        value={pending}
        icon={<Clock className="h-5 w-5" />}
        description="Awaiting processing"
        variant={pendingVariant}
      />

      <StatCard
        title="Retrying"
        value={retrying}
        icon={<RefreshCw className="h-5 w-5" />}
        description="Scheduled for retry"
        variant={retryingVariant}
      />

      <StatCard
        title="Dead Letter Queue"
        value={dlq}
        icon={<AlertTriangle className="h-5 w-5" />}
        description="Failed permanently"
        variant={dlqVariant}
      />

      <StatCard
        title="Processed (1h)"
        value={processed_last_hour}
        icon={<Activity className="h-5 w-5" />}
        description="Last hour throughput"
      />

      <StatCard
        title="Success Rate"
        value={success_rate}
        icon={<CheckCircle className="h-5 w-5" />}
        description={`${success_rate.toFixed(1)}% delivery rate`}
        variant={successVariant}
      />
    </div>
  );
}

/**
 * AsyncJobStatusView - Job progress view
 *
 * Displays the progress and status of an async batch canonicalization job.
 */
import { Loader2, CheckCircle2, AlertCircle, Clock, Activity, XCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { useAsyncJobStatus } from '../api/useAsyncJobStatus';
import type { AsyncJob } from '../types/entities.types';

interface AsyncJobStatusViewProps {
  jobId: string;
  onCompleted?: (job: AsyncJob) => void;
  onViewResults?: (jobId: string) => void;
  className?: string;
}

const StatusIcon = ({ status }: { status: AsyncJob['status'] }) => {
  switch (status) {
    case 'queued':
      return <Clock className="h-5 w-5 text-yellow-500" />;
    case 'processing':
      return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
    case 'completed':
      return <CheckCircle2 className="h-5 w-5 text-green-500" />;
    case 'failed':
      return <XCircle className="h-5 w-5 text-destructive" />;
  }
};

const StatusBadge = ({ status }: { status: AsyncJob['status'] }) => {
  const variants: Record<AsyncJob['status'], 'default' | 'secondary' | 'destructive' | 'outline'> = {
    queued: 'secondary',
    processing: 'default',
    completed: 'outline',
    failed: 'destructive',
  };

  return (
    <Badge variant={variants[status]} className="capitalize">
      {status}
    </Badge>
  );
};

export function AsyncJobStatusView({
  jobId,
  onCompleted,
  onViewResults,
  className,
}: AsyncJobStatusViewProps) {
  const {
    data: job,
    isLoading,
    isError,
    error,
    isProcessing,
    isCompleted,
    isFailed,
    progress,
  } = useAsyncJobStatus(jobId, {
    onCompleted,
  });

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Skeleton className="h-5 w-5 rounded-full" />
            <Skeleton className="h-5 w-32" />
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-2 w-full" />
          <Skeleton className="h-4 w-48" />
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-5 w-5" />
            Job Status Error
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Failed to fetch job status: {error?.message}
          </p>
        </CardContent>
      </Card>
    );
  }

  if (!job) return null;

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <StatusIcon status={job.status} />
            Batch Job Status
          </CardTitle>
          <StatusBadge status={job.status} />
        </div>
        <CardDescription className="font-mono text-xs">{jobId}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Progress</span>
            <span className="font-medium">{progress.toFixed(1)}%</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">Processed</div>
            <div className="text-lg font-semibold">
              {job.stats.processed_entities} / {job.stats.total_entities}
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">Success Rate</div>
            <div className="text-lg font-semibold">
              {job.stats.processed_entities > 0
                ? ((job.stats.successful / job.stats.processed_entities) * 100).toFixed(1)
                : 0}
              %
            </div>
          </div>
        </div>

        {/* Detailed Stats */}
        <div className="grid grid-cols-4 gap-2">
          <div className="p-2 bg-muted rounded text-center">
            <div className="text-lg font-bold">{job.stats.total_entities}</div>
            <div className="text-xs text-muted-foreground">Total</div>
          </div>
          <div className="p-2 bg-muted rounded text-center">
            <div className="text-lg font-bold text-blue-500">{job.stats.processed_entities}</div>
            <div className="text-xs text-muted-foreground">Processed</div>
          </div>
          <div className="p-2 bg-muted rounded text-center">
            <div className="text-lg font-bold text-green-500">{job.stats.successful}</div>
            <div className="text-xs text-muted-foreground">Success</div>
          </div>
          <div className="p-2 bg-muted rounded text-center">
            <div className="text-lg font-bold text-destructive">{job.stats.failed}</div>
            <div className="text-xs text-muted-foreground">Failed</div>
          </div>
        </div>

        {/* Timestamps */}
        <div className="space-y-1 text-xs text-muted-foreground">
          {job.started_at && (
            <div className="flex items-center gap-2">
              <Clock className="h-3 w-3" />
              Started: {new Date(job.started_at).toLocaleString()}
            </div>
          )}
          {job.completed_at && (
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-3 w-3" />
              Completed: {new Date(job.completed_at).toLocaleString()}
            </div>
          )}
        </div>

        {/* Error Message */}
        {isFailed && job.error_message && (
          <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
            <div className="flex items-center gap-2 text-destructive text-sm font-medium">
              <AlertCircle className="h-4 w-4" />
              Error
            </div>
            <p className="mt-1 text-sm text-destructive/80">{job.error_message}</p>
          </div>
        )}

        {/* Actions */}
        {isCompleted && onViewResults && (
          <Button onClick={() => onViewResults(jobId)} className="w-full">
            <Activity className="mr-2 h-4 w-4" />
            View Results
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

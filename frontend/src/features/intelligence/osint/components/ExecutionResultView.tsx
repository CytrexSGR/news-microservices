/**
 * ExecutionResultView - OSINT Execution Results Display
 *
 * Shows the results of an OSINT execution with status and data
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { Badge } from '@/components/ui/badge';
import {
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Timer,
  FileJson,
} from 'lucide-react';
import { useOsintExecution, useOsintExecutionPolling } from '../api';
import type { OsintExecution, ExecutionStatus } from '../types/osint.types';
import { getStatusColor, getStatusBgColor } from '../types/osint.types';

interface ExecutionResultViewProps {
  executionId: string;
  pollWhileRunning?: boolean;
}

export function ExecutionResultView({
  executionId,
  pollWhileRunning = true,
}: ExecutionResultViewProps) {
  const { data: execution, isLoading, error } = useOsintExecution(executionId, true);
  const { data: polledExecution } = useOsintExecutionPolling(
    executionId,
    pollWhileRunning && !!execution && ['pending', 'running'].includes(execution.status)
  );

  // Use polled data if available and more recent
  const currentExecution = polledExecution || execution;

  if (isLoading) {
    return <ExecutionResultSkeleton />;
  }

  if (error || !currentExecution) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-red-500">
            <AlertCircle className="h-5 w-5" />
            <span>Failed to load execution results</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Status Card */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <StatusIcon status={currentExecution.status} />
                Execution Results
              </CardTitle>
              {currentExecution.instance_name && (
                <CardDescription>{currentExecution.instance_name}</CardDescription>
              )}
            </div>
            <Badge
              className={`${getStatusBgColor(currentExecution.status)} ${getStatusColor(currentExecution.status)} border-0`}
            >
              {currentExecution.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <InfoItem
              icon={<Clock className="h-4 w-4" />}
              label="Started"
              value={new Date(currentExecution.started_at).toLocaleString()}
            />
            {currentExecution.completed_at && (
              <InfoItem
                icon={<CheckCircle2 className="h-4 w-4" />}
                label="Completed"
                value={new Date(currentExecution.completed_at).toLocaleString()}
              />
            )}
            {currentExecution.duration_seconds !== undefined && (
              <InfoItem
                icon={<Timer className="h-4 w-4" />}
                label="Duration"
                value={formatDuration(currentExecution.duration_seconds)}
              />
            )}
            {currentExecution.metadata?.triggered_by && (
              <InfoItem
                icon={<FileJson className="h-4 w-4" />}
                label="Triggered By"
                value={currentExecution.metadata.triggered_by}
              />
            )}
          </div>
        </CardContent>
      </Card>

      {/* Error Message */}
      {currentExecution.status === 'failed' && currentExecution.error_message && (
        <Card className="border-red-500/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-500">
              <XCircle className="h-5 w-5" />
              Error
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap text-sm text-red-500 bg-red-500/5 rounded-lg p-4">
              {currentExecution.error_message}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* Results Data */}
      {currentExecution.status === 'completed' && currentExecution.results && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileJson className="h-5 w-5" />
              Results Data
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="rounded-lg bg-muted p-4 text-sm overflow-x-auto max-h-96">
              {JSON.stringify(currentExecution.results, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* Running State */}
      {(currentExecution.status === 'pending' || currentExecution.status === 'running') && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center py-8">
              <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
              <p className="text-lg font-medium">
                {currentExecution.status === 'pending' ? 'Waiting to start...' : 'Execution in progress...'}
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Results will appear here when complete
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

interface StatusIconProps {
  status: ExecutionStatus;
}

function StatusIcon({ status }: StatusIconProps) {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="h-5 w-5 text-green-500" />;
    case 'failed':
      return <XCircle className="h-5 w-5 text-red-500" />;
    case 'running':
      return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
    case 'pending':
      return <Clock className="h-5 w-5 text-gray-500" />;
    default:
      return <AlertCircle className="h-5 w-5 text-gray-500" />;
  }
}

interface InfoItemProps {
  icon: React.ReactNode;
  label: string;
  value: string;
}

function InfoItem({ icon, label, value }: InfoItemProps) {
  return (
    <div className="rounded-lg border p-3">
      <div className="flex items-center gap-2 text-muted-foreground mb-1">
        {icon}
        <span className="text-xs uppercase tracking-wider">{label}</span>
      </div>
      <div className="text-sm font-medium">{value}</div>
    </div>
  );
}

function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
}

function ExecutionResultSkeleton() {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-5 w-24" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="rounded-lg border p-3">
                <Skeleton className="h-4 w-16 mb-2" />
                <Skeleton className="h-5 w-24" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    </div>
  );
}

export default ExecutionResultView;

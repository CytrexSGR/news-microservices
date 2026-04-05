/**
 * Optimization Job Monitor
 *
 * Real-time monitoring of optimization jobs.
 *
 * Features:
 * - List all optimization jobs
 * - Real-time progress updates (polling)
 * - Filter by status (all, running, completed, failed)
 * - Job details with metrics
 * - Cancel running jobs
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/Button';
import { Progress } from '@/components/ui/progress';
import {
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  TrendingUp,
  X,
  RefreshCw,
  Filter,
  Eye,
  Bug
} from 'lucide-react';

import type { OptimizationJob, OptimizationResult } from '../types/optimization';
import { OptimizationResultsView } from './OptimizationResultsView';
import { predictionClient } from '@/lib/api-client';

interface OptimizationJobMonitorProps {
  strategyId?: string; // Optional: filter by strategy
}

export function OptimizationJobMonitor({ strategyId }: OptimizationJobMonitorProps) {
  const [statusFilter, setStatusFilter] = useState<'all' | 'running' | 'completed' | 'failed'>('all');
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Fetch optimization jobs with real-time updates
  const { data: jobs, isLoading, isRefetching } = useQuery<OptimizationJob[]>({
    queryKey: ['optimization-jobs', strategyId, statusFilter],
    queryFn: async () => {
      const params: Record<string, string> = { limit: '50' };
      if (strategyId) params.strategy_id = strategyId;
      if (statusFilter !== 'all') params.status = statusFilter;

      const response = await predictionClient.get<OptimizationJob[]>(
        '/optimization/jobs',
        params
      );

      return response.data;
    },
    refetchInterval: (data) => {
      // Poll every 2 seconds if there are running jobs
      const hasRunningJobs = Array.isArray(data) && data.some(job => job.status === 'running' || job.status === 'pending');
      return hasRunningJobs ? 2000 : 10000; // 2s if running, 10s otherwise
    },
    retry: 2,
  });

  // Fetch job results (for completed jobs)
  const { data: jobResults } = useQuery<OptimizationResult | null>({
    queryKey: ['optimization-results', selectedJobId],
    queryFn: async () => {
      if (!selectedJobId) return null;

      try {
        const response = await predictionClient.get<OptimizationResult>(
          `/optimization/jobs/${selectedJobId}/results`
        );
        return response.data;
      } catch (error) {
        return null;
      }
    },
    enabled: !!selectedJobId,
  });

  // Cancel job mutation
  const cancelJobMutation = useMutation({
    mutationFn: async (jobId: string) => {
      await predictionClient.delete(`/optimization/jobs/${jobId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['optimization-jobs'] });
    },
  });

  const handleViewResults = (jobId: string) => {
    setSelectedJobId(jobId);
  };

  const handleDebugParameters = (job: OptimizationJob) => {
    if (!job.best_params) return;

    // Navigate to debugger with best params pre-filled
    navigate('/trading/debug', {
      state: {
        strategyId: job.strategy_id,
        parameters: job.best_params
      }
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4 text-gray-500" />;
      case 'running':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'cancelled':
        return <X className="h-4 w-4 text-gray-500" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const getStatusBadgeVariant = (status: string): 'default' | 'secondary' | 'destructive' | 'outline' => {
    switch (status) {
      case 'completed':
        return 'default';
      case 'running':
      case 'pending':
        return 'secondary';
      case 'failed':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-8">
          <Loader2 className="h-6 w-6 animate-spin" />
        </CardContent>
      </Card>
    );
  }

  // If viewing results, show OptimizationResultsView
  if (selectedJobId && jobResults) {
    return (
      <OptimizationResultsView
        result={jobResults}
        jobId={selectedJobId}
        onClose={() => setSelectedJobId(null)}
      />
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Optimization Jobs
            {isRefetching && (
              <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
            )}
          </CardTitle>

          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <div className="flex gap-1">
              {(['all', 'running', 'completed', 'failed'] as const).map((status) => (
                <Button
                  key={status}
                  variant={statusFilter === status ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setStatusFilter(status)}
                  className="capitalize"
                >
                  {status}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {!jobs || jobs.length === 0 ? (
          <div className="text-center p-8 text-muted-foreground">
            No optimization jobs found
          </div>
        ) : (
          <div className="space-y-4">
            {jobs.map((job) => (
              <div
                key={job.id}
                className="p-4 rounded-lg border hover:bg-muted/50 transition-colors"
              >
                {/* Job Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(job.status)}
                    <div>
                      <div className="font-medium">
                        Strategy: {job.strategy_id}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Job ID: {job.id.slice(0, 8)}...
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge variant={getStatusBadgeVariant(job.status)}>
                      {job.status}
                    </Badge>
                    {job.status === 'completed' && (
                      <>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleViewResults(job.id)}
                        >
                          <Eye className="h-4 w-4 mr-1" />
                          View Results
                        </Button>
                        {job.best_params && Object.keys(job.best_params).length > 0 && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDebugParameters(job)}
                          >
                            <Bug className="h-4 w-4 mr-1" />
                            Debug Parameters
                          </Button>
                        )}
                      </>
                    )}
                    {(job.status === 'running' || job.status === 'pending') && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => cancelJobMutation.mutate(job.id)}
                        disabled={cancelJobMutation.isPending}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>

                {/* Progress Bar */}
                {(job.status === 'running' || job.status === 'pending') && (
                  <div className="mb-3">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-muted-foreground">Progress</span>
                      <span className="font-medium">
                        {job.trials_completed} / {job.trials_total} trials ({job.progress_percentage.toFixed(1)}%)
                      </span>
                    </div>
                    <Progress value={job.progress_percentage} className="h-2" />
                  </div>
                )}

                {/* Job Details Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">Objective</div>
                    <div className="font-medium capitalize">
                      {job.objective_metric.replace('_', ' ')}
                    </div>
                  </div>

                  {job.best_score && (
                    <div>
                      <div className="text-muted-foreground">Best Score</div>
                      <div className="font-medium">{parseFloat(job.best_score).toFixed(4)}</div>
                    </div>
                  )}

                  {job.started_at && (
                    <div>
                      <div className="text-muted-foreground">Started</div>
                      <div className="font-medium">
                        {new Date(job.started_at).toLocaleTimeString()}
                      </div>
                    </div>
                  )}

                  {job.completed_at && (
                    <div>
                      <div className="text-muted-foreground">Completed</div>
                      <div className="font-medium">
                        {new Date(job.completed_at).toLocaleTimeString()}
                      </div>
                    </div>
                  )}

                  {job.duration_seconds > 0 && (
                    <div>
                      <div className="text-muted-foreground">Duration</div>
                      <div className="font-medium">
                        {formatDuration(job.duration_seconds)}
                      </div>
                    </div>
                  )}
                </div>

                {/* Error Message */}
                {job.error_message && (
                  <div className="mt-3 p-2 bg-destructive/10 text-destructive text-sm rounded">
                    {job.error_message}
                  </div>
                )}

                {/* Best Parameters Preview */}
                {job.best_params && Object.keys(job.best_params).length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm text-muted-foreground mb-1">Best Parameters:</div>
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(job.best_params).map(([key, value]) => (
                        <Badge key={key} variant="outline" className="text-xs">
                          {key}: {typeof value === 'number' ? value.toFixed(4) : value}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

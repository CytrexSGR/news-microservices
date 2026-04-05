/**
 * SchedulerAdminPage
 *
 * Admin dashboard for scheduler-service management:
 * - Scheduler status overview (feed monitor, job processor, cron scheduler)
 * - Queue statistics (pending, processing jobs)
 * - Cron job management (list, run, view history)
 * - Analysis job queue monitoring
 */

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Activity, Clock, Layers, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

// Components
import {
  SchedulerStatusCard,
  JobsTable,
  JobDetailPanel,
} from '@/features/admin/scheduler/components';

// Hooks
import {
  useSchedulerStatus,
  useCronJobs,
  useJobs,
  useJobStats,
} from '@/features/admin/scheduler/api';

// Types
import type { CronJob } from '@/features/admin/scheduler/types';

// Stats Card for queue overview
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';

function QueueStatsCard({
  pending,
  processing,
  completed,
  failed,
}: {
  pending: number;
  processing: number;
  completed: number;
  failed: number;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <Layers className="h-5 w-5" />
          Job Queue Statistics
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center p-3 rounded-lg bg-yellow-500/10">
            <div className="text-2xl font-bold text-yellow-500">{pending}</div>
            <div className="text-xs text-muted-foreground">Pending</div>
          </div>
          <div className="text-center p-3 rounded-lg bg-blue-500/10">
            <div className="text-2xl font-bold text-blue-500">{processing}</div>
            <div className="text-xs text-muted-foreground">Processing</div>
          </div>
          <div className="text-center p-3 rounded-lg bg-green-500/10">
            <div className="text-2xl font-bold text-green-500">{completed}</div>
            <div className="text-xs text-muted-foreground">Completed</div>
          </div>
          <div className="text-center p-3 rounded-lg bg-red-500/10">
            <div className="text-2xl font-bold text-red-500">{failed}</div>
            <div className="text-xs text-muted-foreground">Failed</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function SchedulerAdminPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedJob, setSelectedJob] = useState<CronJob | null>(null);

  // Fetch scheduler status (auto-refresh every 10s)
  const {
    data: schedulerStatus,
    isLoading: statusLoading,
    error: statusError,
  } = useSchedulerStatus(10000);

  // Fetch cron jobs (auto-refresh every 30s)
  const {
    data: cronJobsData,
    isLoading: cronLoading,
    error: cronError,
    refetch: refetchCronJobs,
  } = useCronJobs(30000);

  // Fetch job stats (auto-refresh every 5s)
  const {
    data: jobStats,
    isLoading: statsLoading,
    error: statsError,
  } = useJobStats(5000);

  // Fetch analysis jobs (auto-refresh every 5s)
  const {
    data: analysisJobs,
    isLoading: jobsLoading,
    error: jobsError,
  } = useJobs({ limit: 50 }, 5000);

  const handleJobSelect = (job: CronJob) => {
    setSelectedJob(job);
  };

  const handleCloseDetail = () => {
    setSelectedJob(null);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Scheduler Service</h1>
        <p className="text-muted-foreground">
          Monitor and manage scheduled jobs, cron tasks, and job queues
        </p>
      </div>

      {/* Error Display */}
      {(statusError || cronError || statsError) && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            {statusError?.message || cronError?.message || statsError?.message}
          </AlertDescription>
        </Alert>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview" className="gap-2">
            <Activity className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="cron-jobs" className="gap-2">
            <Clock className="h-4 w-4" />
            Cron Jobs
          </TabsTrigger>
          <TabsTrigger value="queue" className="gap-2">
            <Layers className="h-4 w-4" />
            Job Queue
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          {statusLoading && (
            <div className="text-center py-8 text-muted-foreground">
              Loading scheduler status...
            </div>
          )}

          {schedulerStatus && (
            <div className="grid gap-4 md:grid-cols-2">
              <SchedulerStatusCard status={schedulerStatus} />
              {jobStats && (
                <QueueStatsCard
                  pending={jobStats.total_pending}
                  processing={jobStats.total_processing}
                  completed={jobStats.total_completed}
                  failed={jobStats.total_failed}
                />
              )}
            </div>
          )}

          {/* Job Type Distribution */}
          {jobStats && Object.keys(jobStats.by_type).length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">Jobs by Type</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(jobStats.by_type).map(([type, count]) => (
                    <div
                      key={type}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted"
                    >
                      <span className="text-sm font-medium">{type}</span>
                      <span className="text-sm text-muted-foreground">({count})</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Cron Jobs Tab */}
        <TabsContent value="cron-jobs" className="space-y-4">
          <div className={`grid gap-4 ${selectedJob ? 'lg:grid-cols-3' : ''}`}>
            <div className={selectedJob ? 'lg:col-span-2' : ''}>
              <JobsTable
                jobs={cronJobsData?.jobs || []}
                isLoading={cronLoading}
                onJobSelect={handleJobSelect}
                onRefresh={() => refetchCronJobs()}
              />
            </div>
            {selectedJob && (
              <div className="lg:col-span-1">
                <JobDetailPanel job={selectedJob} onClose={handleCloseDetail} />
              </div>
            )}
          </div>
        </TabsContent>

        {/* Job Queue Tab */}
        <TabsContent value="queue" className="space-y-4">
          {jobsLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              Loading job queue...
            </div>
          ) : jobsError ? (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error loading jobs</AlertTitle>
              <AlertDescription>{jobsError.message}</AlertDescription>
            </Alert>
          ) : analysisJobs ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Layers className="h-5 w-5" />
                  Analysis Job Queue
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="px-4 py-3 text-left text-sm font-medium">
                          Job ID
                        </th>
                        <th className="px-4 py-3 text-left text-sm font-medium">
                          Type
                        </th>
                        <th className="px-4 py-3 text-left text-sm font-medium">
                          Status
                        </th>
                        <th className="px-4 py-3 text-left text-sm font-medium">
                          Priority
                        </th>
                        <th className="px-4 py-3 text-left text-sm font-medium">
                          Created
                        </th>
                        <th className="px-4 py-3 text-left text-sm font-medium">
                          Duration
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {analysisJobs.jobs.length === 0 ? (
                        <tr>
                          <td
                            colSpan={6}
                            className="px-4 py-8 text-center text-muted-foreground"
                          >
                            No jobs in queue
                          </td>
                        </tr>
                      ) : (
                        analysisJobs.jobs.map((job) => (
                          <tr key={job.id} className="border-b hover:bg-muted/50">
                            <td className="px-4 py-3">
                              <div className="font-mono text-xs">
                                {job.id.substring(0, 8)}...
                              </div>
                            </td>
                            <td className="px-4 py-3 text-sm">{job.job_type}</td>
                            <td className="px-4 py-3">
                              <span
                                className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                  job.status === 'COMPLETED'
                                    ? 'bg-green-500/10 text-green-500'
                                    : job.status === 'PROCESSING'
                                      ? 'bg-blue-500/10 text-blue-500'
                                      : job.status === 'PENDING'
                                        ? 'bg-yellow-500/10 text-yellow-500'
                                        : 'bg-red-500/10 text-red-500'
                                }`}
                              >
                                {job.status}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-sm">{job.priority}</td>
                            <td className="px-4 py-3 text-sm text-muted-foreground">
                              {new Date(job.created_at).toLocaleString()}
                            </td>
                            <td className="px-4 py-3 text-sm font-mono">
                              {job.started_at && job.completed_at
                                ? `${((new Date(job.completed_at).getTime() - new Date(job.started_at).getTime()) / 1000).toFixed(1)}s`
                                : job.started_at
                                  ? 'Running...'
                                  : '-'}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
                {analysisJobs.total > analysisJobs.limit && (
                  <div className="mt-4 text-sm text-muted-foreground text-center">
                    Showing {analysisJobs.jobs.length} of {analysisJobs.total} jobs
                  </div>
                )}
              </CardContent>
            </Card>
          ) : null}
        </TabsContent>
      </Tabs>
    </div>
  );
}

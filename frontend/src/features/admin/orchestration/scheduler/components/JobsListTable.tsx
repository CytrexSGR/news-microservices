import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { useJobsList, useCancelJob, useRetryJob } from '../api';
import type { Job, JobStatus } from '../types/scheduler.types';

interface JobsListTableProps {
  className?: string;
  initialStatus?: JobStatus;
  pageSize?: number;
}

/**
 * Job Status Badge
 */
const JobStatusBadge: React.FC<{ status: JobStatus }> = ({ status }) => {
  const colors: Record<JobStatus, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-800',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colors[status]}`}>
      {status.toUpperCase()}
    </span>
  );
};

/**
 * Job Actions
 */
const JobActions: React.FC<{
  job: Job;
  onCancel: (id: string) => void;
  onRetry: (id: string) => void;
  isProcessing: boolean;
}> = ({ job, onCancel, onRetry, isProcessing }) => {
  const canCancel = job.status === 'pending' || job.status === 'running';
  const canRetry = job.status === 'failed';

  return (
    <div className="flex gap-2">
      {canCancel && (
        <button
          onClick={() => onCancel(job.id)}
          disabled={isProcessing}
          className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 disabled:opacity-50"
        >
          Cancel
        </button>
      )}
      {canRetry && (
        <button
          onClick={() => onRetry(job.id)}
          disabled={isProcessing}
          className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
        >
          Retry
        </button>
      )}
    </div>
  );
};

/**
 * Jobs List Table
 *
 * Displays a filterable, paginated table of jobs with actions.
 */
export const JobsListTable: React.FC<JobsListTableProps> = ({
  className,
  initialStatus,
  pageSize = 20,
}) => {
  const [statusFilter, setStatusFilter] = useState<JobStatus | undefined>(initialStatus);
  const [page, setPage] = useState(0);

  const { data, isLoading, error, refetch, isRefetching } = useJobsList({
    status: statusFilter,
    skip: page * pageSize,
    limit: pageSize,
  });

  const cancelJob = useCancelJob();
  const retryJob = useRetryJob();

  const handleCancel = async (jobId: string) => {
    try {
      await cancelJob.mutateAsync(jobId);
    } catch (err) {
      console.error('Failed to cancel job:', err);
    }
  };

  const handleRetry = async (jobId: string) => {
    try {
      await retryJob.mutateAsync(jobId);
    } catch (err) {
      console.error('Failed to retry job:', err);
    }
  };

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleString();
  };

  const statusOptions: (JobStatus | 'all')[] = [
    'all',
    'pending',
    'running',
    'completed',
    'failed',
    'cancelled',
  ];

  if (error) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-red-600">Jobs List</h3>
          <p className="text-sm text-red-500 mb-4">
            Failed to load jobs: {error.message}
          </p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Jobs List</h3>
          <div className="flex gap-2">
            <select
              value={statusFilter || 'all'}
              onChange={(e) => {
                const val = e.target.value;
                setStatusFilter(val === 'all' ? undefined : (val as JobStatus));
                setPage(0);
              }}
              className="px-3 py-1 border rounded text-sm"
            >
              {statusOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt === 'all' ? 'All Status' : opt.charAt(0).toUpperCase() + opt.slice(1)}
                </option>
              ))}
            </select>
            <button
              onClick={() => refetch()}
              disabled={isRefetching}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
            >
              {isRefetching ? 'Loading...' : 'Refresh'}
            </button>
          </div>
        </div>

        {/* Table */}
        {isLoading ? (
          <div className="animate-pulse space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded"></div>
            ))}
          </div>
        ) : data?.jobs.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No jobs found</p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left">ID</th>
                    <th className="px-3 py-2 text-left">Task</th>
                    <th className="px-3 py-2 text-left">Status</th>
                    <th className="px-3 py-2 text-left">Created</th>
                    <th className="px-3 py-2 text-left">Retries</th>
                    <th className="px-3 py-2 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {data?.jobs.map((job) => (
                    <tr key={job.id} className="hover:bg-gray-50">
                      <td className="px-3 py-2 font-mono text-xs">{job.id.slice(0, 8)}...</td>
                      <td className="px-3 py-2">{job.task_name}</td>
                      <td className="px-3 py-2">
                        <JobStatusBadge status={job.status} />
                      </td>
                      <td className="px-3 py-2 text-xs text-gray-600">
                        {formatDate(job.created_at)}
                      </td>
                      <td className="px-3 py-2">
                        {job.retries}/{job.max_retries}
                      </td>
                      <td className="px-3 py-2">
                        <JobActions
                          job={job}
                          onCancel={handleCancel}
                          onRetry={handleRetry}
                          isProcessing={cancelJob.isLoading || retryJob.isLoading}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex justify-between items-center mt-4 pt-4 border-t">
              <p className="text-sm text-gray-600">
                Showing {page * pageSize + 1}-
                {Math.min((page + 1) * pageSize, data?.total || 0)} of {data?.total || 0}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!data || (page + 1) * pageSize >= data.total}
                  className="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </Card>
  );
};

import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { usePendingJobs, useCancelQueueJob, useRetryQueueJob } from '../api';
import type { QueueJob, QueuePriority, QueueJobStatus } from '../types/scraping.types';

interface QueueItemsTableProps {
  className?: string;
  pageSize?: number;
}

/**
 * Priority Badge
 */
const PriorityBadge: React.FC<{ priority: QueuePriority }> = ({ priority }) => {
  const colors: Record<QueuePriority, string> = {
    CRITICAL: 'bg-red-100 text-red-800',
    HIGH: 'bg-orange-100 text-orange-800',
    NORMAL: 'bg-blue-100 text-blue-800',
    LOW: 'bg-gray-100 text-gray-800',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colors[priority]}`}>
      {priority}
    </span>
  );
};

/**
 * Status Badge
 */
const StatusBadge: React.FC<{ status: QueueJobStatus }> = ({ status }) => {
  const colors: Record<QueueJobStatus, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
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
 * Queue Items Table
 *
 * Displays pending and processing queue jobs with actions.
 */
export const QueueItemsTable: React.FC<QueueItemsTableProps> = ({
  className,
  pageSize = 20,
}) => {
  const { data, isLoading, error, refetch, isRefetching } = usePendingJobs({ limit: pageSize });
  const cancelJob = useCancelQueueJob();
  const retryJob = useRetryQueueJob();

  const handleCancel = async (jobId: string) => {
    if (!confirm('Cancel this job?')) return;
    try {
      await cancelJob.mutateAsync(jobId);
    } catch (err) {
      console.error('Failed to cancel job:', err);
    }
  };

  const handleRetry = async (jobId: string) => {
    try {
      const result = await retryJob.mutateAsync(jobId);
      alert(`Job retried. New ID: ${result.new_job_id}`);
    } catch (err) {
      console.error('Failed to retry job:', err);
    }
  };

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleString();
  };

  if (error) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-red-600">Queue Jobs</h3>
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
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Queue Jobs</h3>
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
          >
            {isRefetching ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {isLoading ? (
          <div className="animate-pulse space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded"></div>
            ))}
          </div>
        ) : data?.jobs.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No pending jobs</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left">Job ID</th>
                  <th className="px-3 py-2 text-left">URL</th>
                  <th className="px-3 py-2 text-left">Priority</th>
                  <th className="px-3 py-2 text-left">Status</th>
                  <th className="px-3 py-2 text-left">Method</th>
                  <th className="px-3 py-2 text-left">Created</th>
                  <th className="px-3 py-2 text-left">Retries</th>
                  <th className="px-3 py-2 text-left">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data?.jobs.map((job) => (
                  <tr key={job.job_id} className="hover:bg-gray-50">
                    <td className="px-3 py-2 font-mono text-xs">
                      {job.job_id.slice(0, 8)}...
                    </td>
                    <td className="px-3 py-2 max-w-xs truncate" title={job.url}>
                      {job.url}
                    </td>
                    <td className="px-3 py-2">
                      <PriorityBadge priority={job.priority} />
                    </td>
                    <td className="px-3 py-2">
                      <StatusBadge status={job.status} />
                    </td>
                    <td className="px-3 py-2 text-gray-600">{job.method}</td>
                    <td className="px-3 py-2 text-xs text-gray-500">
                      {formatDate(job.created_at)}
                    </td>
                    <td className="px-3 py-2">
                      {job.retries}/{job.max_retries}
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex gap-1">
                        {job.status === 'pending' && (
                          <button
                            onClick={() => handleCancel(job.job_id)}
                            disabled={cancelJob.isPending}
                            className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 disabled:opacity-50"
                          >
                            Cancel
                          </button>
                        )}
                        {job.status === 'failed' && (
                          <button
                            onClick={() => handleRetry(job.job_id)}
                            disabled={retryJob.isPending}
                            className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
                          >
                            Retry
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {data && data.total > pageSize && (
          <p className="text-sm text-gray-500 mt-4 text-center">
            Showing {data.jobs.length} of {data.total} jobs
          </p>
        )}
      </div>
    </Card>
  );
};

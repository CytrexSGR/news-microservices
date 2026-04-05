import React from 'react';
import { Card } from '@/components/ui/Card';
import { useSchedulerStatus } from '../api';

/**
 * Scheduler Status Card
 *
 * Displays the current scheduler status including active jobs,
 * worker status, and uptime information.
 */
export const SchedulerStatusCard: React.FC<{ className?: string }> = ({ className }) => {
  const { data, isLoading, error, refetch, isRefetching } = useSchedulerStatus();

  if (isLoading) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Scheduler Status</h3>
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-red-600">Scheduler Status</h3>
          <p className="text-sm text-red-500 mb-4">
            Failed to load scheduler status: {error.message}
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

  if (!data) return null;

  const workerStatusColor =
    data.worker_status === 'running'
      ? 'text-green-600 bg-green-100'
      : data.worker_status === 'stopped'
      ? 'text-red-600 bg-red-100'
      : 'text-yellow-600 bg-yellow-100';

  const formatUptime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  return (
    <Card className={className}>
      <div className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Scheduler Status</h3>
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
          >
            {isRefetching ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Worker Status */}
          <div className="col-span-2">
            <p className="text-sm text-gray-600">Worker Status</p>
            <span
              className={`inline-block px-2 py-1 rounded text-sm font-medium ${workerStatusColor}`}
            >
              {data.worker_status.toUpperCase()}
            </span>
          </div>

          {/* Active Jobs */}
          <div>
            <p className="text-sm text-gray-600">Active Jobs</p>
            <p className="text-2xl font-bold text-blue-600" data-testid="active-jobs">
              {data.active_jobs}
            </p>
          </div>

          {/* Pending Jobs */}
          <div>
            <p className="text-sm text-gray-600">Pending Jobs</p>
            <p className="text-2xl font-bold text-yellow-600">
              {data.pending_jobs}
            </p>
          </div>

          {/* Completed Jobs */}
          <div>
            <p className="text-sm text-gray-600">Completed</p>
            <p className="text-xl font-semibold text-green-600">
              {data.completed_jobs.toLocaleString()}
            </p>
          </div>

          {/* Failed Jobs */}
          <div>
            <p className="text-sm text-gray-600">Failed</p>
            <p className="text-xl font-semibold text-red-600">
              {data.failed_jobs.toLocaleString()}
            </p>
          </div>

          {/* Uptime */}
          <div className="col-span-2">
            <p className="text-sm text-gray-600">Uptime</p>
            <p className="text-lg font-medium">{formatUptime(data.uptime_seconds)}</p>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t text-xs text-gray-500">
          <p>Last heartbeat: {new Date(data.last_heartbeat).toLocaleTimeString()}</p>
          <p>Version: {data.version}</p>
        </div>
      </div>
    </Card>
  );
};

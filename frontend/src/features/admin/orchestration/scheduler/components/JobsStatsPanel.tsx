import React from 'react';
import { Card } from '@/components/ui/Card';
import { useJobsStats } from '../api';

/**
 * Jobs Statistics Panel
 *
 * Displays job statistics including counts, success rate,
 * and performance metrics.
 */
export const JobsStatsPanel: React.FC<{ className?: string }> = ({ className }) => {
  const { data, isLoading, error, refetch, isRefetching } = useJobsStats();

  if (isLoading) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Job Statistics</h3>
          <div className="animate-pulse grid grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <div key={i}>
                <div className="h-3 bg-gray-200 rounded w-16 mb-2"></div>
                <div className="h-6 bg-gray-200 rounded w-12"></div>
              </div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-red-600">Job Statistics</h3>
          <p className="text-sm text-red-500 mb-4">
            Failed to load statistics: {error.message}
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

  const successRateColor =
    data.success_rate >= 95
      ? 'text-green-600'
      : data.success_rate >= 80
      ? 'text-yellow-600'
      : 'text-red-600';

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs.toFixed(0)}s`;
  };

  return (
    <Card className={className}>
      <div className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Job Statistics</h3>
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
          >
            {isRefetching ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        <div className="grid grid-cols-4 gap-4">
          {/* Total Jobs */}
          <div>
            <p className="text-sm text-gray-600">Total</p>
            <p className="text-xl font-bold">{data.total.toLocaleString()}</p>
          </div>

          {/* Pending */}
          <div>
            <p className="text-sm text-gray-600">Pending</p>
            <p className="text-xl font-bold text-yellow-600">{data.pending}</p>
          </div>

          {/* Running */}
          <div>
            <p className="text-sm text-gray-600">Running</p>
            <p className="text-xl font-bold text-blue-600">{data.running}</p>
          </div>

          {/* Completed */}
          <div>
            <p className="text-sm text-gray-600">Completed</p>
            <p className="text-xl font-bold text-green-600">
              {data.completed.toLocaleString()}
            </p>
          </div>

          {/* Failed */}
          <div>
            <p className="text-sm text-gray-600">Failed</p>
            <p className="text-xl font-bold text-red-600">
              {data.failed.toLocaleString()}
            </p>
          </div>

          {/* Cancelled */}
          <div>
            <p className="text-sm text-gray-600">Cancelled</p>
            <p className="text-xl font-bold text-gray-600">
              {data.cancelled.toLocaleString()}
            </p>
          </div>

          {/* Success Rate */}
          <div>
            <p className="text-sm text-gray-600">Success Rate</p>
            <p className={`text-xl font-bold ${successRateColor}`}>
              {data.success_rate.toFixed(1)}%
            </p>
          </div>

          {/* Avg Duration */}
          <div>
            <p className="text-sm text-gray-600">Avg Duration</p>
            <p className="text-xl font-bold">
              {formatDuration(data.avg_duration_seconds)}
            </p>
          </div>
        </div>

        {/* Last Hour Stats */}
        <div className="mt-4 pt-4 border-t">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Last Hour</h4>
          <div className="flex gap-6">
            <div>
              <span className="text-sm text-gray-600">Completed: </span>
              <span className="font-semibold text-green-600">
                {data.last_hour.completed}
              </span>
            </div>
            <div>
              <span className="text-sm text-gray-600">Failed: </span>
              <span className="font-semibold text-red-600">
                {data.last_hour.failed}
              </span>
            </div>
            <div>
              <span className="text-sm text-gray-600">Throughput: </span>
              <span className="font-semibold">
                {data.jobs_per_hour.toFixed(1)}/hour
              </span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};

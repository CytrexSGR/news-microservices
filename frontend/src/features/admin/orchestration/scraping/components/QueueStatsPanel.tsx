import React from 'react';
import { Card } from '@/components/ui/Card';
import { useQueueStats, useClearQueue } from '../api';
import type { QueuePriority } from '../types/scraping.types';

interface QueueStatsPanelProps {
  className?: string;
}

/**
 * Priority Badge
 */
const PriorityBadge: React.FC<{ priority: QueuePriority; count: number }> = ({
  priority,
  count,
}) => {
  const colors: Record<QueuePriority, string> = {
    CRITICAL: 'bg-red-100 text-red-800',
    HIGH: 'bg-orange-100 text-orange-800',
    NORMAL: 'bg-blue-100 text-blue-800',
    LOW: 'bg-gray-100 text-gray-800',
  };

  return (
    <div className={`px-3 py-2 rounded ${colors[priority]}`}>
      <p className="text-xs font-medium">{priority}</p>
      <p className="text-lg font-bold">{count}</p>
    </div>
  );
};

/**
 * Stat Card
 */
const StatCard: React.FC<{
  label: string;
  value: string | number;
  color?: 'default' | 'green' | 'yellow' | 'red';
}> = ({ label, value, color = 'default' }) => {
  const colorClasses = {
    default: 'text-gray-900',
    green: 'text-green-600',
    yellow: 'text-yellow-600',
    red: 'text-red-600',
  };

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <p className="text-sm text-gray-600">{label}</p>
      <p className={`text-2xl font-bold ${colorClasses[color]}`}>{value}</p>
    </div>
  );
};

/**
 * Queue Stats Panel
 *
 * Displays queue statistics including pending/processing jobs,
 * priority distribution, and throughput metrics.
 */
export const QueueStatsPanel: React.FC<QueueStatsPanelProps> = ({ className }) => {
  const { data, isLoading, error, refetch, isRefetching } = useQueueStats();
  const clearQueue = useClearQueue();

  const handleClearQueue = async (priority?: QueuePriority) => {
    const msg = priority
      ? `Clear all ${priority} priority jobs?`
      : 'Clear ALL pending jobs?';
    if (!confirm(msg)) return;

    try {
      const result = await clearQueue.mutateAsync(priority);
      alert(`Cleared ${result.jobs_cleared} jobs`);
    } catch (err) {
      console.error('Failed to clear queue:', err);
    }
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Queue Statistics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-20 bg-gray-100 rounded"></div>
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
          <h3 className="text-lg font-semibold mb-4 text-red-600">Queue Statistics</h3>
          <p className="text-sm text-red-500 mb-4">
            Failed to load queue stats: {error.message}
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

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  };

  return (
    <Card className={className}>
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold">Queue Statistics</h3>
          <div className="flex gap-2">
            <button
              onClick={() => refetch()}
              disabled={isRefetching}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
            >
              {isRefetching ? 'Loading...' : 'Refresh'}
            </button>
            <button
              onClick={() => handleClearQueue()}
              disabled={clearQueue.isPending || data.pending_jobs === 0}
              className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 disabled:opacity-50"
            >
              Clear All
            </button>
          </div>
        </div>

        {/* Main Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <StatCard
            label="Pending Jobs"
            value={data.pending_jobs}
            color={data.pending_jobs > 100 ? 'yellow' : 'default'}
          />
          <StatCard
            label="Processing"
            value={data.processing_jobs}
            color={data.processing_jobs > 0 ? 'green' : 'default'}
          />
          <StatCard
            label="Completed (1h)"
            value={data.completed_last_hour}
            color="green"
          />
          <StatCard
            label="Failed (1h)"
            value={data.failed_last_hour}
            color={data.failed_last_hour > 0 ? 'red' : 'default'}
          />
        </div>

        {/* Priority Distribution */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Priority Distribution</h4>
          <div className="grid grid-cols-4 gap-2">
            <PriorityBadge priority="CRITICAL" count={data.priority_distribution.CRITICAL || 0} />
            <PriorityBadge priority="HIGH" count={data.priority_distribution.HIGH || 0} />
            <PriorityBadge priority="NORMAL" count={data.priority_distribution.NORMAL || 0} />
            <PriorityBadge priority="LOW" count={data.priority_distribution.LOW || 0} />
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-gray-50 rounded p-3">
            <p className="text-xs text-gray-500">Avg Wait Time</p>
            <p className="text-lg font-bold">{formatTime(data.avg_wait_time_seconds)}</p>
          </div>
          <div className="bg-gray-50 rounded p-3">
            <p className="text-xs text-gray-500">Avg Processing Time</p>
            <p className="text-lg font-bold">{formatTime(data.avg_processing_time_seconds)}</p>
          </div>
          <div className="bg-gray-50 rounded p-3">
            <p className="text-xs text-gray-500">Throughput</p>
            <p className="text-lg font-bold">{data.throughput_per_minute.toFixed(1)}/min</p>
          </div>
        </div>
      </div>
    </Card>
  );
};

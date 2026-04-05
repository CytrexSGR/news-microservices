import React from 'react';
import { Card } from '@/components/ui/Card';
import { useSchedulerHealth } from '../api';
import type { ComponentHealth } from '../types/scheduler.types';

/**
 * Health Status Icon
 */
const HealthIcon: React.FC<{ healthy: boolean }> = ({ healthy }) => (
  <span className={`text-lg ${healthy ? 'text-green-500' : 'text-red-500'}`}>
    {healthy ? '●' : '○'}
  </span>
);

/**
 * Component Health Row
 */
const ComponentHealthRow: React.FC<{
  name: string;
  health: ComponentHealth;
}> = ({ name, health }) => (
  <div className="flex items-center justify-between py-2 border-b last:border-b-0">
    <div className="flex items-center gap-2">
      <HealthIcon healthy={health.status === 'healthy'} />
      <span className="font-medium capitalize">{name}</span>
    </div>
    <div className="text-right">
      <span
        className={`text-sm ${
          health.status === 'healthy' ? 'text-green-600' : 'text-red-600'
        }`}
      >
        {health.status}
      </span>
      {health.latency_ms !== undefined && (
        <span className="text-xs text-gray-500 ml-2">
          {health.latency_ms}ms
        </span>
      )}
      {health.error && (
        <p className="text-xs text-red-500 mt-1">{health.error}</p>
      )}
    </div>
  </div>
);

/**
 * Scheduler Health Card
 *
 * Displays the health status of all scheduler components
 * including Celery, Redis, and Database connections.
 */
export const SchedulerHealthCard: React.FC<{ className?: string }> = ({ className }) => {
  const { data, isLoading, error, refetch, isRefetching } = useSchedulerHealth();

  if (isLoading) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Health Status</h3>
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-full"></div>
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-red-600">Health Status</h3>
          <p className="text-sm text-red-500 mb-4">
            Failed to check health: {error.message}
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

  const statusColor =
    data.status === 'healthy'
      ? 'bg-green-100 text-green-800 border-green-200'
      : data.status === 'degraded'
      ? 'bg-yellow-100 text-yellow-800 border-yellow-200'
      : 'bg-red-100 text-red-800 border-red-200';

  return (
    <Card className={className}>
      <div className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Health Status</h3>
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
          >
            {isRefetching ? 'Checking...' : 'Check'}
          </button>
        </div>

        {/* Overall Status Badge */}
        <div className="mb-4">
          <span
            className={`inline-block px-3 py-1 rounded-full text-sm font-medium border ${statusColor}`}
          >
            {data.status.toUpperCase()}
          </span>
          {data.details && (
            <p className="text-sm text-gray-600 mt-2">{data.details}</p>
          )}
        </div>

        {/* Components */}
        <div className="space-y-1">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Components</h4>
          <ComponentHealthRow name="Celery" health={data.components.celery} />
          <ComponentHealthRow name="Redis" health={data.components.redis} />
          <ComponentHealthRow name="Database" health={data.components.database} />
        </div>

        <div className="mt-4 pt-4 border-t text-xs text-gray-500">
          Last check: {new Date(data.last_check).toLocaleTimeString()}
        </div>
      </div>
    </Card>
  );
};

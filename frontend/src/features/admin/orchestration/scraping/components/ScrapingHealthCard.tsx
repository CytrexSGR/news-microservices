import React from 'react';
import { Card } from '@/components/ui/Card';
import { useScrapingHealth } from '../api';

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
  healthy: boolean;
}> = ({ name, healthy }) => (
  <div className="flex items-center justify-between py-2 border-b last:border-b-0">
    <div className="flex items-center gap-2">
      <HealthIcon healthy={healthy} />
      <span className="font-medium capitalize">{name}</span>
    </div>
    <span
      className={`text-sm ${healthy ? 'text-green-600' : 'text-red-600'}`}
    >
      {healthy ? 'Healthy' : 'Unhealthy'}
    </span>
  </div>
);

/**
 * Scraping Health Card
 *
 * Displays the health status of the scraping service components
 * including browser, redis, cache, queue, DLQ, and proxy pool.
 */
export const ScrapingHealthCard: React.FC<{ className?: string }> = ({ className }) => {
  const { data, isLoading, error, refetch, isRefetching } = useScrapingHealth();

  if (isLoading) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Scraping Health</h3>
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
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
          <h3 className="text-lg font-semibold mb-4 text-red-600">Scraping Health</h3>
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
          <h3 className="text-lg font-semibold">Scraping Health</h3>
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
        </div>

        {/* Core Components */}
        <div className="space-y-1 mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Core</h4>
          <ComponentHealthRow name="Browser" healthy={data.browser} />
          <ComponentHealthRow name="Redis" healthy={data.redis} />
        </div>

        {/* Service Components */}
        <div className="space-y-1">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Services</h4>
          <ComponentHealthRow name="Cache" healthy={data.components.cache} />
          <ComponentHealthRow name="Queue" healthy={data.components.queue} />
          <ComponentHealthRow name="DLQ" healthy={data.components.dlq} />
          <ComponentHealthRow name="Proxy Pool" healthy={data.components.proxy_pool} />
        </div>

        <div className="mt-4 pt-4 border-t text-xs text-gray-500">
          Last check: {new Date(data.last_check).toLocaleTimeString()}
        </div>
      </div>
    </Card>
  );
};

import React from 'react';
import { Card } from '@/components/ui/Card';
import { useScrapingMetrics } from '../api';

/**
 * Metric Card
 */
const MetricCard: React.FC<{
  label: string;
  value: string | number;
  subValue?: string;
  color?: 'default' | 'green' | 'yellow' | 'red';
}> = ({ label, value, subValue, color = 'default' }) => {
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
      {subValue && <p className="text-xs text-gray-500 mt-1">{subValue}</p>}
    </div>
  );
};

/**
 * Progress Bar
 */
const ProgressBar: React.FC<{
  label: string;
  current: number;
  max: number;
  color?: 'blue' | 'green' | 'yellow' | 'red';
}> = ({ label, current, max, color = 'blue' }) => {
  const percentage = max > 0 ? Math.round((current / max) * 100) : 0;
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500',
  };

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="text-gray-900 font-medium">{current} / {max}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`${colorClasses[color]} h-2 rounded-full transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

/**
 * Scraping Metrics Panel
 *
 * Displays comprehensive metrics about the scraping service
 * including concurrency, retry stats, browser status, and throughput.
 */
export const ScrapingMetricsPanel: React.FC<{ className?: string }> = ({ className }) => {
  const { data, isLoading, error, refetch, isRefetching } = useScrapingMetrics();

  if (isLoading) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Scraping Metrics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
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
          <h3 className="text-lg font-semibold mb-4 text-red-600">Scraping Metrics</h3>
          <p className="text-sm text-red-500 mb-4">
            Failed to load metrics: {error.message}
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
    data.retry_stats.success_rate >= 0.9
      ? 'green'
      : data.retry_stats.success_rate >= 0.7
      ? 'yellow'
      : 'red';

  const concurrencyColor =
    data.concurrency.current / data.concurrency.max > 0.9
      ? 'red'
      : data.concurrency.current / data.concurrency.max > 0.7
      ? 'yellow'
      : 'blue';

  return (
    <Card className={className}>
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold">Scraping Metrics</h3>
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
          >
            {isRefetching ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {/* Concurrency */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Concurrency</h4>
          <ProgressBar
            label="Active Workers"
            current={data.concurrency.current}
            max={data.concurrency.max}
            color={concurrencyColor}
          />
          <p className="text-xs text-gray-500 mt-2">
            {data.concurrency.available} slots available
          </p>
        </div>

        {/* Main Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <MetricCard
            label="Success Rate"
            value={`${(data.retry_stats.success_rate * 100).toFixed(1)}%`}
            color={successRateColor}
          />
          <MetricCard
            label="Total Retries"
            value={data.retry_stats.total_retries.toLocaleString()}
          />
          <MetricCard
            label="Avg Retries/Success"
            value={data.retry_stats.avg_retries_per_success.toFixed(2)}
          />
          <MetricCard
            label="Requests/min"
            value={data.throughput.requests_per_minute.toFixed(1)}
          />
        </div>

        {/* Browser Status */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Browser Instances</h4>
          <div className="grid grid-cols-3 gap-4">
            <MetricCard
              label="Total"
              value={data.browser_status.instances}
            />
            <MetricCard
              label="Healthy"
              value={data.browser_status.healthy}
              color={data.browser_status.healthy === data.browser_status.instances ? 'green' : 'yellow'}
            />
            <MetricCard
              label="Memory"
              value={`${data.browser_status.memory_mb} MB`}
            />
          </div>
        </div>

        {/* Throughput */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-3">Throughput</h4>
          <div className="grid grid-cols-2 gap-4">
            <MetricCard
              label="Requests/min"
              value={data.throughput.requests_per_minute.toFixed(1)}
            />
            <MetricCard
              label="Data/min"
              value={formatBytes(data.throughput.bytes_per_minute)}
            />
          </div>
        </div>
      </div>
    </Card>
  );
};

/**
 * Format bytes to human readable string
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

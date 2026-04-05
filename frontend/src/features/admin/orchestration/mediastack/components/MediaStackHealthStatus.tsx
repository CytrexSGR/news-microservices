import React from 'react';
import { Card } from '@/components/ui/Card';
import { useMediaStackHealth } from '../api';

/**
 * Props for MediaStackHealthStatus
 */
interface MediaStackHealthStatusProps {
  className?: string;
  compact?: boolean;
}

/**
 * Get status color classes
 */
function getStatusColor(status: string): string {
  switch (status) {
    case 'healthy':
      return 'bg-green-100 text-green-800 border-green-200';
    case 'degraded':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'unhealthy':
      return 'bg-red-100 text-red-800 border-red-200';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
  }
}

/**
 * Get status indicator color
 */
function getIndicatorColor(status: string): string {
  switch (status) {
    case 'healthy':
      return 'bg-green-500';
    case 'degraded':
      return 'bg-yellow-500';
    case 'unhealthy':
      return 'bg-red-500';
    default:
      return 'bg-gray-500';
  }
}

/**
 * MediaStack Health Status
 *
 * Displays the health status of the MediaStack API connection.
 * Shows API reachability, key validity, and latency.
 */
export const MediaStackHealthStatus: React.FC<MediaStackHealthStatusProps> = ({
  className,
  compact = false,
}) => {
  const { data, isLoading, error, refetch, isRefetching } = useMediaStackHealth();

  // Compact mode - inline status indicator
  if (compact) {
    if (isLoading) {
      return (
        <div className={`flex items-center gap-2 ${className || ''}`}>
          <div className="w-3 h-3 rounded-full bg-gray-300 animate-pulse" />
          <span className="text-sm text-gray-500">Checking...</span>
        </div>
      );
    }

    if (error || !data) {
      return (
        <div className={`flex items-center gap-2 ${className || ''}`}>
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span className="text-sm text-red-600">Error</span>
        </div>
      );
    }

    return (
      <div className={`flex items-center gap-2 ${className || ''}`}>
        <div className={`w-3 h-3 rounded-full ${getIndicatorColor(data.status)}`} />
        <span className="text-sm capitalize">{data.status}</span>
        {data.latency_ms && (
          <span className="text-xs text-gray-500">({data.latency_ms}ms)</span>
        )}
      </div>
    );
  }

  // Full card mode
  if (isLoading) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">API Health</h3>
          <div className="animate-pulse space-y-3">
            <div className="h-6 bg-gray-200 rounded w-1/3"></div>
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
          <h3 className="text-lg font-semibold mb-4 text-red-600">API Health</h3>
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

  const statusColor = getStatusColor(data.status);

  return (
    <Card className={className}>
      <div className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">API Health</h3>
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
          >
            {isRefetching ? 'Checking...' : 'Check'}
          </button>
        </div>

        {/* Status Badge */}
        <div className="mb-4">
          <span
            className={`inline-block px-3 py-1 rounded-full text-sm font-medium border ${statusColor}`}
          >
            {data.status.toUpperCase()}
          </span>
        </div>

        {/* Health Details */}
        <div className="space-y-3">
          {/* API Reachable */}
          <div className="flex items-center justify-between py-2 border-b">
            <span className="text-sm text-gray-600">API Reachable</span>
            <div className="flex items-center gap-2">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  data.api_reachable ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span className={`text-sm ${data.api_reachable ? 'text-green-600' : 'text-red-600'}`}>
                {data.api_reachable ? 'Yes' : 'No'}
              </span>
            </div>
          </div>

          {/* API Key Valid */}
          <div className="flex items-center justify-between py-2 border-b">
            <span className="text-sm text-gray-600">API Key Valid</span>
            <div className="flex items-center gap-2">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  data.api_key_valid ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span className={`text-sm ${data.api_key_valid ? 'text-green-600' : 'text-red-600'}`}>
                {data.api_key_valid ? 'Yes' : 'No'}
              </span>
            </div>
          </div>

          {/* Latency */}
          <div className="flex items-center justify-between py-2">
            <span className="text-sm text-gray-600">Latency</span>
            <span className="text-sm font-medium">{data.latency_ms}ms</span>
          </div>
        </div>

        {/* Error Message */}
        {data.error && (
          <div className="mt-4 p-3 bg-red-50 rounded-lg">
            <p className="text-sm text-red-600">{data.error}</p>
          </div>
        )}

        {/* Last Check */}
        <div className="mt-4 pt-4 border-t text-xs text-gray-500">
          Last check: {new Date(data.last_check).toLocaleTimeString()}
        </div>
      </div>
    </Card>
  );
};

export default MediaStackHealthStatus;

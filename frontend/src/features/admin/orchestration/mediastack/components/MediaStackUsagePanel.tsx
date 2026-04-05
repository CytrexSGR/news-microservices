import React from 'react';
import { Card } from '@/components/ui/Card';
import { useMediaStackUsage } from '../api';

/**
 * Props for MediaStackUsagePanel
 */
interface MediaStackUsagePanelProps {
  className?: string;
}

/**
 * Get usage percentage color
 */
function getUsageColor(percentage: number): string {
  if (percentage >= 90) return 'bg-red-500';
  if (percentage >= 75) return 'bg-yellow-500';
  if (percentage >= 50) return 'bg-blue-500';
  return 'bg-green-500';
}

/**
 * Get plan type badge color
 */
function getPlanColor(planType: string): string {
  const colors: Record<string, string> = {
    free: 'bg-gray-100 text-gray-800',
    basic: 'bg-blue-100 text-blue-800',
    standard: 'bg-indigo-100 text-indigo-800',
    business: 'bg-purple-100 text-purple-800',
    enterprise: 'bg-amber-100 text-amber-800',
  };
  return colors[planType] || colors.free;
}

/**
 * MediaStack Usage Panel
 *
 * Displays API usage statistics including calls made, remaining,
 * and available features based on the current plan.
 */
export const MediaStackUsagePanel: React.FC<MediaStackUsagePanelProps> = ({ className }) => {
  const { data, isLoading, error, refetch, isRefetching } = useMediaStackUsage();

  if (isLoading) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">API Usage</h3>
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
            <div className="h-6 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-red-600">API Usage</h3>
          <p className="text-sm text-red-500 mb-4">
            Failed to load usage data: {error.message}
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

  const usageColor = getUsageColor(data.usage_percentage);
  const planColor = getPlanColor(data.plan_type);

  return (
    <Card className={className}>
      <div className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">API Usage</h3>
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
          >
            {isRefetching ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {/* Plan Badge */}
        <div className="mb-4">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${planColor}`}>
            {data.plan_name}
          </span>
        </div>

        {/* Usage Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600">API Calls</span>
            <span className="font-medium">
              {data.calls_made.toLocaleString()} / {data.calls_limit.toLocaleString()}
            </span>
          </div>
          <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full ${usageColor} transition-all duration-300`}
              style={{ width: `${Math.min(data.usage_percentage, 100)}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>{data.usage_percentage.toFixed(1)}% used</span>
            <span>{data.calls_remaining.toLocaleString()} remaining</span>
          </div>
        </div>

        {/* Usage Stats Grid */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-blue-600">
              {data.calls_made.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500">Calls Made</p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-green-600">
              {data.calls_remaining.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500">Calls Remaining</p>
          </div>
        </div>

        {/* Features */}
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Available Features</h4>
          <div className="grid grid-cols-2 gap-2">
            <div className="flex items-center gap-2">
              <span className={data.features.live_news ? 'text-green-500' : 'text-gray-400'}>
                {data.features.live_news ? 'OK' : '--'}
              </span>
              <span className="text-sm text-gray-600">Live News</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={data.features.historical_news ? 'text-green-500' : 'text-gray-400'}>
                {data.features.historical_news ? 'OK' : '--'}
              </span>
              <span className="text-sm text-gray-600">Historical</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={data.features.sources_endpoint ? 'text-green-500' : 'text-gray-400'}>
                {data.features.sources_endpoint ? 'OK' : '--'}
              </span>
              <span className="text-sm text-gray-600">Sources</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={data.features.https ? 'text-green-500' : 'text-gray-400'}>
                {data.features.https ? 'OK' : '--'}
              </span>
              <span className="text-sm text-gray-600">HTTPS</span>
            </div>
          </div>
        </div>

        {/* Reset Date */}
        <div className="mt-4 pt-4 border-t text-xs text-gray-500">
          <p>Usage resets: {new Date(data.reset_date).toLocaleDateString()}</p>
        </div>
      </div>
    </Card>
  );
};

export default MediaStackUsagePanel;

import React from 'react';
import { Card } from '@/components/ui/Card';
import { useCacheStats, useInvalidateCache, useClearCache, useExpireCache } from '../api';

interface CacheStatsPanelProps {
  className?: string;
}

/**
 * Progress Ring
 */
const ProgressRing: React.FC<{ percentage: number; label: string; color: string }> = ({
  percentage,
  label,
  color,
}) => {
  const radius = 40;
  const stroke = 8;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <svg height={radius * 2} width={radius * 2}>
        <circle
          stroke="#e5e7eb"
          fill="transparent"
          strokeWidth={stroke}
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
        <circle
          stroke={color}
          fill="transparent"
          strokeWidth={stroke}
          strokeDasharray={`${circumference} ${circumference}`}
          style={{ strokeDashoffset }}
          strokeLinecap="round"
          r={normalizedRadius}
          cx={radius}
          cy={radius}
          transform={`rotate(-90 ${radius} ${radius})`}
        />
        <text
          x="50%"
          y="50%"
          textAnchor="middle"
          dominantBaseline="middle"
          className="text-lg font-bold fill-current"
        >
          {percentage.toFixed(0)}%
        </text>
      </svg>
      <p className="text-sm text-gray-600 mt-2">{label}</p>
    </div>
  );
};

/**
 * Cache Stats Panel
 *
 * Displays cache statistics including hit/miss rates,
 * storage usage, and domain breakdown.
 */
export const CacheStatsPanel: React.FC<CacheStatsPanelProps> = ({ className }) => {
  const { data, isLoading, error, refetch, isRefetching } = useCacheStats();
  const invalidateCache = useInvalidateCache();
  const clearCache = useClearCache();
  const expireCache = useExpireCache();

  const handleClearAll = async () => {
    if (!confirm('Clear ALL cache entries? This cannot be undone.')) return;
    try {
      const result = await clearCache.mutateAsync();
      alert(`Cleared ${result.entries_affected} entries`);
    } catch (err) {
      console.error('Failed to clear cache:', err);
    }
  };

  const handleExpireOld = async () => {
    if (!confirm('Expire cache entries older than 24 hours?')) return;
    try {
      const result = await expireCache.mutateAsync(24);
      alert(`Expired ${result.entries_affected} entries`);
    } catch (err) {
      console.error('Failed to expire cache:', err);
    }
  };

  const handleInvalidateDomain = async (domain: string) => {
    if (!confirm(`Invalidate all cache for ${domain}?`)) return;
    try {
      const result = await invalidateCache.mutateAsync({ domain });
      alert(`Invalidated ${result.entries_affected} entries`);
    } catch (err) {
      console.error('Failed to invalidate:', err);
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(0)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(0)}m`;
    if (seconds < 86400) return `${(seconds / 3600).toFixed(1)}h`;
    return `${(seconds / 86400).toFixed(1)}d`;
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Cache Statistics</h3>
          <div className="animate-pulse grid grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-100 rounded"></div>
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
          <h3 className="text-lg font-semibold mb-4 text-red-600">Cache Statistics</h3>
          <p className="text-sm text-red-500 mb-4">
            Failed to load cache stats: {error.message}
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

  return (
    <Card className={className}>
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold">Cache Statistics</h3>
          <div className="flex gap-2">
            <button
              onClick={() => refetch()}
              disabled={isRefetching}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
            >
              {isRefetching ? 'Loading...' : 'Refresh'}
            </button>
            <button
              onClick={handleExpireOld}
              disabled={expireCache.isPending}
              className="px-3 py-1 text-sm bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 disabled:opacity-50"
            >
              Expire Old
            </button>
            <button
              onClick={handleClearAll}
              disabled={clearCache.isPending}
              className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 disabled:opacity-50"
            >
              Clear All
            </button>
          </div>
        </div>

        {/* Hit/Miss Rates */}
        <div className="flex justify-around mb-6">
          <ProgressRing
            percentage={data.hit_rate * 100}
            label="Hit Rate"
            color="#22c55e"
          />
          <ProgressRing
            percentage={data.miss_rate * 100}
            label="Miss Rate"
            color="#ef4444"
          />
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-50 rounded p-3">
            <p className="text-xs text-gray-500">Total Entries</p>
            <p className="text-xl font-bold">{data.total_entries.toLocaleString()}</p>
          </div>
          <div className="bg-gray-50 rounded p-3">
            <p className="text-xs text-gray-500">Total Size</p>
            <p className="text-xl font-bold">{data.total_size_human}</p>
          </div>
          <div className="bg-gray-50 rounded p-3">
            <p className="text-xs text-gray-500">Avg Age</p>
            <p className="text-xl font-bold">{formatDuration(data.avg_age_seconds)}</p>
          </div>
          <div className="bg-gray-50 rounded p-3">
            <p className="text-xs text-gray-500">Expired</p>
            <p className="text-xl font-bold text-yellow-600">{data.expired_entries}</p>
          </div>
        </div>

        {/* Domain Breakdown */}
        {data.by_domain.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">By Domain</h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {data.by_domain.map((item) => (
                <div
                  key={item.domain}
                  className="flex justify-between items-center p-2 bg-gray-50 rounded hover:bg-gray-100"
                >
                  <div>
                    <span className="font-medium">{item.domain}</span>
                    <span className="text-xs text-gray-500 ml-2">
                      {item.entries} entries
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">{formatBytes(item.size_bytes)}</span>
                    <button
                      onClick={() => handleInvalidateDomain(item.domain)}
                      disabled={invalidateCache.isPending}
                      className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 disabled:opacity-50"
                    >
                      Clear
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

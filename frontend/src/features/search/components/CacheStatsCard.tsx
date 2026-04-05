import { Card } from '@/components/ui/Card';
import { useCacheStats } from '../hooks';

/**
 * Cache Statistics Card Component
 *
 * Displays Redis cache statistics with auto-refresh capability.
 *
 * @example
 * ```tsx
 * <CacheStatsCard refreshInterval={5000} />
 * ```
 */
interface CacheStatsCardProps {
  /** Auto-refresh interval in milliseconds (default: disabled) */
  refreshInterval?: number;
  /** Custom className for styling */
  className?: string;
}

export const CacheStatsCard: React.FC<CacheStatsCardProps> = ({
  refreshInterval,
  className,
}) => {
  const { data, isLoading, error, refetch, isRefetching } = useCacheStats({
    refetchInterval: refreshInterval,
  });

  if (isLoading) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4">Cache Statistics</h3>
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
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
          <h3 className="text-lg font-semibold mb-4 text-red-600">
            Cache Statistics
          </h3>
          <p className="text-sm text-red-500">
            Failed to load cache statistics: {error.message}
          </p>
          <button
            onClick={() => refetch()}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  if (!data) return null;

  const hitRateColor =
    data.hit_rate_percent >= 80
      ? 'text-green-600'
      : data.hit_rate_percent >= 50
      ? 'text-yellow-600'
      : 'text-red-600';

  return (
    <Card className={className}>
      <div className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Cache Statistics</h3>
          <button
            onClick={() => refetch()}
            disabled={isRefetching}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
            title="Refresh cache statistics"
          >
            {isRefetching ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Hit Rate */}
          <div className="col-span-2">
            <p className="text-sm text-gray-600">Hit Rate</p>
            <p className={`text-2xl font-bold ${hitRateColor}`}>
              {data.hit_rate_percent.toFixed(2)}%
            </p>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
              <div
                className={`h-2 rounded-full ${
                  data.hit_rate_percent >= 80
                    ? 'bg-green-600'
                    : data.hit_rate_percent >= 50
                    ? 'bg-yellow-600'
                    : 'bg-red-600'
                }`}
                style={{ width: `${data.hit_rate_percent}%` }}
              ></div>
            </div>
          </div>

          {/* Memory Usage */}
          <div>
            <p className="text-sm text-gray-600">Memory Used</p>
            <p className="text-lg font-semibold">{data.memory_used}</p>
          </div>

          <div>
            <p className="text-sm text-gray-600">Memory Peak</p>
            <p className="text-lg font-semibold">{data.memory_peak}</p>
          </div>

          {/* Total Keys */}
          <div>
            <p className="text-sm text-gray-600">Total Keys</p>
            <p className="text-lg font-semibold">
              {data.total_keys.toLocaleString()}
            </p>
          </div>

          {/* Hit/Miss Stats */}
          <div>
            <p className="text-sm text-gray-600">Hits / Misses</p>
            <p className="text-lg font-semibold">
              {data.total_hits.toLocaleString()} /{' '}
              {data.total_misses.toLocaleString()}
            </p>
          </div>

          {/* Evicted Keys */}
          <div>
            <p className="text-sm text-gray-600">Evicted Keys</p>
            <p className="text-lg font-semibold">
              {data.evicted_keys.toLocaleString()}
            </p>
          </div>

          {/* Expired Keys */}
          <div>
            <p className="text-sm text-gray-600">Expired Keys</p>
            <p className="text-lg font-semibold">
              {data.expired_keys.toLocaleString()}
            </p>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t">
          <p className="text-xs text-gray-500">
            Last updated:{' '}
            {new Date(data.last_updated).toLocaleTimeString()}
          </p>
        </div>
      </div>
    </Card>
  );
};

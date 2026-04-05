import { Card } from '@/components/ui/Card';
import {
  useCacheStats,
  useIndexStats,
  useQueryStats,
  usePerformanceStats,
} from '../hooks';

/**
 * Complete Search Service Dashboard
 *
 * Displays all search service statistics in a dashboard layout.
 *
 * @example
 * ```tsx
 * // In your admin page
 * <SearchDashboard />
 * ```
 */
export const SearchDashboard: React.FC = () => {
  const { data: cacheData, isLoading: cacheLoading } = useCacheStats({
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const { data: indexData, isLoading: indexLoading } = useIndexStats();

  const { data: queryData, isLoading: queryLoading } = useQueryStats(10);

  const { data: perfData, isLoading: perfLoading } = usePerformanceStats();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Search Service Dashboard</h1>
        <p className="text-gray-600">
          Real-time monitoring and statistics for the search service
        </p>
      </div>

      {/* Cache Statistics */}
      <Card>
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">Cache Statistics</h2>
          {cacheLoading ? (
            <div className="animate-pulse">Loading cache stats...</div>
          ) : cacheData ? (
            <div className="grid grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600">Hit Rate</p>
                <p className="text-2xl font-bold text-green-600">
                  {cacheData.hit_rate_percent.toFixed(2)}%
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Memory Used</p>
                <p className="text-xl font-semibold">
                  {cacheData.memory_used}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Keys</p>
                <p className="text-xl font-semibold">
                  {cacheData.total_keys.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Evicted Keys</p>
                <p className="text-xl font-semibold">
                  {cacheData.evicted_keys.toLocaleString()}
                </p>
              </div>
            </div>
          ) : (
            <p className="text-red-500">Failed to load cache statistics</p>
          )}
        </div>
      </Card>

      {/* Index Statistics */}
      <Card>
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">Index Statistics</h2>
          {indexLoading ? (
            <div className="animate-pulse">Loading index stats...</div>
          ) : indexData ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Total Indexed</p>
                  <p className="text-2xl font-bold">
                    {indexData.total_indexed.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Recent (24h)</p>
                  <p className="text-2xl font-bold">
                    {indexData.recent_24h.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Index Size</p>
                  <p className="text-2xl font-bold">{indexData.index_size}</p>
                </div>
              </div>

              {/* Top Sources */}
              <div>
                <h3 className="text-sm font-semibold mb-2">
                  Top Sources
                </h3>
                <div className="space-y-2">
                  {indexData.by_source.slice(0, 5).map((source) => (
                    <div
                      key={source.source}
                      className="flex justify-between items-center"
                    >
                      <span className="text-sm">{source.source}</span>
                      <span className="text-sm font-semibold">
                        {source.count.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Sentiment Distribution */}
              <div>
                <h3 className="text-sm font-semibold mb-2">
                  Sentiment Distribution
                </h3>
                <div className="flex gap-4">
                  {indexData.by_sentiment.map((sentiment) => (
                    <div key={sentiment.sentiment} className="text-center">
                      <p className="text-xs text-gray-600 capitalize">
                        {sentiment.sentiment}
                      </p>
                      <p className="text-lg font-semibold">
                        {sentiment.count.toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-red-500">Failed to load index statistics</p>
          )}
        </div>
      </Card>

      {/* Query Statistics */}
      <Card>
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">Query Statistics</h2>
          {queryLoading ? (
            <div className="animate-pulse">Loading query stats...</div>
          ) : queryData ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Total Searches</p>
                  <p className="text-2xl font-bold">
                    {queryData.total_searches.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Recent (24h)</p>
                  <p className="text-2xl font-bold">
                    {queryData.recent_24h.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Avg Results</p>
                  <p className="text-2xl font-bold">
                    {queryData.avg_results_per_query}
                  </p>
                </div>
              </div>

              {/* Top Queries */}
              <div>
                <h3 className="text-sm font-semibold mb-2">Top Queries</h3>
                <div className="space-y-2">
                  {queryData.top_queries.map((query, index) => (
                    <div
                      key={`${query.query}-${index}`}
                      className="flex justify-between items-center"
                    >
                      <span className="text-sm truncate max-w-xs">
                        {query.query}
                      </span>
                      <span className="text-sm font-semibold">
                        {query.hits.toLocaleString()} hits
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-red-500">Failed to load query statistics</p>
          )}
        </div>
      </Card>

      {/* Performance Statistics */}
      <Card>
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">
            Performance Statistics
          </h2>
          {perfLoading ? (
            <div className="animate-pulse">Loading performance stats...</div>
          ) : perfData ? (
            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-600">
                  Average Execution Time
                </p>
                <p className="text-2xl font-bold">
                  {perfData.avg_execution_time_ms.toFixed(2)}ms
                </p>
              </div>

              {/* Result Distribution */}
              <div>
                <h3 className="text-sm font-semibold mb-2">
                  Result Distribution
                </h3>
                <div className="space-y-2">
                  {perfData.result_distribution.map((dist) => (
                    <div
                      key={dist.range}
                      className="flex justify-between items-center"
                    >
                      <span className="text-sm">{dist.range}</span>
                      <span className="text-sm font-semibold">
                        {dist.count.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-red-500">
              Failed to load performance statistics
            </p>
          )}
        </div>
      </Card>
    </div>
  );
};

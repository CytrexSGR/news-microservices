/**
 * Basic Usage Examples for Search Service Hooks
 *
 * This file demonstrates common usage patterns.
 * Copy these examples into your components as needed.
 */

import { useCacheStats, useIndexStats, useQueryStats } from '../hooks';

/**
 * Example 1: Basic Cache Stats Display
 */
export function Example1_BasicCacheStats() {
  const { data, isLoading, error } = useCacheStats();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div className="p-4 bg-white rounded shadow">
      <h2 className="text-lg font-bold mb-2">Cache Performance</h2>
      <p>Hit Rate: {data?.hit_rate_percent.toFixed(2)}%</p>
      <p>Memory: {data?.memory_used}</p>
      <p>Total Keys: {data?.total_keys.toLocaleString()}</p>
    </div>
  );
}

/**
 * Example 2: Auto-Refreshing Cache Monitor
 */
export function Example2_AutoRefresh() {
  const { data, isRefetching } = useCacheStats({
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  return (
    <div className="p-4 bg-white rounded shadow">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-lg font-bold">Live Cache Monitor</h2>
        {isRefetching && (
          <span className="text-xs text-blue-500">Updating...</span>
        )}
      </div>
      <div className="text-3xl font-bold">
        {data?.hit_rate_percent.toFixed(1)}%
      </div>
      <div className="text-sm text-gray-600">Hit Rate</div>
    </div>
  );
}

/**
 * Example 3: Index Statistics with Top Sources
 */
export function Example3_IndexStats() {
  const { data, isLoading } = useIndexStats();

  if (isLoading) return <div>Loading index stats...</div>;

  return (
    <div className="p-4 bg-white rounded shadow">
      <h2 className="text-lg font-bold mb-4">Search Index</h2>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-2xl font-bold">
            {data?.total_indexed.toLocaleString()}
          </div>
          <div className="text-sm text-gray-600">Total Articles</div>
        </div>
        <div>
          <div className="text-2xl font-bold">{data?.index_size}</div>
          <div className="text-sm text-gray-600">Index Size</div>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold mb-2">Top Sources</h3>
        <ul className="space-y-1">
          {data?.by_source.slice(0, 5).map((source) => (
            <li
              key={source.source}
              className="flex justify-between text-sm"
            >
              <span>{source.source}</span>
              <span className="font-semibold">
                {source.count.toLocaleString()}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

/**
 * Example 4: Popular Queries Chart
 */
export function Example4_PopularQueries() {
  const { data } = useQueryStats(5); // Top 5 queries

  return (
    <div className="p-4 bg-white rounded shadow">
      <h2 className="text-lg font-bold mb-4">Popular Searches</h2>

      <div className="space-y-3">
        {data?.top_queries.map((query, index) => {
          const maxHits = data.top_queries[0].hits;
          const percentage = (query.hits / maxHits) * 100;

          return (
            <div key={`${query.query}-${index}`}>
              <div className="flex justify-between text-sm mb-1">
                <span className="truncate max-w-xs">{query.query}</span>
                <span className="font-semibold">
                  {query.hits.toLocaleString()}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 pt-4 border-t text-sm text-gray-600">
        <p>Total searches: {data?.total_searches.toLocaleString()}</p>
        <p>Searches today: {data?.recent_24h.toLocaleString()}</p>
      </div>
    </div>
  );
}

/**
 * Example 5: Conditional Fetching (Admin Only)
 */
export function Example5_ConditionalFetch({ isAdmin }: { isAdmin: boolean }) {
  const { data, isLoading } = useCacheStats({
    enabled: isAdmin, // Only fetch if user is admin
  });

  if (!isAdmin) {
    return <div>Admin access required</div>;
  }

  if (isLoading) {
    return <div>Loading admin stats...</div>;
  }

  return (
    <div className="p-4 bg-white rounded shadow">
      <h2 className="text-lg font-bold mb-2">Admin: Cache Stats</h2>
      <p>Memory Peak: {data?.memory_peak}</p>
      <p>Evicted Keys: {data?.evicted_keys.toLocaleString()}</p>
      <p>Expired Keys: {data?.expired_keys.toLocaleString()}</p>
    </div>
  );
}

/**
 * Example 6: Manual Refresh with Loading State
 */
export function Example6_ManualRefresh() {
  const { data, isLoading, refetch, isRefetching } = useCacheStats();

  const handleRefresh = async () => {
    await refetch();
  };

  return (
    <div className="p-4 bg-white rounded shadow">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-bold">Cache Statistics</h2>
        <button
          onClick={handleRefresh}
          disabled={isRefetching}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {isRefetching ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {isLoading ? (
        <div>Loading...</div>
      ) : (
        <div>
          <p>Hit Rate: {data?.hit_rate_percent.toFixed(2)}%</p>
          <p>Memory: {data?.memory_used}</p>
          <p className="text-xs text-gray-500 mt-2">
            Last updated: {new Date(data?.last_updated || '').toLocaleTimeString()}
          </p>
        </div>
      )}
    </div>
  );
}

/**
 * Example 7: Multiple Stats in One Component
 */
export function Example7_CombinedStats() {
  const cacheQuery = useCacheStats();
  const indexQuery = useIndexStats();
  const queryQuery = useQueryStats(10);

  const isLoading =
    cacheQuery.isLoading || indexQuery.isLoading || queryQuery.isLoading;

  if (isLoading) {
    return <div>Loading all statistics...</div>;
  }

  return (
    <div className="grid grid-cols-3 gap-4">
      {/* Cache Card */}
      <div className="p-4 bg-white rounded shadow">
        <h3 className="font-bold mb-2">Cache</h3>
        <p className="text-2xl font-bold text-green-600">
          {cacheQuery.data?.hit_rate_percent.toFixed(1)}%
        </p>
        <p className="text-xs text-gray-600">Hit Rate</p>
      </div>

      {/* Index Card */}
      <div className="p-4 bg-white rounded shadow">
        <h3 className="font-bold mb-2">Index</h3>
        <p className="text-2xl font-bold text-blue-600">
          {indexQuery.data?.total_indexed.toLocaleString()}
        </p>
        <p className="text-xs text-gray-600">Articles</p>
      </div>

      {/* Queries Card */}
      <div className="p-4 bg-white rounded shadow">
        <h3 className="font-bold mb-2">Queries</h3>
        <p className="text-2xl font-bold text-purple-600">
          {queryQuery.data?.total_searches.toLocaleString()}
        </p>
        <p className="text-xs text-gray-600">Total Searches</p>
      </div>
    </div>
  );
}

/**
 * Example 8: Error Handling with Retry
 */
export function Example8_ErrorHandling() {
  const { data, error, isError, refetch } = useCacheStats({
    retry: 3, // Retry failed requests 3 times
    retryDelay: 1000, // Wait 1 second between retries
  });

  if (isError) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded">
        <h3 className="text-red-800 font-bold mb-2">Failed to Load Stats</h3>
        <p className="text-sm text-red-600 mb-4">{error.message}</p>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 bg-white rounded shadow">
      <p>Hit Rate: {data?.hit_rate_percent.toFixed(2)}%</p>
    </div>
  );
}

/**
 * MonitoringDashboard Page
 *
 * Main monitoring overview displaying system health at a glance.
 */

import { useState } from 'react';
import { RefreshCw, Clock } from 'lucide-react';
import { useSystemHealth } from '../api/useSystemHealth';
import { useServicesList } from '../api/useServicesList';
import { useQueueHealth } from '../api/useQueueHealth';
import { useDatabaseStats } from '../api/useDatabaseStats';
import { useCacheStats } from '../api/useCacheStats';
import {
  SystemHealthCard,
  ServicesGrid,
  QueueHealthPanel,
  DatabaseStatsPanel,
  CacheStatsPanel,
} from '../components';

export function MonitoringDashboard() {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000);

  const systemHealth = useSystemHealth({ autoRefresh, refetchInterval: refreshInterval });
  const servicesList = useServicesList({ autoRefresh, refetchInterval: refreshInterval });
  const queueHealth = useQueueHealth({ autoRefresh, refetchInterval: refreshInterval });
  const databaseStats = useDatabaseStats({ autoRefresh, refetchInterval: refreshInterval });
  const cacheStats = useCacheStats({ autoRefresh, refetchInterval: refreshInterval });

  const handleRefreshAll = () => {
    systemHealth.invalidate();
    servicesList.invalidate();
    queueHealth.invalidate();
    databaseStats.invalidate();
    cacheStats.invalidate();
  };

  const isRefreshing =
    systemHealth.isFetching ||
    servicesList.isFetching ||
    queueHealth.isFetching ||
    databaseStats.isFetching ||
    cacheStats.isFetching;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">System Monitoring</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Real-time overview of all system components
          </p>
        </div>
        <div className="flex items-center gap-4">
          {/* Auto-refresh toggle */}
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded border-border"
              />
              Auto-refresh
            </label>
            {autoRefresh && (
              <select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                className="text-sm bg-muted border-border rounded px-2 py-1"
              >
                <option value={10000}>10s</option>
                <option value={30000}>30s</option>
                <option value={60000}>1m</option>
                <option value={300000}>5m</option>
              </select>
            )}
          </div>

          {/* Refresh button */}
          <button
            onClick={handleRefreshAll}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* System Health Overview */}
      <SystemHealthCard
        health={systemHealth.data ?? null}
        isLoading={systemHealth.isLoading}
        onRefresh={systemHealth.invalidate}
      />

      {/* Services Grid */}
      <ServicesGrid
        services={servicesList.services}
        isLoading={servicesList.isLoading}
      />

      {/* Infrastructure Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Queue Health */}
        <QueueHealthPanel
          queueHealth={queueHealth.data ?? null}
          isLoading={queueHealth.isLoading}
        />

        {/* Cache Stats */}
        <CacheStatsPanel
          cacheStats={cacheStats.data ?? null}
          isLoading={cacheStats.isLoading}
        />
      </div>

      {/* Database Stats - Full Width */}
      <DatabaseStatsPanel
        databaseStats={databaseStats.data ?? null}
        isLoading={databaseStats.isLoading}
      />

      {/* Footer with last update time */}
      <div className="text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
        <Clock className="w-3 h-3" />
        {autoRefresh
          ? `Auto-refreshing every ${refreshInterval / 1000}s`
          : 'Auto-refresh disabled'}
      </div>
    </div>
  );
}

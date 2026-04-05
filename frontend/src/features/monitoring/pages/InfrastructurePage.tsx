/**
 * InfrastructurePage
 *
 * Displays infrastructure components: queues, databases, and cache.
 */

import { useState } from 'react';
import { RefreshCw, Layers, Database as DbIcon, HardDrive } from 'lucide-react';
import { useQueueHealth } from '../api/useQueueHealth';
import { useDatabaseStats } from '../api/useDatabaseStats';
import { useCacheStats } from '../api/useCacheStats';
import {
  QueueHealthPanel,
  DatabaseStatsPanel,
  CacheStatsPanel,
  HealthBadge,
} from '../components';

type Tab = 'all' | 'queues' | 'databases' | 'cache';

export function InfrastructurePage() {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>('all');

  const queueHealth = useQueueHealth({ autoRefresh, refetchInterval: 30000 });
  const databaseStats = useDatabaseStats({ autoRefresh, refetchInterval: 30000 });
  const cacheStats = useCacheStats({ autoRefresh, refetchInterval: 30000 });

  const handleRefreshAll = () => {
    queueHealth.invalidate();
    databaseStats.invalidate();
    cacheStats.invalidate();
  };

  const isRefreshing =
    queueHealth.isFetching || databaseStats.isFetching || cacheStats.isFetching;

  // Calculate overall status
  const getOverallStatus = () => {
    const statuses = [
      queueHealth.data?.status,
      databaseStats.data?.status,
      cacheStats.data?.status,
    ].filter(Boolean);

    if (statuses.includes('unhealthy')) return 'unhealthy';
    if (statuses.includes('degraded')) return 'degraded';
    if (statuses.every((s) => s === 'healthy')) return 'healthy';
    return 'unknown';
  };

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'all', label: 'All', icon: <HardDrive className="w-4 h-4" /> },
    { id: 'queues', label: 'Queues', icon: <Layers className="w-4 h-4" /> },
    { id: 'databases', label: 'Databases', icon: <DbIcon className="w-4 h-4" /> },
    { id: 'cache', label: 'Cache', icon: <HardDrive className="w-4 h-4" /> },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-foreground">Infrastructure</h1>
            <HealthBadge status={getOverallStatus()} />
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Queues, databases, and cache status
          </p>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-border"
            />
            Auto-refresh
          </label>
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

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Summary Cards (visible in 'all' tab) */}
      {activeTab === 'all' && (
        <div className="grid grid-cols-3 gap-4">
          <div
            className={`p-4 rounded-lg border cursor-pointer transition-all ${
              queueHealth.data?.status === 'healthy'
                ? 'border-green-200 bg-green-50 dark:bg-green-950/30 dark:border-green-800'
                : queueHealth.data?.status === 'degraded'
                ? 'border-yellow-200 bg-yellow-50 dark:bg-yellow-950/30 dark:border-yellow-800'
                : 'border-border bg-card'
            }`}
            onClick={() => setActiveTab('queues')}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium text-foreground">RabbitMQ</span>
              </div>
              {queueHealth.data && <HealthBadge status={queueHealth.data.status} size="sm" />}
            </div>
            <p className="text-xl font-bold text-foreground">
              {queueHealth.data?.total_queues ?? '--'} queues
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {queueHealth.data?.total_messages.toLocaleString() ?? '--'} messages
            </p>
          </div>

          <div
            className={`p-4 rounded-lg border cursor-pointer transition-all ${
              databaseStats.data?.status === 'healthy'
                ? 'border-green-200 bg-green-50 dark:bg-green-950/30 dark:border-green-800'
                : databaseStats.data?.status === 'degraded'
                ? 'border-yellow-200 bg-yellow-50 dark:bg-yellow-950/30 dark:border-yellow-800'
                : 'border-border bg-card'
            }`}
            onClick={() => setActiveTab('databases')}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <DbIcon className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium text-foreground">Databases</span>
              </div>
              {databaseStats.data && (
                <HealthBadge status={databaseStats.data.status} size="sm" />
              )}
            </div>
            <p className="text-xl font-bold text-foreground">
              {(databaseStats.data?.postgresql ? 1 : 0) +
                (databaseStats.data?.neo4j ? 1 : 0)}{' '}
              connected
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              PostgreSQL + Neo4j
            </p>
          </div>

          <div
            className={`p-4 rounded-lg border cursor-pointer transition-all ${
              cacheStats.data?.status === 'healthy'
                ? 'border-green-200 bg-green-50 dark:bg-green-950/30 dark:border-green-800'
                : cacheStats.data?.status === 'degraded'
                ? 'border-yellow-200 bg-yellow-50 dark:bg-yellow-950/30 dark:border-yellow-800'
                : 'border-border bg-card'
            }`}
            onClick={() => setActiveTab('cache')}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <HardDrive className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium text-foreground">Redis Cache</span>
              </div>
              {cacheStats.data && <HealthBadge status={cacheStats.data.status} size="sm" />}
            </div>
            <p className="text-xl font-bold text-foreground">
              {cacheStats.data?.hit_rate_percent.toFixed(1) ?? '--'}% hit rate
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {cacheStats.data?.keys_count.toLocaleString() ?? '--'} keys
            </p>
          </div>
        </div>
      )}

      {/* Content based on active tab */}
      {(activeTab === 'all' || activeTab === 'queues') && (
        <QueueHealthPanel
          queueHealth={queueHealth.data ?? null}
          isLoading={queueHealth.isLoading}
        />
      )}

      {(activeTab === 'all' || activeTab === 'databases') && (
        <DatabaseStatsPanel
          databaseStats={databaseStats.data ?? null}
          isLoading={databaseStats.isLoading}
        />
      )}

      {(activeTab === 'all' || activeTab === 'cache') && (
        <CacheStatsPanel
          cacheStats={cacheStats.data ?? null}
          isLoading={cacheStats.isLoading}
        />
      )}
    </div>
  );
}

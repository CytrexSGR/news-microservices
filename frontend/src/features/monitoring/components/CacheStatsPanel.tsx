/**
 * CacheStatsPanel Component
 *
 * Displays Redis cache statistics and health.
 */

import {
  Database,
  Key,
  Activity,
  MemoryStick,
  Clock,
  TrendingUp,
  Users,
  Trash2,
} from 'lucide-react';
import { HealthBadge } from './HealthBadge';
import type { CacheStatsPanelProps } from '../types';

/**
 * Format memory size
 */
function formatMemory(mb: number): string {
  if (mb >= 1024) return `${(mb / 1024).toFixed(2)} GB`;
  return `${mb.toFixed(1)} MB`;
}

/**
 * Format uptime seconds
 */
function formatUptime(seconds?: number): string {
  if (!seconds) return '--';
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  if (days > 0) return `${days}d ${hours}h`;
  return `${hours}h`;
}

export function CacheStatsPanel({ cacheStats, isLoading }: CacheStatsPanelProps) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <div className="h-5 bg-muted rounded w-40 animate-pulse" />
          <div className="h-6 bg-muted rounded w-24 animate-pulse" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-muted rounded animate-pulse" />
          ))}
        </div>
        <div className="h-32 bg-muted rounded animate-pulse" />
      </div>
    );
  }

  if (!cacheStats) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
        <div className="text-center py-8 text-muted-foreground">
          <Database className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Cache stats unavailable</p>
        </div>
      </div>
    );
  }

  const memoryUsagePercent = (cacheStats.memory_used_mb / cacheStats.memory_max_mb) * 100;
  const isHighMemory = memoryUsagePercent > 80;
  const isLowHitRate = cacheStats.hit_rate_percent < 50;

  return (
    <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-red-500" />
          <h3 className="font-semibold text-foreground">Redis Cache</h3>
          {cacheStats.version && (
            <span className="text-xs text-muted-foreground">v{cacheStats.version}</span>
          )}
        </div>
        <HealthBadge status={cacheStats.status} />
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {/* Hit Rate */}
        <div
          className={`p-4 rounded-lg ${
            isLowHitRate
              ? 'bg-yellow-50 dark:bg-yellow-950/30'
              : 'bg-green-50 dark:bg-green-950/30'
          }`}
        >
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <TrendingUp className="w-4 h-4" />
            <span className="text-sm">Hit Rate</span>
          </div>
          <span
            className={`text-2xl font-bold ${
              isLowHitRate
                ? 'text-yellow-600 dark:text-yellow-400'
                : 'text-green-600 dark:text-green-400'
            }`}
          >
            {cacheStats.hit_rate_percent.toFixed(1)}%
          </span>
        </div>

        {/* Keys */}
        <div className="p-4 rounded-lg bg-muted/50">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <Key className="w-4 h-4" />
            <span className="text-sm">Keys</span>
          </div>
          <span className="text-2xl font-bold text-foreground">
            {cacheStats.keys_count.toLocaleString()}
          </span>
        </div>

        {/* Ops/sec */}
        <div className="p-4 rounded-lg bg-muted/50">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <Activity className="w-4 h-4" />
            <span className="text-sm">Ops/sec</span>
          </div>
          <span className="text-2xl font-bold text-foreground">
            {cacheStats.operations_per_sec.toLocaleString()}
          </span>
        </div>

        {/* Uptime */}
        <div className="p-4 rounded-lg bg-muted/50">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <Clock className="w-4 h-4" />
            <span className="text-sm">Uptime</span>
          </div>
          <span className="text-2xl font-bold text-foreground">
            {formatUptime(cacheStats.uptime_seconds)}
          </span>
        </div>
      </div>

      {/* Memory Usage */}
      <div
        className={`p-4 rounded-lg border ${
          isHighMemory
            ? 'bg-red-50 border-red-200 dark:bg-red-950/30 dark:border-red-800'
            : 'bg-muted/50 border-border'
        }`}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2 text-muted-foreground">
            <MemoryStick className="w-4 h-4" />
            <span className="text-sm">Memory Usage</span>
          </div>
          <span
            className={`text-sm font-medium ${
              isHighMemory ? 'text-red-600 dark:text-red-400' : 'text-foreground'
            }`}
          >
            {formatMemory(cacheStats.memory_used_mb)} / {formatMemory(cacheStats.memory_max_mb)}
          </span>
        </div>
        <div className="h-3 bg-muted rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              isHighMemory ? 'bg-red-500' : memoryUsagePercent > 60 ? 'bg-yellow-500' : 'bg-primary'
            }`}
            style={{ width: `${Math.min(memoryUsagePercent, 100)}%` }}
          />
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          {memoryUsagePercent.toFixed(1)}% used
          {cacheStats.fragmentation_ratio !== undefined && (
            <span className="ml-2">
              (Fragmentation: {cacheStats.fragmentation_ratio.toFixed(2)})
            </span>
          )}
        </p>
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
        {cacheStats.connected_clients !== undefined && (
          <div className="p-3 rounded-lg bg-muted/50">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Users className="w-3 h-3" />
              <span className="text-xs">Clients</span>
            </div>
            <span className="text-lg font-semibold text-foreground">
              {cacheStats.connected_clients}
            </span>
          </div>
        )}

        {cacheStats.total_hits !== undefined && (
          <div className="p-3 rounded-lg bg-muted/50">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <TrendingUp className="w-3 h-3" />
              <span className="text-xs">Total Hits</span>
            </div>
            <span className="text-lg font-semibold text-foreground">
              {cacheStats.total_hits.toLocaleString()}
            </span>
          </div>
        )}

        {cacheStats.expired_keys !== undefined && (
          <div className="p-3 rounded-lg bg-muted/50">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Clock className="w-3 h-3" />
              <span className="text-xs">Expired (1h)</span>
            </div>
            <span className="text-lg font-semibold text-foreground">
              {cacheStats.expired_keys.toLocaleString()}
            </span>
          </div>
        )}

        {cacheStats.evicted_keys !== undefined && (
          <div className="p-3 rounded-lg bg-muted/50">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Trash2 className="w-3 h-3" />
              <span className="text-xs">Evicted (1h)</span>
            </div>
            <span
              className={`text-lg font-semibold ${
                cacheStats.evicted_keys > 0
                  ? 'text-yellow-600 dark:text-yellow-400'
                  : 'text-foreground'
              }`}
            >
              {cacheStats.evicted_keys.toLocaleString()}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * DatabaseStatsPanel Component
 *
 * Displays PostgreSQL and Neo4j database statistics.
 */

import {
  Database,
  HardDrive,
  Users,
  Clock,
  Activity,
  AlertTriangle,
} from 'lucide-react';
import { HealthBadge } from './HealthBadge';
import type { DatabaseStatsPanelProps, DatabaseStats } from '../types';

/**
 * Format size in GB to human-readable
 */
function formatSize(gb: number): string {
  if (gb >= 1) return `${gb.toFixed(2)} GB`;
  return `${(gb * 1024).toFixed(0)} MB`;
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

/**
 * Single database card component
 */
function DatabaseCard({ db }: { db: DatabaseStats }) {
  const poolUtilization = db.pool_utilization_percent ?? (db.connections_active / db.connections_max) * 100;
  const isHighUtilization = poolUtilization > 80;

  return (
    <div
      className={`p-6 rounded-lg border ${
        db.status === 'unhealthy'
          ? 'bg-red-50 border-red-200 dark:bg-red-950/30 dark:border-red-800'
          : db.status === 'degraded'
          ? 'bg-yellow-50 border-yellow-200 dark:bg-yellow-950/30 dark:border-yellow-800'
          : 'bg-card border-border'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className={`p-2 rounded-lg ${
              db.type === 'postgresql'
                ? 'bg-blue-100 dark:bg-blue-950/50'
                : 'bg-green-100 dark:bg-green-950/50'
            }`}
          >
            <Database
              className={`w-5 h-5 ${
                db.type === 'postgresql'
                  ? 'text-blue-600 dark:text-blue-400'
                  : 'text-green-600 dark:text-green-400'
              }`}
            />
          </div>
          <div>
            <h4 className="font-medium text-foreground">{db.name}</h4>
            {db.version && (
              <p className="text-xs text-muted-foreground">v{db.version}</p>
            )}
          </div>
        </div>
        <HealthBadge status={db.status} size="sm" />
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-3">
        {/* Connections */}
        <div className="p-3 rounded-lg bg-muted/50">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <Users className="w-4 h-4" />
            <span className="text-sm">Connections</span>
          </div>
          <div className="flex items-baseline gap-1">
            <span
              className={`text-xl font-bold ${
                isHighUtilization ? 'text-red-600 dark:text-red-400' : 'text-foreground'
              }`}
            >
              {db.connections_active}
            </span>
            <span className="text-sm text-muted-foreground">/ {db.connections_max}</span>
          </div>
          <div className="mt-2 h-2 bg-muted rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${
                isHighUtilization ? 'bg-red-500' : 'bg-primary'
              }`}
              style={{ width: `${Math.min(poolUtilization, 100)}%` }}
            />
          </div>
        </div>

        {/* Size */}
        <div className="p-3 rounded-lg bg-muted/50">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <HardDrive className="w-4 h-4" />
            <span className="text-sm">Size</span>
          </div>
          <span className="text-xl font-bold text-foreground">
            {formatSize(db.size_gb)}
          </span>
        </div>

        {/* Query Time */}
        <div className="p-3 rounded-lg bg-muted/50">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <Activity className="w-4 h-4" />
            <span className="text-sm">Avg Query</span>
          </div>
          <span
            className={`text-xl font-bold ${
              db.query_avg_ms > 100
                ? 'text-yellow-600 dark:text-yellow-400'
                : 'text-foreground'
            }`}
          >
            {db.query_avg_ms.toFixed(1)} ms
          </span>
        </div>

        {/* Uptime */}
        <div className="p-3 rounded-lg bg-muted/50">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <Clock className="w-4 h-4" />
            <span className="text-sm">Uptime</span>
          </div>
          <span className="text-xl font-bold text-foreground">
            {formatUptime(db.uptime_seconds)}
          </span>
        </div>
      </div>

      {/* Slow Queries Warning */}
      {db.slow_queries_count !== undefined && db.slow_queries_count > 0 && (
        <div className="mt-4 p-3 rounded-lg bg-yellow-50 border border-yellow-200 dark:bg-yellow-950/30 dark:border-yellow-800">
          <div className="flex items-center gap-2 text-yellow-700 dark:text-yellow-400">
            <AlertTriangle className="w-4 h-4" />
            <span className="text-sm font-medium">
              {db.slow_queries_count} slow queries in the last hour
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export function DatabaseStatsPanel({
  databaseStats,
  isLoading,
}: DatabaseStatsPanelProps) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <div className="h-5 bg-muted rounded w-40 animate-pulse" />
          <div className="h-6 bg-muted rounded w-24 animate-pulse" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="h-64 bg-muted rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!databaseStats) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
        <div className="text-center py-8 text-muted-foreground">
          <Database className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Database stats unavailable</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-foreground">Databases</h3>
        </div>
        <HealthBadge status={databaseStats.status} />
      </div>

      {/* Database Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {databaseStats.postgresql && (
          <DatabaseCard db={databaseStats.postgresql} />
        )}
        {databaseStats.neo4j && (
          <DatabaseCard db={databaseStats.neo4j} />
        )}
      </div>

      {/* Empty State */}
      {!databaseStats.postgresql && !databaseStats.neo4j && (
        <div className="text-center py-8 text-muted-foreground">
          <Database className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No database connections</p>
        </div>
      )}
    </div>
  );
}

/**
 * SystemHealthCard Component
 *
 * Displays overall system health status with key metrics.
 */

import {
  Activity,
  Server,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Clock,
} from 'lucide-react';
import { HealthBadge } from './HealthBadge';
import type { SystemHealthCardProps } from '../types';

/**
 * Format uptime seconds to human-readable string
 */
function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  const parts = [];
  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0 || parts.length === 0) parts.push(`${minutes}m`);

  return parts.join(' ');
}

/**
 * Format timestamp to relative time
 */
function formatLastCheck(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffSeconds < 60) return 'Just now';
  if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`;
  if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)}h ago`;
  return date.toLocaleDateString();
}

export function SystemHealthCard({
  health,
  isLoading,
  onRefresh,
}: SystemHealthCardProps) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <div className="h-6 bg-muted rounded w-32 animate-pulse" />
          <div className="h-8 bg-muted rounded w-24 animate-pulse" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-muted rounded w-20 mb-2" />
              <div className="h-8 bg-muted rounded w-16" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const healthPercentage = health
    ? Math.round((health.services_healthy / health.services_total) * 100)
    : 0;

  return (
    <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/10">
            <Activity className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">System Health</h3>
            {health && (
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Last check: {formatLastCheck(health.last_check)}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          {health && <HealthBadge status={health.status} size="lg" />}
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-2 rounded-lg hover:bg-muted transition-colors"
              title="Refresh"
            >
              <RefreshCw className="w-4 h-4 text-muted-foreground" />
            </button>
          )}
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {/* Health Percentage */}
        <div className="p-4 rounded-lg bg-muted/50">
          <p className="text-sm text-muted-foreground mb-1">Health Score</p>
          <p className="text-2xl font-bold text-foreground">{healthPercentage}%</p>
        </div>

        {/* Services Status */}
        <div className="p-4 rounded-lg bg-muted/50">
          <p className="text-sm text-muted-foreground mb-1">Services</p>
          <div className="flex items-baseline gap-1">
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
              {health?.services_healthy ?? 0}
            </p>
            <p className="text-sm text-muted-foreground">
              / {health?.services_total ?? 0}
            </p>
          </div>
        </div>

        {/* Uptime */}
        <div className="p-4 rounded-lg bg-muted/50">
          <p className="text-sm text-muted-foreground mb-1">Uptime</p>
          <p className="text-2xl font-bold text-foreground">
            {health ? formatUptime(health.uptime_seconds) : '--'}
          </p>
        </div>

        {/* Issues */}
        <div className="p-4 rounded-lg bg-muted/50">
          <p className="text-sm text-muted-foreground mb-1">Active Issues</p>
          <p
            className={`text-2xl font-bold ${
              (health?.issues.length ?? 0) > 0
                ? 'text-red-600 dark:text-red-400'
                : 'text-foreground'
            }`}
          >
            {health?.issues.length ?? 0}
          </p>
        </div>
      </div>

      {/* Issues List */}
      {health && health.issues.length > 0 && (
        <div className="border-t border-border pt-4">
          <h4 className="text-sm font-medium text-foreground mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-yellow-500" />
            Active Issues
          </h4>
          <div className="space-y-2">
            {health.issues.slice(0, 5).map((issue, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg border ${
                  issue.severity === 'critical'
                    ? 'bg-red-50 border-red-200 dark:bg-red-950/30 dark:border-red-800'
                    : 'bg-yellow-50 border-yellow-200 dark:bg-yellow-950/30 dark:border-yellow-800'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {issue.severity === 'critical' ? (
                      <XCircle className="w-4 h-4 text-red-500" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-yellow-500" />
                    )}
                    <span className="font-medium text-sm text-foreground">
                      {issue.service}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    Since {formatLastCheck(issue.since)}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mt-1 ml-6">
                  {issue.message}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Issues */}
      {health && health.issues.length === 0 && (
        <div className="border-t border-border pt-4">
          <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
            <CheckCircle className="w-4 h-4" />
            <span className="text-sm">All systems operating normally</span>
          </div>
        </div>
      )}
    </div>
  );
}

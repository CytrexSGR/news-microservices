/**
 * HealthSummaryCard Component
 *
 * Displays overall system health status with percentage and key metrics.
 * Color coding: green=healthy, yellow=degraded, red=unhealthy.
 */

import { Activity, Server, CheckCircle, XCircle, AlertTriangle, Cpu, MemoryStick } from 'lucide-react';
import type { HealthSummaryCardProps } from '../types/health';

/**
 * Calculate health percentage from summary data
 */
function calculateHealthPercentage(summary: HealthSummaryCardProps['summary']): {
  percentage: number;
  status: 'healthy' | 'degraded' | 'unhealthy';
  color: string;
  bgColor: string;
} {
  if (!summary) {
    return {
      percentage: 0,
      status: 'unhealthy',
      color: 'text-red-600 dark:text-red-400',
      bgColor: 'bg-red-100 dark:bg-red-950/50',
    };
  }

  const { healthy, running, unhealthy } = summary;
  const checkableContainers = running;
  const percentage = checkableContainers > 0 ? (healthy / checkableContainers) * 100 : 0;

  if (unhealthy > 0 || percentage < 50) {
    return {
      percentage: Math.round(percentage),
      status: 'unhealthy',
      color: 'text-red-600 dark:text-red-400',
      bgColor: 'bg-red-100 dark:bg-red-950/50',
    };
  }

  if (percentage < 80) {
    return {
      percentage: Math.round(percentage),
      status: 'degraded',
      color: 'text-yellow-600 dark:text-yellow-400',
      bgColor: 'bg-yellow-100 dark:bg-yellow-950/50',
    };
  }

  return {
    percentage: Math.round(percentage),
    status: 'healthy',
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-100 dark:bg-green-950/50',
  };
}

export function HealthSummaryCard({ summary, isLoading }: HealthSummaryCardProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-card border border-border rounded-lg p-6 animate-pulse">
            <div className="h-4 bg-muted rounded w-1/2 mb-3" />
            <div className="h-8 bg-muted rounded w-1/3" />
          </div>
        ))}
      </div>
    );
  }

  const healthStatus = calculateHealthPercentage(summary);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Overall Health */}
      <div className={`bg-card border border-border rounded-lg p-6 shadow-sm`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">System Health</p>
            <p className={`text-3xl font-bold ${healthStatus.color}`}>
              {healthStatus.percentage}%
            </p>
            <p className={`text-xs mt-1 ${healthStatus.color}`}>
              {healthStatus.status.charAt(0).toUpperCase() + healthStatus.status.slice(1)}
            </p>
          </div>
          <div className={`p-3 rounded-full ${healthStatus.bgColor}`}>
            {healthStatus.status === 'healthy' && (
              <CheckCircle className={`h-8 w-8 ${healthStatus.color}`} />
            )}
            {healthStatus.status === 'degraded' && (
              <AlertTriangle className={`h-8 w-8 ${healthStatus.color}`} />
            )}
            {healthStatus.status === 'unhealthy' && (
              <XCircle className={`h-8 w-8 ${healthStatus.color}`} />
            )}
          </div>
        </div>
      </div>

      {/* Container Stats */}
      <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Containers</p>
            <div className="flex items-baseline gap-2">
              <p className="text-3xl font-bold text-foreground">
                {summary?.running ?? 0}
              </p>
              <p className="text-sm text-muted-foreground">
                / {summary?.total_containers ?? 0}
              </p>
            </div>
            <div className="flex gap-3 mt-1 text-xs">
              <span className="text-green-600 dark:text-green-400">
                {summary?.healthy ?? 0} healthy
              </span>
              {(summary?.unhealthy ?? 0) > 0 && (
                <span className="text-red-600 dark:text-red-400">
                  {summary?.unhealthy} unhealthy
                </span>
              )}
            </div>
          </div>
          <div className="p-3 rounded-full bg-primary/10">
            <Server className="h-8 w-8 text-primary" />
          </div>
        </div>
      </div>

      {/* CPU Usage */}
      <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Avg CPU Usage</p>
            <p className="text-3xl font-bold text-foreground">
              {summary?.avg_cpu_percent.toFixed(1) ?? '0.0'}%
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {summary?.total_pids ?? 0} processes
            </p>
          </div>
          <div className="p-3 rounded-full bg-purple-100 dark:bg-purple-950/50">
            <Cpu className="h-8 w-8 text-purple-600 dark:text-purple-400" />
          </div>
        </div>
      </div>

      {/* Memory Usage */}
      <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Avg Memory Usage</p>
            <p className="text-3xl font-bold text-foreground">
              {summary?.avg_memory_percent.toFixed(1) ?? '0.0'}%
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              across all containers
            </p>
          </div>
          <div className="p-3 rounded-full bg-orange-100 dark:bg-orange-950/50">
            <MemoryStick className="h-8 w-8 text-orange-600 dark:text-orange-400" />
          </div>
        </div>
      </div>
    </div>
  );
}

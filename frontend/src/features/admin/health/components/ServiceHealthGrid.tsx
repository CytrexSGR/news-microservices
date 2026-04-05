/**
 * ServiceHealthGrid Component
 *
 * Displays a grid of all services with their health status indicators.
 * Color coding: green=healthy, yellow=degraded, red=unhealthy, gray=stopped.
 */

import { CheckCircle, XCircle, Server, Pause, AlertCircle } from 'lucide-react';
import type { ContainerHealth, ServiceHealthGridProps } from '../types/health';

/**
 * Get status color classes based on container health
 */
function getStatusStyles(container: ContainerHealth): {
  bgColor: string;
  textColor: string;
  borderColor: string;
  icon: React.ReactNode;
  label: string;
} {
  const { status, health } = container;

  // Stopped/exited containers
  if (status !== 'running') {
    return {
      bgColor: 'bg-gray-100 dark:bg-gray-900/50',
      textColor: 'text-gray-600 dark:text-gray-400',
      borderColor: 'border-gray-300 dark:border-gray-700',
      icon: <Pause className="w-4 h-4" />,
      label: 'stopped',
    };
  }

  // Running containers with health checks
  if (health === 'healthy') {
    return {
      bgColor: 'bg-green-100 dark:bg-green-950/50',
      textColor: 'text-green-700 dark:text-green-400',
      borderColor: 'border-green-300 dark:border-green-800',
      icon: <CheckCircle className="w-4 h-4" />,
      label: 'healthy',
    };
  }

  if (health === 'unhealthy') {
    return {
      bgColor: 'bg-red-100 dark:bg-red-950/50',
      textColor: 'text-red-700 dark:text-red-400',
      borderColor: 'border-red-300 dark:border-red-800',
      icon: <XCircle className="w-4 h-4" />,
      label: 'unhealthy',
    };
  }

  // Running without health check
  return {
    bgColor: 'bg-muted',
    textColor: 'text-muted-foreground',
    borderColor: 'border-border',
    icon: <Server className="w-4 h-4" />,
    label: 'running',
  };
}

/**
 * Format container name for display (remove common prefixes)
 */
function formatContainerName(name: string): string {
  return name
    .replace(/^news-/, '')
    .replace(/-service$/, '')
    .replace(/-/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Sort containers by health status (unhealthy first, then running, then stopped)
 */
function sortContainers(containers: ContainerHealth[]): ContainerHealth[] {
  return [...containers].sort((a, b) => {
    // Priority: unhealthy > running (no healthcheck) > healthy > stopped
    const getPriority = (c: ContainerHealth) => {
      if (c.status !== 'running') return 4;
      if (c.health === 'unhealthy') return 1;
      if (c.health === null) return 2;
      return 3;
    };
    return getPriority(a) - getPriority(b);
  });
}

export function ServiceHealthGrid({ containers, isLoading }: ServiceHealthGridProps) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground mb-4">Service Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {[...Array(12)].map((_, i) => (
            <div key={i} className="h-16 bg-muted rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  const sortedContainers = sortContainers(containers);

  // Count by status
  const healthyCount = containers.filter(c => c.status === 'running' && c.health === 'healthy').length;
  const unhealthyCount = containers.filter(c => c.status === 'running' && c.health === 'unhealthy').length;
  const runningCount = containers.filter(c => c.status === 'running').length;
  const stoppedCount = containers.filter(c => c.status !== 'running').length;

  return (
    <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-foreground">Service Status</h2>
        <div className="flex gap-4 text-xs">
          <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
            <CheckCircle className="w-3 h-3" /> {healthyCount} healthy
          </span>
          {unhealthyCount > 0 && (
            <span className="flex items-center gap-1 text-red-600 dark:text-red-400">
              <XCircle className="w-3 h-3" /> {unhealthyCount} unhealthy
            </span>
          )}
          <span className="flex items-center gap-1 text-muted-foreground">
            <Server className="w-3 h-3" /> {runningCount} running
          </span>
          {stoppedCount > 0 && (
            <span className="flex items-center gap-1 text-gray-500">
              <Pause className="w-3 h-3" /> {stoppedCount} stopped
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {sortedContainers.map((container) => {
          const styles = getStatusStyles(container);

          return (
            <div
              key={container.name}
              className={`rounded-lg border p-3 transition-all hover:shadow-md ${styles.borderColor} ${styles.bgColor}`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-sm truncate flex-1 text-foreground" title={container.name}>
                  {formatContainerName(container.name)}
                </span>
                <span className={`ml-2 px-2 py-0.5 rounded text-xs flex items-center gap-1 font-medium border ${styles.textColor} ${styles.borderColor} bg-white/50 dark:bg-black/20`}>
                  {styles.icon}
                  {styles.label}
                </span>
              </div>
              {container.status === 'running' && (
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div>
                    <span className="block text-muted-foreground">CPU</span>
                    <span className="font-semibold text-foreground">
                      {container.cpu_percent.toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="block text-muted-foreground">Mem</span>
                    <span className="font-semibold text-foreground">
                      {container.memory_percent.toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="block text-muted-foreground">PIDs</span>
                    <span className="font-semibold text-foreground">
                      {container.pids}
                    </span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

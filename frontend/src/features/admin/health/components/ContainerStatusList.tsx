/**
 * ContainerStatusList Component
 *
 * Displays a detailed list view of Docker containers with resource usage.
 */

import { CheckCircle, XCircle, Server, Pause, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import type { ContainerHealth, ContainerStatusListProps } from '../types/health';

/**
 * Get status badge styling based on container health
 */
function getStatusBadge(container: ContainerHealth): {
  className: string;
  label: string;
  icon: React.ReactNode;
} {
  const { status, health } = container;

  if (status !== 'running') {
    return {
      className: 'bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-900/50 dark:text-gray-400 dark:border-gray-700',
      label: 'Stopped',
      icon: <Pause className="w-3 h-3" />,
    };
  }

  if (health === 'healthy') {
    return {
      className: 'bg-green-100 text-green-700 border-green-300 dark:bg-green-950/50 dark:text-green-400 dark:border-green-800',
      label: 'Healthy',
      icon: <CheckCircle className="w-3 h-3" />,
    };
  }

  if (health === 'unhealthy') {
    return {
      className: 'bg-red-100 text-red-700 border-red-300 dark:bg-red-950/50 dark:text-red-400 dark:border-red-800',
      label: 'Unhealthy',
      icon: <XCircle className="w-3 h-3" />,
    };
  }

  return {
    className: 'bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-950/50 dark:text-blue-400 dark:border-blue-800',
    label: 'Running',
    icon: <Server className="w-3 h-3" />,
  };
}

/**
 * Get progress bar color based on usage percentage
 */
function getUsageColor(percentage: number): string {
  if (percentage >= 90) return 'bg-red-500';
  if (percentage >= 70) return 'bg-yellow-500';
  return 'bg-green-500';
}

export function ContainerStatusList({ containers, isLoading, showDetails = true }: ContainerStatusListProps) {
  const [expandedContainers, setExpandedContainers] = useState<Set<string>>(new Set());
  const [sortBy, setSortBy] = useState<'name' | 'cpu' | 'memory' | 'status'>('status');

  const toggleExpand = (name: string) => {
    setExpandedContainers(prev => {
      const newSet = new Set(prev);
      if (newSet.has(name)) {
        newSet.delete(name);
      } else {
        newSet.add(name);
      }
      return newSet;
    });
  };

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg shadow-sm">
        <div className="p-4 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">Container Details</h2>
        </div>
        <div className="p-4 space-y-3">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-12 bg-muted rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  // Sort containers
  const sortedContainers = [...containers].sort((a, b) => {
    switch (sortBy) {
      case 'cpu':
        return b.cpu_percent - a.cpu_percent;
      case 'memory':
        return b.memory_percent - a.memory_percent;
      case 'name':
        return a.name.localeCompare(b.name);
      case 'status':
      default:
        // Unhealthy first, then by name
        const getStatusPriority = (c: ContainerHealth) => {
          if (c.status !== 'running') return 3;
          if (c.health === 'unhealthy') return 0;
          if (c.health === null) return 2;
          return 1;
        };
        const priorityDiff = getStatusPriority(a) - getStatusPriority(b);
        return priorityDiff !== 0 ? priorityDiff : a.name.localeCompare(b.name);
    }
  });

  return (
    <div className="bg-card border border-border rounded-lg shadow-sm">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">Container Details</h2>
        <div className="flex gap-2">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            className="text-xs bg-muted border border-border rounded px-2 py-1"
          >
            <option value="status">Sort by Status</option>
            <option value="name">Sort by Name</option>
            <option value="cpu">Sort by CPU</option>
            <option value="memory">Sort by Memory</option>
          </select>
        </div>
      </div>

      <div className="divide-y divide-border">
        {sortedContainers.map((container) => {
          const badge = getStatusBadge(container);
          const isExpanded = expandedContainers.has(container.name);

          return (
            <div key={container.name} className="hover:bg-muted/30 transition-colors">
              <div
                className="p-4 flex items-center gap-4 cursor-pointer"
                onClick={() => showDetails && toggleExpand(container.name)}
              >
                {/* Status Badge */}
                <span className={`px-2 py-1 rounded text-xs flex items-center gap-1 font-medium border ${badge.className}`}>
                  {badge.icon}
                  {badge.label}
                </span>

                {/* Container Name */}
                <span className="font-medium text-sm flex-1 truncate text-foreground">
                  {container.name}
                </span>

                {/* Quick Stats (only for running containers) */}
                {container.status === 'running' && (
                  <div className="flex items-center gap-6 text-xs text-muted-foreground">
                    <div className="flex items-center gap-2 w-24">
                      <span>CPU</span>
                      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className={`h-full ${getUsageColor(container.cpu_percent)} transition-all`}
                          style={{ width: `${Math.min(container.cpu_percent, 100)}%` }}
                        />
                      </div>
                      <span className="w-12 text-right font-mono">
                        {container.cpu_percent.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex items-center gap-2 w-24">
                      <span>Mem</span>
                      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className={`h-full ${getUsageColor(container.memory_percent)} transition-all`}
                          style={{ width: `${Math.min(container.memory_percent, 100)}%` }}
                        />
                      </div>
                      <span className="w-12 text-right font-mono">
                        {container.memory_percent.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                )}

                {/* Expand/Collapse Button */}
                {showDetails && (
                  <button className="p-1 hover:bg-muted rounded">
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-muted-foreground" />
                    )}
                  </button>
                )}
              </div>

              {/* Expanded Details */}
              {showDetails && isExpanded && container.status === 'running' && (
                <div className="px-4 pb-4 pt-0 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm border-t border-border/50 mt-2">
                  <div>
                    <span className="text-muted-foreground block text-xs">Memory Usage</span>
                    <span className="font-medium text-foreground">{container.memory_usage}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block text-xs">Processes</span>
                    <span className="font-medium text-foreground">{container.pids} PIDs</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block text-xs">Status</span>
                    <span className="font-medium text-foreground capitalize">{container.status}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block text-xs">Health Check</span>
                    <span className="font-medium text-foreground capitalize">{container.health || 'N/A'}</span>
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

/**
 * ServiceStatusCard Component
 *
 * Displays status information for a single service.
 */

import {
  Server,
  Activity,
  Clock,
  Cpu,
  MemoryStick,
  Zap,
  ChevronRight,
} from 'lucide-react';
import { HealthBadge } from './HealthBadge';
import type { ServiceStatusCardProps } from '../types';

/**
 * Format service name for display
 */
function formatServiceName(name: string): string {
  return name
    .replace(/-service$/, '')
    .replace(/-/g, ' ')
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Format uptime seconds to human-readable string
 */
function formatUptime(seconds?: number): string {
  if (!seconds) return '--';
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

/**
 * Get service type icon
 */
function getServiceIcon(type: string) {
  switch (type) {
    case 'api':
      return <Server className="w-4 h-4" />;
    case 'worker':
      return <Zap className="w-4 h-4" />;
    case 'database':
      return <Activity className="w-4 h-4" />;
    default:
      return <Server className="w-4 h-4" />;
  }
}

export function ServiceStatusCard({
  service,
  onClick,
}: ServiceStatusCardProps) {
  const hasMetrics = !!service.metrics;

  return (
    <div
      className={`bg-card border border-border rounded-lg p-4 shadow-sm transition-all ${
        onClick ? 'cursor-pointer hover:shadow-md hover:border-primary/50' : ''
      }`}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded bg-muted">
            {getServiceIcon(service.type)}
          </div>
          <div>
            <h4 className="font-medium text-foreground text-sm">
              {formatServiceName(service.name)}
            </h4>
            {service.port && (
              <p className="text-xs text-muted-foreground">
                Port {service.port}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <HealthBadge status={service.status} size="sm" showLabel={false} />
          {onClick && (
            <ChevronRight className="w-4 h-4 text-muted-foreground" />
          )}
        </div>
      </div>

      {/* Metrics */}
      {hasMetrics && (
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="p-2 rounded bg-muted/50">
            <div className="flex items-center gap-1 text-muted-foreground mb-1">
              <Cpu className="w-3 h-3" />
              <span>CPU</span>
            </div>
            <p className="font-semibold text-foreground">
              {service.metrics!.cpu_percent.toFixed(1)}%
            </p>
          </div>
          <div className="p-2 rounded bg-muted/50">
            <div className="flex items-center gap-1 text-muted-foreground mb-1">
              <MemoryStick className="w-3 h-3" />
              <span>Mem</span>
            </div>
            <p className="font-semibold text-foreground">
              {service.metrics!.memory_mb.toFixed(0)} MB
            </p>
          </div>
          <div className="p-2 rounded bg-muted/50">
            <div className="flex items-center gap-1 text-muted-foreground mb-1">
              <Activity className="w-3 h-3" />
              <span>Req/m</span>
            </div>
            <p className="font-semibold text-foreground">
              {service.metrics!.requests_per_minute}
            </p>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-3 pt-3 border-t border-border flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span>Uptime: {formatUptime(service.uptime_seconds)}</span>
        </div>
        {service.version && <span>v{service.version}</span>}
      </div>
    </div>
  );
}

/**
 * QueueHealthPanel Component
 *
 * Displays RabbitMQ queue health status and metrics.
 */

import {
  Layers,
  Users,
  Mail,
  Activity,
  MemoryStick,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import { HealthBadge } from './HealthBadge';
import type { QueueHealthPanelProps, QueueHealth } from '../types';

/**
 * Single queue card component
 */
function QueueCard({ queue }: { queue: QueueHealth }) {
  const isBacklogged = queue.messages_ready > 1000;
  const hasLowConsumers = queue.consumers < 1;

  return (
    <div
      className={`p-4 rounded-lg border ${
        queue.status === 'unhealthy'
          ? 'bg-red-50 border-red-200 dark:bg-red-950/30 dark:border-red-800'
          : queue.status === 'degraded'
          ? 'bg-yellow-50 border-yellow-200 dark:bg-yellow-950/30 dark:border-yellow-800'
          : 'bg-card border-border'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-primary" />
          <span className="font-medium text-sm text-foreground truncate" title={queue.name}>
            {queue.name}
          </span>
        </div>
        <HealthBadge status={queue.status} size="sm" showLabel={false} />
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="p-2 rounded bg-muted/50">
          <div className="flex items-center gap-1 text-muted-foreground mb-1">
            <Mail className="w-3 h-3" />
            <span>Ready</span>
          </div>
          <p
            className={`font-semibold ${
              isBacklogged ? 'text-red-600 dark:text-red-400' : 'text-foreground'
            }`}
          >
            {queue.messages_ready.toLocaleString()}
          </p>
        </div>
        <div className="p-2 rounded bg-muted/50">
          <div className="flex items-center gap-1 text-muted-foreground mb-1">
            <Activity className="w-3 h-3" />
            <span>Unacked</span>
          </div>
          <p className="font-semibold text-foreground">
            {queue.messages_unacked.toLocaleString()}
          </p>
        </div>
        <div className="p-2 rounded bg-muted/50">
          <div className="flex items-center gap-1 text-muted-foreground mb-1">
            <Users className="w-3 h-3" />
            <span>Consumers</span>
          </div>
          <p
            className={`font-semibold ${
              hasLowConsumers ? 'text-yellow-600 dark:text-yellow-400' : 'text-foreground'
            }`}
          >
            {queue.consumers}
          </p>
        </div>
        <div className="p-2 rounded bg-muted/50">
          <div className="flex items-center gap-1 text-muted-foreground mb-1">
            <MemoryStick className="w-3 h-3" />
            <span>Memory</span>
          </div>
          <p className="font-semibold text-foreground">{queue.memory_mb.toFixed(1)} MB</p>
        </div>
      </div>

      {/* Rate indicators */}
      {(queue.publish_rate !== undefined || queue.deliver_rate !== undefined) && (
        <div className="mt-3 pt-3 border-t border-border flex items-center justify-between text-xs">
          {queue.publish_rate !== undefined && (
            <div className="flex items-center gap-1 text-muted-foreground">
              <TrendingUp className="w-3 h-3 text-green-500" />
              <span>{queue.publish_rate.toFixed(1)} msg/s in</span>
            </div>
          )}
          {queue.deliver_rate !== undefined && (
            <div className="flex items-center gap-1 text-muted-foreground">
              <TrendingDown className="w-3 h-3 text-blue-500" />
              <span>{queue.deliver_rate.toFixed(1)} msg/s out</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function QueueHealthPanel({ queueHealth, isLoading }: QueueHealthPanelProps) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="h-5 bg-muted rounded w-40 animate-pulse" />
          <div className="h-6 bg-muted rounded w-24 animate-pulse" />
        </div>
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-16 bg-muted rounded animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-40 bg-muted rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!queueHealth) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
        <div className="text-center py-8 text-muted-foreground">
          <Layers className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Queue health data unavailable</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-foreground">RabbitMQ Queues</h3>
          {queueHealth.version && (
            <span className="text-xs text-muted-foreground">v{queueHealth.version}</span>
          )}
        </div>
        <HealthBadge status={queueHealth.status} />
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="p-4 rounded-lg bg-muted/50">
          <p className="text-sm text-muted-foreground mb-1">Total Queues</p>
          <p className="text-2xl font-bold text-foreground">{queueHealth.total_queues}</p>
        </div>
        <div className="p-4 rounded-lg bg-muted/50">
          <p className="text-sm text-muted-foreground mb-1">Total Messages</p>
          <p className="text-2xl font-bold text-foreground">
            {queueHealth.total_messages.toLocaleString()}
          </p>
        </div>
        <div className="p-4 rounded-lg bg-muted/50">
          <p className="text-sm text-muted-foreground mb-1">Total Consumers</p>
          <p className="text-2xl font-bold text-foreground">{queueHealth.total_consumers}</p>
        </div>
        <div className="p-4 rounded-lg bg-muted/50">
          <p className="text-sm text-muted-foreground mb-1">Memory Usage</p>
          <p className="text-2xl font-bold text-foreground">
            {queueHealth.total_memory_mb.toFixed(1)} MB
          </p>
        </div>
      </div>

      {/* Queue Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {queueHealth.queues.map((queue) => (
          <QueueCard key={queue.name} queue={queue} />
        ))}
      </div>

      {/* Empty State */}
      {queueHealth.queues.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          <Layers className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No queues found</p>
        </div>
      )}
    </div>
  );
}

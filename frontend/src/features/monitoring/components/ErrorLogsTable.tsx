/**
 * ErrorLogsTable Component
 *
 * Displays error logs in a table format with filtering.
 */

import { useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  XCircle,
  ChevronDown,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import type { ErrorLogsTableProps, ErrorLog, LogLevel } from '../types';

/**
 * Get icon and styles based on log level
 */
function getLogLevelConfig(level: LogLevel): {
  icon: React.ReactNode;
  bgColor: string;
  textColor: string;
  borderColor: string;
} {
  switch (level) {
    case 'critical':
      return {
        icon: <XCircle className="w-4 h-4" />,
        bgColor: 'bg-red-100 dark:bg-red-950/50',
        textColor: 'text-red-700 dark:text-red-400',
        borderColor: 'border-red-300 dark:border-red-800',
      };
    case 'error':
      return {
        icon: <AlertCircle className="w-4 h-4" />,
        bgColor: 'bg-orange-100 dark:bg-orange-950/50',
        textColor: 'text-orange-700 dark:text-orange-400',
        borderColor: 'border-orange-300 dark:border-orange-800',
      };
    case 'warning':
    default:
      return {
        icon: <AlertTriangle className="w-4 h-4" />,
        bgColor: 'bg-yellow-100 dark:bg-yellow-950/50',
        textColor: 'text-yellow-700 dark:text-yellow-400',
        borderColor: 'border-yellow-300 dark:border-yellow-800',
      };
  }
}

/**
 * Format timestamp to readable format
 */
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

/**
 * Single error log row component
 */
function ErrorLogRow({
  log,
  isExpanded,
  onToggle,
}: {
  log: ErrorLog;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const config = getLogLevelConfig(log.level);

  return (
    <div className={`border-b border-border last:border-b-0 ${config.bgColor}`}>
      {/* Main Row */}
      <div
        className="flex items-center gap-3 p-3 cursor-pointer hover:bg-black/5 dark:hover:bg-white/5"
        onClick={onToggle}
      >
        <button className="shrink-0">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="w-4 h-4 text-muted-foreground" />
          )}
        </button>

        <span className={`shrink-0 ${config.textColor}`}>{config.icon}</span>

        <span
          className={`shrink-0 px-2 py-0.5 rounded text-xs font-medium uppercase ${config.textColor} ${config.bgColor} border ${config.borderColor}`}
        >
          {log.level}
        </span>

        <span className="shrink-0 text-sm font-medium text-foreground min-w-24">
          {log.service}
        </span>

        <span className="flex-1 text-sm text-foreground truncate" title={log.message}>
          {log.message}
        </span>

        <span className="shrink-0 text-xs text-muted-foreground">
          {formatTimestamp(log.timestamp)}
        </span>

        {log.count > 1 && (
          <span className="shrink-0 px-2 py-0.5 bg-muted rounded text-xs font-medium text-muted-foreground">
            x{log.count}
          </span>
        )}
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="px-10 pb-3">
          <div className="bg-black/5 dark:bg-white/5 rounded-lg p-3 space-y-3">
            {/* Full Message */}
            <div>
              <h5 className="text-xs font-medium text-muted-foreground mb-1">
                Message
              </h5>
              <p className="text-sm text-foreground whitespace-pre-wrap">
                {log.message}
              </p>
            </div>

            {/* Stack Trace */}
            {log.stack_trace && (
              <div>
                <h5 className="text-xs font-medium text-muted-foreground mb-1">
                  Stack Trace
                </h5>
                <pre className="text-xs text-muted-foreground font-mono overflow-x-auto p-2 bg-muted rounded">
                  {log.stack_trace}
                </pre>
              </div>
            )}

            {/* Meta Info */}
            <div className="flex flex-wrap gap-4 text-xs">
              <div>
                <span className="text-muted-foreground">ID:</span>{' '}
                <span className="font-mono text-foreground">{log.id}</span>
              </div>
              {log.first_seen && (
                <div>
                  <span className="text-muted-foreground">First seen:</span>{' '}
                  <span className="text-foreground">{formatTimestamp(log.first_seen)}</span>
                </div>
              )}
              {log.last_seen && (
                <div>
                  <span className="text-muted-foreground">Last seen:</span>{' '}
                  <span className="text-foreground">{formatTimestamp(log.last_seen)}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function ErrorLogsTable({
  logs,
  isLoading,
  onLogClick,
}: ErrorLogsTableProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg shadow-sm">
        <div className="p-4 border-b border-border">
          <div className="h-5 bg-muted rounded w-32 animate-pulse" />
        </div>
        <div className="divide-y divide-border">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="p-4 animate-pulse">
              <div className="flex items-center gap-3">
                <div className="h-4 w-4 bg-muted rounded" />
                <div className="h-4 w-16 bg-muted rounded" />
                <div className="h-4 w-20 bg-muted rounded" />
                <div className="h-4 flex-1 bg-muted rounded" />
                <div className="h-4 w-24 bg-muted rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Count by level
  const criticalCount = logs.filter((l) => l.level === 'critical').length;
  const errorCount = logs.filter((l) => l.level === 'error').length;
  const warningCount = logs.filter((l) => l.level === 'warning').length;

  return (
    <div className="bg-card border border-border rounded-lg shadow-sm">
      {/* Header */}
      <div className="p-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-foreground">Error Logs</h3>
          <span className="text-sm text-muted-foreground">({logs.length})</span>
        </div>
        <div className="flex gap-4 text-xs">
          {criticalCount > 0 && (
            <span className="flex items-center gap-1 text-red-600 dark:text-red-400">
              <XCircle className="w-3 h-3" />
              {criticalCount} critical
            </span>
          )}
          {errorCount > 0 && (
            <span className="flex items-center gap-1 text-orange-600 dark:text-orange-400">
              <AlertCircle className="w-3 h-3" />
              {errorCount} errors
            </span>
          )}
          {warningCount > 0 && (
            <span className="flex items-center gap-1 text-yellow-600 dark:text-yellow-400">
              <AlertTriangle className="w-3 h-3" />
              {warningCount} warnings
            </span>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="max-h-[500px] overflow-y-auto">
        {logs.map((log) => (
          <ErrorLogRow
            key={log.id}
            log={log}
            isExpanded={expandedIds.has(log.id)}
            onToggle={() => toggleExpand(log.id)}
          />
        ))}
      </div>

      {/* Empty State */}
      {logs.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          <AlertCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No error logs found</p>
        </div>
      )}
    </div>
  );
}

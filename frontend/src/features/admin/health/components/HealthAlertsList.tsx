/**
 * HealthAlertsList Component
 *
 * Displays recent health alerts with severity indicators.
 * Color coding: red=critical, yellow=warning, blue=info.
 */

import { AlertTriangle, AlertCircle, Info, Clock, Bell } from 'lucide-react';
import type { HealthAlert, HealthAlertsListProps, AlertSeverity } from '../types/health';

/**
 * Get severity styling for an alert
 */
function getSeverityStyles(severity: AlertSeverity): {
  bgColor: string;
  textColor: string;
  borderColor: string;
  icon: React.ReactNode;
} {
  switch (severity) {
    case 'CRITICAL':
      return {
        bgColor: 'bg-red-50 dark:bg-red-950/30',
        textColor: 'text-red-800 dark:text-red-300',
        borderColor: 'border-red-200 dark:border-red-800',
        icon: <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400" />,
      };
    case 'WARNING':
      return {
        bgColor: 'bg-yellow-50 dark:bg-yellow-950/30',
        textColor: 'text-yellow-800 dark:text-yellow-300',
        borderColor: 'border-yellow-200 dark:border-yellow-800',
        icon: <AlertTriangle className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />,
      };
    case 'INFO':
    default:
      return {
        bgColor: 'bg-blue-50 dark:bg-blue-950/30',
        textColor: 'text-blue-800 dark:text-blue-300',
        borderColor: 'border-blue-200 dark:border-blue-800',
        icon: <Info className="w-4 h-4 text-blue-600 dark:text-blue-400" />,
      };
  }
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return timestamp;
  }
}

export function HealthAlertsList({ alerts, isLoading, limit = 10 }: HealthAlertsListProps) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg shadow-sm">
        <div className="p-4 border-b border-border flex items-center gap-2">
          <Bell className="w-5 h-5 text-muted-foreground" />
          <h2 className="text-lg font-semibold text-foreground">Recent Alerts</h2>
        </div>
        <div className="p-4 space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-16 bg-muted rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  const displayedAlerts = alerts.slice(0, limit);
  const criticalCount = alerts.filter(a => a.severity === 'CRITICAL').length;
  const warningCount = alerts.filter(a => a.severity === 'WARNING').length;

  return (
    <div className="bg-card border border-border rounded-lg shadow-sm">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bell className="w-5 h-5 text-muted-foreground" />
          <h2 className="text-lg font-semibold text-foreground">Recent Alerts</h2>
        </div>
        {alerts.length > 0 && (
          <div className="flex gap-3 text-xs">
            {criticalCount > 0 && (
              <span className="flex items-center gap-1 text-red-600 dark:text-red-400">
                <AlertCircle className="w-3 h-3" />
                {criticalCount} critical
              </span>
            )}
            {warningCount > 0 && (
              <span className="flex items-center gap-1 text-yellow-600 dark:text-yellow-400">
                <AlertTriangle className="w-3 h-3" />
                {warningCount} warnings
              </span>
            )}
          </div>
        )}
      </div>

      <div className="divide-y divide-border">
        {displayedAlerts.length === 0 ? (
          <div className="p-8 text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-green-100 dark:bg-green-950/50 mb-3">
              <AlertCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
            <p className="text-muted-foreground">No recent alerts</p>
            <p className="text-xs text-muted-foreground mt-1">System is running smoothly</p>
          </div>
        ) : (
          displayedAlerts.map((alert, index) => {
            const styles = getSeverityStyles(alert.severity);

            return (
              <div
                key={alert.id ?? index}
                className={`p-4 ${styles.bgColor} border-l-4 ${styles.borderColor}`}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">{styles.icon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`font-semibold ${styles.textColor}`}>
                        {alert.service}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium border ${styles.borderColor} ${styles.textColor} bg-white/50 dark:bg-black/20`}>
                        {alert.severity}
                      </span>
                    </div>
                    <p className={`text-sm ${styles.textColor}`}>{alert.message}</p>
                    <div className="flex items-center gap-1 mt-2 text-xs text-muted-foreground">
                      <Clock className="w-3 h-3" />
                      {formatTimestamp(alert.timestamp)}
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {alerts.length > limit && (
        <div className="p-3 text-center border-t border-border">
          <span className="text-xs text-muted-foreground">
            Showing {limit} of {alerts.length} alerts
          </span>
        </div>
      )}
    </div>
  );
}

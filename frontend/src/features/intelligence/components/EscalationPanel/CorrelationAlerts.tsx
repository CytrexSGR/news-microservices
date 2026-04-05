// frontend/src/features/intelligence/components/EscalationPanel/CorrelationAlerts.tsx
import type { CorrelationAlert, AlertType } from "../../types/escalation";
import { AlertTriangle, CheckCircle, Eye } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface CorrelationAlertsProps {
  alerts: CorrelationAlert[];
  onClusterClick?: (clusterId: string) => void;
}

export function CorrelationAlerts({ alerts, onClusterClick }: CorrelationAlertsProps) {
  const getAlertIcon = (type: AlertType) => {
    switch (type) {
      case "CONFIRMATION":
        return <CheckCircle className="w-4 h-4 text-red-500" />;
      case "DIVERGENCE":
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case "EARLY_WARNING":
        return <Eye className="w-4 h-4 text-blue-500" />;
    }
  };

  const getAlertBadgeColor = (type: AlertType): string => {
    switch (type) {
      case "CONFIRMATION":
        return "bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300";
      case "DIVERGENCE":
        return "bg-yellow-100 dark:bg-yellow-900/50 text-yellow-700 dark:text-yellow-300";
      case "EARLY_WARNING":
        return "bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300";
    }
  };

  if (alerts.length === 0) {
    return (
      <div className="bg-card rounded-lg border border-border p-4">
        <h3 className="text-sm font-medium text-muted-foreground mb-4">Correlation Alerts</h3>
        <p className="text-sm text-muted-foreground/70 text-center py-4">
          No active alerts
        </p>
      </div>
    );
  }

  return (
    <div className="bg-card rounded-lg border border-border p-4">
      <h3 className="text-sm font-medium text-muted-foreground mb-4">
        Correlation Alerts
        <span className="ml-2 text-xs text-muted-foreground/70">({alerts.length})</span>
      </h3>

      <div className="space-y-3 max-h-64 overflow-y-auto">
        {alerts.map((alert, idx) => (
          <div
            key={`${alert.type}-${alert.timestamp}-${idx}`}
            className="border border-border/50 rounded-lg p-3 hover:bg-muted transition-colors"
          >
            <div className="flex items-start gap-2">
              {getAlertIcon(alert.type)}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${getAlertBadgeColor(alert.type)}`}>
                    {alert.type.replace("_", " ")}
                  </span>
                  <span className="text-xs text-muted-foreground/70">
                    {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                  </span>
                </div>
                <p className="text-sm text-foreground">{alert.message}</p>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-xs text-muted-foreground/70">
                    Confidence: {(alert.confidence * 100).toFixed(0)}%
                  </span>
                  {alert.clusterId && onClusterClick && (
                    <button
                      onClick={() => onClusterClick(alert.clusterId!)}
                      className="text-xs text-blue-500 hover:text-blue-700"
                    >
                      View Cluster →
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

import { useAlerts, useMarkAlertsRead } from '../../hooks/useWatchlist';
import { THREAT_LEVEL_COLORS } from '../../types/security.types';

interface AlertDropdownProps {
  onClose: () => void;
}

export function AlertDropdown({ onClose }: AlertDropdownProps) {
  const { data: alertData, isLoading } = useAlerts(false, 1);
  const markReadMutation = useMarkAlertsRead();

  const handleMarkAllRead = () => {
    if (!alertData?.alerts) return;
    const unreadIds = alertData.alerts.filter(a => !a.is_read).map(a => a.id);
    if (unreadIds.length > 0) {
      markReadMutation.mutate(unreadIds);
    }
  };

  const handleMarkRead = (alertId: string) => {
    markReadMutation.mutate([alertId]);
  };

  return (
    <div className="absolute right-0 top-full mt-2 w-96 bg-slate-800 rounded-lg shadow-xl border border-slate-700 z-50">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-slate-700">
        <h4 className="font-semibold">Alerts</h4>
        {alertData && alertData.unread_count > 0 && (
          <button
            onClick={handleMarkAllRead}
            className="text-xs text-blue-400 hover:text-blue-300"
          >
            Mark all read
          </button>
        )}
      </div>

      {/* Alert List */}
      <div className="max-h-96 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-slate-400">Loading...</div>
        ) : alertData?.alerts && alertData.alerts.length > 0 ? (
          alertData.alerts.slice(0, 10).map((alert) => (
            <div
              key={alert.id}
              className={`p-3 border-b border-slate-700/50 hover:bg-slate-700/50 cursor-pointer ${
                !alert.is_read ? 'bg-slate-700/30' : ''
              }`}
              onClick={() => !alert.is_read && handleMarkRead(alert.id)}
            >
              <div className="flex items-start gap-2">
                <span
                  className="w-2 h-2 rounded-full mt-1.5 flex-shrink-0"
                  style={{ backgroundColor: THREAT_LEVEL_COLORS[alert.threat_level] }}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{alert.title}</p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Matched: <span className="text-slate-300">{alert.matched_value}</span>
                    {alert.country_code && (
                      <span className="ml-2">• {alert.country_code}</span>
                    )}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {new Date(alert.created_at).toLocaleString()}
                  </p>
                </div>
                {!alert.is_read && (
                  <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0" />
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="p-8 text-center text-slate-400">
            <p>No alerts yet</p>
            <p className="text-sm mt-1">Add items to your watchlist to receive alerts</p>
          </div>
        )}
      </div>

      {/* Footer */}
      {alertData && alertData.total > 10 && (
        <div className="p-3 border-t border-slate-700 text-center">
          <button className="text-sm text-blue-400 hover:text-blue-300">
            View all {alertData.total} alerts
          </button>
        </div>
      )}
    </div>
  );
}

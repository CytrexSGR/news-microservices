import type { WatchlistItem as WatchlistItemType } from '../../types/security.types';
import { WATCHLIST_TYPE_ICONS } from '../../types/security.types';

interface WatchlistItemProps {
  item: WatchlistItemType;
  onRemove: (id: string) => void;
}

export function WatchlistItem({ item, onRemove }: WatchlistItemProps) {
  const icon = WATCHLIST_TYPE_ICONS[item.item_type] || '📌';
  const hasRecentMatches = item.match_count_24h > 0;

  return (
    <div className={`flex items-center gap-3 p-3 rounded-lg ${hasRecentMatches ? 'bg-red-900/20 border border-red-700/50' : 'bg-slate-800/50'}`}>
      <span className="text-xl">{icon}</span>

      <div className="flex-1 min-w-0">
        <div className="font-medium truncate">
          {item.display_name || item.item_value}
        </div>
        <div className="text-xs text-slate-400 flex gap-2">
          <span>{item.item_type}</span>
          {item.match_count_24h > 0 && (
            <span className="text-red-400">
              {item.match_count_24h} today
            </span>
          )}
          {item.match_count_7d > 0 && (
            <span className="text-slate-500">
              {item.match_count_7d} this week
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className={`px-2 py-0.5 text-xs rounded ${
          item.priority >= 8 ? 'bg-red-600' :
          item.priority >= 6 ? 'bg-orange-600' :
          'bg-slate-600'
        }`}>
          P{item.priority}
        </span>

        <button
          onClick={() => onRemove(item.id)}
          className="p-1 text-slate-500 hover:text-red-400 transition-colors"
          title="Remove from watchlist"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}

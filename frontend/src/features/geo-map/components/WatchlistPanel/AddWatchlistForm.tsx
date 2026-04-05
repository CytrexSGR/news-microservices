import { useState } from 'react';
import type { WatchlistItemCreate, WatchlistItemType } from '../../types/security.types';
import { WATCHLIST_TYPE_ICONS } from '../../types/security.types';

interface AddWatchlistFormProps {
  onAdd: (item: WatchlistItemCreate) => void;
  isLoading: boolean;
}

export function AddWatchlistForm({ onAdd, isLoading }: AddWatchlistFormProps) {
  const [itemType, setItemType] = useState<WatchlistItemType>('country');
  const [itemValue, setItemValue] = useState('');
  const [priority, setPriority] = useState(7);
  const [threshold, setThreshold] = useState(7);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!itemValue.trim()) return;

    onAdd({
      item_type: itemType,
      item_value: itemValue.trim(),
      priority,
      notify_threshold: threshold,
      notify_on_new: true,
    });

    setItemValue('');
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3 p-3 bg-slate-800/50 rounded-lg">
      <div className="flex gap-2">
        {(['country', 'entity', 'keyword', 'region'] as WatchlistItemType[]).map((type) => (
          <button
            key={type}
            type="button"
            onClick={() => setItemType(type)}
            className={`flex-1 p-2 text-xs rounded transition-colors ${
              itemType === type
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            {WATCHLIST_TYPE_ICONS[type]} {type}
          </button>
        ))}
      </div>

      <input
        type="text"
        value={itemValue}
        onChange={(e) => setItemValue(e.target.value)}
        placeholder={
          itemType === 'country' ? 'Country code (e.g., UA, RU)' :
          itemType === 'entity' ? 'Entity name (e.g., Putin)' :
          itemType === 'keyword' ? 'Keyword (e.g., nuclear)' :
          'Region name (e.g., Middle East)'
        }
        className="w-full px-3 py-2 bg-slate-700 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />

      <div className="flex gap-4">
        <div className="flex-1">
          <label className="block text-xs text-slate-400 mb-1">Priority</label>
          <input
            type="range"
            min={1}
            max={10}
            value={priority}
            onChange={(e) => setPriority(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-600 rounded-lg appearance-none cursor-pointer"
          />
          <div className="text-xs text-center mt-1">{priority}</div>
        </div>

        <div className="flex-1">
          <label className="block text-xs text-slate-400 mb-1">Alert Threshold</label>
          <input
            type="range"
            min={1}
            max={10}
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-600 rounded-lg appearance-none cursor-pointer"
          />
          <div className="text-xs text-center mt-1">{threshold}</div>
        </div>
      </div>

      <button
        type="submit"
        disabled={isLoading || !itemValue.trim()}
        className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded text-sm font-medium transition-colors"
      >
        {isLoading ? 'Adding...' : 'Add to Watchlist'}
      </button>
    </form>
  );
}

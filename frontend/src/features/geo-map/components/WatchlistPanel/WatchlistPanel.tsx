import { useState } from 'react';
import { useWatchlist, useAddWatchlistItem, useRemoveWatchlistItem } from '../../hooks/useWatchlist';
import { WatchlistItem } from './WatchlistItem';
import { AddWatchlistForm } from './AddWatchlistForm';
import type { WatchlistItemCreate } from '../../types/security.types';

export function WatchlistPanel() {
  const [showAddForm, setShowAddForm] = useState(false);
  const { data: watchlist, isLoading } = useWatchlist();
  const addMutation = useAddWatchlistItem();
  const removeMutation = useRemoveWatchlistItem();

  const handleAdd = (item: WatchlistItemCreate) => {
    addMutation.mutate(item, {
      onSuccess: () => setShowAddForm(false),
    });
  };

  const handleRemove = (id: string) => {
    if (confirm('Remove this item from your watchlist?')) {
      removeMutation.mutate(id);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <span>👁️</span> Watchlist
        </h3>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className={`p-2 rounded-lg transition-colors ${
            showAddForm ? 'bg-slate-700' : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {showAddForm ? '✕' : '+ Add'}
        </button>
      </div>

      {/* Add Form */}
      {showAddForm && (
        <AddWatchlistForm
          onAdd={handleAdd}
          isLoading={addMutation.isPending}
        />
      )}

      {/* Watchlist Items */}
      <div className="space-y-2">
        {isLoading ? (
          <div className="text-center py-8 text-slate-400">Loading...</div>
        ) : watchlist && watchlist.length > 0 ? (
          watchlist.map((item) => (
            <WatchlistItem
              key={item.id}
              item={item}
              onRemove={handleRemove}
            />
          ))
        ) : (
          <div className="text-center py-8 text-slate-400">
            <p>No items in watchlist</p>
            <p className="text-sm mt-1">Add countries, entities, or keywords to track</p>
          </div>
        )}
      </div>
    </div>
  );
}

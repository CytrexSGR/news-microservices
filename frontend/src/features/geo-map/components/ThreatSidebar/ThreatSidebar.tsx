/**
 * ThreatSidebar Component
 *
 * Security/Intelligence view sidebar showing:
 * - Threat overview statistics
 * - Top hotspot countries
 * - Recent critical events
 */

import { useState } from 'react';
import { useSecurityOverview } from '../../hooks/useSecurityData';
import { ThreatOverview } from './ThreatOverview';
import { HotspotList } from './HotspotList';
import { CriticalEventList } from './CriticalEventList';
import { CategoryBreakdown } from './CategoryBreakdown';
import { WatchlistPanel } from '../WatchlistPanel';
import { AlertBell } from '../AlertBell';
import { AnomalyPanel } from '../AnomalyPanel';
import { EntityGraph } from '../EntityGraph';

type TabId = 'overview' | 'hotspots' | 'events' | 'anomalies' | 'graph' | 'watchlist';

interface Tab {
  id: TabId;
  label: string;
  icon: string;
}

const TABS: Tab[] = [
  { id: 'overview', label: 'Overview', icon: '📊' },
  { id: 'hotspots', label: 'Hotspots', icon: '🔥' },
  { id: 'events', label: 'Events', icon: '⚡' },
  { id: 'anomalies', label: 'Anomalies', icon: '🎯' },
  { id: 'graph', label: 'Network', icon: '🕸️' },
  { id: 'watchlist', label: 'Watchlist', icon: '👁️' },
];

export function ThreatSidebar() {
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const { data: overview, isLoading, error } = useSecurityOverview(5);

  return (
    <div className="w-96 bg-slate-900 text-white flex flex-col h-full overflow-hidden border-l border-slate-700">
      {/* Header */}
      <div className="p-4 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🛡️</span>
            <div>
              <h2 className="text-lg font-bold">Security View</h2>
              <p className="text-xs text-slate-400">Intelligence Dashboard</p>
            </div>
          </div>
          <AlertBell />
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex bg-slate-800 border-b border-slate-700">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 py-2 px-3 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-slate-700 text-white border-b-2 border-blue-500'
                : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
            }`}
          >
            <span className="mr-1">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          </div>
        ) : error ? (
          <div className="p-4 text-red-400 text-center">
            <p>Failed to load security data</p>
            <p className="text-xs mt-2">{String(error)}</p>
          </div>
        ) : overview ? (
          <>
            {activeTab === 'overview' && (
              <div className="p-4 space-y-4">
                <ThreatOverview overview={overview} />
                <CategoryBreakdown byCategory={overview.by_category} />
              </div>
            )}

            {activeTab === 'hotspots' && (
              <div className="p-4">
                <HotspotList hotspots={overview.hotspots} />
              </div>
            )}

            {activeTab === 'events' && (
              <div className="p-4">
                <CriticalEventList events={overview.critical_events} />
              </div>
            )}

            {activeTab === 'anomalies' && (
              <div className="p-4">
                <AnomalyPanel />
              </div>
            )}

            {activeTab === 'graph' && (
              <div className="p-4">
                <EntityGraph />
              </div>
            )}

            {activeTab === 'watchlist' && (
              <div className="p-4">
                <WatchlistPanel />
              </div>
            )}
          </>
        ) : null}
      </div>

      {/* Footer with timestamp */}
      {overview && (
        <div className="p-3 bg-slate-800 border-t border-slate-700 text-xs text-slate-400">
          <div className="flex justify-between">
            <span>
              {new Date(overview.from_date).toLocaleDateString()} -{' '}
              {new Date(overview.to_date).toLocaleDateString()}
            </span>
            <span>{overview.total_events.toLocaleString()} events</span>
          </div>
        </div>
      )}
    </div>
  );
}

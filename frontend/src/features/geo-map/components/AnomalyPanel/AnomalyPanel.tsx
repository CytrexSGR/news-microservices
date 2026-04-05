// frontend/src/features/geo-map/components/AnomalyPanel/AnomalyPanel.tsx

import { useState } from 'react';
import { useAnomalies } from '../../hooks/useAnomalies';
import { AnomalyCard } from './AnomalyCard';

export function AnomalyPanel() {
  const [period, setPeriod] = useState<'24h' | '7d'>('24h');
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
  const { data, isLoading, error } = useAnomalies(period);

  const handleAnomalyClick = (entity: string) => {
    // Toggle selection
    if (selectedRegion === entity) {
      setSelectedRegion(null);
    } else {
      setSelectedRegion(entity);
      // Note: Region-to-countries mapping could be added here to highlight on map
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <span>🎯</span> Anomaly Detection
        </h3>
        <div className="flex gap-1 bg-slate-800 rounded p-0.5">
          <button
            onClick={() => setPeriod('24h')}
            className={`px-3 py-1 text-xs rounded transition-colors ${
              period === '24h' ? 'bg-blue-600' : 'hover:bg-slate-700'
            }`}
          >
            24h
          </button>
          <button
            onClick={() => setPeriod('7d')}
            className={`px-3 py-1 text-xs rounded transition-colors ${
              period === '7d' ? 'bg-blue-600' : 'hover:bg-slate-700'
            }`}
          >
            7d
          </button>
        </div>
      </div>

      {/* Escalating Regions Warning */}
      {data?.escalating_regions && data.escalating_regions.length > 0 && (
        <div className="p-3 bg-red-900/30 border border-red-700/50 rounded-lg">
          <div className="flex items-center gap-2 text-red-400 font-semibold mb-1">
            <span>🚨</span> Escalating Regions
          </div>
          <div className="flex flex-wrap gap-2">
            {data.escalating_regions.map((region) => (
              <span key={region} className="px-2 py-0.5 bg-red-800/50 rounded text-sm">
                {region}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Anomaly Cards */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="text-center py-8 text-slate-400">Analyzing patterns...</div>
        ) : error ? (
          <div className="text-center py-8 text-red-400">Failed to load anomaly data</div>
        ) : data?.anomalies && data.anomalies.length > 0 ? (
          data.anomalies.map((anomaly) => (
            <AnomalyCard
              key={anomaly.entity}
              anomaly={anomaly}
              isHighlighted={selectedRegion === anomaly.entity}
              onClick={() => handleAnomalyClick(anomaly.entity)}
            />
          ))
        ) : (
          <div className="text-center py-8 text-slate-400">
            <p>No significant anomalies detected</p>
            <p className="text-sm mt-1">All regions within normal activity range</p>
          </div>
        )}
      </div>

      {/* Baseline Info */}
      {data && (
        <div className="text-xs text-slate-500 text-center">
          Comparing to {data.baseline_days}-day baseline
        </div>
      )}
    </div>
  );
}

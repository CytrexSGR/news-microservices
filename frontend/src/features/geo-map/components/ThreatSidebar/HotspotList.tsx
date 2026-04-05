/**
 * HotspotList Component
 *
 * Displays top threat hotspot countries with map interaction
 */

import type { CountryThreatSummary, ThreatLevel } from '../../types/security.types';
import {
  THREAT_LEVEL_COLORS,
  CATEGORY_ICONS,
} from '../../types/security.types';
import { useGeoMapStore } from '../../store/geoMapStore';

interface HotspotListProps {
  hotspots: CountryThreatSummary[];
}

function ThreatBadge({ level }: { level: ThreatLevel }) {
  const colors: Record<ThreatLevel, string> = {
    critical: 'bg-red-500/20 text-red-400 border-red-500/50',
    high: 'bg-orange-500/20 text-orange-400 border-orange-500/50',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
    low: 'bg-green-500/20 text-green-400 border-green-500/50',
  };

  return (
    <span
      className={`px-2 py-0.5 text-xs font-medium rounded border ${colors[level]}`}
    >
      {level.toUpperCase()}
    </span>
  );
}

export function HotspotList({ hotspots }: HotspotListProps) {
  const { highlightedCountries, setHighlightedCountries, setSelectedCountry, setMapView } = useGeoMapStore();

  const handleHotspotClick = (countryCode: string) => {
    // Toggle highlight: if already highlighted, clear; otherwise set
    if (highlightedCountries.includes(countryCode)) {
      setHighlightedCountries([]);
    } else {
      setHighlightedCountries([countryCode]);
      // Also select the country to show its details
      setSelectedCountry(countryCode);
    }
  };

  const handleHotspotDoubleClick = (countryCode: string, countryName: string) => {
    // Double-click zooms to the country
    // Using approximate country centers - could be enhanced with a lookup table
    setHighlightedCountries([countryCode]);
    setSelectedCountry(countryCode);
  };

  if (hotspots.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        <p>No hotspots identified</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-300">
          Top Threat Hotspots
        </h3>
        {highlightedCountries.length > 0 && (
          <button
            onClick={() => setHighlightedCountries([])}
            className="text-xs text-slate-400 hover:text-white transition-colors"
          >
            Clear highlight
          </button>
        )}
      </div>

      {hotspots.map((hotspot, index) => {
        const isHighlighted = highlightedCountries.includes(hotspot.country_code);
        return (
        <div
          key={hotspot.country_code}
          onClick={() => handleHotspotClick(hotspot.country_code)}
          onDoubleClick={() => handleHotspotDoubleClick(hotspot.country_code, hotspot.country_name)}
          className={`bg-slate-800 rounded-lg p-3 transition-colors cursor-pointer ${
            isHighlighted
              ? 'ring-2 ring-orange-500 bg-slate-700'
              : 'hover:bg-slate-750'
          }`}
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-slate-400">
                #{index + 1}
              </span>
              <div>
                <div className="font-medium text-white">
                  {hotspot.country_name}
                </div>
                <div className="text-xs text-slate-500">
                  {hotspot.region || 'Unknown'}
                </div>
              </div>
            </div>
            <ThreatBadge level={hotspot.max_threat_level} />
          </div>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-2 mt-3">
            <div className="text-center">
              <div className="text-sm font-bold text-slate-300">
                {hotspot.total_events}
              </div>
              <div className="text-xs text-slate-500">Events</div>
            </div>
            <div className="text-center">
              <div className="text-sm font-bold text-slate-300">
                {hotspot.max_priority_score}
              </div>
              <div className="text-xs text-slate-500">Max Pri</div>
            </div>
            <div className="text-center">
              <div className="text-sm font-bold text-slate-300">
                {hotspot.avg_priority_score.toFixed(1)}
              </div>
              <div className="text-xs text-slate-500">Avg Pri</div>
            </div>
            <div className="text-center">
              <div className="text-sm font-bold text-slate-300">
                {hotspot.avg_regional_stability_risk?.toFixed(1) || '-'}
              </div>
              <div className="text-xs text-slate-500">Risk</div>
            </div>
          </div>

          {/* Category Breakdown */}
          <div className="flex gap-2 mt-3 pt-2 border-t border-slate-700">
            {hotspot.conflict_count > 0 && (
              <span className="text-xs text-slate-400">
                {CATEGORY_ICONS.CONFLICT} {hotspot.conflict_count}
              </span>
            )}
            {hotspot.security_count > 0 && (
              <span className="text-xs text-slate-400">
                {CATEGORY_ICONS.SECURITY} {hotspot.security_count}
              </span>
            )}
            {hotspot.humanitarian_count > 0 && (
              <span className="text-xs text-slate-400">
                {CATEGORY_ICONS.HUMANITARIAN} {hotspot.humanitarian_count}
              </span>
            )}
            {hotspot.politics_count > 0 && (
              <span className="text-xs text-slate-400">
                {CATEGORY_ICONS.POLITICS} {hotspot.politics_count}
              </span>
            )}
          </div>

          {/* Last Event */}
          {hotspot.last_event_at && (
            <div className="text-xs text-slate-500 mt-2">
              Last: {new Date(hotspot.last_event_at).toLocaleString()}
            </div>
          )}
        </div>
        );
      })}
    </div>
  );
}

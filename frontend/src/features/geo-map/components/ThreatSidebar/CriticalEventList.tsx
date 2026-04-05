/**
 * CriticalEventList Component
 *
 * Displays recent critical security events with map interaction
 */

import type { SecurityEvent, ThreatLevel } from '../../types/security.types';
import { CATEGORY_ICONS } from '../../types/security.types';
import { useGeoMapStore } from '../../store/geoMapStore';

interface CriticalEventListProps {
  events: SecurityEvent[];
}

function ThreatIndicator({ level }: { level: ThreatLevel }) {
  const colors: Record<ThreatLevel, string> = {
    critical: 'bg-red-500',
    high: 'bg-orange-500',
    medium: 'bg-yellow-500',
    low: 'bg-green-500',
  };

  return (
    <div
      className={`w-2 h-2 rounded-full ${colors[level]} animate-pulse`}
      title={level}
    />
  );
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export function CriticalEventList({ events }: CriticalEventListProps) {
  const { highlightedCountries, setHighlightedCountries, setSelectedCountry } = useGeoMapStore();

  const handleEventClick = (event: SecurityEvent) => {
    // Highlight the primary country and any involved countries
    const allCountries = [event.country_code, ...event.countries_involved].filter(Boolean);

    // Toggle: if primary country already highlighted, clear
    if (highlightedCountries.includes(event.country_code)) {
      setHighlightedCountries([]);
    } else {
      setHighlightedCountries(allCountries);
      setSelectedCountry(event.country_code);
    }
  };

  if (events.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        <p>No critical events in timeframe</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-300">Critical Events</h3>
        <div className="flex items-center gap-2">
          {highlightedCountries.length > 0 && (
            <button
              onClick={() => setHighlightedCountries([])}
              className="text-xs text-slate-400 hover:text-white transition-colors"
            >
              Clear
            </button>
          )}
          <span className="text-xs text-red-400">
            {events.length} critical
          </span>
        </div>
      </div>

      {events.map((event) => {
        const isHighlighted = highlightedCountries.includes(event.country_code);
        return (
        <div
          key={event.id}
          onClick={() => handleEventClick(event)}
          className={`bg-slate-800 rounded-lg p-3 transition-colors cursor-pointer border-l-2 ${
            isHighlighted
              ? 'border-orange-500 ring-2 ring-orange-500/50 bg-slate-700'
              : 'border-red-500 hover:bg-slate-750'
          }`}
        >
          {/* Header */}
          <div className="flex items-start gap-2">
            <ThreatIndicator level={event.threat_level} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs px-1.5 py-0.5 bg-slate-700 rounded text-slate-400">
                  {event.category}
                </span>
                <span className="text-xs text-slate-500">
                  Pri: {event.priority_score}
                </span>
              </div>
              <h4 className="text-sm font-medium text-white line-clamp-2">
                {event.title}
              </h4>
            </div>
          </div>

          {/* Location & Time */}
          <div className="flex items-center justify-between mt-2 text-xs text-slate-500">
            <span>
              📍 {event.country_name} ({event.country_code})
            </span>
            <span>
              {event.published_at ? formatTimeAgo(event.published_at) : 'Unknown'}
            </span>
          </div>

          {/* Metrics */}
          {(event.conflict_severity || event.regional_stability_risk) && (
            <div className="flex gap-3 mt-2 pt-2 border-t border-slate-700">
              {event.conflict_severity && (
                <span className="text-xs text-slate-400">
                  Severity: {event.conflict_severity.toFixed(1)}
                </span>
              )}
              {event.regional_stability_risk && (
                <span className="text-xs text-slate-400">
                  Risk: {event.regional_stability_risk.toFixed(1)}
                </span>
              )}
            </div>
          )}

          {/* Propaganda Warning */}
          {event.propaganda_detected && (
            <div className="mt-2 flex items-center gap-1 text-xs text-amber-400">
              <span>⚠️</span>
              <span>Propaganda indicators detected</span>
            </div>
          )}

          {/* Countries Involved */}
          {event.countries_involved.length > 0 && (
            <div className="mt-2 text-xs text-slate-500">
              Involves: {event.countries_involved.slice(0, 4).join(', ')}
              {event.countries_involved.length > 4 && ` +${event.countries_involved.length - 4} more`}
            </div>
          )}
        </div>
        );
      })}
    </div>
  );
}

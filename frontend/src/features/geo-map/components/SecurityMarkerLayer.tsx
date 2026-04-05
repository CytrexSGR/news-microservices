/**
 * SecurityMarkerLayer Component
 *
 * Renders security threat markers on the map with threat-level styling
 */

import { CircleMarker, Popup, Tooltip } from 'react-leaflet';
import type { SecurityMarker, ThreatLevel } from '../types/security.types';
import { THREAT_LEVEL_COLORS, CATEGORY_ICONS } from '../types/security.types';

interface SecurityMarkerLayerProps {
  markers: SecurityMarker[];
  onMarkerClick?: (marker: SecurityMarker) => void;
}

function getMarkerRadius(priorityScore: number): number {
  // Scale from 6 (low priority) to 14 (critical)
  if (priorityScore >= 9) return 14;
  if (priorityScore >= 7) return 11;
  if (priorityScore >= 5) return 8;
  return 6;
}

function getMarkerOpacity(threatLevel: ThreatLevel): number {
  switch (threatLevel) {
    case 'critical':
      return 0.9;
    case 'high':
      return 0.8;
    case 'medium':
      return 0.7;
    default:
      return 0.6;
  }
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffHours < 1) return 'Just now';
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export function SecurityMarkerLayer({
  markers,
  onMarkerClick,
}: SecurityMarkerLayerProps) {
  return (
    <>
      {markers.map((marker) => {
        const color = THREAT_LEVEL_COLORS[marker.threat_level];
        const radius = getMarkerRadius(marker.priority_score);
        const opacity = getMarkerOpacity(marker.threat_level);
        const icon =
          CATEGORY_ICONS[marker.category as keyof typeof CATEGORY_ICONS] || '📍';

        return (
          <CircleMarker
            key={marker.id}
            center={[marker.lat, marker.lon]}
            radius={radius}
            pathOptions={{
              color: color,
              fillColor: color,
              fillOpacity: opacity,
              weight: marker.threat_level === 'critical' ? 3 : 2,
            }}
            eventHandlers={{
              click: () => onMarkerClick?.(marker),
            }}
          >
            {/* Tooltip on hover */}
            <Tooltip direction="top" offset={[0, -10]} opacity={0.95}>
              <div className="text-xs">
                <div className="font-bold">{marker.country_code}</div>
                <div className="text-gray-600">
                  {marker.threat_level.toUpperCase()} • Pri: {marker.priority_score}
                </div>
              </div>
            </Tooltip>

            {/* Popup on click */}
            <Popup>
              <div className="min-w-[280px] max-w-[320px]">
                {/* Header */}
                <div className="flex items-start gap-2 mb-2">
                  <span className="text-xl">{icon}</span>
                  <div className="flex-1">
                    <span
                      className="inline-block px-2 py-0.5 text-xs font-medium rounded"
                      style={{
                        backgroundColor: `${color}20`,
                        color: color,
                        border: `1px solid ${color}50`,
                      }}
                    >
                      {marker.threat_level.toUpperCase()}
                    </span>
                    <span className="ml-2 text-xs text-gray-500">
                      Priority: {marker.priority_score}/10
                    </span>
                  </div>
                </div>

                {/* Title */}
                <h3 className="font-semibold text-sm mb-2 line-clamp-2">
                  {marker.title}
                </h3>

                {/* Location */}
                <div className="text-xs text-gray-600 mb-2">
                  📍 {marker.country_code} • {marker.category}
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-2 text-xs bg-gray-50 p-2 rounded mb-2">
                  {marker.conflict_severity && (
                    <div>
                      <span className="text-gray-500">Severity:</span>{' '}
                      <span className="font-medium">
                        {marker.conflict_severity.toFixed(1)}
                      </span>
                    </div>
                  )}
                  {marker.impact_score && (
                    <div>
                      <span className="text-gray-500">Impact:</span>{' '}
                      <span className="font-medium">
                        {marker.impact_score.toFixed(1)}
                      </span>
                    </div>
                  )}
                  {marker.dominant_frame && (
                    <div>
                      <span className="text-gray-500">Frame:</span>{' '}
                      <span className="font-medium capitalize">
                        {marker.dominant_frame}
                      </span>
                    </div>
                  )}
                </div>

                {/* Propaganda Warning */}
                {marker.propaganda_detected && (
                  <div className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded mb-2">
                    ⚠️ Propaganda indicators detected
                  </div>
                )}

                {/* Timestamp */}
                <div className="text-xs text-gray-400">
                  {formatTimeAgo(marker.first_seen)}
                </div>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </>
  );
}

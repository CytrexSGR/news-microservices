import { MapContainer, TileLayer, ZoomControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

import { useGeoMapStore } from '../store/geoMapStore';
import { useMapGeoJSON, useMarkers } from '../hooks/useGeoData';
import { useSecurityMarkers } from '../hooks/useSecurityData';
import { useGeoWebSocket } from '../hooks/useGeoWebSocket';
import { CountryLayer } from './CountryLayer';
import { MarkerLayer } from './MarkerLayer';
import { SecurityMarkerLayer } from './SecurityMarkerLayer';
import { MapControls } from './MapControls';
import { NewsSidebar } from './NewsSidebar/NewsSidebar';
import { ThreatSidebar } from './ThreatSidebar';

export function MapVisualization() {
  const {
    mapCenter,
    mapZoom,
    viewMode,
    selectedCountry,
    securityViewEnabled,
    securityMinPriority,
  } = useGeoMapStore();
  const { data: geoJSON, isLoading: loadingGeo } = useMapGeoJSON();
  const { data: markers } = useMarkers();
  const { data: securityMarkers } = useSecurityMarkers(securityMinPriority);

  // Connect to WebSocket for real-time updates
  useGeoWebSocket();

  if (loadingGeo) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="flex h-full">
      {/* Map Container */}
      <div className="flex-1 relative">
        <MapContainer
          center={mapCenter}
          zoom={mapZoom}
          className="h-full w-full"
          zoomControl={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Country polygons with coloring */}
          {geoJSON && viewMode === 'countries' && (
            <CountryLayer geoJSON={geoJSON} />
          )}

          {/* Article markers (normal view) */}
          {!securityViewEnabled && markers && viewMode === 'countries' && (
            <MarkerLayer markers={markers} />
          )}

          {/* Security markers (security view) */}
          {securityViewEnabled && securityMarkers && (
            <SecurityMarkerLayer markers={securityMarkers} />
          )}

          <ZoomControl position="bottomright" />
        </MapContainer>

        {/* Controls overlay */}
        <MapControls />
      </div>

      {/* Sidebar: News (normal) or Threat (security view) */}
      {securityViewEnabled ? (
        <ThreatSidebar />
      ) : (
        selectedCountry && <NewsSidebar />
      )}
    </div>
  );
}

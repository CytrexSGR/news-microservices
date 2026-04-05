/**
 * GeoMapPage - Interactive News Map Page
 *
 * Displays an interactive world map for visualizing geopolitical news events.
 * Uses Leaflet for mapping with country-level granularity.
 */

import { MapVisualization } from '@/features/geo-map/components/MapVisualization';
import { NewsSidebar } from '@/features/geo-map/components/NewsSidebar';
import { useGeoMapStore } from '@/features/geo-map/store/geoMapStore';

export function GeoMapPage() {
  const selectedCountry = useGeoMapStore((state) => state.selectedCountry);

  return (
    <div className="flex h-[calc(100vh-4rem)] w-full">
      {/* Main Map Area */}
      <div className="flex-1 relative">
        <MapVisualization />
      </div>

      {/* News Sidebar - shows when country is selected */}
      {selectedCountry && (
        <div className="w-96 border-l border-border bg-card overflow-hidden">
          <NewsSidebar />
        </div>
      )}
    </div>
  );
}

export default GeoMapPage;

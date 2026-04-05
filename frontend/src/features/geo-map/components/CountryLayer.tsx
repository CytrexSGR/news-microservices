import { GeoJSON } from 'react-leaflet';
import type { Feature, GeoJsonObject } from 'geojson';
import type { PathOptions, Layer, LeafletMouseEvent } from 'leaflet';

import { useGeoMapStore } from '../store/geoMapStore';

interface Props {
  geoJSON: GeoJsonObject;
}

export function CountryLayer({ geoJSON }: Props) {
  const { selectedCountry, setSelectedCountry, highlightedCountries } = useGeoMapStore();

  const getStyle = (feature?: Feature): PathOptions => {
    const isoCode = feature?.properties?.iso_code;
    const articleCount = feature?.properties?.article_count || 0;
    const isHighlighted = highlightedCountries.includes(isoCode);
    const isSelected = isoCode === selectedCountry;

    // Highlighted countries get orange/amber glow
    if (isHighlighted) {
      return {
        fillColor: 'rgba(251, 146, 60, 0.5)',  // Orange highlight
        fillOpacity: 0.8,
        color: '#f97316',  // Orange border
        weight: 4,
        dashArray: '5, 5',  // Dashed border for visibility
      };
    }

    // Color intensity based on article count
    const intensity = Math.min(articleCount / 100, 1);
    const fillColor = articleCount > 0
      ? `rgba(59, 130, 246, ${0.2 + intensity * 0.6})`  // Blue gradient
      : 'rgba(200, 200, 200, 0.2)';  // Gray for no articles

    return {
      fillColor,
      fillOpacity: 0.7,
      color: isSelected ? '#1d4ed8' : '#666',
      weight: isSelected ? 3 : 1,
    };
  };

  const onEachFeature = (feature: Feature, layer: Layer) => {
    const props = feature.properties;
    const isoCode = props?.iso_code;

    layer.bindTooltip(
      `<strong>${props?.name}</strong><br/>Articles: ${props?.article_count || 0}`,
      { sticky: true }
    );

    layer.on({
      click: () => {
        setSelectedCountry(isoCode || null);
      },
      mouseover: (e: LeafletMouseEvent) => {
        const target = e.target;
        // Don't override highlight styling on hover
        if (!highlightedCountries.includes(isoCode)) {
          target.setStyle({ weight: 2, color: '#1d4ed8' });
        }
      },
      mouseout: (e: LeafletMouseEvent) => {
        const target = e.target;
        // Restore appropriate style based on state
        if (highlightedCountries.includes(isoCode)) {
          target.setStyle({ weight: 4, color: '#f97316', dashArray: '5, 5' });
        } else if (isoCode !== selectedCountry) {
          target.setStyle({ weight: 1, color: '#666', dashArray: undefined });
        }
      },
    });
  };

  return (
    <GeoJSON
      key={`geo-${highlightedCountries.join('-')}-${selectedCountry}`}
      data={geoJSON}
      style={getStyle}
      onEachFeature={onEachFeature}
    />
  );
}

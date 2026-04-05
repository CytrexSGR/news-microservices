import { CircleMarker, Popup } from 'react-leaflet';
import type { MapMarker } from '../types/geo.types';

interface Props {
  markers: MapMarker[];
}

export function MarkerLayer({ markers }: Props) {
  return (
    <>
      {markers.map((marker) => (
        <CircleMarker
          key={marker.id}
          center={[marker.lat, marker.lon]}
          radius={8}
          pathOptions={{
            color: '#dc2626',
            fillColor: '#ef4444',
            fillOpacity: 0.8,
          }}
        >
          <Popup>
            <div className="p-2">
              <p className="font-medium text-sm">{marker.title || 'Article'}</p>
              <p className="text-xs text-gray-500">{marker.country_code}</p>
              {marker.category && (
                <span className="inline-block mt-1 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded">
                  {marker.category}
                </span>
              )}
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </>
  );
}

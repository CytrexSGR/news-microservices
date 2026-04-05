import { useQuery } from '@tanstack/react-query';
import { useGlobeStore } from '../store/globeStore';
import { useEffect } from 'react';
import type { SpatialEntity } from '../types/globe.types';

export function useGeoData() {
  const upsertEntities = useGlobeStore((s) => s.upsertEntities);

  const { data: markers } = useQuery({
    queryKey: ['globe-markers'],
    queryFn: async () => {
      const res = await fetch('/api/geo/map/markers?limit=200');
      if (!res.ok) throw new Error('Failed to fetch markers');
      return res.json();
    },
    refetchInterval: 60_000,
  });

  useEffect(() => {
    if (!markers?.length) return;
    const entities: SpatialEntity[] = markers.map((m: any) => ({
      id: `marker-${m.id || m.article_id}`,
      type: 'news-events' as const,
      lat: m.lat,
      lon: m.lon,
      label: m.title || '',
      metadata: m,
      timestamp: Date.now(),
    }));
    upsertEntities(entities);
  }, [markers, upsertEntities]);
}

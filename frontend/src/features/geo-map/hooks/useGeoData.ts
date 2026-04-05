import { useQuery } from '@tanstack/react-query';
import { geoApi } from '../api/geoApi';
import { useGeoMapStore } from '../store/geoMapStore';

export function useCountries() {
  const { filters } = useGeoMapStore();
  const region = filters.regions.length === 1 ? filters.regions[0] : undefined;

  return useQuery({
    queryKey: ['geo', 'countries', region],
    queryFn: () => geoApi.getCountries(region),
    staleTime: 60_000,
  });
}

export function useMapGeoJSON() {
  const { filters } = useGeoMapStore();

  return useQuery({
    queryKey: ['geo', 'map', 'geojson', filters.timeRange],
    queryFn: () => {
      const fromDate = getFromDate(filters.timeRange);
      return geoApi.getMapGeoJSON(fromDate);
    },
    staleTime: 60_000,
  });
}

export function useMarkers() {
  const { filters } = useGeoMapStore();
  const region = filters.regions.length === 1 ? filters.regions[0] : undefined;
  const categories = filters.categories.length > 0 ? filters.categories : undefined;

  return useQuery({
    queryKey: ['geo', 'markers', filters.timeRange, region, categories],
    queryFn: () => geoApi.getMarkers(filters.timeRange, region, categories),
    staleTime: 30_000,
  });
}

export function useCategories() {
  return useQuery({
    queryKey: ['geo', 'categories'],
    queryFn: () => geoApi.getCategories(),
    staleTime: 300_000, // 5 minutes - categories don't change often
  });
}

export function useCountryDetail(isoCode: string | null) {
  return useQuery({
    queryKey: ['geo', 'country', isoCode],
    queryFn: () => (isoCode ? geoApi.getCountry(isoCode) : null),
    enabled: !!isoCode,
  });
}

export function useCountryArticles(isoCode: string | null, limit = 20) {
  return useQuery({
    queryKey: ['geo', 'country', isoCode, 'articles', limit],
    queryFn: () => (isoCode ? geoApi.getCountryArticles(isoCode, limit) : []),
    enabled: !!isoCode,
    staleTime: 30_000,
  });
}

export function useRegions() {
  return useQuery({
    queryKey: ['geo', 'regions'],
    queryFn: () => geoApi.getRegions(),
    staleTime: 300_000,
  });
}

function getFromDate(timeRange: string): Date {
  const now = new Date();
  switch (timeRange) {
    case 'today':
      return new Date(now.setHours(0, 0, 0, 0));
    case '7d':
      return new Date(now.setDate(now.getDate() - 7));
    case '30d':
      return new Date(now.setDate(now.getDate() - 30));
    default:
      return new Date(now.setDate(now.getDate() - 7));
  }
}

import { create } from 'zustand';
import type { GeoFilters, ViewMode } from '../types/geo.types';

interface GeoMapStore {
  viewMode: ViewMode;
  setViewMode: (mode: ViewMode) => void;
  selectedCountry: string | null;
  setSelectedCountry: (code: string | null) => void;
  filters: GeoFilters;
  setFilters: (filters: Partial<GeoFilters>) => void;
  mapCenter: [number, number];
  mapZoom: number;
  setMapView: (center: [number, number], zoom: number) => void;
  newArticleIds: string[];
  addNewArticle: (id: string) => void;
  clearNewArticles: () => void;
  // Security View
  securityViewEnabled: boolean;
  setSecurityViewEnabled: (enabled: boolean) => void;
  securityMinPriority: number;
  setSecurityMinPriority: (priority: number) => void;
  // Highlight state for sidebar-to-map interaction
  highlightedCountries: string[];
  setHighlightedCountries: (codes: string[]) => void;
  addHighlightedCountry: (code: string) => void;
  removeHighlightedCountry: (code: string) => void;
  clearHighlightedCountries: () => void;
  highlightedEntity: string | null;
  setHighlightedEntity: (entity: string | null) => void;
}

export const useGeoMapStore = create<GeoMapStore>((set) => ({
  viewMode: 'countries',
  setViewMode: (mode) => set({ viewMode: mode }),
  selectedCountry: null,
  setSelectedCountry: (code) => set({ selectedCountry: code }),
  filters: {
    timeRange: '7d',
    regions: [],
    categories: [],
  },
  setFilters: (newFilters) =>
    set((state) => ({
      filters: { ...state.filters, ...newFilters },
    })),
  mapCenter: [50, 10],
  mapZoom: 4,
  setMapView: (center, zoom) => set({ mapCenter: center, mapZoom: zoom }),
  newArticleIds: [],
  addNewArticle: (id) =>
    set((state) => ({
      newArticleIds: [...state.newArticleIds.slice(-99), id],
    })),
  clearNewArticles: () => set({ newArticleIds: [] }),
  // Security View
  securityViewEnabled: false,
  setSecurityViewEnabled: (enabled) => set({ securityViewEnabled: enabled }),
  securityMinPriority: 6,
  setSecurityMinPriority: (priority) => set({ securityMinPriority: priority }),
  // Highlight state for sidebar-to-map interaction
  highlightedCountries: [],
  setHighlightedCountries: (codes) => set({ highlightedCountries: codes }),
  addHighlightedCountry: (code) =>
    set((state) => ({
      highlightedCountries: state.highlightedCountries.includes(code)
        ? state.highlightedCountries
        : [...state.highlightedCountries, code],
    })),
  removeHighlightedCountry: (code) =>
    set((state) => ({
      highlightedCountries: state.highlightedCountries.filter((c) => c !== code),
    })),
  clearHighlightedCountries: () => set({ highlightedCountries: [] }),
  highlightedEntity: null,
  setHighlightedEntity: (entity) => set({ highlightedEntity: entity }),
}));

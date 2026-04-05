import axios from 'axios';
import type { Country, MapMarker } from '../types/geo.types';

// Use dynamic host detection for network access
const getApiBase = () => {
  const hostname = window.location.hostname;
  const port = 8115;
  const protocol = window.location.protocol;
  return `${protocol}//${hostname}:${port}/api/v1`;
};

const API_BASE = getApiBase();

export const geoApi = {
  async getCountries(region?: string): Promise<Country[]> {
    const params = region ? { region } : {};
    const { data } = await axios.get(`${API_BASE}/geo/countries`, { params });
    return data;
  },

  async getCountry(isoCode: string) {
    const { data } = await axios.get(`${API_BASE}/geo/countries/${isoCode}`);
    return data;
  },

  async getCountryArticles(isoCode: string, limit = 20) {
    const { data } = await axios.get(
      `${API_BASE}/geo/countries/${isoCode}/articles`,
      { params: { limit } }
    );
    // API returns { articles: [...], pagination: {...} }
    return data.articles || [];
  },

  async getMapGeoJSON(fromDate?: Date, toDate?: Date) {
    const params: Record<string, string> = {};
    if (fromDate) params.from_date = fromDate.toISOString();
    if (toDate) params.to_date = toDate.toISOString();
    const { data } = await axios.get(`${API_BASE}/geo/map/countries`, { params });
    return data;
  },

  async getMarkers(
    timeRange?: string,
    region?: string,
    categories?: string[],
    limit = 100
  ): Promise<MapMarker[]> {
    const params: Record<string, unknown> = { limit };
    if (timeRange) params.time_range = timeRange;
    if (region) params.region = region;
    if (categories && categories.length > 0) {
      params.categories = categories.join(',');
    }
    const { data } = await axios.get(`${API_BASE}/geo/map/markers`, { params });
    return data;
  },

  async getHeatmapData(fromDate?: Date) {
    const params = fromDate ? { from_date: fromDate.toISOString() } : {};
    const { data } = await axios.get(`${API_BASE}/geo/map/heatmap`, { params });
    return data;
  },

  async getRegions() {
    const { data } = await axios.get(`${API_BASE}/geo/filters/regions`);
    return data;
  },

  async getCategories() {
    const { data } = await axios.get(`${API_BASE}/geo/filters/categories`);
    return data;
  },
};

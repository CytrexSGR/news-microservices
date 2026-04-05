/**
 * Security View API Client
 *
 * Provides access to Security View endpoints in geolocation-service
 * Base URL: http://{hostname}:8115/api/v1/geo/security
 */

import axios from 'axios';
import type {
  SecurityOverview,
  SecurityEventList,
  CountryThreatSummary,
  CountryThreatDetail,
  SecurityMarker,
  SecurityFilters,
} from '../types/security.types';

// =============================================================================
// Configuration
// =============================================================================

const getApiBase = () => {
  const hostname = window.location.hostname;
  const port = 8115;
  const protocol = window.location.protocol;
  return `${protocol}//${hostname}:${port}/api/v1/geo/security`;
};

const API_BASE = getApiBase();

// =============================================================================
// API Functions
// =============================================================================

export const securityApi = {
  /**
   * Get global security overview for dashboard
   */
  async getOverview(
    days: number = 7,
    minPriority: number = 5
  ): Promise<SecurityOverview> {
    const { data } = await axios.get(`${API_BASE}/overview`, {
      params: { days, min_priority: minPriority },
    });
    return data;
  },

  /**
   * Get paginated security events with filters
   */
  async getEvents(filters: Partial<SecurityFilters> & {
    page?: number;
    per_page?: number;
  } = {}): Promise<SecurityEventList> {
    const params: Record<string, unknown> = {
      days: filters.days ?? 7,
      min_priority: filters.min_priority ?? 5,
      page: filters.page ?? 1,
      per_page: filters.per_page ?? 50,
    };

    if (filters.category) params.category = filters.category;
    if (filters.country) params.country = filters.country;
    if (filters.region) params.region = filters.region;
    if (filters.threat_level) params.threat_level = filters.threat_level;

    const { data } = await axios.get(`${API_BASE}/events`, { params });
    return data;
  },

  /**
   * Get aggregated threat data per country
   */
  async getCountryThreats(
    days: number = 7,
    minPriority: number = 5,
    region?: string,
    minEvents: number = 1,
    limit: number = 50
  ): Promise<CountryThreatSummary[]> {
    const params: Record<string, unknown> = {
      days,
      min_priority: minPriority,
      min_events: minEvents,
      limit,
    };
    if (region) params.region = region;

    const { data } = await axios.get(`${API_BASE}/countries`, { params });
    return data;
  },

  /**
   * Get detailed threat profile for single country
   */
  async getCountryDetail(
    isoCode: string,
    days: number = 7
  ): Promise<CountryThreatDetail> {
    const { data } = await axios.get(`${API_BASE}/country/${isoCode}`, {
      params: { days },
    });
    return data;
  },

  /**
   * Get security markers for map visualization
   */
  async getMarkers(
    days: number = 7,
    minPriority: number = 6,
    categories?: string[],
    region?: string,
    limit: number = 200
  ): Promise<SecurityMarker[]> {
    const params: Record<string, unknown> = {
      days,
      min_priority: minPriority,
      limit,
    };
    if (categories && categories.length > 0) {
      params.categories = categories.join(',');
    }
    if (region) params.region = region;

    const { data } = await axios.get(`${API_BASE}/markers`, { params });
    return data;
  },
};

export default securityApi;

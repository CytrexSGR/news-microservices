// frontend/src/features/intelligence/bursts/api/burstApi.ts

/**
 * Burst Detection API Client
 * Connects to clustering-service Bursts API (Port 8122)
 */

import { createApiClient } from '@/shared/api';
import type {
  BurstListResponse,
  BurstListParams,
  BurstStats,
  BurstAlert,
  AcknowledgeResponse,
} from '../types';

// =============================================================================
// Configuration
// =============================================================================

const getBaseUrl = () => {
  if (import.meta.env.VITE_CLUSTERING_API_URL) {
    return import.meta.env.VITE_CLUSTERING_API_URL;
  }
  const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  return `http://${hostname}:8122/api/v1`;
};

const BURSTS_BASE_URL = getBaseUrl();

export const burstApi = createApiClient(BURSTS_BASE_URL);

// =============================================================================
// API Functions
// =============================================================================

/**
 * List burst alerts with pagination and filtering
 */
export async function getBursts(params: BurstListParams = {}): Promise<BurstListResponse> {
  const { hours = 24, severity, category, limit = 50, offset = 0 } = params;
  const queryParams = new URLSearchParams();
  queryParams.append('hours', String(hours));
  queryParams.append('limit', String(limit));
  queryParams.append('offset', String(offset));
  if (severity) {
    queryParams.append('severity', severity);
  }
  if (category) {
    queryParams.append('category', category);
  }

  const response = await burstApi.get<BurstListResponse>(`/bursts?${queryParams}`);
  return response.data;
}

/**
 * List active (unacknowledged) burst alerts
 */
export async function getActiveBursts(params: BurstListParams = {}): Promise<BurstListResponse> {
  const { hours = 24, severity, category, limit = 50, offset = 0 } = params;
  const queryParams = new URLSearchParams();
  queryParams.append('hours', String(hours));
  queryParams.append('limit', String(limit));
  queryParams.append('offset', String(offset));
  if (severity) {
    queryParams.append('severity', severity);
  }
  if (category) {
    queryParams.append('category', category);
  }

  const response = await burstApi.get<BurstListResponse>(`/bursts/active?${queryParams}`);
  return response.data;
}

/**
 * Get burst statistics
 */
export async function getBurstStats(): Promise<BurstStats> {
  const response = await burstApi.get<BurstStats>('/bursts/stats');
  return response.data;
}

/**
 * Get specific burst alert
 */
export async function getBurstById(id: string): Promise<BurstAlert> {
  const response = await burstApi.get<BurstAlert>(`/bursts/${id}`);
  return response.data;
}

/**
 * Acknowledge a burst alert
 */
export async function acknowledgeBurst(id: string): Promise<AcknowledgeResponse> {
  const response = await burstApi.post<AcknowledgeResponse>(`/bursts/${id}/acknowledge`, {});
  return response.data;
}

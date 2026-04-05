/**
 * SITREP Service API Client
 *
 * Provides access to SITREP (Situation Report) endpoints for generating
 * and retrieving AI-powered intelligence briefings.
 *
 * Base URL: http://localhost:8123/api/v1
 */

import { createApiClient } from '@/shared/api';
import type {
  Sitrep,
  SitrepListResponse,
  SitrepListParams,
  SitrepGenerateRequest,
  SitrepGenerateResponse,
} from '../types/sitrep.types';

// =============================================================================
// Configuration
// =============================================================================

/**
 * SITREP Service base URL
 * Uses the same hostname as the frontend to support remote access
 */
const getBaseUrl = () => {
  if (import.meta.env.VITE_SITREP_API_URL) {
    return import.meta.env.VITE_SITREP_API_URL;
  }
  // Use same hostname as frontend for remote access support
  const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  return `http://${hostname}:8123/api/v1`;
};

const SITREP_BASE_URL = getBaseUrl();

/**
 * SITREP API client instance
 */
export const sitrepApi = createApiClient(SITREP_BASE_URL);

// =============================================================================
// API Functions
// =============================================================================

/**
 * Get list of SITREPs with pagination
 */
export async function getSitreps(params: SitrepListParams = {}): Promise<SitrepListResponse> {
  const { limit = 20, offset = 0, report_type, category } = params;
  const queryParams = new URLSearchParams();
  queryParams.append('limit', String(limit));
  queryParams.append('offset', String(offset));
  if (report_type) {
    queryParams.append('report_type', report_type);
  }
  if (category) {
    queryParams.append('category', category);
  }

  const response = await sitrepApi.get<SitrepListResponse>(`/sitreps?${queryParams}`);
  return response.data;
}

/**
 * Get single SITREP by ID
 */
export async function getSitrepById(id: string): Promise<Sitrep> {
  const response = await sitrepApi.get<Sitrep>(`/sitreps/${id}`);
  return response.data;
}

/**
 * Get the latest SITREP
 */
export async function getLatestSitrep(reportType: string = 'daily'): Promise<Sitrep> {
  const response = await sitrepApi.get<Sitrep>(`/sitreps/latest?report_type=${reportType}`);
  return response.data;
}

/**
 * Generate a new SITREP
 */
export async function generateSitrep(request: SitrepGenerateRequest): Promise<SitrepGenerateResponse> {
  const response = await sitrepApi.post<SitrepGenerateResponse>('/sitreps/generate', request);
  return response.data;
}

/**
 * Mark a SITREP as reviewed
 */
export async function markSitrepReviewed(id: string, reviewed: boolean = true): Promise<Sitrep> {
  const response = await sitrepApi.patch<Sitrep>(`/sitreps/${id}/review?reviewed=${reviewed}`);
  return response.data;
}

/**
 * Delete a SITREP
 */
export async function deleteSitrep(id: string): Promise<void> {
  await sitrepApi.delete(`/sitreps/${id}`);
}

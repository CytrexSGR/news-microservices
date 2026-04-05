/**
 * Narrative Service API Client
 *
 * Provides access to Narrative Service endpoints for frame analysis,
 * bias detection, and sentiment analysis.
 *
 * Base URL: http://localhost:8119/api/v1
 */

import { createApiClient } from '@/shared/api';

// =============================================================================
// Configuration
// =============================================================================

/**
 * Narrative Service base URL
 * Note: Backend routes are under /api/v1/narrative/...
 * Uses window.location.hostname to work from any client (localhost or remote IP)
 */
const NARRATIVE_BASE_URL =
  import.meta.env.VITE_NARRATIVE_API_URL ||
  `http://${window.location.hostname}:8119/api/v1/narrative`;

/**
 * Narrative API client instance
 */
export const narrativeApi = createApiClient(NARRATIVE_BASE_URL);

// =============================================================================
// Types
// =============================================================================

export interface NarrativeOverviewParams {
  days?: number;
  include_recent?: boolean;
  max_recent?: number;
}

/**
 * Response from /api/v1/narrative/overview endpoint
 * Matches backend schema: NarrativeOverviewResponse
 */
export interface NarrativeOverviewResponse {
  total_frames: number;
  total_clusters: number;
  frame_distribution: Record<string, number>;
  bias_distribution: Record<string, number>;
  avg_bias_score: number;
  avg_sentiment: number;
  top_narratives: Array<{
    id: string;
    name: string;
    dominant_frame: string;
    frame_count: number;
    bias_score: number | null;
    keywords: string[];
    entities: Record<string, string[]> | null;
    sentiment: number | null;
    perspectives: Record<string, unknown> | null;
    is_active: boolean;
    created_at: string;
    updated_at: string;
  }>;
  timestamp: string;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Fetch narrative dashboard overview
 */
export async function fetchNarrativeOverview(
  params: NarrativeOverviewParams = {}
): Promise<NarrativeOverviewResponse> {
  const { days = 7, include_recent = true, max_recent = 10 } = params;

  const queryParams = new URLSearchParams();
  queryParams.append('days', String(days));
  queryParams.append('include_recent', String(include_recent));
  queryParams.append('max_recent', String(max_recent));

  try {
    const response = await narrativeApi.get<NarrativeOverviewResponse>(
      `/overview?${queryParams}`
    );
    return response.data;
  } catch (error) {
    // Return empty data structure if service is not available
    console.warn('Narrative service not available:', error);
    return {
      total_frames: 0,
      total_clusters: 0,
      frame_distribution: {},
      bias_distribution: {},
      avg_bias_score: 0,
      avg_sentiment: 0,
      top_narratives: [],
      timestamp: new Date().toISOString(),
    };
  }
}

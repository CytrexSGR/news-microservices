/**
 * SITREP Feature Exports
 *
 * Central export file for the SITREP (Situation Report) feature.
 */

// Pages
export { SitrepListPage } from './pages/SitrepListPage';
export { SitrepDetailPage } from './pages/SitrepDetailPage';

// API
export { sitrepApi, getSitreps, getSitrepById, getLatestSitrep, generateSitrep, markSitrepReviewed, deleteSitrep } from './api/sitrepApi';
export { useSitreps, useSitrep, useLatestSitrep, useGenerateSitrep, useMarkSitrepReviewed, useDeleteSitrep, sitrepKeys } from './api/useSitreps';

// Types
export type {
  Sitrep,
  SitrepListResponse,
  SitrepListParams,
  SitrepGenerateRequest,
  SitrepGenerateResponse,
  KeyDevelopment,
  TopStory,
  KeyEntity,
  SentimentSummary,
  EmergingSignal,
  RiskAssessment,
} from './types/sitrep.types';

/**
 * Content Analysis API Client
 *
 * Provides access to article analysis endpoints for entity extraction,
 * sentiment analysis, and content processing.
 *
 * Base URL: http://localhost:8101/api/v1/analysis
 */
import axios from 'axios';
import { useAuthStore } from '@/store/authStore';
import type {
  AnalyzeArticleRequest,
  AnalyzeArticleResponse,
  EntitiesResponse,
  AnalysisStatusResponse,
  AnalysisResult,
} from '../types/analysis.types';

const analysisApi = axios.create({
  baseURL: import.meta.env.VITE_ANALYSIS_API_URL || 'http://localhost:8101/api/v1/analysis',
});

// Add auth interceptor
analysisApi.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Trigger analysis for an article
 * POST /api/v1/analysis/analyze
 */
export const analyzeArticle = async (
  request: AnalyzeArticleRequest
): Promise<AnalyzeArticleResponse> => {
  const response = await analysisApi.post('/analyze', request);
  return response.data;
};

/**
 * Get extracted entities for an article
 * GET /api/v1/analysis/entities/{article_id}
 */
export const extractEntities = async (articleId: string): Promise<EntitiesResponse> => {
  const response = await analysisApi.get(`/entities/${articleId}`);
  return response.data;
};

/**
 * Get analysis status for an article
 * GET /api/v1/analysis/status/{article_id}
 */
export const getAnalysisStatus = async (articleId: string): Promise<AnalysisStatusResponse> => {
  const response = await analysisApi.get(`/status/${articleId}`);
  return response.data;
};

/**
 * Get complete analysis result for an article
 * GET /api/v1/analysis/result/{article_id}
 */
export const getAnalysisResult = async (articleId: string): Promise<AnalysisResult> => {
  const response = await analysisApi.get(`/result/${articleId}`);
  return response.data;
};

export { analysisApi };

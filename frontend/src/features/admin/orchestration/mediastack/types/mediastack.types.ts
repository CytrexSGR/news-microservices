/**
 * MediaStack News API Types
 *
 * TypeScript type definitions for MediaStack MCP tools.
 * Based on: mcp-orchestration-server mediastack tools
 */

/**
 * MediaStack Article
 */
export interface MediaStackArticle {
  author: string | null;
  title: string;
  description: string;
  url: string;
  source: string;
  image: string | null;
  category: string;
  language: string;
  country: string;
  published_at: string;
}

/**
 * MediaStack Pagination
 */
export interface MediaStackPagination {
  limit: number;
  offset: number;
  count: number;
  total: number;
}

/**
 * MediaStack News Response (Live & Historical)
 */
export interface MediaStackNewsResponse {
  pagination: MediaStackPagination;
  data: MediaStackArticle[];
}

/**
 * MediaStack News Request Parameters
 */
export interface MediaStackNewsParams {
  keywords?: string;
  sources?: string[];
  categories?: string[];
  countries?: string[];
  languages?: string[];
  sort?: 'published_desc' | 'published_asc' | 'popularity';
  limit?: number;
  offset?: number;
}

/**
 * MediaStack Historical News Parameters (extends base params)
 */
export interface MediaStackHistoricalParams extends MediaStackNewsParams {
  date_from: string; // YYYY-MM-DD
  date_to: string;   // YYYY-MM-DD
}

/**
 * MediaStack Source
 */
export interface MediaStackSource {
  id: string;
  name: string;
  url: string;
  country: string;
  category: string;
  language: string;
}

/**
 * MediaStack Sources Response
 */
export interface MediaStackSourcesResponse {
  data: MediaStackSource[];
  pagination: MediaStackPagination;
}

/**
 * MediaStack Sources Filter Parameters
 */
export interface MediaStackSourcesParams {
  countries?: string[];
  categories?: string[];
  languages?: string[];
  search?: string;
  limit?: number;
  offset?: number;
}

/**
 * MediaStack API Usage
 */
export interface MediaStackUsage {
  plan_name: string;
  plan_type: 'free' | 'basic' | 'standard' | 'business' | 'enterprise';
  calls_made: number;
  calls_remaining: number;
  calls_limit: number;
  usage_percentage: number;
  reset_date: string;
  features: {
    live_news: boolean;
    historical_news: boolean;
    sources_endpoint: boolean;
    https: boolean;
  };
}

/**
 * MediaStack Categories (available options)
 */
export const MEDIASTACK_CATEGORIES = [
  'general',
  'business',
  'entertainment',
  'health',
  'science',
  'sports',
  'technology',
] as const;

export type MediaStackCategory = typeof MEDIASTACK_CATEGORIES[number];

/**
 * MediaStack Countries (common options)
 */
export const MEDIASTACK_COUNTRIES = [
  'de', // Germany
  'at', // Austria
  'ch', // Switzerland
  'us', // USA
  'gb', // UK
  'fr', // France
  'nl', // Netherlands
] as const;

export type MediaStackCountry = typeof MEDIASTACK_COUNTRIES[number];

/**
 * MediaStack Languages
 */
export const MEDIASTACK_LANGUAGES = [
  'de', // German
  'en', // English
  'fr', // French
  'es', // Spanish
  'it', // Italian
  'nl', // Dutch
] as const;

export type MediaStackLanguage = typeof MEDIASTACK_LANGUAGES[number];

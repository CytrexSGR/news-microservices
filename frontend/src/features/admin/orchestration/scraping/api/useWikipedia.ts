import { useQuery, useMutation, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type {
  WikipediaSearchParams,
  WikipediaSearchResponse,
  WikipediaArticleParams,
  WikipediaArticle,
  WikipediaRelationshipsResponse,
} from '../types/scraping.types';

/**
 * Query keys for Wikipedia
 */
export const wikipediaSearchQueryKey = (query: string, language?: string) =>
  ['scraping', 'wikipedia', 'search', query, language] as const;
export const wikipediaArticleQueryKey = (title: string, language?: string) =>
  ['scraping', 'wikipedia', 'article', title, language] as const;

/**
 * Search Wikipedia
 */
async function searchWikipedia(params: WikipediaSearchParams): Promise<WikipediaSearchResponse> {
  return mcpClient.callTool<WikipediaSearchResponse>('scraping_wikipedia_search', params);
}

/**
 * Fetch Wikipedia article
 */
async function fetchWikipediaArticle(params: WikipediaArticleParams): Promise<WikipediaArticle> {
  return mcpClient.callTool<WikipediaArticle>('scraping_wikipedia_article', params);
}

/**
 * Extract relationships from Wikipedia article
 */
async function extractWikipediaRelationships(title: string, language?: string): Promise<WikipediaRelationshipsResponse> {
  return mcpClient.callTool<WikipediaRelationshipsResponse>('scraping_wikipedia_relationships', { title, language });
}

/**
 * Get Wikipedia article summary
 */
async function getWikipediaSummary(title: string, language?: string): Promise<{ title: string; summary: string }> {
  return mcpClient.callTool<{ title: string; summary: string }>('scraping_wikipedia_summary', { title, language });
}

/**
 * Hook to search Wikipedia (as query for autocomplete)
 *
 * @example
 * ```tsx
 * const { data } = useWikipediaSearch({ query: 'React', language: 'en', limit: 10 });
 * ```
 */
export function useWikipediaSearch(
  params: WikipediaSearchParams,
  options?: Omit<UseQueryOptions<WikipediaSearchResponse>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: wikipediaSearchQueryKey(params.query, params.language),
    queryFn: () => searchWikipedia(params),
    enabled: params.query.length >= 2,
    staleTime: 300000, // 5 minutes
    ...options,
  });
}

/**
 * Hook to search Wikipedia (as mutation for form submission)
 */
export function useWikipediaSearchMutation(
  options?: Omit<UseMutationOptions<WikipediaSearchResponse, Error, WikipediaSearchParams>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: searchWikipedia,
    ...options,
  });
}

/**
 * Hook to fetch Wikipedia article
 */
export function useWikipediaArticle(
  params: WikipediaArticleParams,
  options?: Omit<UseQueryOptions<WikipediaArticle>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: wikipediaArticleQueryKey(params.title, params.language),
    queryFn: () => fetchWikipediaArticle(params),
    enabled: !!params.title,
    staleTime: 600000, // 10 minutes
    ...options,
  });
}

/**
 * Hook to fetch Wikipedia article (as mutation)
 */
export function useWikipediaArticleMutation(
  options?: Omit<UseMutationOptions<WikipediaArticle, Error, WikipediaArticleParams>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: fetchWikipediaArticle,
    ...options,
  });
}

/**
 * Hook to extract relationships from Wikipedia article
 */
export function useWikipediaRelationships(
  options?: Omit<UseMutationOptions<WikipediaRelationshipsResponse, Error, { title: string; language?: string }>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: ({ title, language }) => extractWikipediaRelationships(title, language),
    ...options,
  });
}

/**
 * Hook to get Wikipedia summary
 */
export function useWikipediaSummary(
  options?: Omit<UseMutationOptions<{ title: string; summary: string }, Error, { title: string; language?: string }>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: ({ title, language }) => getWikipediaSummary(title, language),
    ...options,
  });
}

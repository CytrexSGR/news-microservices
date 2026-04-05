import { useMutation, UseMutationOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { DirectScrapeParams, DirectScrapeResult, ScrapingMethod } from '../types/scraping.types';

/**
 * Batch scrape params
 */
interface BatchScrapeParams {
  urls: string[];
  method?: ScrapingMethod;
  timeout_seconds?: number;
  use_proxy?: boolean;
  max_concurrent?: number;
}

/**
 * Batch scrape result
 */
interface BatchScrapeResult {
  total: number;
  successful: number;
  failed: number;
  results: DirectScrapeResult[];
  total_time_ms: number;
}

/**
 * Scrape a single URL directly
 */
async function scrapeUrl(params: DirectScrapeParams): Promise<DirectScrapeResult> {
  return mcpClient.callTool<DirectScrapeResult>('scraping_scrape_url', params, { timeout: 60000 });
}

/**
 * Batch scrape multiple URLs
 */
async function batchScrape(params: BatchScrapeParams): Promise<BatchScrapeResult> {
  return mcpClient.callTool<BatchScrapeResult>('scraping_batch_scrape', params, { timeout: 300000 });
}

/**
 * Fetch raw HTML content
 */
async function fetchRawHtml(url: string, use_proxy?: boolean): Promise<{ html: string; status_code: number }> {
  return mcpClient.callTool<{ html: string; status_code: number }>('scraping_fetch_raw', { url, use_proxy }, { timeout: 30000 });
}

/**
 * Render JavaScript and fetch content
 */
async function renderPage(url: string, wait_seconds?: number): Promise<{ html: string; screenshot?: string }> {
  return mcpClient.callTool<{ html: string; screenshot?: string }>('scraping_render_page', { url, wait_seconds }, { timeout: 60000 });
}

/**
 * Hook to scrape a single URL
 *
 * @example
 * ```tsx
 * const scrape = useDirectScrape();
 *
 * const handleScrape = async (url: string) => {
 *   const result = await scrape.mutateAsync({ url, method: 'auto' });
 *   if (result.success) {
 *     console.log(result.content);
 *   }
 * };
 * ```
 */
export function useDirectScrape(
  options?: Omit<UseMutationOptions<DirectScrapeResult, Error, DirectScrapeParams>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: scrapeUrl,
    ...options,
  });
}

/**
 * Hook to batch scrape multiple URLs
 */
export function useBatchScrape(
  options?: Omit<UseMutationOptions<BatchScrapeResult, Error, BatchScrapeParams>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: batchScrape,
    ...options,
  });
}

/**
 * Hook to fetch raw HTML
 */
export function useFetchRawHtml(
  options?: Omit<UseMutationOptions<{ html: string; status_code: number }, Error, { url: string; use_proxy?: boolean }>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: ({ url, use_proxy }) => fetchRawHtml(url, use_proxy),
    ...options,
  });
}

/**
 * Hook to render a page with JavaScript
 */
export function useRenderPage(
  options?: Omit<UseMutationOptions<{ html: string; screenshot?: string }, Error, { url: string; wait_seconds?: number }>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: ({ url, wait_seconds }) => renderPage(url, wait_seconds),
    ...options,
  });
}

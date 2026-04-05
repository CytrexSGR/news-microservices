import { useMutation, UseMutationOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';

/**
 * Article extraction result
 */
interface ArticleExtractionResult {
  success: boolean;
  url: string;
  title: string;
  content: string;
  author?: string;
  published_date?: string;
  language?: string;
  word_count: number;
  reading_time_minutes: number;
  images: string[];
  extraction_time_ms: number;
  error?: string;
}

/**
 * Metadata extraction result
 */
interface MetadataExtractionResult {
  success: boolean;
  url: string;
  title?: string;
  description?: string;
  keywords?: string[];
  author?: string;
  published_date?: string;
  modified_date?: string;
  og_title?: string;
  og_description?: string;
  og_image?: string;
  og_type?: string;
  twitter_card?: string;
  canonical_url?: string;
  favicon?: string;
  language?: string;
  site_name?: string;
}

/**
 * Links extraction result
 */
interface LinksExtractionResult {
  success: boolean;
  url: string;
  internal_links: Array<{ href: string; text: string }>;
  external_links: Array<{ href: string; text: string; domain: string }>;
  total_links: number;
}

/**
 * Images extraction result
 */
interface ImagesExtractionResult {
  success: boolean;
  url: string;
  images: Array<{
    src: string;
    alt?: string;
    width?: number;
    height?: number;
    is_lazy_loaded: boolean;
  }>;
  total_images: number;
}

/**
 * Tables extraction result
 */
interface TablesExtractionResult {
  success: boolean;
  url: string;
  tables: Array<{
    headers: string[];
    rows: string[][];
    caption?: string;
  }>;
  total_tables: number;
}

/**
 * Structured data extraction result
 */
interface StructuredDataResult {
  success: boolean;
  url: string;
  json_ld: Record<string, unknown>[];
  microdata: Record<string, unknown>[];
  rdfa: Record<string, unknown>[];
}

/**
 * Extract article content
 */
async function extractArticle(url: string): Promise<ArticleExtractionResult> {
  return mcpClient.callTool<ArticleExtractionResult>('scraping_extract_article', { url }, { timeout: 60000 });
}

/**
 * Extract page metadata
 */
async function extractMetadata(url: string): Promise<MetadataExtractionResult> {
  return mcpClient.callTool<MetadataExtractionResult>('scraping_extract_metadata', { url }, { timeout: 30000 });
}

/**
 * Extract links from page
 */
async function extractLinks(url: string, include_external?: boolean): Promise<LinksExtractionResult> {
  return mcpClient.callTool<LinksExtractionResult>('scraping_extract_links', { url, include_external }, { timeout: 30000 });
}

/**
 * Extract images from page
 */
async function extractImages(url: string): Promise<ImagesExtractionResult> {
  return mcpClient.callTool<ImagesExtractionResult>('scraping_extract_images', { url }, { timeout: 30000 });
}

/**
 * Extract tables from page
 */
async function extractTables(url: string): Promise<TablesExtractionResult> {
  return mcpClient.callTool<TablesExtractionResult>('scraping_extract_tables', { url }, { timeout: 30000 });
}

/**
 * Extract structured data (JSON-LD, Microdata, RDFa)
 */
async function extractStructuredData(url: string): Promise<StructuredDataResult> {
  return mcpClient.callTool<StructuredDataResult>('scraping_extract_structured_data', { url }, { timeout: 30000 });
}

/**
 * Hook to extract article content
 *
 * @example
 * ```tsx
 * const extract = useArticleExtraction();
 *
 * const handleExtract = async (url: string) => {
 *   const result = await extract.mutateAsync(url);
 *   if (result.success) {
 *     setArticle({ title: result.title, content: result.content });
 *   }
 * };
 * ```
 */
export function useArticleExtraction(
  options?: Omit<UseMutationOptions<ArticleExtractionResult, Error, string>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: extractArticle,
    ...options,
  });
}

/**
 * Hook to extract page metadata
 */
export function useMetadataExtraction(
  options?: Omit<UseMutationOptions<MetadataExtractionResult, Error, string>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: extractMetadata,
    ...options,
  });
}

/**
 * Hook to extract links
 */
export function useLinksExtraction(
  options?: Omit<UseMutationOptions<LinksExtractionResult, Error, { url: string; include_external?: boolean }>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: ({ url, include_external }) => extractLinks(url, include_external),
    ...options,
  });
}

/**
 * Hook to extract images
 */
export function useImagesExtraction(
  options?: Omit<UseMutationOptions<ImagesExtractionResult, Error, string>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: extractImages,
    ...options,
  });
}

/**
 * Hook to extract tables
 */
export function useTablesExtraction(
  options?: Omit<UseMutationOptions<TablesExtractionResult, Error, string>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: extractTables,
    ...options,
  });
}

/**
 * Hook to extract structured data
 */
export function useStructuredDataExtraction(
  options?: Omit<UseMutationOptions<StructuredDataResult, Error, string>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: extractStructuredData,
    ...options,
  });
}

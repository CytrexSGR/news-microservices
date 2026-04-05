import { useMutation, UseMutationOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';

/**
 * Screenshot params
 */
interface ScreenshotParams {
  url: string;
  full_page?: boolean;
  width?: number;
  height?: number;
  format?: 'png' | 'jpeg' | 'webp';
  quality?: number;
  wait_seconds?: number;
  selector?: string;
}

/**
 * Screenshot result
 */
interface ScreenshotResult {
  success: boolean;
  url: string;
  image_base64: string;
  format: string;
  width: number;
  height: number;
  file_size_bytes: number;
  capture_time_ms: number;
  error?: string;
}

/**
 * Preview params
 */
interface PreviewParams {
  url: string;
  width?: number;
  height?: number;
  format?: 'png' | 'jpeg';
}

/**
 * Preview result
 */
interface PreviewResult {
  success: boolean;
  url: string;
  title?: string;
  description?: string;
  image_base64?: string;
  favicon_url?: string;
  og_image_url?: string;
}

/**
 * PDF params
 */
interface PdfParams {
  url: string;
  format?: 'A4' | 'Letter' | 'Legal';
  landscape?: boolean;
  print_background?: boolean;
  margin?: {
    top?: string;
    bottom?: string;
    left?: string;
    right?: string;
  };
}

/**
 * PDF result
 */
interface PdfResult {
  success: boolean;
  url: string;
  pdf_base64: string;
  file_size_bytes: number;
  pages: number;
}

/**
 * Take screenshot of a URL
 */
async function takeScreenshot(params: ScreenshotParams): Promise<ScreenshotResult> {
  return mcpClient.callTool<ScreenshotResult>('scraping_take_screenshot', params, { timeout: 60000 });
}

/**
 * Generate link preview
 */
async function generatePreview(params: PreviewParams): Promise<PreviewResult> {
  return mcpClient.callTool<PreviewResult>('scraping_generate_preview', params, { timeout: 30000 });
}

/**
 * Generate PDF from URL
 */
async function generatePdf(params: PdfParams): Promise<PdfResult> {
  return mcpClient.callTool<PdfResult>('scraping_generate_pdf', params, { timeout: 60000 });
}

/**
 * Take screenshot of a specific element
 */
async function screenshotElement(url: string, selector: string): Promise<ScreenshotResult> {
  return mcpClient.callTool<ScreenshotResult>('scraping_screenshot_element', { url, selector }, { timeout: 60000 });
}

/**
 * Hook to take a screenshot of a URL
 *
 * @example
 * ```tsx
 * const screenshot = useScreenshot();
 *
 * const handleCapture = async () => {
 *   const result = await screenshot.mutateAsync({
 *     url: 'https://example.com',
 *     full_page: true,
 *     format: 'png'
 *   });
 *   if (result.success) {
 *     setImageSrc(`data:image/png;base64,${result.image_base64}`);
 *   }
 * };
 * ```
 */
export function useScreenshot(
  options?: Omit<UseMutationOptions<ScreenshotResult, Error, ScreenshotParams>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: takeScreenshot,
    ...options,
  });
}

/**
 * Hook to generate a link preview
 */
export function usePreview(
  options?: Omit<UseMutationOptions<PreviewResult, Error, PreviewParams>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: generatePreview,
    ...options,
  });
}

/**
 * Hook to generate a PDF from URL
 */
export function usePdf(
  options?: Omit<UseMutationOptions<PdfResult, Error, PdfParams>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: generatePdf,
    ...options,
  });
}

/**
 * Hook to take screenshot of a specific element
 */
export function useElementScreenshot(
  options?: Omit<UseMutationOptions<ScreenshotResult, Error, { url: string; selector: string }>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: ({ url, selector }) => screenshotElement(url, selector),
    ...options,
  });
}

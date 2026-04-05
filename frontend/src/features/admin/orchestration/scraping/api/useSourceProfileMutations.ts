import { useMutation, useQueryClient, UseMutationOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { SourceProfile, ScrapingMethod } from '../types/scraping.types';
import { sourceProfilesQueryKey } from './useSourceProfiles';

/**
 * Create source profile params
 */
interface CreateSourceProfileParams {
  domain: string;
  scraping_method?: ScrapingMethod;
  requires_js?: boolean;
  requires_proxy?: boolean;
  rate_limit_rpm?: number;
  custom_selectors?: {
    title?: string;
    content?: string;
    author?: string;
    date?: string;
  };
  notes?: string;
}

/**
 * Update source profile params
 */
interface UpdateSourceProfileParams {
  domain: string;
  scraping_method?: ScrapingMethod;
  requires_js?: boolean;
  requires_proxy?: boolean;
  rate_limit_rpm?: number;
  custom_selectors?: {
    title?: string;
    content?: string;
    author?: string;
    date?: string;
  };
  notes?: string;
}

/**
 * Action response
 */
interface ActionResponse {
  success: boolean;
  message: string;
}

/**
 * Test source result
 */
interface TestSourceResult {
  success: boolean;
  domain: string;
  method_used: ScrapingMethod;
  response_time_ms: number;
  status_code?: number;
  content_length?: number;
  requires_js: boolean;
  requires_proxy: boolean;
  error?: string;
}

/**
 * Create source profile
 */
async function createSourceProfile(params: CreateSourceProfileParams): Promise<SourceProfile> {
  return mcpClient.callTool<SourceProfile>('scraping_create_source_profile', params);
}

/**
 * Update source profile
 */
async function updateSourceProfile(params: UpdateSourceProfileParams): Promise<SourceProfile> {
  return mcpClient.callTool<SourceProfile>('scraping_update_source_profile', params);
}

/**
 * Delete source profile
 */
async function deleteSourceProfile(domain: string): Promise<ActionResponse> {
  return mcpClient.callTool<ActionResponse>('scraping_delete_source_profile', { domain });
}

/**
 * Test source profile
 */
async function testSourceProfile(domain: string): Promise<TestSourceResult> {
  return mcpClient.callTool<TestSourceResult>('scraping_test_source_profile', { domain });
}

/**
 * Reset source profile stats
 */
async function resetSourceProfileStats(domain: string): Promise<ActionResponse> {
  return mcpClient.callTool<ActionResponse>('scraping_reset_source_stats', { domain });
}

/**
 * Hook to create a source profile
 */
export function useCreateSourceProfile(
  options?: Omit<UseMutationOptions<SourceProfile, Error, CreateSourceProfileParams>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createSourceProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sourceProfilesQueryKey });
    },
    ...options,
  });
}

/**
 * Hook to update a source profile
 */
export function useUpdateSourceProfile(
  options?: Omit<UseMutationOptions<SourceProfile, Error, UpdateSourceProfileParams>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateSourceProfile,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: sourceProfilesQueryKey });
      queryClient.invalidateQueries({ queryKey: ['scraping', 'sources', variables.domain] });
    },
    ...options,
  });
}

/**
 * Hook to delete a source profile
 */
export function useDeleteSourceProfile(
  options?: Omit<UseMutationOptions<ActionResponse, Error, string>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteSourceProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sourceProfilesQueryKey });
    },
    ...options,
  });
}

/**
 * Hook to test a source profile
 */
export function useTestSourceProfile(
  options?: Omit<UseMutationOptions<TestSourceResult, Error, string>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: testSourceProfile,
    ...options,
  });
}

/**
 * Hook to reset source profile stats
 */
export function useResetSourceProfileStats(
  options?: Omit<UseMutationOptions<ActionResponse, Error, string>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: resetSourceProfileStats,
    onSuccess: (_, domain) => {
      queryClient.invalidateQueries({ queryKey: ['scraping', 'sources', domain] });
    },
    ...options,
  });
}

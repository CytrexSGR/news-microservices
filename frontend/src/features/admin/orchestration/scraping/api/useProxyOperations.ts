import { useMutation, useQueryClient, UseMutationOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';
import type { AddProxyParams, ProxyActionResponse, ProxyInfo } from '../types/scraping.types';
import { proxyListQueryKey, proxyStatsQueryKey } from './useProxyList';

/**
 * Rotate proxy response
 */
interface RotateProxyResponse {
  success: boolean;
  old_proxy_id?: string;
  new_proxy_id: string;
  message: string;
}

/**
 * Test proxy response
 */
interface TestProxyResponse {
  success: boolean;
  proxy_id: string;
  response_time_ms: number;
  external_ip?: string;
  error?: string;
}

/**
 * Add a new proxy
 */
async function addProxy(params: AddProxyParams): Promise<ProxyActionResponse> {
  return mcpClient.callTool<ProxyActionResponse>('scraping_add_proxy', params);
}

/**
 * Remove a proxy
 */
async function removeProxy(proxyId: string): Promise<ProxyActionResponse> {
  return mcpClient.callTool<ProxyActionResponse>('scraping_remove_proxy', { proxy_id: proxyId });
}

/**
 * Rotate to next available proxy
 */
async function rotateProxy(domain?: string): Promise<RotateProxyResponse> {
  return mcpClient.callTool<RotateProxyResponse>('scraping_rotate_proxy', domain ? { domain } : {});
}

/**
 * Test a proxy
 */
async function testProxy(proxyId: string): Promise<TestProxyResponse> {
  return mcpClient.callTool<TestProxyResponse>('scraping_test_proxy', { proxy_id: proxyId });
}

/**
 * Enable a proxy
 */
async function enableProxy(proxyId: string): Promise<ProxyActionResponse> {
  return mcpClient.callTool<ProxyActionResponse>('scraping_enable_proxy', { proxy_id: proxyId });
}

/**
 * Disable a proxy
 */
async function disableProxy(proxyId: string): Promise<ProxyActionResponse> {
  return mcpClient.callTool<ProxyActionResponse>('scraping_disable_proxy', { proxy_id: proxyId });
}

/**
 * Hook to add a proxy
 *
 * @example
 * ```tsx
 * const addProxy = useAddProxy();
 *
 * await addProxy.mutateAsync({
 *   host: '192.168.1.100',
 *   port: 8080,
 *   type: 'http',
 * });
 * ```
 */
export function useAddProxy(
  options?: Omit<UseMutationOptions<ProxyActionResponse, Error, AddProxyParams>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: addProxy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: proxyListQueryKey });
      queryClient.invalidateQueries({ queryKey: proxyStatsQueryKey });
    },
    ...options,
  });
}

/**
 * Hook to remove a proxy
 */
export function useRemoveProxy(
  options?: Omit<UseMutationOptions<ProxyActionResponse, Error, string>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: removeProxy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: proxyListQueryKey });
      queryClient.invalidateQueries({ queryKey: proxyStatsQueryKey });
    },
    ...options,
  });
}

/**
 * Hook to rotate proxy
 */
export function useRotateProxy(
  options?: Omit<UseMutationOptions<RotateProxyResponse, Error, string | undefined>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: rotateProxy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: proxyListQueryKey });
    },
    ...options,
  });
}

/**
 * Hook to test a proxy
 */
export function useTestProxy(
  options?: Omit<UseMutationOptions<TestProxyResponse, Error, string>, 'mutationFn'>
) {
  return useMutation({
    mutationFn: testProxy,
    ...options,
  });
}

/**
 * Hook to enable a proxy
 */
export function useEnableProxy(
  options?: Omit<UseMutationOptions<ProxyActionResponse, Error, string>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: enableProxy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: proxyListQueryKey });
      queryClient.invalidateQueries({ queryKey: proxyStatsQueryKey });
    },
    ...options,
  });
}

/**
 * Hook to disable a proxy
 */
export function useDisableProxy(
  options?: Omit<UseMutationOptions<ProxyActionResponse, Error, string>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: disableProxy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: proxyListQueryKey });
      queryClient.invalidateQueries({ queryKey: proxyStatsQueryKey });
    },
    ...options,
  });
}

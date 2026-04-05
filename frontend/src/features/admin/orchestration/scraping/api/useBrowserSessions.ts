import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { mcpClient } from '@/shared/api/mcpClient';

/**
 * Query keys
 */
export const browserSessionsQueryKey = ['scraping', 'browser', 'sessions'] as const;
export const browserSessionQueryKey = (sessionId: string) => ['scraping', 'browser', 'sessions', sessionId] as const;
export const browserStatusQueryKey = ['scraping', 'browser', 'status'] as const;

/**
 * Browser session
 */
interface BrowserSession {
  session_id: string;
  created_at: string;
  last_used_at: string;
  url?: string;
  pages_count: number;
  memory_mb: number;
  is_active: boolean;
}

/**
 * Browser status
 */
interface BrowserStatus {
  instances_running: number;
  total_sessions: number;
  active_sessions: number;
  memory_usage_mb: number;
  max_instances: number;
  is_healthy: boolean;
}

/**
 * Create session params
 */
interface CreateSessionParams {
  headless?: boolean;
  proxy_id?: string;
  user_agent?: string;
  viewport?: { width: number; height: number };
  timeout_seconds?: number;
}

/**
 * Session action response
 */
interface SessionActionResponse {
  success: boolean;
  session_id?: string;
  message: string;
}

/**
 * Fetch browser sessions
 */
async function fetchBrowserSessions(): Promise<{ sessions: BrowserSession[] }> {
  return mcpClient.callTool<{ sessions: BrowserSession[] }>('scraping_list_browser_sessions');
}

/**
 * Fetch browser status
 */
async function fetchBrowserStatus(): Promise<BrowserStatus> {
  return mcpClient.callTool<BrowserStatus>('scraping_get_browser_status');
}

/**
 * Fetch single browser session
 */
async function fetchBrowserSession(sessionId: string): Promise<BrowserSession> {
  return mcpClient.callTool<BrowserSession>('scraping_get_browser_session', { session_id: sessionId });
}

/**
 * Create browser session
 */
async function createBrowserSession(params?: CreateSessionParams): Promise<SessionActionResponse> {
  return mcpClient.callTool<SessionActionResponse>('scraping_create_browser_session', params || {});
}

/**
 * Destroy browser session
 */
async function destroyBrowserSession(sessionId: string): Promise<SessionActionResponse> {
  return mcpClient.callTool<SessionActionResponse>('scraping_destroy_browser_session', { session_id: sessionId });
}

/**
 * Destroy all browser sessions
 */
async function destroyAllBrowserSessions(): Promise<{ success: boolean; destroyed: number }> {
  return mcpClient.callTool<{ success: boolean; destroyed: number }>('scraping_destroy_all_browser_sessions', {});
}

/**
 * Restart browser pool
 */
async function restartBrowserPool(): Promise<{ success: boolean; message: string }> {
  return mcpClient.callTool<{ success: boolean; message: string }>('scraping_restart_browser_pool', {});
}

/**
 * Hook to fetch browser sessions
 *
 * @example
 * ```tsx
 * const { data } = useBrowserSessions();
 * const activeSessions = data?.sessions.filter(s => s.is_active);
 * ```
 */
export function useBrowserSessions(
  options?: Omit<UseQueryOptions<{ sessions: BrowserSession[] }>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: browserSessionsQueryKey,
    queryFn: fetchBrowserSessions,
    staleTime: 10000,
    refetchInterval: 30000,
    ...options,
  });
}

/**
 * Hook to fetch browser status
 */
export function useBrowserStatus(
  options?: Omit<UseQueryOptions<BrowserStatus>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: browserStatusQueryKey,
    queryFn: fetchBrowserStatus,
    staleTime: 5000,
    refetchInterval: 15000,
    ...options,
  });
}

/**
 * Hook to fetch a single browser session
 */
export function useBrowserSession(
  sessionId: string,
  options?: Omit<UseQueryOptions<BrowserSession>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: browserSessionQueryKey(sessionId),
    queryFn: () => fetchBrowserSession(sessionId),
    enabled: !!sessionId,
    staleTime: 10000,
    ...options,
  });
}

/**
 * Hook to create a browser session
 */
export function useCreateBrowserSession(
  options?: Omit<UseMutationOptions<SessionActionResponse, Error, CreateSessionParams | undefined>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createBrowserSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: browserSessionsQueryKey });
      queryClient.invalidateQueries({ queryKey: browserStatusQueryKey });
    },
    ...options,
  });
}

/**
 * Hook to destroy a browser session
 */
export function useDestroyBrowserSession(
  options?: Omit<UseMutationOptions<SessionActionResponse, Error, string>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: destroyBrowserSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: browserSessionsQueryKey });
      queryClient.invalidateQueries({ queryKey: browserStatusQueryKey });
    },
    ...options,
  });
}

/**
 * Hook to destroy all browser sessions
 */
export function useDestroyAllBrowserSessions(
  options?: Omit<UseMutationOptions<{ success: boolean; destroyed: number }, Error, void>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: destroyAllBrowserSessions,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: browserSessionsQueryKey });
      queryClient.invalidateQueries({ queryKey: browserStatusQueryKey });
    },
    ...options,
  });
}

/**
 * Hook to restart browser pool
 */
export function useRestartBrowserPool(
  options?: Omit<UseMutationOptions<{ success: boolean; message: string }, Error, void>, 'mutationFn'>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: restartBrowserPool,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: browserSessionsQueryKey });
      queryClient.invalidateQueries({ queryKey: browserStatusQueryKey });
    },
    ...options,
  });
}

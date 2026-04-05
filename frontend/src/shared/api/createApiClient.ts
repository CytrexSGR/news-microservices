import axios from 'axios';
import type { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/store/authStore';

/**
 * Standard API response wrapper
 * Used for endpoints that return structured responses
 */
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

/**
 * API error response type
 * Standardized error format from backend services
 */
export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
  status?: number;
}

/**
 * Paginated response wrapper
 * Used for list endpoints that support pagination
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

/**
 * API Client configuration options
 */
export interface ApiClientConfig {
  /** Request timeout in milliseconds (default: 30000) */
  timeout?: number;
  /** Custom headers to include with every request */
  headers?: Record<string, string>;
  /** Whether to automatically add auth token (default: true) */
  withAuth?: boolean;
  /** Whether to logout on 401 response (default: true) */
  logoutOn401?: boolean;
}

/**
 * Custom error class for API errors
 * Provides structured error information
 */
export class ApiClientError extends Error {
  constructor(
    message: string,
    public readonly code?: string,
    public readonly status?: number,
    public readonly details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'ApiClientError';
  }

  /**
   * Create ApiClientError from AxiosError
   */
  static fromAxiosError(error: AxiosError<ApiError>): ApiClientError {
    const responseData = error.response?.data;
    return new ApiClientError(
      responseData?.message || error.message || 'Unknown error',
      responseData?.code || error.code,
      error.response?.status,
      responseData?.details
    );
  }
}

/**
 * Creates a configured Axios client instance for API communication
 *
 * Features:
 * - Automatic auth token injection from authStore
 * - Automatic logout on 401 responses
 * - Standardized error handling
 * - Configurable timeout and headers
 *
 * @param baseURL - The base URL for all requests
 * @param config - Optional configuration options
 * @returns Configured AxiosInstance
 *
 * @example
 * ```ts
 * // Create client for feed service
 * const feedClient = createApiClient('http://localhost:8101/api/v1');
 *
 * // Make authenticated request
 * const feeds = await feedClient.get<Feed[]>('/feeds');
 *
 * // Create client without auto-auth
 * const publicClient = createApiClient('http://localhost:8100/api/v1', {
 *   withAuth: false,
 * });
 * ```
 */
export function createApiClient(
  baseURL: string,
  config: ApiClientConfig = {}
): AxiosInstance {
  const {
    timeout = 30000,
    headers = {},
    withAuth = true,
    logoutOn401 = true,
  } = config;

  // Create axios instance with base configuration
  const client = axios.create({
    baseURL,
    timeout,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  });

  // Request interceptor for auth token injection
  if (withAuth) {
    client.interceptors.request.use(
      (requestConfig: InternalAxiosRequestConfig) => {
        const token = useAuthStore.getState().accessToken;
        if (token) {
          requestConfig.headers.Authorization = `Bearer ${token}`;
        }
        return requestConfig;
      },
      (error) => Promise.reject(error)
    );
  }

  // Response interceptor for error handling
  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError<ApiError>) => {
      // Handle 401 Unauthorized - logout user
      if (error.response?.status === 401 && logoutOn401) {
        useAuthStore.getState().logout();
      }

      // Convert to ApiClientError for consistent error handling
      return Promise.reject(ApiClientError.fromAxiosError(error));
    }
  );

  return client;
}

/**
 * Type helper for extracting data from AxiosResponse
 * Useful when working with the response directly
 */
export type ExtractData<T> = T extends ApiResponse<infer D> ? D : T;

/**
 * Type helper for paginated list endpoints
 */
export type PaginatedList<T> = PaginatedResponse<T>;

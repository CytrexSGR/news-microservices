/**
 * Shared API Client Module
 *
 * This module provides a unified approach to creating API clients
 * with consistent auth handling and error management.
 *
 * @example
 * ```ts
 * import { createApiClient, ApiResponse, PaginatedResponse } from '@/shared/api';
 *
 * // Create service-specific client
 * const feedClient = createApiClient(import.meta.env.VITE_FEED_API_URL);
 *
 * // Use with typed responses
 * interface Feed {
 *   id: string;
 *   name: string;
 * }
 *
 * const { data } = await feedClient.get<ApiResponse<Feed[]>>('/feeds');
 * ```
 */

// Main factory function
export { createApiClient } from './createApiClient';

// Types
export type {
  ApiResponse,
  ApiError,
  PaginatedResponse,
  ApiClientConfig,
  ExtractData,
  PaginatedList,
} from './createApiClient';

// Error class
export { ApiClientError } from './createApiClient';

// Re-export MCP client for convenience
export { mcpClient, MCPClient, MCPClientError } from './mcpClient';

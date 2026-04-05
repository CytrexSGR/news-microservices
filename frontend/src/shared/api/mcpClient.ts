import axios from 'axios';
import type { AxiosInstance, AxiosError } from 'axios';

/**
 * MCP Tool Call Request
 */
interface MCPToolCallRequest {
  tool_name: string;
  arguments: Record<string, unknown>;
}

/**
 * MCP Tool Call Response
 */
interface MCPToolCallResponse<T = unknown> {
  success: boolean;
  data: T | null;
  error?: string;
  metadata?: Record<string, unknown>;
}

/**
 * MCP Client Error
 */
export class MCPClientError extends Error {
  constructor(
    message: string,
    public readonly code?: string,
    public readonly status?: number
  ) {
    super(message);
    this.name = 'MCPClientError';
  }
}

/**
 * MCP Orchestration Client
 *
 * Centralized client for communicating with the MCP Orchestration Server.
 * All MCP tool calls should go through this client.
 *
 * @example
 * ```ts
 * import { mcpClient } from '@/shared/api/mcpClient';
 *
 * const status = await mcpClient.callTool<SchedulerStatus>('scheduler_status');
 * ```
 */
class MCPClient {
  private client: AxiosInstance;
  private authToken: string | null = null;

  constructor(baseURL: string = import.meta.env.VITE_MCP_API_URL || 'http://localhost:9008') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30 seconds default
    });

    // Add auth interceptor
    this.client.interceptors.request.use((config) => {
      if (this.authToken) {
        config.headers.Authorization = `Bearer ${this.authToken}`;
      }
      return config;
    });

    // Add response error interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response) {
          throw new MCPClientError(
            error.response.data?.error || error.message,
            error.code,
            error.response.status
          );
        }
        throw new MCPClientError(error.message, error.code);
      }
    );
  }

  /**
   * Set authentication token for protected endpoints
   */
  setAuthToken(token: string | null): void {
    this.authToken = token;
  }

  /**
   * Call MCP Tool
   *
   * @param toolName - Name of the MCP tool to call
   * @param args - Arguments to pass to the tool
   * @param options - Optional configuration
   * @returns Tool response data
   */
  async callTool<T = unknown>(
    toolName: string,
    args: Record<string, unknown> = {},
    options?: { timeout?: number }
  ): Promise<T> {
    const request: MCPToolCallRequest = {
      tool_name: toolName,
      arguments: args,
    };

    const response = await this.client.post<MCPToolCallResponse<T>>(
      '/mcp/tools/call',
      request,
      { timeout: options?.timeout }
    );

    if (!response.data.success) {
      throw new MCPClientError(
        response.data.error || `MCP tool call failed: ${toolName}`
      );
    }

    return response.data.data as T;
  }

  /**
   * Get All Available MCP Tools
   */
  async getTools(): Promise<{ tools: Array<{ name: string; description: string }> }> {
    const response = await this.client.get('/mcp/tools');
    return response.data;
  }

  /**
   * Health check for MCP server
   */
  async healthCheck(): Promise<{ status: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

// Export singleton instance
export const mcpClient = new MCPClient();

// Export class for testing
export { MCPClient };

/**
 * Research Service Types
 *
 * Based on research-service/app/schemas/research.py
 * Port: 8103
 */

// ============================================================================
// Enums and Literals
// ============================================================================

export type ResearchModel = 'sonar' | 'sonar-pro' | 'sonar-reasoning-pro';
export type ResearchDepth = 'quick' | 'standard' | 'deep';
export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
export type ExportFormat = 'pdf' | 'markdown' | 'json';

export type ResearchFunction =
  | 'feed_source_assessment'
  | 'fact_check'
  | 'trend_analysis';

// ============================================================================
// Request DTOs
// ============================================================================

export interface ResearchTaskCreate {
  query: string;
  model_name?: ResearchModel;
  depth?: ResearchDepth;
  feed_id?: string;
  legacy_feed_id?: number;
  article_id?: string;
  legacy_article_id?: number;
  research_function?: ResearchFunction;
  function_parameters?: Record<string, unknown>;
}

export interface ResearchTaskBatchCreate {
  queries: string[];
  model_name?: ResearchModel;
  depth?: ResearchDepth;
  feed_id?: string;
  legacy_feed_id?: number;
}

export interface TemplateApply {
  variables?: Record<string, unknown>;
  model_name?: ResearchModel;
  depth?: ResearchDepth;
  feed_id?: string;
  legacy_feed_id?: number;
  article_id?: string;
  legacy_article_id?: number;
}

// ============================================================================
// Response DTOs
// ============================================================================

export interface ResearchTaskResponse {
  id: number;
  user_id: number;
  query: string;
  model_name: string;
  depth: string;
  status: TaskStatus;
  result?: Record<string, unknown>;
  error_message?: string;
  structured_data?: Record<string, unknown>;
  validation_status?: string;
  tokens_used: number;
  cost: number;
  feed_id?: string;
  legacy_feed_id?: number;
  article_id?: string;
  legacy_article_id?: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface ResearchTaskList {
  tasks: ResearchTaskResponse[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface TemplateResponse {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  query_template: string;
  parameters: Record<string, unknown>;
  default_model: string;
  default_depth: string;
  is_active: boolean;
  is_public: boolean;
  usage_count: number;
  last_used_at?: string;
  created_at: string;
  updated_at: string;
  research_function?: string;
  function_parameters?: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
}

export interface TemplatePreview {
  template_id: number;
  variables: Record<string, unknown>;
  rendered_query: string;
  estimated_cost: number;
}

export interface UsageStats {
  total_requests: number;
  total_tokens: number;
  total_cost: number;
  requests_by_model: Record<string, number>;
  cost_by_model: Record<string, number>;
  avg_tokens_per_request: number;
  period_start: string;
  period_end: string;
}

export interface ResearchFunctionInfo {
  name: string;
  description: string;
  parameters: Record<string, {
    type: string;
    description: string;
    required: boolean;
    default?: unknown;
  }>;
}

// ============================================================================
// Query Parameters
// ============================================================================

export interface ResearchTasksQuery {
  status?: TaskStatus;
  feed_id?: string;
  page?: number;
  page_size?: number;
}

export interface ResearchHistoryQuery {
  days?: number;
  page?: number;
  page_size?: number;
}

// ============================================================================
// Source Types
// ============================================================================

export interface ResearchSource {
  url: string;
  title: string;
  snippet: string;
  relevance_score: number;
  domain: string;
  published_date?: string;
}

export interface ResearchSourcesResponse {
  task_id: number;
  sources: ResearchSource[];
  total: number;
}

// ============================================================================
// Export Types
// ============================================================================

export interface ExportRequest {
  format: ExportFormat;
  include_sources?: boolean;
  include_metadata?: boolean;
}

export interface ExportResponse {
  task_id: number;
  format: ExportFormat;
  content: string;
  filename: string;
  mime_type: string;
}

// ============================================================================
// Cancel/Retry Types
// ============================================================================

export interface CancelResponse {
  task_id: number;
  status: TaskStatus;
  message: string;
}

export interface RetryResponse {
  original_task_id: number;
  new_task_id: number;
  status: TaskStatus;
  message: string;
}

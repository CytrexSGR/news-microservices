/**
 * Topic Browser TypeScript Types
 * Based on clustering-service batch_cluster.py schemas
 */

// ----- Core Types -----

export interface TopicArticle {
  article_id: string;
  title: string;
  url?: string;
  distance?: number;
  published_at?: string;
  assigned_at?: string;
}

export interface TopicSummary {
  id: number;
  label?: string;
  keywords?: string[];
  article_count: number;
  label_confidence?: number;
}

export interface TopicDetail extends TopicSummary {
  batch_id: string;
  cluster_idx: number;
  created_at?: string;
  sample_articles: TopicArticle[];
}

export interface TopicSearchResult {
  cluster_id: number;
  label?: string;
  keywords?: string[];
  article_count: number;
  match_count?: number;        // Keyword mode: number of matching articles
  similarity?: number;         // Semantic mode: cosine similarity (0-1)
}

export interface BatchInfo {
  batch_id: string;
  status: 'running' | 'completed' | 'failed';
  article_count: number;
  cluster_count: number;
  noise_count: number;
  csai_score?: number;
  started_at?: string;
  completed_at?: string;
}

// ----- API Response Types -----

export interface TopicListResponse {
  topics: TopicSummary[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
  batch_id?: string;
}

export interface TopicSearchResponse {
  results: TopicSearchResult[];
  query: string;
  mode: 'semantic' | 'keyword';  // Search mode used
  batch_id?: string;
}

export interface BatchListResponse {
  batches: BatchInfo[];
}

export interface FeedbackResponse {
  success: boolean;
  feedback_id: number;
  message: string;
}

// ----- Request Types -----

export interface TopicListParams {
  min_size?: number;
  limit?: number;
  offset?: number;
  batch_id?: string;
}

export interface TopicSearchParams {
  q: string;
  mode?: 'semantic' | 'keyword';   // Default: 'semantic'
  limit?: number;
  min_similarity?: number;         // For semantic mode (0-1, default: 0.3)
}

export interface TopicFeedbackRequest {
  label: string;
  confidence?: number;
}

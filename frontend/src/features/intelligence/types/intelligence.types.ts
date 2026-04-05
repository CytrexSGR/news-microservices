/**
 * Intelligence Service Types
 * Based on intelligence-service API schemas
 */

export interface ClusterSummary {
  id: string;
  name: string;
  risk_score: number;
  risk_delta: number;
  event_count: number;
  keywords: string[];
  category?: string;
  time_window?: string;
  last_updated: string;
}

export interface TopRegion {
  name: string;
  event_count: number;
  risk_score: number;
}

export interface OverviewResponse {
  global_risk_index: number;
  top_clusters: ClusterSummary[];
  geo_risk: number;
  finance_risk: number;
  top_regions: TopRegion[];
  total_clusters: number;
  total_events: number;
  timestamp: string;
}

export interface TimelinePoint {
  date: string;
  event_count: number;
  avg_sentiment: number;
}

export interface ClusterDetail extends ClusterSummary {
  avg_sentiment: number;
  unique_sources: number;
  is_active: boolean;
  first_seen: string;
  timeline: TimelinePoint[];
}

export interface ClustersResponse {
  clusters: ClusterDetail[];
  total: number;
  page: number;
  per_page: number;
  timestamp: string;
}

export interface EventEntity {
  persons: string[];
  organizations: string[];
  locations: string[];
}

export interface IntelligenceEvent {
  id: string;
  title: string;
  description?: string;
  source: string;
  source_url?: string;
  published_at: string;
  entities: EventEntity;
  keywords: string[];
  sentiment?: number;
  bias_score?: number;
  confidence?: number;
  cluster?: {
    id: string;
    name: string;
    risk_score: number;
  };
}

export interface LatestEventsResponse {
  events: IntelligenceEvent[];
  total: number;
  hours: number;
  timestamp: string;
}

export interface ClusterEventsResponse {
  cluster_id: string;
  cluster_name: string;
  events: IntelligenceEvent[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface SubcategoryTopic {
  name: string;
  risk_score: number;
  event_count: number;
  clusters: string[];
}

export interface SubcategoriesResponse {
  geo: SubcategoryTopic[];
  finance: SubcategoryTopic[];
  tech: SubcategoryTopic[];
}

export interface RiskHistoryPoint {
  date: string;
  global_risk: number;
  geo_risk: number;
  finance_risk: number;
  event_count: number;
}

export interface RiskHistoryResponse {
  history: RiskHistoryPoint[];
  days: number;
  total_points: number;
}

export type RiskLevel = 'low' | 'moderate' | 'elevated' | 'high' | 'critical';

export function getRiskLevel(score: number): RiskLevel {
  if (score < 20) return 'low';
  if (score < 40) return 'moderate';
  if (score < 60) return 'elevated';
  if (score < 80) return 'high';
  return 'critical';
}

export function getRiskColor(score: number): string {
  const level = getRiskLevel(score);
  switch (level) {
    case 'low': return 'text-green-500';
    case 'moderate': return 'text-yellow-500';
    case 'elevated': return 'text-orange-500';
    case 'high': return 'text-red-500';
    case 'critical': return 'text-red-700';
    default: return 'text-gray-500';
  }
}

export function getRiskBgColor(score: number): string {
  const level = getRiskLevel(score);
  switch (level) {
    case 'low': return 'bg-green-500/10';
    case 'moderate': return 'bg-yellow-500/10';
    case 'elevated': return 'bg-orange-500/10';
    case 'high': return 'bg-red-500/10';
    case 'critical': return 'bg-red-700/10';
    default: return 'bg-gray-500/10';
  }
}

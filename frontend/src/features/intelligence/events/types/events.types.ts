/**
 * Intelligence Events Types
 *
 * Type definitions for the Intelligence Events sub-feature
 */

export type EventCategory = 'breaking' | 'developing' | 'trend' | 'recurring' | 'anomaly';
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface IntelligenceEvent {
  id: string;
  title: string;
  description: string;
  category: EventCategory;
  risk_level: RiskLevel;
  risk_score: number;
  entities: string[];
  sources: string[];
  first_seen: string;
  last_updated: string;
  article_count: number;
  url?: string; // Original article URL
}

export interface EventCluster {
  id: string;
  name: string;
  category: EventCategory;
  events_count: number;
  risk_level: RiskLevel;
  avg_risk_score: number;
  top_entities: string[];
  created_at: string;
  last_activity: string;
  trending: boolean;
}

export interface ClusterDetails extends EventCluster {
  events: IntelligenceEvent[];
  related_clusters: string[];
  keywords: string[];
  timeline: TimelineEntry[];
}

export interface TimelineEntry {
  timestamp: string;
  event_type: 'article_added' | 'entity_linked' | 'risk_changed' | 'cluster_merged';
  details: Record<string, unknown>;
}

export interface IntelligenceOverview {
  total_events: number;
  active_clusters: number;
  avg_risk_score: number;
  risk_distribution: Record<RiskLevel, number>;
  trending_clusters: EventCluster[];
  recent_events: IntelligenceEvent[];
  events_by_category: Record<EventCategory, number>;
  last_updated: string;
}

export interface Subcategory {
  name: string;
  parent_category: EventCategory;
  count: number;
  avg_risk: number;
}

export interface RiskHistoryEntry {
  timestamp: string;
  risk_score: number;
  events_count: number;
  top_contributors: string[];
}

// API Response types
export interface EventClustersResponse {
  clusters: EventCluster[];
  total: number;
  page: number;
  per_page: number;
}

export interface ClusterEventsResponse {
  cluster_id: string;
  events: IntelligenceEvent[];
  total: number;
  page: number;
  per_page: number;
}

export interface LatestEventsResponse {
  events: IntelligenceEvent[];
  total: number;
  limit: number;
}

export interface SubcategoriesResponse {
  subcategories: Subcategory[];
  total: number;
}

export interface RiskHistoryResponse {
  history: RiskHistoryEntry[];
  timeframe: string;
  total_points: number;
}

// Filter types
export interface ClusterFilters {
  category?: EventCategory;
  risk_level?: RiskLevel;
  min_events?: number;
  trending_only?: boolean;
  page?: number;
  per_page?: number;
}

export interface EventFilters {
  category?: EventCategory;
  risk_level?: RiskLevel;
  cluster_id?: string;
  limit?: number;
  offset?: number;
}

// Helper functions
export function getRiskLevelColor(level: RiskLevel): string {
  switch (level) {
    case 'low':
      return 'text-green-500';
    case 'medium':
      return 'text-yellow-500';
    case 'high':
      return 'text-orange-500';
    case 'critical':
      return 'text-red-500';
    default:
      return 'text-gray-500';
  }
}

export function getRiskLevelBgColor(level: RiskLevel): string {
  switch (level) {
    case 'low':
      return 'bg-green-500/10';
    case 'medium':
      return 'bg-yellow-500/10';
    case 'high':
      return 'bg-orange-500/10';
    case 'critical':
      return 'bg-red-500/10';
    default:
      return 'bg-gray-500/10';
  }
}

export function getCategoryColor(category: EventCategory): string {
  switch (category) {
    case 'breaking':
      return 'text-red-500';
    case 'developing':
      return 'text-orange-500';
    case 'trend':
      return 'text-blue-500';
    case 'recurring':
      return 'text-purple-500';
    case 'anomaly':
      return 'text-pink-500';
    default:
      return 'text-gray-500';
  }
}

export function getCategoryBgColor(category: EventCategory): string {
  switch (category) {
    case 'breaking':
      return 'bg-red-500/10';
    case 'developing':
      return 'bg-orange-500/10';
    case 'trend':
      return 'bg-blue-500/10';
    case 'recurring':
      return 'bg-purple-500/10';
    case 'anomaly':
      return 'bg-pink-500/10';
    default:
      return 'bg-gray-500/10';
  }
}

export function getCategoryIcon(category: EventCategory): string {
  switch (category) {
    case 'breaking':
      return 'zap';
    case 'developing':
      return 'trending-up';
    case 'trend':
      return 'bar-chart-2';
    case 'recurring':
      return 'repeat';
    case 'anomaly':
      return 'alert-triangle';
    default:
      return 'circle';
  }
}

export function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

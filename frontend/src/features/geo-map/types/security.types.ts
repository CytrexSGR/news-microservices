/**
 * Security View Types for Military/Intelligence Perspective
 *
 * These types match the backend schemas in geolocation-service/app/schemas/security.py
 */

// =============================================================================
// Enums
// =============================================================================

export type ThreatLevel = 'critical' | 'high' | 'medium' | 'low';

export type SecurityCategory = 'CONFLICT' | 'SECURITY' | 'HUMANITARIAN' | 'POLITICS';

export type TrendDirection = 'escalating' | 'stable' | 'de-escalating';

// =============================================================================
// Security Event
// =============================================================================

export interface SecurityEvent {
  id: string;
  article_id: string;
  title: string;
  country_code: string;
  country_name: string;
  lat: number;
  lon: number;

  // Classification
  category: string;
  threat_level: ThreatLevel;
  priority_score: number;

  // Tier1 metrics
  impact_score?: number;
  urgency_score?: number;

  // Tier2 geopolitical metrics
  conflict_severity?: number;
  diplomatic_impact?: number;
  regional_stability_risk?: number;
  countries_involved: string[];

  // Tier2 narrative metrics
  dominant_frame?: string;
  narrative_tension?: number;
  propaganda_detected: boolean;

  // Entities
  entities: Array<{
    name: string;
    type: string;
    role?: string;
    mentions?: number;
    confidence?: number;
  }>;

  // Temporal
  published_at?: string;
  created_at: string;
}

export interface SecurityEventList {
  events: SecurityEvent[];
  total: number;
  page: number;
  per_page: number;
  filters_applied: Record<string, unknown>;
}

// =============================================================================
// Country Threat Profile
// =============================================================================

export interface CountryThreatSummary {
  country_code: string;
  country_name: string;
  lat: number;
  lon: number;
  region?: string;

  // Counts by category
  total_events: number;
  conflict_count: number;
  security_count: number;
  humanitarian_count: number;
  politics_count: number;

  // Severity metrics
  max_priority_score: number;
  avg_priority_score: number;
  max_threat_level: ThreatLevel;

  // Geopolitical metrics (averaged)
  avg_conflict_severity?: number;
  avg_regional_stability_risk?: number;
  avg_diplomatic_impact?: number;

  // Trend
  trend: TrendDirection;
  trend_change_percent: number;

  // Last update
  last_event_at?: string;
}

export interface CountryThreatDetail extends CountryThreatSummary {
  // Key entities in this country's events
  key_entities: Array<Record<string, unknown>>;

  // Geopolitical relations
  relations: Array<Record<string, unknown>>;

  // Recent events preview
  recent_events: SecurityEvent[];
}

// =============================================================================
// Security Overview (Dashboard)
// =============================================================================

export interface SecurityOverview {
  // Time range
  from_date: string;
  to_date: string;

  // Global counts
  total_events: number;
  critical_count: number;
  high_count: number;
  medium_count: number;

  // By category
  by_category: Record<string, number>;

  // By region
  by_region: Record<string, number>;

  // Top threat countries
  hotspots: CountryThreatSummary[];

  // Recent critical events
  critical_events: SecurityEvent[];

  // Trend comparison
  trend_vs_previous: Record<string, number>;
}

// =============================================================================
// Security Marker (for map)
// =============================================================================

export interface SecurityMarker {
  id: string;
  lat: number;
  lon: number;
  country_code: string;

  // Threat classification
  threat_level: ThreatLevel;
  category: string;

  // Content
  title: string;
  summary?: string;

  // Metrics
  priority_score: number;
  conflict_severity?: number;
  impact_score?: number;

  // Context
  entities: string[];
  countries_involved: string[];
  article_count: number;

  // Temporal
  first_seen: string;
  last_update: string;

  // Analysis flags
  dominant_frame?: string;
  propaganda_detected: boolean;
}

// =============================================================================
// Filter Options
// =============================================================================

export interface SecurityFilters {
  days: number;
  min_priority: number;
  category?: SecurityCategory;
  country?: string;
  region?: string;
  threat_level?: ThreatLevel;
}

// =============================================================================
// Threat Level Styling
// =============================================================================

export const THREAT_LEVEL_COLORS: Record<ThreatLevel, string> = {
  critical: '#dc2626', // red-600
  high: '#ea580c', // orange-600
  medium: '#ca8a04', // yellow-600
  low: '#16a34a', // green-600
};

export const THREAT_LEVEL_BG_COLORS: Record<ThreatLevel, string> = {
  critical: 'bg-red-100',
  high: 'bg-orange-100',
  medium: 'bg-yellow-100',
  low: 'bg-green-100',
};

export const THREAT_LEVEL_TEXT_COLORS: Record<ThreatLevel, string> = {
  critical: 'text-red-800',
  high: 'text-orange-800',
  medium: 'text-yellow-800',
  low: 'text-green-800',
};

export const CATEGORY_ICONS: Record<SecurityCategory, string> = {
  CONFLICT: '⚔️',
  SECURITY: '🛡️',
  HUMANITARIAN: '🏥',
  POLITICS: '🏛️',
};

// =============================================================================
// Watchlist Types
// =============================================================================

export type WatchlistItemType = 'entity' | 'country' | 'keyword' | 'region';

export interface WatchlistItem {
  id: string;
  user_id: string;
  item_type: WatchlistItemType;
  item_value: string;
  display_name: string | null;
  notes: string | null;
  priority: number;
  notify_on_new: boolean;
  notify_threshold: number;
  created_at: string;
  updated_at: string;
  match_count_24h: number;
  match_count_7d: number;
  last_match_at: string | null;
}

export interface WatchlistItemCreate {
  item_type: WatchlistItemType;
  item_value: string;
  display_name?: string;
  notes?: string;
  priority?: number;
  notify_on_new?: boolean;
  notify_threshold?: number;
}

export interface SecurityAlertItem {
  id: string;
  watchlist_id: string;
  article_id: string;
  title: string;
  priority_score: number;
  threat_level: ThreatLevel;
  country_code: string | null;
  matched_value: string;
  is_read: boolean;
  created_at: string;
}

export interface AlertList {
  alerts: SecurityAlertItem[];
  total: number;
  unread_count: number;
  page: number;
  per_page: number;
}

export interface AlertStats {
  total_unread: number;
  critical_unread: number;
  high_unread: number;
  last_alert_at: string | null;
}

// Icon mapping for watchlist types
export const WATCHLIST_TYPE_ICONS: Record<WatchlistItemType, string> = {
  entity: '👤',
  country: '🌍',
  keyword: '🔍',
  region: '📍',
};

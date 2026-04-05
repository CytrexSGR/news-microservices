export interface Country {
  iso_code: string;
  name: string;
  name_de?: string;
  region?: string;
  article_count_24h: number;
  article_count_7d: number;
  centroid?: [number, number]; // [lon, lat]
}

export interface MapMarker {
  id: string;
  lat: number;
  lon: number;
  country_code: string;
  article_id: string;
  title: string;
  category?: string;
  impact_score?: number;
}

export interface GeoFilters {
  timeRange: 'today' | '7d' | '30d' | 'custom';
  dateFrom?: Date;
  dateTo?: Date;
  regions: string[];
  categories: string[];
}

export interface GeoWebSocketMessage {
  type: 'connected' | 'heartbeat' | 'subscribed' | 'article_new' | 'stats_update' | 'pong' | 'error';
  client_id?: string;
  timestamp?: string;
  data?: unknown;
  filters?: Record<string, unknown>;
  message?: string;
}

export type ViewMode = 'countries' | 'heatmap';

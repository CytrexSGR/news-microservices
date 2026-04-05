export type GlobeViewMode = 'standard' | 'nvg' | 'flir' | 'threat';

export type DataLayerType =
  | 'news-events'
  | 'flights'
  | 'vessels'
  | 'satellites'
  | 'earthquakes'
  | 'gdelt'
  | 'anomalies';

export interface DataLayerConfig {
  type: DataLayerType;
  visible: boolean;
  opacity: number;
}

export interface SpatialEntity {
  id: string;
  type: DataLayerType;
  lat: number;
  lon: number;
  alt?: number;
  heading?: number;
  velocity?: number;
  label?: string;
  metadata?: Record<string, unknown>;
  timestamp: number;
}

export interface DCAAlert {
  id: string;
  lat: number;
  lon: number;
  radius: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  type: string;
  signals: string[];
  kValue: number;
  timestamp: number;
  description: string;
}

export interface GlobeCamera {
  lat: number;
  lon: number;
  height: number;
  heading: number;
  pitch: number;
}

export interface GraphDomainStats {
  domain: string;
  nodes: number;
  edges: number;
  avg_weight: number;
  min_weight: number;
  max_weight: number;
  edge_types: Record<string, number>;
}

export interface GraphState {
  flight: GraphDomainStats | null;
  vessel: GraphDomainStats | null;
  satellite: GraphDomainStats | null;
}

export interface GraphEdge {
  u: string;
  v: string;
  u_lat: number;
  u_lon: number;
  v_lat: number;
  v_lon: number;
  weight: number;
  edge_type: string;
}

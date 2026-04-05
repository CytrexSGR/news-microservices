import { create } from 'zustand';
import type {
  GlobeViewMode,
  DataLayerConfig,
  SpatialEntity,
  DCAAlert,
  GlobeCamera,
  DataLayerType,
  GraphState,
  GraphEdge,
} from '../types/globe.types';

export type EdgeLayerType =
  | 'proximity'
  | 'same-operator'
  | 'same-orbit'
  | 'cross-domain';

export interface EdgeLayerConfig {
  type: EdgeLayerType;
  label: string;
  visible: boolean;
  color: string;
}

interface GlobeStore {
  viewMode: GlobeViewMode;
  setViewMode: (mode: GlobeViewMode) => void;
  camera: GlobeCamera;
  setCamera: (camera: Partial<GlobeCamera>) => void;
  layers: DataLayerConfig[];
  toggleLayer: (type: DataLayerType) => void;
  setLayerOpacity: (type: DataLayerType, opacity: number) => void;
  edgeLayers: EdgeLayerConfig[];
  toggleEdgeLayer: (type: EdgeLayerType) => void;
  entities: Map<string, SpatialEntity>;
  upsertEntity: (entity: SpatialEntity) => void;
  upsertEntities: (entities: SpatialEntity[]) => void;
  removeEntity: (id: string) => void;
  alerts: DCAAlert[];
  addAlert: (alert: DCAAlert) => void;
  clearAlerts: () => void;
  graphState: GraphState;
  updateGraphState: (state: Partial<GraphState>) => void;
  graphEdges: GraphEdge[];
  setGraphEdges: (edges: GraphEdge[]) => void;
  selectedEntityId: string | null;
  setSelectedEntity: (id: string | null) => void;
}

const DEFAULT_LAYERS: DataLayerConfig[] = [
  { type: 'news-events', visible: true, opacity: 1 },
  { type: 'flights', visible: true, opacity: 0.8 },
  { type: 'vessels', visible: true, opacity: 0.8 },
  { type: 'satellites', visible: true, opacity: 0.6 },
  { type: 'earthquakes', visible: true, opacity: 1 },
  { type: 'gdelt', visible: true, opacity: 0.7 },
  { type: 'anomalies', visible: true, opacity: 1 },
];

const DEFAULT_EDGE_LAYERS: EdgeLayerConfig[] = [
  { type: 'proximity', label: 'Proximity', visible: false, color: '#ffff00' },
  { type: 'same-operator', label: 'Same Operator', visible: false, color: '#ff8c00' },
  { type: 'same-orbit', label: 'Same Orbit', visible: false, color: '#ffffff' },
  { type: 'cross-domain', label: 'Cross-Domain', visible: false, color: '#ff00ff' },
];

export const useGlobeStore = create<GlobeStore>((set) => ({
  viewMode: 'standard',
  setViewMode: (mode) => set({ viewMode: mode }),
  camera: { lat: 50, lon: 10, height: 15_000_000, heading: 0, pitch: -90 },
  setCamera: (partial) =>
    set((s) => ({ camera: { ...s.camera, ...partial } })),

  layers: DEFAULT_LAYERS,
  toggleLayer: (type) =>
    set((s) => ({
      layers: s.layers.map((l) =>
        l.type === type ? { ...l, visible: !l.visible } : l
      ),
    })),
  setLayerOpacity: (type, opacity) =>
    set((s) => ({
      layers: s.layers.map((l) =>
        l.type === type ? { ...l, opacity } : l
      ),
    })),

  edgeLayers: DEFAULT_EDGE_LAYERS,
  toggleEdgeLayer: (type) =>
    set((s) => ({
      edgeLayers: s.edgeLayers.map((l) =>
        l.type === type ? { ...l, visible: !l.visible } : l
      ),
    })),

  entities: new Map(),
  upsertEntity: (entity) =>
    set((s) => {
      const next = new Map(s.entities);
      next.set(entity.id, entity);
      return { entities: next };
    }),
  upsertEntities: (entities) =>
    set((s) => {
      const next = new Map(s.entities);
      for (const e of entities) next.set(e.id, e);
      return { entities: next };
    }),
  removeEntity: (id) =>
    set((s) => {
      const next = new Map(s.entities);
      next.delete(id);
      return { entities: next };
    }),

  alerts: [],
  addAlert: (alert) =>
    set((s) => ({ alerts: [...s.alerts.slice(-99), alert] })),
  clearAlerts: () => set({ alerts: [] }),

  graphState: { flight: null, vessel: null, satellite: null },
  updateGraphState: (state) =>
    set((s) => ({ graphState: { ...s.graphState, ...state } })),

  graphEdges: [],
  setGraphEdges: (edges) => set({ graphEdges: edges }),
  selectedEntityId: null,
  setSelectedEntity: (id) => set({ selectedEntityId: id }),
}));

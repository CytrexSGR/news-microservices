import { create } from "zustand";

export interface NodeView {
  id: string;
  lat: number;
  lon: number;
  node_type: string;
  label?: string;
  weight?: number;
  [key: string]: unknown;
}

export interface EdgeView {
  u: string;
  v: string;
  weight: number;
  edge_type: string;
}

export interface ClusterView {
  lat: number;
  lon: number;
  count: number;
  dominant_type: string;
}

export interface BBox {
  lat_min: number;
  lat_max: number;
  lon_min: number;
  lon_max: number;
}

export interface GraphSlice {
  layers: string[];
  bbox?: BBox | null;
  context?: string[];
  semantic?: string | null;
  max_entities?: number;
  min_weight?: number;
}

export interface SliceState {
  nodes: Map<string, NodeView>;
  edges: Map<string, EdgeView>;
  clusters: ClusterView[];
  seq: number;
  totalMatching: number;
}

interface SliceStoreState {
  slices: Map<string, SliceState>;
  activeSliceId: string;
  alertCount: number;

  applySnapshot: (sliceId: string, data: {
    nodes: NodeView[];
    edges: EdgeView[];
    seq: number;
    total_matching: number;
  }) => void;

  applyDelta: (sliceId: string, data: {
    seq: number;
    added_nodes: NodeView[];
    removed_node_ids: string[];
    updated_nodes: NodeView[];
    added_edges: EdgeView[];
    removed_edge_keys: [string, string][];
    total_matching: number;
  }) => void;

  addAlert: (alert: { entity_id: string; reason: string; surprisal: number }) => void;

  updateLOD: (sliceId: string, data: {
    total_matching: number;
    clusters: ClusterView[];
  }) => void;

  setActiveSlice: (sliceId: string) => void;
}

function edgeKey(u: string, v: string): string {
  return u < v ? `${u}|${v}` : `${v}|${u}`;
}

export const useSliceStore = create<SliceStoreState>((set) => ({
  slices: new Map(),
  activeSliceId: "main",
  alertCount: 0,

  applySnapshot: (sliceId, data) =>
    set((state) => {
      const nodes = new Map<string, NodeView>();
      for (const n of data.nodes) nodes.set(n.id, n);
      const edges = new Map<string, EdgeView>();
      for (const e of data.edges) edges.set(edgeKey(e.u, e.v), e);
      const slices = new Map(state.slices);
      slices.set(sliceId, {
        nodes, edges, clusters: [], seq: data.seq,
        totalMatching: data.total_matching,
      });
      return { slices };
    }),

  applyDelta: (sliceId, data) =>
    set((state) => {
      const prev = state.slices.get(sliceId);
      if (!prev) return state;
      const nodes = new Map(prev.nodes);
      for (const n of data.added_nodes) nodes.set(n.id, n);
      for (const id of data.removed_node_ids) nodes.delete(id);
      for (const n of data.updated_nodes) nodes.set(n.id, n);
      const edges = new Map(prev.edges);
      for (const e of data.added_edges) edges.set(edgeKey(e.u, e.v), e);
      for (const [u, v] of data.removed_edge_keys) edges.delete(edgeKey(u, v));
      const slices = new Map(state.slices);
      slices.set(sliceId, {
        nodes, edges, clusters: prev.clusters, seq: data.seq,
        totalMatching: data.total_matching,
      });
      return { slices };
    }),

  addAlert: () =>
    set((state) => ({ alertCount: state.alertCount + 1 })),

  updateLOD: (sliceId, data) =>
    set((state) => {
      const prev = state.slices.get(sliceId);
      if (!prev) return state;
      const slices = new Map(state.slices);
      slices.set(sliceId, {
        ...prev, clusters: data.clusters, totalMatching: data.total_matching,
      });
      return { slices };
    }),

  setActiveSlice: (sliceId) => set({ activeSliceId: sliceId }),
}));

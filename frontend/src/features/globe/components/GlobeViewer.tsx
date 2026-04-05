import {
  Ion,
  Color,
  Cartesian3,
  OpenStreetMapImageryProvider,
  PostProcessStage,
  EllipsoidTerrainProvider,
  Viewer as CesiumViewer,
  PointPrimitiveCollection,
  PolylineCollection,
  Material,
  NearFarScalar,
} from 'cesium';
import 'cesium/Build/Cesium/Widgets/widgets.css';
import { useRef, useCallback, useMemo, useEffect } from 'react';
import { useGlobeStore } from '../store/globeStore';
import type { EdgeLayerType } from '../store/globeStore';
import { useGeoWebSocket } from '../hooks/useGeoWebSocket';
import { useGeoData } from '../hooks/useGeoData';
import { useSpatialWebSocket } from '../hooks/useSpatialWebSocket';
import { TDAPanel } from "./TDAPanel";
import { PatternPanel } from "./PatternPanel";
import { GraphPulsePanel } from "./GraphPulsePanel";
import { FilterPanel } from "./FilterPanel";
import { NVG_FRAGMENT_SHADER } from '../shaders/nvgShader';
import { FLIR_FRAGMENT_SHADER } from '../shaders/flirShader';
import { useGraphWebSocket } from "../hooks/useGraphWebSocket";
import { useCameraViewport } from "../hooks/useCameraViewport";
import { useSliceStore } from "../store/sliceStore";

Ion.defaultAccessToken = '';

const TYPE_COLORS: Record<string, Color> = {
  'news-events': Color.ORANGE,
  earthquakes: Color.RED,
  gdelt: Color.CYAN,
  flights: Color.YELLOW,
  vessels: Color.CORNFLOWERBLUE,
  satellites: Color.WHITE,
  anomalies: Color.MAGENTA,
};

const TYPE_SIZES: Record<string, number> = {
  'news-events': 8,
  earthquakes: 12,
  gdelt: 6,
  flights: 6,
  vessels: 7,
  satellites: 4,
  anomalies: 14,
};

const GRAPH_TYPE_MAP: Record<string, string> = {
  vessel: 'vessels',
  flight: 'flights',
  satellite: 'satellites',
};

const SEVERITY_COLORS: Record<string, Color> = {
  low: Color.YELLOW.withAlpha(0.25),
  medium: Color.ORANGE.withAlpha(0.35),
  high: Color.RED.withAlpha(0.45),
  critical: Color.DARKRED.withAlpha(0.55),
};

const SEVERITY_OUTLINE: Record<string, Color> = {
  low: Color.YELLOW,
  medium: Color.ORANGE,
  high: Color.RED,
  critical: Color.DARKRED,
};

// Map raw edge_type strings to EdgeLayerType for filtering
function edgeTypeToLayer(edgeType: string): EdgeLayerType {
  if (edgeType === 'same_orbit') return 'same-orbit';
  if (edgeType.startsWith('cross:')) return 'cross-domain';
  if (edgeType === 'proximity') return 'proximity';
  if (edgeType === 'same-operator') return 'same-operator';
  if (edgeType === 'voyage') return 'voyage';
  if (edgeType === 'orbit') return 'same-orbit';
  return 'cross-domain'; // fallback
}

const EDGE_TYPE_COLORS: Record<string, [Color, number]> = {
  'proximity': [Color.YELLOW, 1.0],
  'same-operator': [Color.ORANGE, 0.5],
  'voyage': [Color.CORNFLOWERBLUE, 1.0],
  'orbit': [Color.WHITE, 0.5],
  'same_orbit': [Color.WHITE, 0.5],
  'cross:flight-vessel': [Color.MAGENTA, 1.5],
  'cross:vessel-flight': [Color.MAGENTA, 1.5],
  'cross:flight-satellite': [Color.LIME, 1.0],
  'cross:satellite-flight': [Color.LIME, 1.0],
  'cross:vessel-satellite': [Color.AQUA, 1.0],
  'cross:satellite-vessel': [Color.AQUA, 1.0],
};

export function GlobeViewer() {
  const viewerRef = useRef<CesiumViewer | null>(null);
  const viewMode = useGlobeStore((s) => s.viewMode);
  const entities = useGlobeStore((s) => s.entities);
  const layers = useGlobeStore((s) => s.layers);
  const alerts = useGlobeStore((s) => s.alerts);
  const edgeLayers = useGlobeStore((s) => s.edgeLayers);

  useGeoWebSocket();
  useGeoData();
  useSpatialWebSocket();

  const { updateViewport } = useGraphWebSocket();
  const activeSlice = useSliceStore((s) => s.slices.get(s.activeSliceId));
  const graphNodeCount = activeSlice?.nodes.size ?? 0;
  const graphEdgeCount = activeSlice?.edges.size ?? 0;

  useCameraViewport(viewerRef.current, updateViewport, 300);

  useEffect(() => {
    console.log(`[graph-store] ${graphNodeCount} nodes, ${graphEdgeCount} edges`);
  }, [graphNodeCount, graphEdgeCount]);

  // Visible edge types set
  const visibleEdgeTypes = useMemo(
    () => new Set(edgeLayers.filter((l) => l.visible).map((l) => l.type)),
    [edgeLayers]
  );

  useEffect(() => {
    (window as any).__GLOBE_DEBUG__ = {
      getEntities: () => entities.size,
      getVisible: () => visibleEntities.length,
      getLayers: () => layers.map(l => l.type + ':' + l.visible),
      getAlerts: () => alerts.length,
      getViewer: () => viewerRef.current,
      getEntityTypes: () => {
        const types: Record<string, number> = {};
        entities.forEach(e => { types[e.type] = (types[e.type] || 0) + 1; });
        return types;
      },
    };
  });

  const visibleTypes = useMemo(
    () => new Set(layers.filter((l) => l.visible).map((l) => l.type)),
    [layers]
  );

  const visibleEntities = useMemo(
    () => Array.from(entities.values()).filter((e) => visibleTypes.has(e.type)),
    [entities, visibleTypes]
  );

  const showAnomalies = useMemo(
    () => layers.find((l) => l.type === 'anomalies')?.visible ?? true,
    [layers]
  );

  const initViewer = useCallback((container: HTMLDivElement | null) => {
    if (!container || viewerRef.current) return;

    const viewer = new CesiumViewer(container, {
      timeline: false,
      animation: false,
      homeButton: false,
      geocoder: false,
      navigationHelpButton: false,
      baseLayerPicker: false,
      sceneModePicker: false,
      fullscreenButton: false,
      selectionIndicator: false,
      infoBox: false,
      scene3DOnly: true,
      terrainProvider: new EllipsoidTerrainProvider(),
      imageryProvider: false as any,
      requestRenderMode: true,
      maximumRenderTimeChange: Infinity,
    });

    viewerRef.current = viewer;

    const creditContainer = viewer.cesiumWidget.creditContainer as HTMLElement;
    creditContainer.style.display = 'none';

    viewer.scene.globe.showGroundAtmosphere = false;
    viewer.scene.globe.depthTestAgainstTerrain = false;
    viewer.scene.globe.enableLighting = true;

    viewer.imageryLayers.removeAll();
    viewer.imageryLayers.addImageryProvider(
      new OpenStreetMapImageryProvider({
        url: 'https://tile.openstreetmap.org/',
      })
    );

    viewer.camera.flyTo({
      destination: Cartesian3.fromDegrees(10, 50, 15_000_000),
      duration: 0,
    });
  }, []);

  useEffect(() => {
    return () => {
      if (viewerRef.current && !viewerRef.current.isDestroyed()) {
        viewerRef.current.destroy();
        viewerRef.current = null;
      }
    };
  }, []);

  // Render entities via PointPrimitiveCollection (GPU-batched) + DCA alerts as Entities
  const pointCollectionRef = useRef<PointPrimitiveCollection | null>(null);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || viewer.isDestroyed()) return;

    if (pointCollectionRef.current) {
      viewer.scene.primitives.remove(pointCollectionRef.current);
      pointCollectionRef.current = null;
    }

    const points = new PointPrimitiveCollection();
    for (const e of visibleEntities) {
      const color = TYPE_COLORS[e.type] || Color.WHITE;
      const size = TYPE_SIZES[e.type] || 8;
      points.add({
        position: Cartesian3.fromDegrees(e.lon, e.lat, e.alt || 0),
        pixelSize: size,
        color,
        outlineColor: Color.BLACK,
        outlineWidth: 1,
        scaleByDistance: new NearFarScalar(1e3, 1.2, 1.5e7, 0.5),
      });
    }
    viewer.scene.primitives.add(points);
    pointCollectionRef.current = points;

    viewer.entities.removeAll();
    if (showAnomalies) {
      for (const alert of alerts) {
        const severity = alert.severity || 'low';
        const radiusKm = alert.radius || 200;
        const fillColor = SEVERITY_COLORS[severity] || SEVERITY_COLORS.low;
        const outlineColor = SEVERITY_OUTLINE[severity] || SEVERITY_OUTLINE.low;

        viewer.entities.add({
          position: Cartesian3.fromDegrees(alert.lon, alert.lat),
          name: alert.description || 'DCA Alert: ' + severity,
          description: alert.description || '',
          ellipse: {
            semiMajorAxis: radiusKm * 1000,
            semiMinorAxis: radiusKm * 1000,
            material: fillColor,
            outline: true,
            outlineColor,
            outlineWidth: 2,
          },
          point: {
            pixelSize: 16,
            color: outlineColor,
            outlineColor: Color.WHITE,
            outlineWidth: 2,
          },
        });
      }
    }

    viewer.scene.requestRender();
  }, [visibleEntities, alerts, showAnomalies]);

  // --- Render graph nodes from SliceStore ---
  const graphPointsRef = useRef<PointPrimitiveCollection | null>(null);
  const graphNodes = activeSlice?.nodes;

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || viewer.isDestroyed()) return;

    if (graphPointsRef.current) {
      viewer.scene.primitives.remove(graphPointsRef.current);
      graphPointsRef.current = null;
    }

    if (!graphNodes || graphNodes.size === 0) return;

    const points = new PointPrimitiveCollection();
    for (const node of graphNodes.values()) {
      const renderType = GRAPH_TYPE_MAP[node.node_type] || node.node_type;
      if (!visibleTypes.has(renderType)) continue;
      const baseColor = TYPE_COLORS[renderType] || Color.WHITE;
      const size = TYPE_SIZES[renderType] || 7;
      const anomalyScore = (node.anomaly_score as number) || 0;
      const color = anomalyScore > 0
        ? Color.lerp(baseColor, Color.RED, Math.min(1.0, anomalyScore), new Color())
        : baseColor;
      const pointSize = anomalyScore > 0 ? size + anomalyScore * 6 : size;
      points.add({
        position: Cartesian3.fromDegrees(node.lon, node.lat, 0),
        pixelSize: pointSize,
        color,
        outlineColor: anomalyScore > 0.5 ? Color.RED : Color.BLACK,
        outlineWidth: anomalyScore > 0.5 ? 2 : 1,
        scaleByDistance: new NearFarScalar(1e3, 1.2, 1.5e7, 0.5),
      });
    }
    viewer.scene.primitives.add(points);
    graphPointsRef.current = points;
    viewer.scene.requestRender();
  }, [graphNodes, visibleTypes]);

  // Apply NVG/FLIR shaders
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || viewer.isDestroyed()) return;

    const stages = viewer.scene.postProcessStages;
    stages.removeAll();

    if (viewMode === 'nvg') {
      viewer.scene.globe.baseColor = Color.fromCssColorString('#001100');
      stages.add(new PostProcessStage({ fragmentShader: NVG_FRAGMENT_SHADER }));
    } else if (viewMode === 'flir') {
      viewer.scene.globe.baseColor = Color.BLUE;
      stages.add(new PostProcessStage({ fragmentShader: FLIR_FRAGMENT_SHADER }));
    } else {
      viewer.scene.globe.baseColor = Color.fromCssColorString('#000011');
    }
    viewer.scene.requestRender();
  }, [viewMode]);

  // --- Multi-domain edge rendering from SliceStore (filtered by edgeLayers) ---
  const edgeCollectionRef = useRef<PolylineCollection | null>(null);
  const graphEdges = activeSlice?.edges;

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || viewer.isDestroyed()) return;

    if (edgeCollectionRef.current) {
      viewer.scene.primitives.remove(edgeCollectionRef.current);
      edgeCollectionRef.current = null;
    }

    if (!graphEdges || graphEdges.size === 0 || !graphNodes) return;

    // Skip entirely if no edge layers are visible
    if (visibleEdgeTypes.size === 0) {
      viewer.scene.requestRender();
      return;
    }

    const lines = new PolylineCollection();
    for (const edge of graphEdges.values()) {
      // Filter by edge layer visibility
      const layerType = edgeTypeToLayer(edge.edge_type);
      if (!visibleEdgeTypes.has(layerType)) continue;

      const nodeU = graphNodes.get(edge.u);
      const nodeV = graphNodes.get(edge.v);
      if (!nodeU || !nodeV) continue;

      const alpha = Math.max(0.1, Math.min(0.8, edge.weight));
      const [baseColor, baseWidth] = EDGE_TYPE_COLORS[edge.edge_type] || [Color.GRAY, 0.5];
      const color = baseColor.withAlpha(alpha * 0.4);

      lines.add({
        positions: Cartesian3.fromDegreesArrayHeights([
          nodeU.lon, nodeU.lat, 0,
          nodeV.lon, nodeV.lat, 0,
        ]),
        width: baseWidth,
        material: Material.fromType('Color', { color }),
      });
    }

    viewer.scene.primitives.add(lines);
    edgeCollectionRef.current = lines;
    viewer.scene.requestRender();
  }, [graphEdges, graphNodes, visibleEdgeTypes]);

  return (
    <div className="w-full h-full relative">
      <div ref={initViewer} className="w-full h-full" />
      <TDAPanel />
      <PatternPanel />
      <GraphPulsePanel />
      <FilterPanel />
      {alerts.length > 0 && showAnomalies && (
        <div className="absolute bottom-4 left-4 right-72 bg-red-900/80 backdrop-blur-sm border border-red-500 rounded-lg p-3 z-10 max-h-32 overflow-y-auto">
          <h4 className="text-xs font-bold text-red-300 mb-1">DCA ALERTS ({alerts.length})</h4>
          {alerts.slice(-5).reverse().map((a) => (
            <div key={a.id} className="text-xs text-red-100 truncate">
              [{a.severity?.toUpperCase() || 'LOW'}] {a.description} — k={a.kValue?.toFixed(2) || '?'}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

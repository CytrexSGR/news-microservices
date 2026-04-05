import { useEffect, useRef } from 'react';
import { useGlobeStore } from '../store/globeStore';
import type { SpatialEntity, DCAAlert } from '../types/globe.types';

// Map backend event types to frontend layer types
const TYPE_MAP: Record<string, string> = {
  flight: 'flights',
  vessel: 'vessels',
  earthquake: 'earthquakes',
  satellite: 'satellites',
  gdelt: 'gdelt',
  news: 'news-events',
};

export function useSpatialWebSocket() {
  const upsertEntities = useGlobeStore((s) => s.upsertEntities);
  const addAlert = useGlobeStore((s) => s.addAlert);
  const updateGraphState = useGlobeStore((s) => s.updateGraphState);
  const setGraphEdges = useGlobeStore((s) => s.setGraphEdges);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let cancelled = false;

    const connect = () => {
      if (cancelled) return;
      // Clean up previous connection
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WebSocket(
        `${protocol}//${window.location.hostname}:8124/ws/spatial`
      );
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[SpatialWS] Connected');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // Graph state update (object with type field)
          if (data?.type === 'graph_update' && data.data) {
            updateGraphState(data.data);
            // Fetch top edges for visualization
            const flightStats = data.data.flight;
            if (flightStats && flightStats.edges > 0) {
              fetch(`http://${window.location.hostname}:8124/api/graph/edges/flight?limit=500&min_weight=0.5`)
                .then(r => r.json())
                .then(d => { if (d.edges) setGraphEdges(d.edges); })
                .catch(() => {});
            } else {
              setGraphEdges([]);
            }
            return;
          }

          if (!Array.isArray(data)) return;

          const entities: SpatialEntity[] = [];
          for (const item of data) {
            if (item.type === 'anomaly') {
              const alert: DCAAlert = {
                id: item.id,
                lat: item.lat,
                lon: item.lon,
                radius: item.metadata?.radius_km || 200,
                severity: item.metadata?.severity || 'low',
                type: 'anomaly',
                signals: item.metadata?.signals || [],
                kValue: item.metadata?.k_value || 0,
                timestamp: new Date(item.timestamp).getTime(),
                description: item.metadata?.description || item.label || '',
              };
              addAlert(alert);
            } else {
              const mappedType = TYPE_MAP[item.type] || item.type;
              entities.push({
                id: item.id,
                type: mappedType,
                lat: item.lat,
                lon: item.lon,
                alt: item.alt,
                heading: item.heading,
                velocity: item.velocity,
                label: item.label || '',
                metadata: item.metadata || {},
                timestamp: new Date(item.timestamp).getTime(),
              });
            }
          }
          if (entities.length > 0) {
            upsertEntities(entities);
          }
        } catch {
          // ignore parse errors
        }
      };

      ws.onclose = () => {
        console.log('[SpatialWS] Disconnected, reconnecting in 5s...');
        if (!cancelled) {
          reconnectRef.current = setTimeout(connect, 5000);
        }
      };

      ws.onerror = () => ws.close();
    };

    connect();

    return () => {
      cancelled = true;
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [upsertEntities, addAlert, updateGraphState, setGraphEdges]);
}

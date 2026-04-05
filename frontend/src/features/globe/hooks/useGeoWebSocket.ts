import { useEffect, useRef, useCallback } from 'react';
import { useGlobeStore } from '../store/globeStore';
import type { SpatialEntity } from '../types/globe.types';

const getWsUrl = () => {
  const hostname = window.location.hostname;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${hostname}:8115/ws/geo-live`;
};

export function useGeoWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const upsertEntity = useGlobeStore((s) => s.upsertEntity);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(getWsUrl());
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[GlobeWS] Connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'article_new' && data.data) {
          const d = data.data;
          if (d.lat != null && d.lon != null) {
            const entity: SpatialEntity = {
              id: `news-${d.article_id}`,
              type: 'news-events',
              lat: d.lat,
              lon: d.lon,
              label: d.title || 'News Event',
              metadata: d,
              timestamp: Date.now(),
            };
            upsertEntity(entity);
          }
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onclose = () => {
      console.log('[GlobeWS] Disconnected, reconnecting in 5s...');
      setTimeout(() => {
        if (wsRef.current === ws) {
          wsRef.current = null;
          connect();
        }
      }, 5000);
    };
  }, [upsertEntity]);

  useEffect(() => {
    connect();
    return () => {
      const ws = wsRef.current;
      wsRef.current = null;
      ws?.close();
    };
  }, [connect]);
}

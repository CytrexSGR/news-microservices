import { useEffect, useRef, useCallback } from 'react';
import { useGeoMapStore } from '../store/geoMapStore';
import type { GeoWebSocketMessage } from '../types/geo.types';

// Use dynamic host detection for network access
const getWsUrl = () => {
  const hostname = window.location.hostname;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${hostname}:8115/ws/geo-live`;
};

const WS_URL = getWsUrl();

export function useGeoWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const { filters, addNewArticle } = useGeoMapStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log('[GeoWS] Connected');
      ws.send(JSON.stringify({
        action: 'subscribe',
        filters: { regions: filters.regions },
      }));
    };

    ws.onmessage = (event) => {
      const message: GeoWebSocketMessage = JSON.parse(event.data);

      switch (message.type) {
        case 'article_new':
          const data = message.data as { article_id: string };
          addNewArticle(data.article_id);
          break;
        case 'heartbeat':
          break;
        case 'error':
          console.error('[GeoWS] Error:', message.message);
          break;
      }
    };

    ws.onclose = () => {
      console.log('[GeoWS] Disconnected, reconnecting in 5s...');
      setTimeout(connect, 5000);
    };

    wsRef.current = ws;
  }, [filters.regions, addNewArticle]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  const updateSubscription = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'subscribe',
        filters: { regions: filters.regions },
      }));
    }
  }, [filters.regions]);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  useEffect(() => {
    updateSubscription();
  }, [updateSubscription]);

  return { connect, disconnect };
}

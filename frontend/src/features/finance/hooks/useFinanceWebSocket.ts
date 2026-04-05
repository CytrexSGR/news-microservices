/**
 * React Hook for Finance WebSocket
 *
 * Manages WebSocket connection lifecycle and provides real-time data updates
 */

import { useEffect, useRef, useState } from 'react';
import { FinanceWebSocket, type WSEventHandlers } from '../services/websocket';
import type { Quote, MarketStatusResponse } from '../types/market.types';
import type { SystemHealth } from '../types/system.types';

export interface FinanceWebSocketState {
  prices: Quote[];
  status: MarketStatusResponse | null;
  health: SystemHealth | null;
  connected: boolean;
  error: Event | null;
}

export interface FinanceWebSocketActions {
  connect: () => void;
  disconnect: () => void;
}

export function useFinanceWebSocket(
  autoConnect = true
): [FinanceWebSocketState, FinanceWebSocketActions] {
  const wsRef = useRef<FinanceWebSocket | null>(null);
  const [state, setState] = useState<FinanceWebSocketState>({
    prices: [],
    status: null,
    health: null,
    connected: false,
    error: null,
  });

  useEffect(() => {
    // Create WebSocket instance with event handlers
    const handlers: WSEventHandlers = {
      onPriceUpdate: (quotes) => {
        setState((prev) => ({ ...prev, prices: quotes }));
      },

      onStatusUpdate: (status) => {
        setState((prev) => ({ ...prev, status }));
      },

      onHealthUpdate: (health) => {
        setState((prev) => ({ ...prev, health }));
      },

      onConnect: () => {
        setState((prev) => ({ ...prev, connected: true, error: null }));
      },

      onDisconnect: () => {
        setState((prev) => ({ ...prev, connected: false }));
      },

      onError: (error) => {
        setState((prev) => ({ ...prev, error }));
      },
    };

    wsRef.current = new FinanceWebSocket(handlers);

    // Auto-connect if enabled
    if (autoConnect) {
      wsRef.current.connect();
    }

    // Cleanup on unmount
    return () => {
      wsRef.current?.disconnect();
    };
  }, [autoConnect]);

  const actions: FinanceWebSocketActions = {
    connect: () => wsRef.current?.connect(),
    disconnect: () => wsRef.current?.disconnect(),
  };

  return [state, actions];
}

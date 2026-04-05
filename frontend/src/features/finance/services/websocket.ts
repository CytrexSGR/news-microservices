/**
 * Finance Terminal WebSocket Service
 *
 * Manages real-time connections for:
 * - Price updates (1-second interval)
 * - Market status updates (60-second interval)
 * - System health updates (30-second interval)
 */

import type { Quote, MarketStatusResponse } from '../types/market.types';
import type { SystemHealth } from '../types/system.types';

const WS_URL = import.meta.env.VITE_FMP_WS_URL || 'ws://localhost:8113';

/**
 * WebSocket event types
 */
export type WSEventType = 'prices' | 'status' | 'health';

/**
 * WebSocket message payload
 */
export interface WSMessage<T> {
  type: WSEventType;
  data: T;
  timestamp: string;
}

/**
 * WebSocket event handlers
 */
export interface WSEventHandlers {
  onPriceUpdate?: (quotes: Quote[]) => void;
  onStatusUpdate?: (status: MarketStatusResponse) => void;
  onHealthUpdate?: (health: SystemHealth) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

/**
 * WebSocket connection manager
 */
export class FinanceWebSocket {
  private ws: WebSocket | null = null;
  private reconnectTimeout: number | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000; // 2 seconds
  private handlers: WSEventHandlers = {};

  constructor(handlers: WSEventHandlers = {}) {
    this.handlers = handlers;
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('[FinanceWS] Already connected');
      return;
    }

    try {
      console.log('[FinanceWS] Connecting to', WS_URL);
      this.ws = new WebSocket(`${WS_URL}/ws/finance`);

      this.ws.onopen = () => {
        console.log('[FinanceWS] Connected');
        this.reconnectAttempts = 0;
        this.handlers.onConnect?.();
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WSMessage<unknown>;
          this.handleMessage(message);
        } catch (error) {
          console.error('[FinanceWS] Failed to parse message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[FinanceWS] Error:', error);
        this.handlers.onError?.(error);
      };

      this.ws.onclose = () => {
        console.log('[FinanceWS] Disconnected');
        this.handlers.onDisconnect?.();
        this.attemptReconnect();
      };
    } catch (error) {
      console.error('[FinanceWS] Connection error:', error);
      this.attemptReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.reconnectAttempts = 0;
  }

  /**
   * Handle incoming WebSocket message
   */
  private handleMessage(message: WSMessage<unknown>): void {
    switch (message.type) {
      case 'prices':
        this.handlers.onPriceUpdate?.(message.data as Quote[]);
        break;

      case 'status':
        this.handlers.onStatusUpdate?.(message.data as MarketStatusResponse);
        break;

      case 'health':
        this.handlers.onHealthUpdate?.(message.data as SystemHealth);
        break;

      default:
        console.warn('[FinanceWS] Unknown message type:', message.type);
    }
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[FinanceWS] Max reconnect attempts reached');
      return;
    }

    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    console.log(`[FinanceWS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);

    this.reconnectTimeout = window.setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  /**
   * Get current connection state
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Update event handlers
   */
  setHandlers(handlers: WSEventHandlers): void {
    this.handlers = { ...this.handlers, ...handlers };
  }
}

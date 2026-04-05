type ConnectionStatus = 'connecting' | 'open' | 'closed' | 'error'

interface WebSocketMessage {
  widget_id: string
  data: any
}

interface WebSocketServiceOptions {
  reconnectInterval?: number
  maxReconnectAttempts?: number
  backoffMultiplier?: number
}

class WebSocketService {
  private ws: WebSocket | null = null
  private dashboardId: string | null = null
  private onMessageCallback: ((data: WebSocketMessage) => void) | null = null
  private reconnectAttempts = 0
  private reconnectTimer: number | null = null
  private status: ConnectionStatus = 'closed'
  private statusListeners: ((status: ConnectionStatus) => void)[] = []

  private options: Required<WebSocketServiceOptions> = {
    reconnectInterval: 1000, // Start with 1 second
    maxReconnectAttempts: 10,
    backoffMultiplier: 1.5,
  }

  constructor(options?: WebSocketServiceOptions) {
    if (options) {
      this.options = { ...this.options, ...options }
    }
  }

  /**
   * Connect to WebSocket endpoint for a specific dashboard
   */
  connect(dashboardId: string, onMessage: (data: WebSocketMessage) => void): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    this.dashboardId = dashboardId
    this.onMessageCallback = onMessage
    this.reconnectAttempts = 0
    this.establishConnection()
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    // Clear reconnect timer
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    // Close WebSocket
    if (this.ws) {
      this.ws.onclose = null // Prevent reconnection on intentional close
      this.ws.close()
      this.ws = null
    }

    this.dashboardId = null
    this.onMessageCallback = null
    this.reconnectAttempts = 0
    this.setStatus('closed')
  }

  /**
   * Get current connection status
   */
  getStatus(): ConnectionStatus {
    return this.status
  }

  /**
   * Subscribe to status changes
   */
  onStatusChange(listener: (status: ConnectionStatus) => void): () => void {
    this.statusListeners.push(listener)

    // Return unsubscribe function
    return () => {
      this.statusListeners = this.statusListeners.filter((l) => l !== listener)
    }
  }

  /**
   * Establish WebSocket connection
   */
  private establishConnection(): void {
    if (!this.dashboardId) {
      return
    }

    try {
      this.setStatus('connecting')

      // Determine WebSocket URL based on environment
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const analyticsUrl = import.meta.env.VITE_ANALYTICS_API_URL || 'http://localhost:8107/api/v1'
      const baseUrl = analyticsUrl.replace(/^https?:\/\//, '').replace(/\/api\/v1$/, '')
      const wsUrl = `${protocol}//${baseUrl}/api/v1/dashboards/${this.dashboardId}/ws`

      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = this.handleOpen.bind(this)
      this.ws.onmessage = this.handleMessage.bind(this)
      this.ws.onerror = this.handleError.bind(this)
      this.ws.onclose = this.handleClose.bind(this)
    } catch (error) {
      this.setStatus('error')
      this.scheduleReconnect()
    }
  }

  /**
   * Handle WebSocket open event
   */
  private handleOpen(): void {
    this.reconnectAttempts = 0
    this.setStatus('open')
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)

      if (this.onMessageCallback) {
        this.onMessageCallback(message)
      }
    } catch (error) {
      // Silently ignore malformed messages
    }
  }

  /**
   * Handle WebSocket error event
   */
  private handleError(_error: Event): void {
    this.setStatus('error')
  }

  /**
   * Handle WebSocket close event
   */
  private handleClose(_event: CloseEvent): void {
    this.setStatus('closed')
    this.ws = null

    // Attempt reconnection if not intentionally closed
    if (this.dashboardId && this.onMessageCallback) {
      this.scheduleReconnect()
    }
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      this.setStatus('error')
      return
    }

    // Calculate backoff delay with exponential increase
    const delay = this.options.reconnectInterval * Math.pow(
      this.options.backoffMultiplier,
      this.reconnectAttempts
    )

    this.reconnectAttempts++

    this.reconnectTimer = setTimeout(() => {
      this.establishConnection()
    }, delay)
  }

  /**
   * Update and notify status change
   */
  private setStatus(status: ConnectionStatus): void {
    if (this.status !== status) {
      this.status = status
      this.statusListeners.forEach((listener) => listener(status))
    }
  }
}

// Export singleton instance
export const websocketService = new WebSocketService()

// Export types
export type { ConnectionStatus, WebSocketMessage }

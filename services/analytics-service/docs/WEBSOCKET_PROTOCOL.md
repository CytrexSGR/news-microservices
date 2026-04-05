# WebSocket Protocol Documentation

## Overview

The Analytics Service provides real-time metrics streaming via WebSocket connections. This document describes the WebSocket protocol, message formats, and client implementation guidelines.

## Connection

### Endpoint

```
ws://localhost:8007/ws/metrics?token=<jwt_token>
```

### Authentication

Authentication is performed via JWT token passed as a query parameter:

```javascript
const token = "your_jwt_token_here";
const ws = new WebSocket(`ws://localhost:8007/ws/metrics?token=${token}`);
```

**Note:** Token must be obtained from the Auth Service before establishing WebSocket connection.

## Message Protocol

All messages are JSON-formatted. The protocol is bidirectional:
- **Client → Server**: Actions and commands
- **Server → Client**: Data updates, notifications, and heartbeats

### Message Types

#### 1. Connection Messages

**Connected (Server → Client)**

Sent immediately after successful connection:

```json
{
  "type": "connected",
  "client_id": "ws_andreas_1700000000.123",
  "timestamp": "2025-11-24T10:00:00Z"
}
```

**Heartbeat (Server → Client)**

Sent every 30 seconds to keep connection alive:

```json
{
  "type": "heartbeat",
  "timestamp": "2025-11-24T10:00:30Z"
}
```

#### 2. Subscription Messages

**Subscribe (Client → Server)**

Subscribe to a specific channel:

```json
{
  "action": "subscribe",
  "channel": "metrics"
}
```

Available channels:
- `metrics` - Real-time metrics updates
- `alerts` - System alerts (future)
- `events` - System events (future)

**Subscribed Confirmation (Server → Client)**

```json
{
  "type": "subscribed",
  "channel": "metrics"
}
```

**Unsubscribe (Client → Server)**

```json
{
  "action": "unsubscribe",
  "channel": "metrics"
}
```

**Unsubscribed Confirmation (Server → Client)**

```json
{
  "type": "unsubscribed",
  "channel": "metrics"
}
```

#### 3. Data Messages

**Get Metrics (Client → Server)**

Request current metrics snapshot:

```json
{
  "action": "get_metrics"
}
```

**Metrics Response (Server → Client)**

```json
{
  "type": "metrics",
  "data": {
    "timestamp": "2025-11-24T10:00:00Z",
    "services": {
      "auth-service": {
        "total_requests": 1234,
        "error_rate": 0.005,
        "avg_latency_ms": 45.2,
        "active_users": 150
      },
      "feed-service": {
        "total_requests": 5678,
        "error_rate": 0.001,
        "avg_latency_ms": 120.5,
        "active_users": 200
      }
    },
    "system_health": "healthy",
    "active_alerts": 0,
    "total_users": 350,
    "total_articles": 12500
  },
  "timestamp": "2025-11-24T10:00:00Z"
}
```

**Metrics Update (Server → Client)**

Broadcast to all clients subscribed to "metrics" (every 10 seconds):

```json
{
  "type": "metrics_update",
  "data": {
    // Same structure as metrics response
  },
  "timestamp": "2025-11-24T10:00:10Z"
}
```

#### 4. Control Messages

**Ping (Client → Server)**

Client can send ping to test connection:

```json
{
  "action": "ping"
}
```

**Pong (Server → Client)**

```json
{
  "type": "pong",
  "timestamp": "2025-11-24T10:00:00Z"
}
```

**Error (Server → Client)**

Sent when an error occurs:

```json
{
  "type": "error",
  "message": "Unknown action: invalid_action"
}
```

## Client Implementation

### Basic Example (JavaScript)

```javascript
class AnalyticsWebSocket {
  constructor(token) {
    this.token = token;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 1000; // Start with 1 second
  }

  connect() {
    this.ws = new WebSocket(`ws://localhost:8007/ws/metrics?token=${this.token}`);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;

      // Subscribe to metrics
      this.subscribe('metrics');
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.reconnect();
    };
  }

  handleMessage(message) {
    switch (message.type) {
      case 'connected':
        console.log('Connected with client_id:', message.client_id);
        break;

      case 'heartbeat':
        console.log('Heartbeat received');
        break;

      case 'metrics':
      case 'metrics_update':
        this.onMetricsUpdate(message.data);
        break;

      case 'subscribed':
        console.log('Subscribed to:', message.channel);
        break;

      case 'error':
        console.error('Server error:', message.message);
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }

  subscribe(channel) {
    this.send({
      action: 'subscribe',
      channel: channel
    });
  }

  unsubscribe(channel) {
    this.send({
      action: 'unsubscribe',
      channel: channel
    });
  }

  getMetrics() {
    this.send({
      action: 'get_metrics'
    });
  }

  ping() {
    this.send({
      action: 'ping'
    });
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error('WebSocket not connected');
    }
  }

  reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      60000 // Max 60 seconds
    );

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})...`);

    setTimeout(() => {
      this.connect();
    }, delay);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  onMetricsUpdate(data) {
    // Override this method in your implementation
    console.log('Metrics update:', data);
  }
}

// Usage
const analytics = new AnalyticsWebSocket('your_jwt_token');
analytics.connect();

// Custom metrics handler
analytics.onMetricsUpdate = (data) => {
  // Update your UI with new metrics
  document.getElementById('total-users').textContent = data.total_users;
  // ... update other UI elements
};
```

### Python Example

```python
import asyncio
import json
import websockets

class AnalyticsWebSocket:
    def __init__(self, token: str):
        self.token = token
        self.ws = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10

    async def connect(self):
        uri = f"ws://localhost:8007/ws/metrics?token={self.token}"

        try:
            async with websockets.connect(uri) as websocket:
                self.ws = websocket
                self.reconnect_attempts = 0

                # Subscribe to metrics
                await self.subscribe("metrics")

                # Message loop
                async for message in websocket:
                    data = json.loads(message)
                    await self.handle_message(data)

        except Exception as e:
            print(f"WebSocket error: {e}")
            await self.reconnect()

    async def handle_message(self, message: dict):
        msg_type = message.get("type")

        if msg_type == "connected":
            print(f"Connected with client_id: {message['client_id']}")

        elif msg_type == "heartbeat":
            print("Heartbeat received")

        elif msg_type in ["metrics", "metrics_update"]:
            await self.on_metrics_update(message["data"])

        elif msg_type == "subscribed":
            print(f"Subscribed to: {message['channel']}")

        elif msg_type == "error":
            print(f"Server error: {message['message']}")

    async def subscribe(self, channel: str):
        await self.send({"action": "subscribe", "channel": channel})

    async def send(self, data: dict):
        if self.ws:
            await self.ws.send(json.dumps(data))

    async def reconnect(self):
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            print("Max reconnection attempts reached")
            return

        self.reconnect_attempts += 1
        delay = min(2 ** self.reconnect_attempts, 60)

        print(f"Reconnecting in {delay}s (attempt {self.reconnect_attempts})...")
        await asyncio.sleep(delay)
        await self.connect()

    async def on_metrics_update(self, data: dict):
        # Override in your implementation
        print(f"Metrics update: {data}")

# Usage
async def main():
    analytics = AnalyticsWebSocket("your_jwt_token")
    await analytics.connect()

asyncio.run(main())
```

## Connection Stability

### Heartbeat Mechanism

The server sends heartbeat messages every 30 seconds. Clients should:

1. **Monitor heartbeats**: Track when the last heartbeat was received
2. **Detect disconnections**: If no heartbeat for 60+ seconds, assume disconnection
3. **Client-side ping**: Send `{"action": "ping"}` to actively test connection

### Reconnection Strategy

Recommended exponential backoff strategy:

```
Attempt 1: Wait 1 second
Attempt 2: Wait 2 seconds
Attempt 3: Wait 4 seconds
Attempt 4: Wait 8 seconds
Attempt 5: Wait 16 seconds
Attempt 6+: Wait 60 seconds (max)
```

**Best Practices:**

1. **Persist subscriptions**: Re-subscribe to channels after reconnection
2. **State restoration**: Request fresh metrics after reconnection
3. **Jitter**: Add random delay (±50%) to prevent thundering herd
4. **Max attempts**: Limit reconnection attempts (e.g., 10 attempts)
5. **User notification**: Inform user about connection issues

### Error Handling

**Common errors:**

1. **Authentication failure** (code 1008)
   - Invalid or expired JWT token
   - Solution: Obtain new token from Auth Service

2. **Connection timeout**
   - Network issues
   - Solution: Retry with exponential backoff

3. **Invalid JSON**
   - Malformed message
   - Server responds with error message

4. **Unknown action**
   - Invalid action in message
   - Server responds with error message

## Performance Considerations

### Server Limits

- **Max concurrent connections**: 1000+ (tested with 100+ concurrent)
- **Heartbeat interval**: 30 seconds
- **Metrics broadcast interval**: 10 seconds
- **Message rate limit**: None (reasonable use expected)

### Client Optimization

1. **Single connection**: Use one WebSocket per client
2. **Subscription management**: Subscribe only to needed channels
3. **Message throttling**: Debounce UI updates to avoid excessive rendering
4. **Memory management**: Clean up event listeners on disconnect

## Monitoring

### Connection Statistics

Get WebSocket statistics via REST API:

```bash
GET /api/v1/ws/stats
Authorization: Bearer <token>
```

Response:

```json
{
  "total_connections": 50,
  "connections": [
    {
      "client_id": "ws_andreas_1700000000.123",
      "user_id": "andreas",
      "connected_at": "2025-11-24T10:00:00Z",
      "last_heartbeat": "2025-11-24T10:05:30Z",
      "subscriptions": ["metrics"]
    }
  ]
}
```

## Troubleshooting

### Connection Fails

**Symptom**: WebSocket connection fails immediately

**Causes:**
1. Invalid JWT token
2. Network firewall blocking WebSocket
3. Service not running

**Solutions:**
1. Verify token validity: `curl -H "Authorization: Bearer <token>" http://localhost:8007/health`
2. Check service status: `docker compose ps analytics-service`
3. Check logs: `docker compose logs analytics-service`

### No Messages Received

**Symptom**: Connected but no metrics updates

**Causes:**
1. Not subscribed to channel
2. No metrics data available

**Solutions:**
1. Send subscribe message: `{"action": "subscribe", "channel": "metrics"}`
2. Request metrics manually: `{"action": "get_metrics"}`

### Frequent Disconnections

**Symptom**: Connection drops repeatedly

**Causes:**
1. Network instability
2. Server overload
3. Client timeout too short

**Solutions:**
1. Implement exponential backoff
2. Check server load: `GET /api/v1/monitoring/health`
3. Increase client timeout

## Security

### Authentication

- JWT token required for all connections
- Token validated on connection
- Connection closed if authentication fails

### Authorization

- Users can only access their own metrics
- Admin users can access all metrics (future)

### Best Practices

1. **Secure token storage**: Never expose token in client-side logs
2. **Token refresh**: Obtain new token before expiration
3. **HTTPS in production**: Use `wss://` protocol
4. **Rate limiting**: Implement client-side rate limiting
5. **Input validation**: Validate all incoming messages

## Future Enhancements

Planned features:

1. **Selective subscriptions**: Subscribe to specific services only
2. **Historical data**: Request historical metrics
3. **Alerts channel**: Real-time alert notifications
4. **Compression**: Message compression for large payloads
5. **Binary protocol**: Optional binary format for efficiency

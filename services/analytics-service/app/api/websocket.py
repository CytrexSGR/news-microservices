"""
WebSocket API for real-time analytics updates

Provides:
- Real-time metrics streaming
- Stable connections with heartbeat
- Automatic reconnection support
- Connection pool management
"""
import asyncio
import json
from typing import Set, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.core.auth import verify_token
from app.services.metrics_service import MetricsService

logger = structlog.get_logger()

router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections with stability features

    Features:
    - Connection pool management
    - Heartbeat/ping-pong mechanism
    - Automatic cleanup of dead connections
    - Broadcasting to multiple clients
    """

    def __init__(self, heartbeat_interval: int = 30):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket, client_id: str, user_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()

        self.active_connections[client_id] = websocket
        self.connection_metadata[client_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_heartbeat": datetime.utcnow(),
            "subscriptions": set()
        }

        logger.info(
            "websocket_connected",
            client_id=client_id,
            user_id=user_id,
            total_connections=len(self.active_connections)
        )

        # Start heartbeat task if not running
        if self.heartbeat_task is None or self.heartbeat_task.done():
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            websocket = self.active_connections.pop(client_id)
            metadata = self.connection_metadata.pop(client_id, {})

            try:
                await websocket.close()
            except Exception as e:
                logger.warning(
                    "websocket_close_error",
                    client_id=client_id,
                    error=str(e)
                )

            logger.info(
                "websocket_disconnected",
                client_id=client_id,
                user_id=metadata.get("user_id"),
                total_connections=len(self.active_connections)
            )

        # Stop heartbeat if no connections
        if not self.active_connections and self.heartbeat_task:
            self.heartbeat_task.cancel()
            self.heartbeat_task = None

    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        """Send message to a specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(
                    "websocket_send_error",
                    client_id=client_id,
                    error=str(e)
                )
                await self.disconnect(client_id)

    async def broadcast(self, message: Dict[str, Any], subscription: Optional[str] = None):
        """
        Broadcast message to all connected clients or specific subscription

        Args:
            message: Message to send
            subscription: Optional subscription filter (e.g., "metrics", "alerts")
        """
        dead_connections = []

        for client_id, websocket in self.active_connections.items():
            # Check subscription filter
            if subscription:
                metadata = self.connection_metadata.get(client_id, {})
                subscriptions = metadata.get("subscriptions", set())
                if subscription not in subscriptions:
                    continue

            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(
                    "websocket_broadcast_error",
                    client_id=client_id,
                    error=str(e)
                )
                dead_connections.append(client_id)

        # Clean up dead connections
        for client_id in dead_connections:
            await self.disconnect(client_id)

    def subscribe(self, client_id: str, subscription: str):
        """Subscribe a client to a specific channel"""
        if client_id in self.connection_metadata:
            self.connection_metadata[client_id]["subscriptions"].add(subscription)
            logger.debug(
                "websocket_subscribed",
                client_id=client_id,
                subscription=subscription
            )

    def unsubscribe(self, client_id: str, subscription: str):
        """Unsubscribe a client from a specific channel"""
        if client_id in self.connection_metadata:
            subscriptions = self.connection_metadata[client_id]["subscriptions"]
            subscriptions.discard(subscription)
            logger.debug(
                "websocket_unsubscribed",
                client_id=client_id,
                subscription=subscription
            )

    async def _heartbeat_loop(self):
        """Send periodic heartbeat to all connections"""
        try:
            while self.active_connections:
                await asyncio.sleep(self.heartbeat_interval)

                heartbeat_message = {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                }

                dead_connections = []

                for client_id in list(self.active_connections.keys()):
                    try:
                        await self.send_personal_message(heartbeat_message, client_id)
                        self.connection_metadata[client_id]["last_heartbeat"] = datetime.utcnow()
                    except Exception:
                        dead_connections.append(client_id)

                # Clean up dead connections
                for client_id in dead_connections:
                    await self.disconnect(client_id)

        except asyncio.CancelledError:
            logger.info("websocket_heartbeat_cancelled")
        except Exception as e:
            logger.error(
                "websocket_heartbeat_error",
                error=str(e),
                exc_info=True
            )

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "connections": [
                {
                    "client_id": client_id,
                    "user_id": metadata["user_id"],
                    "connected_at": metadata["connected_at"].isoformat(),
                    "last_heartbeat": metadata["last_heartbeat"].isoformat(),
                    "subscriptions": list(metadata["subscriptions"])
                }
                for client_id, metadata in self.connection_metadata.items()
            ]
        }


# Global connection manager
manager = ConnectionManager(heartbeat_interval=30)


async def get_current_user_ws(
    websocket: WebSocket,
    token: str = Query(...)
) -> str:
    """
    Authenticate WebSocket connection via query parameter

    Usage: ws://localhost:8007/ws/metrics?token=<jwt_token>
    """
    try:
        user_data = verify_token(token)
        return user_data.get("sub", "unknown")
    except Exception as e:
        logger.warning(
            "websocket_auth_failed",
            error=str(e)
        )
        await websocket.close(code=1008, reason="Authentication failed")
        raise


@router.websocket("/ws/metrics")
async def websocket_metrics_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_ws)
):
    """
    WebSocket endpoint for real-time metrics updates

    Protocol:
    - Client sends: {"action": "subscribe", "channel": "metrics"}
    - Server sends: {"type": "metrics", "data": {...}}
    - Server sends periodic: {"type": "heartbeat", "timestamp": "..."}

    Client reconnection strategy:
    1. If disconnected, wait 1 second
    2. Retry with exponential backoff: 2s, 4s, 8s, 16s, max 60s
    3. Include previous subscriptions in reconnect
    """
    client_id = f"ws_{user_id}_{datetime.utcnow().timestamp()}"

    await manager.connect(websocket, client_id, user_id)

    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connected",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat()
        }, client_id)

        # Message handling loop
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_json()

                action = data.get("action")

                if action == "subscribe":
                    channel = data.get("channel", "metrics")
                    manager.subscribe(client_id, channel)
                    await manager.send_personal_message({
                        "type": "subscribed",
                        "channel": channel
                    }, client_id)

                elif action == "unsubscribe":
                    channel = data.get("channel", "metrics")
                    manager.unsubscribe(client_id, channel)
                    await manager.send_personal_message({
                        "type": "unsubscribed",
                        "channel": channel
                    }, client_id)

                elif action == "get_metrics":
                    # Fetch current metrics
                    metrics_service = MetricsService(db)
                    overview = await metrics_service.get_overview()

                    await manager.send_personal_message({
                        "type": "metrics",
                        "data": overview.model_dump(),
                        "timestamp": datetime.utcnow().isoformat()
                    }, client_id)

                elif action == "ping":
                    # Respond to client ping
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, client_id)

                else:
                    await manager.send_personal_message({
                        "type": "error",
                        "message": f"Unknown action: {action}"
                    }, client_id)

            except WebSocketDisconnect:
                logger.info(
                    "websocket_client_disconnected",
                    client_id=client_id
                )
                break

            except json.JSONDecodeError as e:
                logger.warning(
                    "websocket_invalid_json",
                    client_id=client_id,
                    error=str(e)
                )
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON"
                }, client_id)

            except Exception as e:
                logger.error(
                    "websocket_message_error",
                    client_id=client_id,
                    error=str(e),
                    exc_info=True
                )
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Internal server error"
                }, client_id)

    except Exception as e:
        logger.error(
            "websocket_connection_error",
            client_id=client_id,
            error=str(e),
            exc_info=True
        )

    finally:
        await manager.disconnect(client_id)


@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return manager.get_connection_stats()


# Background task to broadcast metrics updates
async def broadcast_metrics_updates(db: Session):
    """
    Background task that periodically broadcasts metrics to all subscribed clients

    Should be started on application startup
    """
    metrics_service = MetricsService(db)

    while True:
        try:
            # Wait 10 seconds between updates
            await asyncio.sleep(10)

            # Get current metrics
            overview = await metrics_service.get_overview()

            # Broadcast to all clients subscribed to "metrics"
            await manager.broadcast({
                "type": "metrics_update",
                "data": overview.model_dump(),
                "timestamp": datetime.utcnow().isoformat()
            }, subscription="metrics")

        except asyncio.CancelledError:
            logger.info("metrics_broadcast_cancelled")
            break
        except Exception as e:
            logger.error(
                "metrics_broadcast_error",
                error=str(e),
                exc_info=True
            )
            # Continue despite errors
            await asyncio.sleep(5)

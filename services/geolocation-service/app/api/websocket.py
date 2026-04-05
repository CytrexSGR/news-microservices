"""WebSocket endpoint for real-time geo updates."""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Set, Optional, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections for geo-live updates.

    Features:
    - Client subscription with filter support (regions, categories)
    - Heartbeat mechanism (every 30 seconds)
    - Broadcast to all clients or filtered subsets
    """

    def __init__(self):
        # Map client_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Map client_id -> subscription filters
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        # Heartbeat task
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = {}
        logger.info(f"Client connected: {client_id} (total: {len(self.active_connections)})")

        # Send connected message
        await websocket.send_json({
            "type": "connected",
            "client_id": client_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Start heartbeat if not running
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    def disconnect(self, client_id: str) -> None:
        """Remove client connection."""
        self.active_connections.pop(client_id, None)
        self.subscriptions.pop(client_id, None)
        logger.info(f"Client disconnected: {client_id} (remaining: {len(self.active_connections)})")

    async def subscribe(self, client_id: str, filters: Dict[str, Any]) -> None:
        """Update client subscription filters."""
        if client_id in self.subscriptions:
            self.subscriptions[client_id] = filters
            websocket = self.active_connections.get(client_id)
            if websocket:
                await websocket.send_json({
                    "type": "subscribed",
                    "filters": filters,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            logger.debug(f"Client {client_id} subscribed with filters: {filters}")

    def _matches_filters(self, client_id: str, iso_code: str, category: str = None) -> bool:
        """Check if message matches client's subscription filters."""
        filters = self.subscriptions.get(client_id, {})

        # No filters = receive everything
        if not filters:
            return True

        # Check region filter
        regions = filters.get("regions", [])
        if regions:
            # We'd need to look up country -> region mapping
            # For now, accept all if regions filter is set but we don't have region info
            pass

        # Check category filter
        categories = filters.get("categories", [])
        if categories and category and category not in categories:
            return False

        return True

    async def broadcast_article(self, data: Dict[str, Any]) -> None:
        """Broadcast new article to all matching subscribers."""
        iso_code = data.get("iso_code", "")
        category = data.get("category")

        message = {
            "type": "article_new",
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        disconnected = []
        for client_id, websocket in self.active_connections.items():
            if self._matches_filters(client_id, iso_code, category):
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send to {client_id}: {e}")
                    disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)

    async def broadcast_stats_update(self, iso_code: str, stats: Dict[str, Any]) -> None:
        """Broadcast country stats update to all subscribers."""
        message = {
            "type": "stats_update",
            "data": {
                "iso_code": iso_code,
                **stats,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        disconnected = []
        for client_id, websocket in self.active_connections.items():
            if self._matches_filters(client_id, iso_code):
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send to {client_id}: {e}")
                    disconnected.append(client_id)

        for client_id in disconnected:
            self.disconnect(client_id)

    async def _heartbeat_loop(self) -> None:
        """Send heartbeat to all clients every 30 seconds."""
        while self.active_connections:
            await asyncio.sleep(30)

            message = {
                "type": "heartbeat",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            disconnected = []
            for client_id, websocket in list(self.active_connections.items()):
                try:
                    await websocket.send_json(message)
                except Exception:
                    disconnected.append(client_id)

            for client_id in disconnected:
                self.disconnect(client_id)

        logger.debug("Heartbeat loop stopped (no connections)")


# Global manager instance
manager = ConnectionManager()


@router.websocket("/ws/geo-live")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time geo updates.

    Client -> Server actions:
    - {"action": "subscribe", "filters": {"regions": ["Europe"], "categories": ["conflict"]}}
    - {"action": "unsubscribe"}
    - {"action": "ping"}
    - {"action": "get_stats"}

    Server -> Client messages:
    - {"type": "connected", "client_id": "...", "timestamp": "..."}
    - {"type": "heartbeat", "timestamp": "..."}
    - {"type": "subscribed", "filters": {...}, "timestamp": "..."}
    - {"type": "article_new", "data": {...}, "timestamp": "..."}
    - {"type": "stats_update", "data": {...}, "timestamp": "..."}
    - {"type": "pong", "timestamp": "..."}
    - {"type": "stats", "data": {"total_connections": N}}
    - {"type": "error", "message": "..."}
    """
    # Generate unique client ID
    client_id = f"geo_user_{int(datetime.now(timezone.utc).timestamp() * 1000)}"

    await manager.connect(websocket, client_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            action = data.get("action", "")

            if action == "subscribe":
                filters = data.get("filters", {})
                await manager.subscribe(client_id, filters)

            elif action == "unsubscribe":
                await manager.subscribe(client_id, {})

            elif action == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            elif action == "get_stats":
                await websocket.send_json({
                    "type": "stats",
                    "data": {
                        "total_connections": len(manager.active_connections),
                    },
                })

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown action: {action}",
                })

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)

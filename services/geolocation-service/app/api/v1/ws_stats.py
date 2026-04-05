"""WebSocket statistics endpoint."""
from fastapi import APIRouter

router = APIRouter(prefix="/geo/ws", tags=["websocket"])


@router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    from app.api.websocket import manager

    return {
        "total_connections": len(manager.active_connections),
        "connections": [
            {
                "client_id": client_id,
                "filters": manager.subscriptions.get(client_id, {}),
            }
            for client_id in manager.active_connections.keys()
        ],
    }

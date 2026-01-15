"""WebSocket endpoints for real-time updates."""

import asyncio
from typing import Set
import orjson
import structlog

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = structlog.get_logger()

router = APIRouter()

# Connected clients
connected_clients: Set[WebSocket] = set()


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("websocket_connected", total_clients=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info("websocket_disconnected", total_clients=len(self.active_connections))

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return

        data = orjson.dumps(message).decode()
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)

    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send message to specific client."""
        data = orjson.dumps(message).decode()
        await websocket.send_text(data)


manager = ConnectionManager()


@router.websocket("/updates")
async def websocket_updates(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.
    
    Sends events:
    - sync_started: When sync begins
    - sync_progress: During sync with progress
    - sync_completed: When sync finishes
    - new_transactions: When new transactions arrive
    - metrics_updated: When metrics change
    """
    await manager.connect(websocket)
    
    try:
        # Send initial connection confirmation
        await manager.send_personal(websocket, {
            "type": "connected",
            "message": "Connected to PSP Dashboard updates",
        })

        # Keep connection alive and wait for messages
        while True:
            try:
                # Wait for any message (ping/pong or commands)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second timeout for ping
                )
                
                # Handle client messages
                try:
                    message = orjson.loads(data)
                    if message.get("type") == "ping":
                        await manager.send_personal(websocket, {"type": "pong"})
                    elif message.get("type") == "subscribe":
                        # Client can subscribe to specific events
                        await manager.send_personal(websocket, {
                            "type": "subscribed",
                            "events": message.get("events", ["all"]),
                        })
                except orjson.JSONDecodeError:
                    pass

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await manager.send_personal(websocket, {"type": "ping"})
                except Exception:
                    break

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("websocket_error", error=str(e))
        manager.disconnect(websocket)


async def broadcast_sync_started(source: str):
    """Broadcast sync started event."""
    await manager.broadcast({
        "type": "sync_started",
        "source": source,
    })


async def broadcast_sync_progress(source: str, progress: int, total: int):
    """Broadcast sync progress event."""
    await manager.broadcast({
        "type": "sync_progress",
        "source": source,
        "progress": progress,
        "total": total,
        "percent": round(progress / total * 100, 1) if total > 0 else 0,
    })


async def broadcast_sync_completed(source: str, records_synced: int):
    """Broadcast sync completed event."""
    await manager.broadcast({
        "type": "sync_completed",
        "source": source,
        "records_synced": records_synced,
    })


async def broadcast_new_transactions(count: int, source: str):
    """Broadcast new transactions event."""
    await manager.broadcast({
        "type": "new_transactions",
        "count": count,
        "source": source,
    })


async def broadcast_metrics_updated():
    """Broadcast metrics updated event."""
    await manager.broadcast({
        "type": "metrics_updated",
    })

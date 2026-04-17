"""WebSocket log streaming."""

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])

# ----- WebSocket connection manager -----

class LogBroadcaster:
    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self._connections:
            self._connections.remove(ws)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self._connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


log_broadcaster = LogBroadcaster()


# ----- Python logging handler that pushes to broadcaster -----

class WSLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        message = {
            "level": record.levelname,
            "logger": record.name,
            "message": self.format(record),
            "time": record.created,
        }
        # Schedule broadcast in the running event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(log_broadcaster.broadcast(message))
        except RuntimeError:
            pass


def install_ws_log_handler():
    """Call on startup to wire logs into the WebSocket broadcaster."""
    handler = WSLogHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logging.getLogger("nepsebot").addHandler(handler)


# ----- Route -----

@router.websocket("/ws/logs")
async def ws_logs(websocket: WebSocket):
    await log_broadcaster.connect(websocket)
    try:
        while True:
            # Keep connection alive; client sends pings
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        log_broadcaster.disconnect(websocket)
    except Exception:
        log_broadcaster.disconnect(websocket)

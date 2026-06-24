"""WebSocket connection manager for broadcasting alertas in real-time."""

from __future__ import annotations

import json
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Gestiona conexiones WebSocket activas de autoridades.

    Mantiene un conjunto de conexiones activas y permite broadcast
    de mensajes a todas ellas. Maneja desconexiones automáticamente.
    """

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Acepta la conexión y la agrega al conjunto activo."""
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remueve la conexión del conjunto activo."""
        self._connections.discard(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Envía un mensaje JSON a todas las conexiones activas.

        Las conexiones que fallen se remueven automáticamente.
        """
        data = json.dumps(message, default=str)
        dead: set[WebSocket] = set()
        for ws in self._connections:
            try:
                await ws.send_text(data)
            except Exception:
                dead.add(ws)
        self._connections -= dead


# Singleton global — importado por alerta_service y el endpoint ws
manager = ConnectionManager()

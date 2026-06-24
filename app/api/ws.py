"""WebSocket endpoints for real-time alert streaming."""

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token
from app.services.websocket_manager import manager

router = APIRouter()


@router.websocket("/ws/alertas")
async def alertas_websocket(
    websocket: WebSocket,
    token: str = Query(...),
):
    """WebSocket para autoridades — recibe alertas en tiempo real.

    Conecta con: ``ws://host/ws/alertas?token=<JWT_autoridad>``

    El token debe ser un JWT de autoridad (``tipo: "autoridad"``).
    """
    # Validar token
    payload = decode_access_token(token)
    if payload is None or payload.get("tipo") != "autoridad":
        await websocket.close(code=4001)
        return

    await manager.connect(websocket)
    try:
        # Mantener conexión abierta — escucha por si el cliente envía algo
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

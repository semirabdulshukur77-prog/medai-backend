from fastapi import APIRouter, WebSocket
from typing import List

router = APIRouter()
active_connections: List[WebSocket] = []

@router.websocket("/ws/signaling")
async def websocket_signaling(ws: WebSocket):
    await ws.accept()
    active_connections.append(ws)
    try:
        while True:
            data = await ws.receive_text()
            # Broadcast to all other clients
            for conn in active_connections:
                if conn != ws:
                    try:
                        await conn.send_text(data)
                    except:
                        if conn in active_connections:
                            active_connections.remove(conn)
    except:
        if ws in active_connections:
            active_connections.remove(ws)


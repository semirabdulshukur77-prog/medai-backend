from fastapi import APIRouter, WebSocket
from app.services.realtime_service import connect_client, disconnect_client, broadcast_status, update_doctor_status, update_patient_status
import asyncio

router = APIRouter()
broadcast_task_started = False

@router.websocket("/ws/realtime/{role}/{user_id}")
async def websocket_realtime(ws: WebSocket, role: str, user_id: int):
    global broadcast_task_started
    await connect_client(ws, role)

    # Update online status
    if role == "doctor":
        update_doctor_status(user_id, f"Dr {user_id}", True)
    else:
        update_patient_status(user_id, f"Patient {user_id}", True)

    # Start broadcasting loop once
    if not broadcast_task_started:
        asyncio.create_task(broadcast_status())
        broadcast_task_started = True

    try:
        while True:
            await ws.receive_text()  # optional: can handle client messages
    except:
        await disconnect_client(ws, role)
        if role == "doctor":
            update_doctor_status(user_id, f"Dr {user_id}", False)
        else:
            update_patient_status(user_id, f"Patient {user_id}", False)


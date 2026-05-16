from typing import List, Dict
from fastapi import WebSocket
import asyncio
from app.services.recommendation_module import get_ai_recommendations

# Connected clients
active_doctor_connections: List[WebSocket] = []
active_patient_connections: List[WebSocket] = []

# Online status
doctor_status: Dict[int, Dict] = {}   # {doctorId: {name, online}}
patient_status: Dict[int, Dict] = {}  # {patientId: {name, online}}

# -----------------------------
# Connection management
# -----------------------------
async def connect_client(ws: WebSocket, role: str):
    await ws.accept()
    if role == "doctor":
        active_doctor_connections.append(ws)
    elif role == "patient":
        active_patient_connections.append(ws)

async def disconnect_client(ws: WebSocket, role: str):
    if role == "doctor" and ws in active_doctor_connections:
        active_doctor_connections.remove(ws)
    elif role == "patient" and ws in active_patient_connections:
        active_patient_connections.remove(ws)

# -----------------------------
# Broadcast status + AI recommendations
# -----------------------------
async def broadcast_status():
    while True:
        try:
            # Get live AI recommendations
            ai_recommendations = await get_ai_recommendations()

            # Prepare payloads
            data_doctors = {
                "type": "doctor_status",
                "payload": list(doctor_status.values()),
                "recommendations": ai_recommendations
            }
            data_patients = {
                "type": "patient_status",
                "payload": list(patient_status.values()),
                "recommendations": ai_recommendations
            }

            # Send to connected patients
            for ws in active_patient_connections[:]:
                try:
                    await ws.send_json(data_doctors)
                except:
                    await disconnect_client(ws, "patient")

            # Send to connected doctors
            for ws in active_doctor_connections[:]:
                try:
                    await ws.send_json(data_patients)
                except:
                    await disconnect_client(ws, "doctor")

            await asyncio.sleep(2)  # update interval
        except Exception:
            await asyncio.sleep(2)

# -----------------------------
# Update online status
# -----------------------------
def update_doctor_status(doctor_id: int, name: str, online: bool):
    doctor_status[doctor_id] = {"id": doctor_id, "name": name, "online": online}

def update_patient_status(patient_id: int, name: str, online: bool):
    patient_status[patient_id] = {"id": patient_id, "name": name, "online": online}


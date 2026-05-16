# backend/app/routes/lll_history.py
from fastapi import APIRouter, WebSocket
from app.db import get_db
import json
import asyncio

router = APIRouter()

@router.websocket("/ws/patient_history/{patient_id}")
async def websocket_patient_history(websocket: WebSocket, patient_id: int):
    await websocket.accept()
    try:
        while True:
            await asyncio.sleep(10)  # update every 10 seconds
            db = get_db()
            history = db.execute(
                "SELECT * FROM patient_llm_history WHERE patient_id = ? ORDER BY created_at DESC LIMIT 10",
                (patient_id,)
            ).fetchall()
            history_list = [
                {
                    "id": row["id"],
                    "query": row["query"],
                    "response": row["response"],
                    "created_at": row["created_at"]
                }
                for row in history
            ]
            await websocket.send_text(json.dumps(history_list))
    except:
        pass


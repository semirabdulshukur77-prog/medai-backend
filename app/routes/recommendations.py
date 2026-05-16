# app/routes/recommendations.py
from fastapi import APIRouter, WebSocket, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import json
import asyncio
from app.services.recommendation_engine import MedicalRecommendationEngine
from app.db import get_db
router = APIRouter()
recommendation_engine = MedicalRecommendationEngine()
# WebSocket clients for real-time updates
recommendation_clients: Dict[int, List[WebSocket]] = {}
# Request Models
class RecommendationRequest(BaseModel):
    patient_id: int
    symptoms: List[str]
    medical_history: Optional[str] = ""
    current_medications: Optional[List[str]] = None
    consultation_id: Optional[str] = None
    language: str = "en"  # "en" or "am"
    include_scheduling: bool = True
class VoiceRecommendationRequest(BaseModel):
    patient_id: int
    audio_text: str  # Transcribed voice input
    language: str = "en"  # "en" or "am"
# REST API Endpoints
@router.post("/api/recommendations/generate")
async def generate_ai_recommendations(request: RecommendationRequest):
    """
    Generate comprehensive AI-powered medical recommendations
    Includes: diagnosis, medications, lifestyle, scheduling, voice instructions
    """
    try:
        recommendations = await recommendation_engine.generate_comprehensive_recommendations(
            patient_id=request.patient_id,
            symptoms=request.symptoms,
            medical_history=request.medical_history,
            current_medications=request.current_medications,
            consultation_id=request.consultation_id,
            language=request.language,
            include_scheduling=request.include_scheduling
        )
        # Broadcast to WebSocket clients if any
        await broadcast_to_patient(request.patient_id, recommendations)
        return {
            "status": "success",
            "recommendation_id": recommendations["recommendation_id"],
            "data": recommendations,
            "generated_at": datetime.now().isoformat(),
            "message": "AI recommendations generated successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate AI recommendations: {str(e)}"
        )
@router.post("/api/recommendations/voice")
async def generate_voice_recommendations(request: VoiceRecommendationRequest):
    """
    Generate recommendations from voice input (Amharic/English)
    """
    try:
        # Extract symptoms from voice text (simplified)
        # In production, use NLP to extract medical information
        symptoms = extract_symptoms_from_text(request.audio_text)
        recommendations = await recommendation_engine.generate_comprehensive_recommendations(
            patient_id=request.patient_id,
            symptoms=symptoms,
            language=request.language,
            include_scheduling=True
        )
        # Format for voice response
        voice_response = {
            "text_response": format_for_voice(recommendations, request.language),
            "recommendations": recommendations,
            "language": request.language
        }
        return {
            "status": "success",
            "data": voice_response,
            "message": "Voice recommendations generated"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Voice recommendation failed: {str(e)}"
        )
@router.get("/api/recommendations/patient/{patient_id}")
async def get_patient_recommendations(patient_id: int, limit: int = 10):
    """Get recommendation history for a patient"""
    try:
        db = get_db()
        recommendations = db.execute(
            """
            SELECT * FROM medical_recommendations 
            WHERE patient_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
            """,
            (patient_id, limit)
        ).fetchall()
        return {
            "status": "success",
            "patient_id": patient_id,
            "count": len(recommendations),
            "recommendations": [
                {
                    **dict(rec),
                    "recommendations_json": json.loads(rec["recommendations_json"])
                }
                for rec in recommendations
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get recommendations: {str(e)}"
        )
@router.get("/api/recommendations/{recommendation_id}")
async def get_recommendation_details(recommendation_id: str):
    """Get detailed information about a specific recommendation"""
    try:
        db = get_db()
        recommendation = db.execute(
            "SELECT * FROM medical_recommendations WHERE recommendation_id = ?",
            (recommendation_id,)
        ).fetchone()
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        return {
            "status": "success",
            "data": {
                **dict(recommendation),
                "recommendations_json": json.loads(recommendation["recommendations_json"])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get recommendation: {str(e)}"
        )
# WebSocket Endpoint for Real-time Updates
@router.websocket("/ws/recommendations/{patient_id}")
async def websocket_recommendations(websocket: WebSocket, patient_id: int):
    """
    WebSocket for real-time recommendation updates
    Patients receive live updates when new recommendations are generated
    """
    await websocket.accept()
    # Add client to patient's connection list
    if patient_id not in recommendation_clients:
        recommendation_clients[patient_id] = []
    recommendation_clients[patient_id].append(websocket)
    try:
        # Send initial recommendations if any
        db = get_db()
        recent_rec = db.execute(
            """
            SELECT * FROM medical_recommendations 
            WHERE patient_id = ? 
            ORDER BY created_at DESC 
            LIMIT 1
            """,
            (patient_id,)
        ).fetchone()
        if recent_rec:
            await websocket.send_json({
                "type": "initial_recommendation",
                "data": {
                    **dict(recent_rec),
                    "recommendations_json": json.loads(recent_rec["recommendations_json"])
                }
            })
        # Keep connection alive and listen for messages
        while True:
            # Wait for client messages (optional)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except Exception:
        # Remove client on disconnect
        if patient_id in recommendation_clients and websocket in recommendation_clients[patient_id]:
            recommendation_clients[patient_id].remove(websocket)
        if patient_id in recommendation_clients and not recommendation_clients[patient_id]:
            del recommendation_clients[patient_id]
# Helper Functions
async def broadcast_to_patient(patient_id: int, recommendations: Dict):
    """Broadcast new recommendations to patient's WebSocket clients"""
    if patient_id in recommendation_clients:
        for websocket in recommendation_clients[patient_id][:]:  # Copy list
            try:
                await websocket.send_json({
                    "type": "new_recommendation",
                    "data": recommendations,
                    "timestamp": datetime.now().isoformat()
                })
            except:
                # Remove disconnected client
                recommendation_clients[patient_id].remove(websocket)
def extract_symptoms_from_text(text: str) -> List[str]:
    """Extract symptoms from voice/text input (simplified)"""
    # In production, use NLP/ML for symptom extraction
    common_symptoms = [
        "fever", "cough", "headache", "pain", "nausea", "dizziness",
        "fatigue", "shortness of breath", "chest pain", "sore throat"
    ]
    symptoms = []
    text_lower = text.lower()
    for symptom in common_symptoms:
        if symptom in text_lower:
            symptoms.append(symptom)
    return symptoms if symptoms else ["general consultation"]
def format_for_voice(recommendations: Dict, language: str) -> str:
    """Format recommendations for voice response"""
    if language == "am":
        return f"""
        የህክምና ምክር:
        አስጨናቂ ሁኔታ: {recommendations.get('urgency_level', 'ዝቅተኛ')}
        የሚመከር ልዩ ዶክተር: {', '.join(recommendations.get('specialist_referrals', ['አጠቃላይ ዶክተር']))}
        ወዲያውኑ ማድረግ ያለብዎት: {', '.join(recommendations.get('immediate_actions', ['ይደረቁ']))}
        """
    else:
        return f"""
        Medical Recommendations:
        Urgency Level: {recommendations.get('urgency_level', 'Low')}
        Recommended Specialist: {', '.join(recommendations.get('specialist_referrals', ['General Physician']))}
        Immediate Actions: {', '.join(recommendations.get('immediate_actions', ['Rest']))}
        """

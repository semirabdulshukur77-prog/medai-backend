# app/routes/consultation.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
import uuid
from datetime import datetime
from app.services.llm_service import query_llm
from app.db import get_db
router = APIRouter(prefix="/api/consultation", tags=["Consultation"])
class ConsultationRequest(BaseModel):
    patient_id: int
    symptoms: List[str]
    medical_history: Optional[str] = ""
    current_medications: Optional[List[str]] = None
    voice_note_url: Optional[str] = None  # For Amharic/English voice
    image_url: Optional[str] = None  # For medical images
class ConsultationResponse(BaseModel):
    consultation_id: str
    diagnosis: str
    recommendations: List[str]
    urgency: str  # "low", "medium", "high", "emergency"
    follow_up_required: bool
    suggested_specialist: Optional[str] = None
class VoiceConsultationRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    language: str = "en"  # "en" or "am" for Amharic
# In-memory storage (use database in production)
consultations_db: Dict[str, dict] = {}
@router.post("/start")
async def start_consultation(request: ConsultationRequest) -> ConsultationResponse:
    """Start a new medical consultation"""
    consultation_id = str(uuid.uuid4())
    # Prepare query for LLM
    symptoms_text = ", ".join(request.symptoms)
    query = f"""
    Patient Consultation:
    - Symptoms: {symptoms_text}
    - Medical History: {request.medical_history or 'None provided'}
    - Current Medications: {', '.join(request.current_medications) if request.current_medications else 'None'}
    Please provide:
    1. Preliminary diagnosis
    2. Urgency level (low/medium/high/emergency)
    3. Recommendations
    4. Whether follow-up is needed
    5. Suggested specialist if any
    """
    # Get AI diagnosis (using your LLM service)
    try:
        ai_response = await query_llm(query)
        # Parse AI response (simplified - in reality, structure the prompt better)
        diagnosis = f"AI Assessment: {ai_response[:200]}..."
        recommendations = [
            "Monitor symptoms for 24-48 hours",
            "Drink plenty of fluids",
            "Get adequate rest",
            "Return if symptoms worsen"
        ]
        # Determine urgency based on symptoms
        emergency_keywords = ["chest pain", "difficulty breathing", "severe", "bleeding"]
        urgency = "low"
        for symptom in request.symptoms:
            if any(keyword in symptom.lower() for keyword in emergency_keywords):
                urgency = "emergency"
                break
        consultation = {
            "id": consultation_id,
            "patient_id": request.patient_id,
            "symptoms": request.symptoms,
            "medical_history": request.medical_history,
            "diagnosis": diagnosis,
            "recommendations": recommendations,
            "urgency": urgency,
            "created_at": datetime.now().isoformat(),
            "voice_note": request.voice_note_url,
            "image": request.image_url
        }
        consultations_db[consultation_id] = consultation
        # Store in database if needed
        db = get_db()
        db.execute(
            """
            INSERT INTO consultations 
            (consultation_id, patient_id, symptoms, diagnosis, urgency, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (consultation_id, request.patient_id, 
             ', '.join(request.symptoms), diagnosis, 
             urgency, datetime.now().isoformat())
        )
        db.commit()
        return ConsultationResponse(
            consultation_id=consultation_id,
            diagnosis=diagnosis,
            recommendations=recommendations,
            urgency=urgency,
            follow_up_required=urgency in ["high", "emergency"],
            suggested_specialist="General Physician" if urgency == "low" else "Emergency Department"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Consultation failed: {str(e)}")
@router.post("/voice")
async def voice_consultation(request: VoiceConsultationRequest):
    """Voice-based consultation (supports Amharic and English)"""
    # TODO: Integrate with speech-to-text and language detection
    # For now, return mock response
    return {
        "message": "Voice consultation received",
        "language": request.language,
        "consultation_id": str(uuid.uuid4()),
        "transcription": "[Speech-to-text would go here]"
    }
@router.get("/{consultation_id}")
async def get_consultation(consultation_id: str):
    """Retrieve consultation details"""
    if consultation_id not in consultations_db:
        raise HTTPException(status_code=404, detail="Consultation not found")
    return consultations_db[consultation_id]
@router.get("/patient/{patient_id}")
async def get_patient_consultations(patient_id: int):
    """Get all consultations for a patient"""
    patient_consultations = [
        consult for consult in consultations_db.values() 
        if consult["patient_id"] == patient_id
    ]
    return {"consultations": patient_consultations}
@router.post("/{consultation_id}/prescription")
async def add_prescription(consultation_id: str):
    """Add prescription to consultation"""
    if consultation_id not in consultations_db:
        raise HTTPException(status_code=404, detail="Consultation not found")
    # TODO: Integrate with drug interaction checking
    return {
        "message": "Prescription added",
        "consultation_id": consultation_id,
        "prescription_id": str(uuid.uuid4())
    }

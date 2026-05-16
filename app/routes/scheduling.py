# app/routes/scheduling.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import uuid
from datetime import datetime, timedelta
from app.db import get_db
router = APIRouter(prefix="/api/scheduling", tags=["Scheduling"])
class AppointmentRequest(BaseModel):
    patient_id: int
    doctor_id: Optional[int] = None
    preferred_date: str  # YYYY-MM-DD
    preferred_time: str  # HH:MM
    reason: str
    urgency: str = "routine"  # routine, urgent, emergency
    consultation_id: Optional[str] = None  # Link to consultation
class AppointmentResponse(BaseModel):
    appointment_id: str
    patient_id: int
    doctor_id: Optional[int]
    scheduled_date: str
    scheduled_time: str
    status: str  # pending, confirmed, cancelled, completed
    reason: str
    meeting_link: Optional[str] = None  # For virtual consultations
class AvailableSlot(BaseModel):
    doctor_id: int
    date: str
    time_slots: List[str]
# In-memory storage
appointments_db: Dict[str, dict] = {}
doctor_schedule: Dict[int, List[str]] = {
    1: ["09:00", "10:00", "11:00", "14:00", "15:00"],  # Doctor 1
    2: ["09:30", "10:30", "13:00", "14:30", "16:00"],  # Doctor 2
    3: ["08:00", "11:00", "12:00", "15:00", "17:00"],  # Doctor 3
}
@router.post("/appointment")
async def schedule_appointment(request: AppointmentRequest) -> AppointmentResponse:
    """Schedule a new appointment"""
    appointment_id = str(uuid.uuid4())
    # Find available doctor if not specified
    doctor_id = request.doctor_id
    if not doctor_id:
        # Auto-assign based on availability and urgency
        doctor_id = find_available_doctor(request.preferred_date, request.preferred_time)
        if not doctor_id:
            raise HTTPException(status_code=400, detail="No doctors available at requested time")
    # Validate time slot
    available_slots = doctor_schedule.get(doctor_id, [])
    if request.preferred_time not in available_slots:
        raise HTTPException(
            status_code=400, 
            detail=f"Time slot not available. Available slots: {', '.join(available_slots)}"
        )
    # Create appointment
    appointment = {
        "appointment_id": appointment_id,
        "patient_id": request.patient_id,
        "doctor_id": doctor_id,
        "scheduled_date": request.preferred_date,
        "scheduled_time": request.preferred_time,
        "status": "confirmed",
        "reason": request.reason,
        "urgency": request.urgency,
        "consultation_id": request.consultation_id,
        "created_at": datetime.now().isoformat(),
        "meeting_link": f"https://meet.medai.example.com/{appointment_id}" if request.urgency != "emergency" else None
    }
    appointments_db[appointment_id] = appointment
    # Store in database
    db = get_db()
    db.execute(
        """
        INSERT INTO appointments 
        (appointment_id, patient_id, doctor_id, scheduled_date, 
         scheduled_time, status, reason, urgency, consultation_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (appointment_id, request.patient_id, doctor_id, 
         request.preferred_date, request.preferred_time,
         "confirmed", request.reason, request.urgency,
         request.consultation_id)
    )
    db.commit()
    return AppointmentResponse(**appointment)
@router.get("/available-slots/{doctor_id}/{date}")
async def get_available_slots(doctor_id: int, date: str) -> AvailableSlot:
    """Get available time slots for a doctor on a specific date"""
    # In production, check against existing appointments
    slots = doctor_schedule.get(doctor_id, [])
    # Filter out booked slots
    db = get_db()
    booked_slots = db.execute(
        """
        SELECT scheduled_time FROM appointments 
        WHERE doctor_id = ? AND scheduled_date = ? AND status != 'cancelled'
        """,
        (doctor_id, date)
    ).fetchall()
    booked_times = [slot["scheduled_time"] for slot in booked_slots]
    available_slots = [slot for slot in slots if slot not in booked_times]
    return AvailableSlot(
        doctor_id=doctor_id,
        date=date,
        time_slots=available_slots
    )
@router.get("/doctor/{doctor_id}")
async def get_doctor_appointments(doctor_id: int):
    """Get all appointments for a doctor"""
    doctor_appointments = [
        appt for appt in appointments_db.values() 
        if appt["doctor_id"] == doctor_id
    ]
    return {"appointments": doctor_appointments}
@router.get("/patient/{patient_id}")
async def get_patient_appointments(patient_id: int):
    """Get all appointments for a patient"""
    patient_appointments = [
        appt for appt in appointments_db.values() 
        if appt["patient_id"] == patient_id
    ]
    return {"appointments": patient_appointments}
@router.post("/{appointment_id}/cancel")
async def cancel_appointment(appointment_id: str):
    """Cancel an appointment"""
    if appointment_id not in appointments_db:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appointments_db[appointment_id]["status"] = "cancelled"
    db = get_db()
    db.execute(
        "UPDATE appointments SET status = 'cancelled' WHERE appointment_id = ?",
        (appointment_id,)
    )
    db.commit()
    return {"message": "Appointment cancelled", "appointment_id": appointment_id}
@router.post("/{appointment_id}/complete")
async def complete_appointment(appointment_id: str):
    """Mark appointment as completed"""
    if appointment_id not in appointments_db:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appointments_db[appointment_id]["status"] = "completed"
    db = get_db()
    db.execute(
        "UPDATE appointments SET status = 'completed' WHERE appointment_id = ?",
        (appointment_id,)
    )
    db.commit()
    return {"message": "Appointment completed", "appointment_id": appointment_id}
def find_available_doctor(date: str, time: str) -> Optional[int]:
    """Find available doctor for given date and time"""
    for doctor_id, slots in doctor_schedule.items():
        if time in slots:
            # Check if slot is already booked
            db = get_db()
            existing = db.execute(
                """
                SELECT COUNT(*) as count FROM appointments 
                WHERE doctor_id = ? AND scheduled_date = ? 
                AND scheduled_time = ? AND status != 'cancelled'
                """,
                (doctor_id, date, time)
            ).fetchone()
            if existing["count"] == 0:
                return doctor_id
    return None

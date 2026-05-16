# backend/app/routes/doctors.py
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.db import get_db
from typing import Optional, List
import math

router = APIRouter()

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    Returns distance in kilometers.
    """
    R = 6371  # Earth radius in kilometers
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (
        math.sin(dlat / 2) ** 2 +
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
        math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

@router.get("/api/doctors/nearby")
async def get_nearby_doctors(
    latitude: float = Query(..., description="User's latitude"),
    longitude: float = Query(..., description="User's longitude"),
    radius_km: float = Query(10.0, description="Search radius in kilometers"),
    available_only: bool = Query(False, description="Filter only available doctors"),
    limit: int = Query(20, description="Maximum number of results")
):
    """
    Get nearby doctors based on user location.
    """
    try:
        db = get_db()
        
        # Build query
        query = """
            SELECT 
                doctor_id,
                online,
                available,
                latitude,
                longitude,
                updated_at
            FROM doctor_realtime
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """
        
        params = []
        
        if available_only:
            query += " AND available = 1 AND online = 1"
        
        # Get all doctors first
        doctors = db.execute(query, params).fetchall()
        
        # Calculate distances and filter by radius
        nearby_doctors = []
        for doctor in doctors:
            distance = calculate_distance(
                latitude, longitude,
                doctor["latitude"], doctor["longitude"]
            )
            
            if distance <= radius_km:
                # Get doctor details (you can extend this to join with a doctors table)
                doctor_data = {
                    "doctor_id": doctor["doctor_id"],
                    "name": f"Dr. {doctor['doctor_id']}",  # Replace with actual name from doctors table
                    "specialty": "General Practice",  # Replace with actual specialty
                    "latitude": doctor["latitude"],
                    "longitude": doctor["longitude"],
                    "available": bool(doctor["available"]),
                    "online": bool(doctor["online"]),
                    "distance_km": round(distance, 2),
                    "updated_at": doctor["updated_at"]
                }
                nearby_doctors.append(doctor_data)
        
        # Sort by distance
        nearby_doctors.sort(key=lambda x: x["distance_km"])
        
        # Apply limit
        nearby_doctors = nearby_doctors[:limit]
        
        return JSONResponse(content={
            "doctors": nearby_doctors,
            "count": len(nearby_doctors),
            "user_location": {"latitude": latitude, "longitude": longitude},
            "radius_km": radius_km
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get nearby doctors: {str(e)}"}
        )

@router.get("/api/doctors/realtime")
async def get_realtime_doctors():
    """
    Get all doctors with real-time status.
    """
    try:
        db = get_db()
        doctors = db.execute("""
            SELECT 
                doctor_id,
                online,
                available,
                latitude,
                longitude,
                updated_at
            FROM doctor_realtime
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """).fetchall()
        
        doctors_list = [
            {
                "doctor_id": doc["doctor_id"],
                "name": f"Dr. {doc['doctor_id']}",
                "specialty": "General Practice",
                "latitude": doc["latitude"],
                "longitude": doc["longitude"],
                "available": bool(doc["available"]),
                "online": bool(doc["online"]),
                "updated_at": doc["updated_at"]
            }
            for doc in doctors
        ]
        
        return JSONResponse(content={"doctors": doctors_list})
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get doctors: {str(e)}"}
        )


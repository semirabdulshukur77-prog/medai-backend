# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import traceback

from app.db import get_db
from app.core.config import settings

# Import routers
from app.routes import (
    consultation,
    scheduling,
    recommendations,
    radiology,
    assistant,
    drug_interactions,
    signaling,
    realtime,
    lll_history,
    doctors
)

app = FastAPI(title="Multi-Agent Medical AI Framework", version="1.0.0")

# -----------------------------
# CORS configuration
# -----------------------------
origins = getattr(settings, "ALLOWED_ORIGINS", ["*"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Include API routers
# -----------------------------
app.include_router(recommendations.router)
app.include_router(radiology.router)
app.include_router(assistant.router)
app.include_router(drug_interactions.router)
app.include_router(realtime.router)
app.include_router(signaling.router)  # WebSocket
app.include_router(lll_history.router)
app.include_router(doctors.router)  # Nearby doctors
app.include_router(consultation.router)
app.include_router(scheduling.router)

# -----------------------------
# Root endpoint
# -----------------------------
@app.get("/")
async def root():
    return {"message": "Multi-Agent Medical AI Framework is running."}

# -----------------------------
# Startup event: DB initialization + seeding
# -----------------------------
@app.on_event("startup")
async def startup_event():
    try:
        db = get_db()
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        migrations_path = os.path.join(base_dir, "app", "models", "migration.sql")
        
        # 1ï¸âƒ£ Create tables
        if os.path.exists(migrations_path):
            with open(migrations_path, "r") as f:
                db.executescript(f.read())
            print("[DB] Tables checked/created successfully.")
        else:
            print(f"[DB] Warning: migrations.sql not found at {migrations_path}")
        
        # 2ï¸âƒ£ Seed drug_interactions if empty
        try:
            drug_count = db.execute("SELECT COUNT(*) FROM drug_interactions").fetchone()[0]
            if drug_count == 0:
                print("[DB] Seeding sample drug interactions...")
                sample_interactions = [
                    ("Aspirin", "Warfarin", "Increased risk of bleeding"),
                    ("Metformin", "Contrast Dye", "Risk of lactic acidosis"),
                    ("Ibuprofen", "Lisinopril", "May reduce effectiveness of Lisinopril"),
                    ("Paracetamol", "Alcohol", "Liver toxicity risk if overdosed")
                ]
                for drug1, drug2, message in sample_interactions:
                    db.execute(
                        "INSERT INTO drug_interactions (drug1, drug2, interaction) VALUES (?, ?, ?)",
                        (drug1, drug2, message)
                    )
                db.commit()
                print("[DB] Drug interactions seeded.")
        except Exception as e:
            print(f"[DB] Error seeding drug interactions: {e}")

        # 3ï¸âƒ£ Seed doctor_realtime if empty
        try:
            doctor_count = db.execute("SELECT COUNT(*) FROM doctor_realtime").fetchone()[0]
            if doctor_count == 0:
                print("[DB] Seeding sample doctor realtime data...")
                sample_doctors = [
                    (1, True, True, 9.0, 38.7),
                    (2, True, True, 9.01, 38.71),
                    (3, False, True, 9.02, 38.72),
                ]
                for doctor_id, online, available, lat, lon in sample_doctors:
                    db.execute("""
                        INSERT INTO doctor_realtime (doctor_id, online, available, latitude, longitude)
                        VALUES (?, ?, ?, ?, ?)
                    """, (doctor_id, online, available, lat, lon))
                db.commit()
                print("[DB] Doctor realtime data seeded.")
        except Exception as e:
            print(f"[DB] Error seeding doctor realtime: {e}")

        print("âœ… Multi-Agent Medical AI Framework startup complete!")

    except Exception as e:
        print("[DB] Error during startup:")
        print(traceback.format_exc())


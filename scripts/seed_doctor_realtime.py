# backend/scripts/seed_doctor_realtime.py

from app.db import get_db

sample_doctors = [
    (1, True, True, 9.0, 38.7),
    (2, True, True, 9.01, 38.71),
    (3, False, True, 9.02, 38.72),
]

db = get_db()

for doctor_id, online, available, lat, lon in sample_doctors:
    db.execute("""
        INSERT INTO doctor_realtime (doctor_id, online, available, latitude, longitude)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(doctor_id) DO UPDATE SET
            online=excluded.online,
            available=excluded.available,
            latitude=excluded.latitude,
            longitude=excluded.longitude
    """, (doctor_id, online, available, lat, lon))

db.commit()
print("Doctor realtime data seeded successfully.")

# backend/scripts/seed_drug_interactions.py

from app.db import get_db

sample_interactions = [
    ("Aspirin", "Warfarin", "Increased risk of bleeding"),
    ("Metformin", "Contrast Dye", "Risk of lactic acidosis"),
    ("Ibuprofen", "Lisinopril", "May reduce effectiveness of Lisinopril"),
    ("Paracetamol", "Alcohol", "Liver toxicity risk if overdosed")
]

db = get_db()

for drug1, drug2, message in sample_interactions:
    db.execute(
        "INSERT INTO drug_interactions (drug1, drug2, interaction) VALUES (?, ?, ?)",
        (drug1, drug2, message)
    )

db.commit()
print("Drug interactions seeded successfully.")

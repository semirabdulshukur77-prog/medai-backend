-- backend/models/migrations.sql

-- 1. Patient LLM query history
CREATE TABLE IF NOT EXISTS patient_llm_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Doctor real-time status
CREATE TABLE IF NOT EXISTS doctor_realtime (
    doctor_id INTEGER PRIMARY KEY,
    online BOOLEAN DEFAULT FALSE,
    available BOOLEAN DEFAULT TRUE,
    latitude REAL,
    longitude REAL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. Drug interactions
CREATE TABLE IF NOT EXISTS drug_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drug1 TEXT NOT NULL,
    drug2 TEXT NOT NULL,
    interaction TEXT NOT NULL
);

-- Add to your existing migration.sql file
CREATE TABLE IF NOT EXISTS medical_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_id TEXT UNIQUE NOT NULL,
    patient_id INTEGER NOT NULL,
    consultation_id TEXT,
    urgency_level TEXT CHECK(urgency_level IN ('low', 'medium', 'high', 'emergency')),
    recommendations_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    language TEXT DEFAULT 'en',
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (consultation_id) REFERENCES consultations(consultation_id)
);
CREATE INDEX IF NOT EXISTS idx_recommendations_patient ON medical_recommendations(patient_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_created ON medical_recommendations(created_at DESC);

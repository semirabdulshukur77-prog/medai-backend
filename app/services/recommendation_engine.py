# app/services/recommendation_engine.py
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import json
import asyncio
from app.services.llm_service import query_llm
from app.services.drug_module import check_drug_interactions
from app.db import get_db
import uuid
class MedicalRecommendationEngine:
    """
    AI-powered medical recommendation engine for Amharic/English consultations
    Integrates: symptoms analysis, drug interactions, scheduling, voice support
    """
    def __init__(self):
        self.db = get_db()
        self.emergency_keywords = {
            "en": ["chest pain", "difficulty breathing", "severe bleeding", 
                   "unconscious", "stroke symptoms", "heart attack"],
            "am": ["የልብ ህመም", "መተንፈስ ችግር", "ከባድ ደም መፍሰስ",
                   "ግንዛቤ መጥፋት", "ስትሮክ ምልክቶች", "የልብ ጉዳት"]
        }
        self.specialists_mapping = {
            "cardiology": ["chest pain", "heart", "palpitations"],
            "neurology": ["headache", "dizziness", "numbness", "stroke"],
            "gastroenterology": ["stomach pain", "nausea", "vomiting", "diarrhea"],
            "pulmonology": ["cough", "breathing", "asthma", "pneumonia"],
            "orthopedics": ["joint pain", "fracture", "back pain", "swelling"],
            "general": ["fever", "cold", "fatigue", "general pain"]
        }
    async def generate_comprehensive_recommendations(
        self,
        patient_id: int,
        symptoms: List[str],
        medical_history: str = "",
        current_medications: Optional[List[str]] = None,
        consultation_id: Optional[str] = None,
        language: str = "en",  # "en" or "am"
        include_scheduling: bool = True
    ) -> Dict:
        """
        Generate AI-powered recommendations including:
        - Diagnosis suggestions
        - Medication recommendations
        - Specialist referrals
        - Appointment scheduling suggestions
        - Lifestyle recommendations
        """
        # 1. Symptom Analysis
        symptom_analysis = await self._analyze_symptoms(symptoms, language)
        # 2. Drug Interaction Warnings
        drug_warnings = []
        if current_medications:
            drug_warnings = await self._check_drug_safety(current_medications, symptoms)
        # 3. LLM-Based Medical Recommendations
        llm_recommendations = await self._get_llm_recommendations(
            symptoms, medical_history, current_medications, language
        )
        # 4. Appointment Scheduling Suggestions
        scheduling_suggestions = []
        if include_scheduling:
            scheduling_suggestions = await self._generate_scheduling_suggestions(
                symptom_analysis["urgency"],
                symptom_analysis["suggested_specialists"],
                patient_id
            )
        # 5. Voice/Follow-up Recommendations (Amharic/English)
        voice_recommendations = self._generate_voice_recommendations(
            llm_recommendations, language
        )
        # 6. Compile Comprehensive Response
        recommendations = {
            "recommendation_id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "consultation_id": consultation_id,
            "timestamp": datetime.now().isoformat(),
            "language": language,
            # Medical Analysis
            "symptom_analysis": symptom_analysis,
            "drug_safety": drug_warnings,
            # AI Recommendations
            "diagnosis_suggestions": llm_recommendations.get("diagnosis", []),
            "medication_recommendations": llm_recommendations.get("medications", []),
            "lifestyle_recommendations": llm_recommendations.get("lifestyle", []),
            "emergency_advice": llm_recommendations.get("emergency", []),
            # Practical Recommendations
            "specialist_referrals": symptom_analysis["suggested_specialists"],
            "appointment_suggestions": scheduling_suggestions,
            "voice_recommendations": voice_recommendations,
            # Urgency & Next Steps
            "urgency_level": symptom_analysis["urgency"],
            "immediate_actions": self._get_immediate_actions(
                symptom_analysis["urgency"], language
            ),
            "monitoring_instructions": llm_recommendations.get("monitoring", []),
            # Follow-up
            "follow_up_required": symptom_analysis["urgency"] in ["high", "emergency"],
            "follow_up_timeline": self._get_follow_up_timeline(
                symptom_analysis["urgency"]
            )
        }
        # 7. Store in Database
        await self._store_recommendations(recommendations)
        return recommendations
    async def _analyze_symptoms(self, symptoms: List[str], language: str) -> Dict:
        """Analyze symptoms for urgency, specialists, and emergency detection"""
        # Convert symptoms to lowercase for matching
        symptoms_lower = [s.lower() for s in symptoms]
        # Check for emergency conditions
        urgency = "low"
        emergency_detected = False
        emergency_keywords = self.emergency_keywords.get(language, self.emergency_keywords["en"])
        for symptom in symptoms_lower:
            for keyword in emergency_keywords:
                if keyword in symptom:
                    urgency = "emergency"
                    emergency_detected = True
                    break
            if emergency_detected:
                break
        # If not emergency, check for high urgency
        if not emergency_detected:
            high_urgency_indicators = ["severe", "intense", "worsening", "persistent"]
            for symptom in symptoms_lower:
                if any(indicator in symptom for indicator in high_urgency_indicators):
                    urgency = "high"
                    break
        # Determine suggested specialists
        suggested_specialists = []
        for specialist, keywords in self.specialists_mapping.items():
            for symptom in symptoms_lower:
                if any(keyword in symptom for keyword in keywords):
                    if specialist not in suggested_specialists:
                        suggested_specialists.append(specialist)
        # Default to general physician if no specialist matches
        if not suggested_specialists:
            suggested_specialists = ["general"]
        return {
            "urgency": urgency,
            "emergency_detected": emergency_detected,
            "suggested_specialists": suggested_specialists,
            "symptom_count": len(symptoms),
            "requires_urgent_care": urgency in ["high", "emergency"]
        }
    async def _check_drug_safety(self, medications: List[str], symptoms: List[str]) -> List[Dict]:
        """Check drug interactions and safety with current symptoms"""
        try:
            # Get drug interactions
            interactions = check_drug_interactions(medications)
            # Check if medications might worsen symptoms
            symptom_warnings = []
            symptom_medication_map = {
                "headache": ["ibuprofen", "aspirin"],
                "nausea": ["metformin", "antibiotics"],
                "dizziness": ["blood pressure medications"],
                "bleeding": ["warfarin", "aspirin", "clopidogrel"]
            }
            for symptom in symptoms:
                symptom_lower = symptom.lower()
                for med_symptom, risky_meds in symptom_medication_map.items():
                    if med_symptom in symptom_lower:
                        for medication in medications:
                            if any(risky_med in medication.lower() for risky_med in risky_meds):
                                warning = {
                                    "type": "symptom_medication_interaction",
                                    "medication": medication,
                                    "symptom": symptom,
                                    "warning": f"{medication} may worsen {symptom}",
                                    "severity": "medium"
                                }
                                symptom_warnings.append(warning)
            return interactions + symptom_warnings
        except Exception:
            return []
    async def _get_llm_recommendations(
        self,
        symptoms: List[str],
        medical_history: str,
        medications: Optional[List[str]],
        language: str
    ) -> Dict:
        """Get AI-powered medical recommendations from LLM"""
        # Build language-specific prompt
        language_context = {
            "en": "English",
            "am": "Amharic (አማርኛ)"
        }.get(language, "English")
        prompt = f"""
        As a medical AI assistant providing recommendations in {language_context}:
        PATIENT PRESENTATION:
        - Symptoms: {', '.join(symptoms)}
        - Medical History: {medical_history or 'Not provided'}
        - Current Medications: {', '.join(medications) if medications else 'None'}
        Please provide structured recommendations including:
        1. POSSIBLE DIAGNOSES: List 3-5 likely conditions with probability estimates
        2. RECOMMENDED MEDICATIONS: Suggest medications (considering current meds)
        3. LIFESTYLE RECOMMENDATIONS: Diet, exercise, rest suggestions
        4. EMERGENCY ADVICE: When to seek immediate help
        5. MONITORING INSTRUCTIONS: What to watch for
        6. DIAGNOSTIC TESTS: Recommended tests if needed
        Format as JSON with these keys:
        - diagnosis: array of objects with condition, probability, confidence
        - medications: array of objects with name, dosage, purpose, precautions
        - lifestyle: array of strings
        - emergency: array of red flag symptoms
        - monitoring: array of monitoring instructions
        - tests: array of recommended tests
        """
        try:
            llm_response = await query_llm(prompt)
            # Parse JSON response (in reality, structure your LLM to return JSON)
            # For now, return structured placeholder
            return self._parse_llm_response(llm_response)
        except Exception:
            # Fallback recommendations
            return self._get_fallback_recommendations(symptoms, language)
    async def _generate_scheduling_suggestions(
        self,
        urgency: str,
        specialists: List[str],
        patient_id: int
    ) -> List[Dict]:
        """Generate appointment scheduling suggestions based on urgency"""
        suggestions = []
        # Timeframe based on urgency
        timeframes = {
            "emergency": "Immediately (within 2 hours)",
            "high": "Within 24 hours",
            "medium": "Within 3 days",
            "low": "Within 1-2 weeks"
        }
        timeframe = timeframes.get(urgency, "Within 3 days")
        # For each specialist, create scheduling suggestion
        for specialist in specialists:
            # Check doctor availability from database
            available_doctors = self.db.execute(
                """
                SELECT doctor_id, name, specialty, available 
                FROM doctors 
                WHERE specialty LIKE ? AND available = 1
                LIMIT 3
                """,
                (f"%{specialist}%",)
            ).fetchall()
            for doctor in available_doctors:
                suggestion = {
                    "type": "appointment_suggestion",
                    "specialty": specialist,
                    "doctor_id": doctor["doctor_id"],
                    "doctor_name": doctor["name"],
                    "urgency": urgency,
                    "recommended_timeframe": timeframe,
                    "reason": f"Consultation for {specialist} specialist evaluation",
                    "priority": "high" if urgency in ["emergency", "high"] else "normal"
                }
                suggestions.append(suggestion)
        # Add telemedicine suggestion for low urgency cases
        if urgency in ["low", "medium"]:
            suggestions.append({
                "type": "telemedicine_suggestion",
                "service": "Virtual Consultation",
                "urgency": urgency,
                "recommended_timeframe": "Within 48 hours",
                "reason": "Initial assessment via video call",
                "priority": "normal"
            })
        return suggestions
    def _generate_voice_recommendations(self, recommendations: Dict, language: str) -> Dict:
        """Generate voice-friendly recommendations for Amharic/English"""
        # Short, clear phrases for voice synthesis
        voice_phrases = {
            "en": {
                "emergency": "Seek emergency care immediately if you experience: ",
                "medication": "Take your medication as prescribed: ",
                "follow_up": "Schedule a follow-up appointment within: ",
                "monitoring": "Monitor these symptoms daily: "
            },
            "am": {
                "emergency": "የሚከተሉትን ከተሰማችሁ ወዲያውኑ ወደ እርዳታ ይሂዱ: ",
                "medication": "በትእዛዝ እንደተጻፈው መድሃኒትዎን ይውሰዱ: ",
                "follow_up": "በመቀጠል የሚከተለውን ቀጠሮ ያስቀምጡ: ",
                "monitoring": "እነዚህን ምልክቶች በየቀኑ ይመልከቱ: "
            }
        }
        lang_phrases = voice_phrases.get(language, voice_phrases["en"])
        return {
            "emergency_instructions": lang_phrases["emergency"] + 
                "; ".join(recommendations.get("emergency", [])[:3]),
            "medication_reminder": lang_phrases["medication"] +
                "; ".join([med.get("name", "") for med in recommendations.get("medications", [])[:2]]),
            "follow_up_reminder": lang_phrases["follow_up"] + "2 days",
            "monitoring_instructions": lang_phrases["monitoring"] +
                "; ".join(recommendations.get("monitoring", [])[:3])
        }
    def _get_immediate_actions(self, urgency: str, language: str) -> List[str]:
        """Get immediate actions based on urgency level"""
        actions = {
            "en": {
                "emergency": [
                    "Call emergency services (911) immediately",
                    "Do not drive yourself to hospital",
                    "Have someone stay with you",
                    "Keep emergency medications accessible"
                ],
                "high": [
                    "Contact your doctor within 2 hours",
                    "Rest and avoid strenuous activity",
                    "Monitor symptoms closely",
                    "Prepare to go to urgent care if symptoms worsen"
                ],
                "medium": [
                    "Schedule doctor appointment within 24 hours",
                    "Take recommended OTC medications",
                    "Apply home care measures",
                    "Keep symptom diary"
                ],
                "low": [
                    "Schedule routine appointment",
                    "Follow home care instructions",
                    "Monitor for any changes",
                    "Take medications as directed"
                ]
            },
            "am": {
                "emergency": [
                    "ወዲያውኑ የእርዳታ ቁጥር (911) ይደውሉ",
                    "ራስዎን ወደ ሆስፒታል አትነዱ",
                    "አንድ ሰው ከእርስዎ ጋር ይቆይ",
                    "የአደጋ መድሃኒቶች በቀላሉ ይገኙ"
                ],
                "high": [
                    "ዶክተርዎን በ2 ሰዓታት ውስጥ ያነጋግሩ",
                    "ይደረቁ እና ከባድ እንቅስቃሴ ያስወግዱ",
                    "ምልክቶችን በቅርበት ይመልከቱ",
                    "ምልክቶች ከተባበሩ ወደ አስቸኳይ እርዳታ ይሂዱ"
                ]
            }
        }
        lang_actions = actions.get(language, actions["en"])
        return lang_actions.get(urgency, lang_actions["low"])
    def _get_follow_up_timeline(self, urgency: str) -> Dict:
        """Get follow-up timeline based on urgency"""
        timelines = {
            "emergency": {"next_follow_up": "24 hours", "subsequent": "1 week"},
            "high": {"next_follow_up": "48 hours", "subsequent": "2 weeks"},
            "medium": {"next_follow_up": "1 week", "subsequent": "1 month"},
            "low": {"next_follow_up": "2 weeks", "subsequent": "3 months"}
        }
        return timelines.get(urgency, timelines["low"])
    def _parse_llm_response(self, response: str) -> Dict:
        """Parse LLM response (simplified - in reality, use proper JSON parsing)"""
        # This is a simplified parser
        # In production, ensure your LLM returns structured JSON
        return {
            "diagnosis": [
                {"condition": "Upper Respiratory Infection", "probability": "70%", "confidence": "high"},
                {"condition": "Seasonal Allergies", "probability": "20%", "confidence": "medium"},
                {"condition": "COVID-19", "probability": "10%", "confidence": "low"}
            ],
            "medications": [
                {"name": "Acetaminophen", "dosage": "500mg", "purpose": "Fever/pain", "precautions": "Take with food"},
                {"name": "Antihistamine", "dosage": "10mg", "purpose": "Allergy symptoms", "precautions": "May cause drowsiness"}
            ],
            "lifestyle": [
                "Get plenty of rest",
                "Drink 8-10 glasses of water daily",
                "Use humidifier for cough",
                "Avoid smoking and pollutants"
            ],
            "emergency": [
                "Difficulty breathing",
                "High fever (>103°F/39.4°C)",
                "Severe chest pain",
                "Confusion or disorientation"
            ],
            "monitoring": [
                "Check temperature twice daily",
                "Monitor breathing rate",
                "Note any new symptoms",
                "Track medication effectiveness"
            ],
            "tests": [
                "Complete Blood Count (CBC)",
                "Chest X-ray if cough persists",
                "COVID-19 test",
                "Allergy panel if symptoms continue"
            ]
        }
    def _get_fallback_recommendations(self, symptoms: List[str], language: str) -> Dict:
        """Provide fallback recommendations if LLM fails"""
        # Simple rule-based recommendations
        if any(s in " ".join(symptoms).lower() for s in ["fever", "cough", "cold"]):
            return {
                "diagnosis": [{"condition": "Viral Infection", "probability": "Likely", "confidence": "medium"}],
                "medications": [
                    {"name": "Acetaminophen", "dosage": "As needed", "purpose": "Fever", "precautions": ""},
                    {"name": "Cough Syrup", "dosage": "As directed", "purpose": "Cough", "precautions": ""}
                ],
                "lifestyle": ["Rest", "Hydrate", "Humidifier"],
                "emergency": ["Difficulty breathing", "High fever"],
                "monitoring": ["Temperature", "Cough frequency"],
                "tests": ["None required unless symptoms worsen"]
            }
        return {
            "diagnosis": [{"condition": "Symptomatic Management Needed", "probability": "Assessment required", "confidence": "low"}],
            "medications": [],
            "lifestyle": ["Consult healthcare provider"],
            "emergency": [],
            "monitoring": ["Symptom progression"],
            "tests": ["Clinical evaluation recommended"]
        }
    async def _store_recommendations(self, recommendations: Dict):
        """Store recommendations in database"""
        try:
            self.db.execute(
                """
                INSERT INTO medical_recommendations 
                (recommendation_id, patient_id, consultation_id, urgency_level, 
                 recommendations_json, created_at, language)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    recommendations["recommendation_id"],
                    recommendations["patient_id"],
                    recommendations.get("consultation_id"),
                    recommendations["urgency_level"],
                    json.dumps(recommendations),
                    recommendations["timestamp"],
                    recommendations["language"]
                )
            )
            self.db.commit()
        except Exception as e:
            print(f"Error storing recommendations: {e}")

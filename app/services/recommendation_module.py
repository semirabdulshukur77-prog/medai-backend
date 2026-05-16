import asyncio

async def get_ai_recommendations():
    """
    Return live AI recommendations for dashboard.
    Replace with real LLM or recommendation agent logic in production.
    """
    await asyncio.sleep(0.1)  # simulate async processing
    return [
        {"patient": "Patient 1", "recommendation": "Follow-up lab test suggested"},
        {"patient": "Patient 2", "recommendation": "Check vitals daily"},
    ]


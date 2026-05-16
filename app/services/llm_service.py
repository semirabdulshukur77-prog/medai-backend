# backend/app/services/llm_service.py
from typing import Optional
from fastapi import UploadFile
from app.core.config import settings

async def query_llm(query: str, image: Optional[UploadFile] = None) -> str:
    """
    Generate response from LLM for text + optional image.
    """
    # Placeholder implementation - integrate with Gemini API or other LLM
    response_text = f"Processed query: {query}"

    if image:
        # You can integrate an image captioning / analysis ML model here
        response_text += f" | Image '{image.filename}' analyzed successfully."

    # Future: integrate voice or recommendation context
    return response_text

async def generate_multimodal_response(query: str, image=None) -> str:
    """
    Placeholder: Generate response from LLM for text + optional image.
    """
    return await query_llm(query, image)


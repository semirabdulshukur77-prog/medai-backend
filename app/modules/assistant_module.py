from fastapi import UploadFile
from app.services.llm_service import query_llm
from app.services.radiology_module import analyze_image
from app.services.drug_module import check_drug_interactions
from typing import List, Optional

async def handle_assistant_query(
    text: Optional[str] = None,
    image: Optional[UploadFile] = None,
    drugs: Optional[List[str]] = None
):
    """
    Handles multimodal queries:
    - text queries → LLM
    - images → radiology analysis
    - drug list → interaction check
    """
    response = {"text": None, "image_analysis": None, "drug_interactions": None}

    # Text / LLM
    if text:
        response["text"] = await query_llm(text)

    # Image / Radiology
    if image:
        response["image_analysis"] = await analyze_image(image)

    # Drug Interactions
    if drugs:
        response["drug_interactions"] = check_drug_interactions(drugs)

    return response


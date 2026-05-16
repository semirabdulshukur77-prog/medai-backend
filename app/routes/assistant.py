from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from app.modules.assistant_module import handle_assistant_query
from typing import List, Optional

router = APIRouter()

@router.post("/api/assistant/query")
async def assistant_query(
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    drugs: Optional[List[str]] = Form(None)
):
    """
    Accepts multimodal input (text, image, drugs) and returns AI responses
    """
    try:
        result = await handle_assistant_query(text, image, drugs)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


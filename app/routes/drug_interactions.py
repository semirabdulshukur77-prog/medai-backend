# backend/app/routes/drug_interactions.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.services.drug_module import check_drug_interactions
from pydantic import BaseModel
from typing import List

router = APIRouter()

class DrugListRequest(BaseModel):
    drugs: List[str]

@router.post("/api/drug_interactions")
async def check_drug_interaction(request: DrugListRequest):
    """
    Accepts a list of drugs and returns known interactions.
    """
    try:
        interactions = check_drug_interactions(request.drugs)
        return JSONResponse(content={"interactions": interactions})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


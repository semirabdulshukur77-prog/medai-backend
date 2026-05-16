from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.services.radiology_module import analyze_image

router = APIRouter()

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "tiff"}

def allowed_file(filename: str) -> bool:
    if not filename:
        return False
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@router.post("/api/radiology/analyze")
async def radiology_analyze(image: UploadFile = File(...)):
    """
    Accepts an image (X-ray, MRI, etc.) and returns AI analysis.
    Validates file type and handles errors.
    """
    if not allowed_file(image.filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: png, jpg, jpeg, bmp, tiff"
        )

    try:
        # Call the AI analysis service
        result = await analyze_image(image)

        # Structure the response with metadata for future expansion
        response = {
            "filename": image.filename,
            "content_type": image.content_type,
            "analysis": result,
            "status": "success"
        }
        return JSONResponse(content=response)

    except Exception as e:
        # Handle unexpected errors
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Failed to analyze image: {str(e)}"
            }
        )


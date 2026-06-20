from fastapi import APIRouter, File, UploadFile, HTTPException
from app.schemas.ml import AnalyzeImageResponse
from app.ml.analyzer import analyze_image

router = APIRouter(
    prefix="/analyze",
    tags=["ML Analysis"]
)

@router.post("/image", response_model=AnalyzeImageResponse)
async def analyze_road_image(file: UploadFile = File(...)):
    
    # Only allow images
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files allowed")
    
    # Read image bytes
    image_bytes = await file.read()
    
    # Pass to ML model
    result = analyze_image(image_bytes)
    
    return result
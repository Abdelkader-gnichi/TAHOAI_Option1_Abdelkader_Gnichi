from fastapi import APIRouter, UploadFile, File, HTTPException
from models.schemas import ClassificationRequest, ClassificationResponse
from services.classification import classify_text_with_google
from services.database import log_classification
from core.logging_config import logger

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.post("/classify", response_model=ClassificationResponse)
async def classify(request: ClassificationRequest):
    try:
        text = request.text.strip()
        if len(text) < 10:
            raise HTTPException(status_code=400, detail="Text is too short for classification")
        if len(text) > 2000:
            logger.info(f"Truncating text from {len(text)} to 2000 characters")
            text = text[:2000]
        result = await classify_text_with_google(text)
        log_classification(len(text), result["label"], result["confidence"])
        return result
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail="Classification error")

@router.post("/classify/file", response_model=ClassificationResponse)
async def classify_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = content.decode("utf-8").strip()
        if len(text) < 10:
            raise HTTPException(status_code=400, detail="File content too short")
        if len(text) > 2000:
            logger.info(f"Truncating text from {len(text)} to 2000 characters")
            text = text[:2000]
        result = await classify_text_with_google(text)
        log_classification(len(text), result["label"], result["confidence"])
        return result
    except Exception as e:
        logger.error(f"File classification error: {e}")
        raise HTTPException(status_code=500, detail="File classification error")

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
from typing import Optional
import sqlite3
import datetime
from transformers import pipeline
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Document Classification API")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize document classifier
# We're using a zero-shot classifier that can classify text without specific training
classifier = pipeline("zero-shot-classification")
DOCUMENT_LABELS = ["Invoice", "Contract", "Resume", "Email", "Report"]

# Database setup
def setup_db():
    conn = sqlite3.connect("classification_logs.db")
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS classification_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        text_length INTEGER,
        label TEXT,
        confidence REAL
    )
    ''')
    conn.commit()
    conn.close()

# Setup DB on startup
@app.on_event("startup")
async def startup_event():
    setup_db()
    logger.info("Application started, database initialized")

# Request models
class ClassificationRequest(BaseModel):
    text: str

class ClassificationResponse(BaseModel):
    label: str
    confidence: float

# Log classification to database
def log_classification(text_length, label, confidence):
    try:
        conn = sqlite3.connect("classification_logs.db")
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO classification_logs (timestamp, text_length, label, confidence) VALUES (?, ?, ?, ?)",
            (timestamp, text_length, label, confidence)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Database logging error: {e}")

# API endpoints
@app.post("/classify", response_model=ClassificationResponse)
async def classify_document(request: ClassificationRequest):
    try:
        text = request.text
        
        # Validate input
        if not text or len(text.strip()) < 10:
            raise HTTPException(status_code=400, detail="Text is too short for classification")
            
        # Truncate very long text to avoid model issues
        if len(text) > 1024:
            logger.info(f"Truncating input text from {len(text)} to 1024 characters")
            text = text[:1024]
        
        # Perform classification using the model
        result = classifier(text, DOCUMENT_LABELS, multi_label=False)
        
        # Extract the best label and its confidence
        best_label = result["labels"][0]
        confidence = round(result["scores"][0], 2)
        
        # Log the classification
        log_classification(len(text), best_label, confidence)
        
        logger.info(f"Document classified as {best_label} with confidence {confidence}")
        return {"label": best_label, "confidence": confidence}
        
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")

@app.post("/classify/file")
async def classify_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = content.decode("utf-8")
        
        # Validate input
        if not text or len(text.strip()) < 10:
            raise HTTPException(status_code=400, detail="File content is too short for classification")
            
        # Truncate very long text to avoid model issues
        if len(text) > 1024:
            logger.info(f"Truncating input text from {len(text)} to 1024 characters")
            text = text[:1024]
        
        # Perform classification using the model
        result = classifier(text, DOCUMENT_LABELS, multi_label=False)
        
        # Extract the best label and its confidence
        best_label = result["labels"][0]
        confidence = round(result["scores"][0], 2)
        
        # Log the classification
        log_classification(len(text), best_label, confidence)
        
        logger.info(f"Document classified as {best_label} with confidence {confidence}")
        return {"label": best_label, "confidence": confidence}
        
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
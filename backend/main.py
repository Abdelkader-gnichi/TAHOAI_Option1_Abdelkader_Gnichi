from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
from typing import Optional
import sqlite3
import datetime
import os
import google.generativeai as genai
from google.oauth2 import service_account
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

# Initialize Google AI configuration
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    logger.warning("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=API_KEY)

# Document classification categories
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

# Classification function using Google's Generative AI
async def classify_text_with_google(text):
    prompt = f"""
    Classify the following document into exactly one of these categories: 
    {', '.join(DOCUMENT_LABELS)}. 
    
    Respond with a JSON object containing only two fields:
    - "label": the chosen category
    - "confidence": a decimal between 0 and 1 representing your confidence
    
    Document text:
    "{text}"
    
    JSON response (only):
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        # Parse the JSON response from the model
        response_text = response.text.strip()
        
        # Handle the case where the response might include markdown code block formatting
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].strip()
            
        result = json.loads(response_text)
        
        # Basic validation of the result
        if "label" not in result or "confidence" not in result:
            raise ValueError("Invalid response format from the model")
            
        # Ensure label is one of our defined categories
        if result["label"] not in DOCUMENT_LABELS:
            raise ValueError(f"Invalid category: {result['label']}")
            
        # Ensure confidence is between 0 and 1
        if not 0 <= result["confidence"] <= 1:
            result["confidence"] = max(0, min(result["confidence"], 1))
            
        return result
        
    except Exception as e:
        logger.error(f"Google AI classification error: {e}")
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")

# API endpoints
@app.post("/classify", response_model=ClassificationResponse)
async def classify_document(request: ClassificationRequest):
    try:
        text = request.text
        
        # Validate input
        if not text or len(text.strip()) < 10:
            raise HTTPException(status_code=400, detail="Text is too short for classification")
            
        # Truncate very long text to avoid model issues
        if len(text) > 2000:
            logger.info(f"Truncating input text from {len(text)} to 2000 characters")
            text = text[:2000]
        
        # Perform classification using the Google AI
        result = await classify_text_with_google(text)
        
        # Extract the label and its confidence
        label = result["label"]
        confidence = result["confidence"]
        
        # Log the classification
        log_classification(len(text), label, confidence)
        
        logger.info(f"Document classified as {label} with confidence {confidence}")
        return {"label": label, "confidence": confidence}
        
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")

@app.post("/classify/file", response_model=ClassificationResponse)
async def classify_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = content.decode("utf-8")
        
        # Validate input
        if not text or len(text.strip()) < 10:
            raise HTTPException(status_code=400, detail="File content is too short for classification")
            
        # Truncate very long text to avoid model issues
        if len(text) > 2000:
            logger.info(f"Truncating input text from {len(text)} to 2000 characters")
            text = text[:2000]
        
        # Perform classification using the Google AI
        result = await classify_text_with_google(text)
        
        # Extract the label and its confidence
        label = result["label"]
        confidence = result["confidence"]
        
        # Log the classification
        log_classification(len(text), label, confidence)
        
        logger.info(f"Document classified as {label} with confidence {confidence}")
        return {"label": label, "confidence": confidence}
        
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
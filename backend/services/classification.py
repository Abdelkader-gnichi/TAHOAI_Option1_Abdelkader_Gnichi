import json
import os
from fastapi import HTTPException
from core.logging_config import logger
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

DOCUMENT_LABELS = ["Invoice", "Contract", "Resume", "Email", "Report"]

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    logger.warning("GOOGLE_API_KEY is not set in .env")
genai.configure(api_key=API_KEY)

async def classify_text_with_google(text: str):
    prompt = f"""
    Classify the following document into one of the categories: {', '.join(DOCUMENT_LABELS)}.
    Return a JSON with "label" and "confidence" between 0 and 1.
    
    Text: "{text}"
    
    JSON only:
    """
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        content = response.text.strip()

        # Remove Markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()

        result = json.loads(content)

        if "label" not in result or "confidence" not in result:
            raise ValueError("Model response format invalid")

        label = result["label"]
        confidence = result["confidence"]

        if label not in DOCUMENT_LABELS:
            raise ValueError(f"Invalid label returned: {label}")

        confidence = max(0, min(confidence, 1))

        return {"label": label, "confidence": confidence}

    except Exception as e:
        logger.error(f"Google AI classification error: {e}")
        raise HTTPException(status_code=500, detail="Classification error")

# TAHO AI Document Classifier

A fullstack application that allows users to classify documents using AI. The application exposes Google's Generative AI (Gemini) via a backend API and presents the results in a frontend interface.



https://github.com/user-attachments/assets/cd0d7fbf-03bd-4308-bb28-29977b92dc74




## Project Structure
   
```

├── backend/                      # Backend (FastAPI) code
│   ├── api/                      # API endpoint definitions
│   │   └── routes.py             # Route handlers
│   ├── core/                     # Core configurations
│   │   └── logging_config.py     # Logging setup
│   ├── models/                   # Data models/schemas
│   │   └── schemas.py            # Pydantic schemas
│   ├── services/                 # Business logic
│   │   ├── classification.py     # ML classification service
│   │   └── database.py           # Database operations
│   ├── main.py                   # FastAPI app entrypoint
│   ├── Dockerfile                # Backend Docker configuration
│   └── requirements.txt          # Python dependencies
│
├── frontend/                     # Frontend (React) code
│   ├── src/                      
│   │   ├── App.tsx               # Root React component
│   │   └── ...                   # Other components/assets
│   ├── package.json              # Frontend dependencies
│   └── Dockerfile                # Frontend Docker configuration
│
├── classification_logs.db        # SQLite database (consider moving to `backend/data/`)
├── .env                          # Environment variables
├── docker-compose.yml            # Multi-container setup
└── README.md                     # Project docs
```

## Features

- Frontend allows users to paste text or upload a text file
- Backend API classifies the document and returns a label and confidence score
- Classification results are logged to a SQLite database
- Error handling and loading states in the UI
- Docker setup for easy deployment

## AI Model Information

This application uses Google's Generative AI (gemini-2.0-flash) to classify documents into predefined categories:
- Invoice
- Contract
- Resume
- Email
- Report

The model analyzes the text and determines the most likely category based on content.

## Prerequisites

1. **Google API Key**: You need to obtain a Google API key for Gemini:
   - Go to https://ai.google.dev/ and sign up
   - Create a new API key
   - Add it to your `.env` file as `GOOGLE_API_KEY=your_key_here`

## How to Run Locally

### Option 1: With Docker (Recommended)

1. Make sure you have Docker and Docker Compose installed
2. Clone this repository

Run the following command to clone the repository to your local machine:

```bash
git clone https://github.com/Abdelkader-gnichi/TAHOAI_Option1_Abdelkader_Gnichi.git

```
3. Create a `.env` file in the backend directory with your Google API key
4. Run ` docker compose up --build -d`
5. Access the frontend at http://localhost:5173/

### Option 2: Without Docker

#### Backend Setup

1. Navigate to the backend directory: `cd backend`
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with your Google API key
6. Run the backend: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`

#### Frontend Setup

1. Navigate to the frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Run the frontend: `npm run dev`
4. Access the frontend at http://localhost:5173/

## API Documentation

The backend API is available at http://localhost:8000/docs when the server is running.

### Endpoints

- `POST /classify`: Accepts a JSON payload with a text field and returns classification results
- `POST /classify/file`: Accepts a file upload and returns classification results
- `GET /health`: Health check endpoint

## Implementation Notes

### ML Model

- The application uses Google's Generative AI (gemini-2.0-flash) for document classification
- The model is prompted to classify document text into one of the predefined categories
- The model returns a label and confidence score
- No model downloading or local computation is required

### Alternative Implementation

I initially implemented the solution using Hugging Face's zero-shot classification model, which:
- Required installing transformers, torch, and other dependencies
- Took considerable time to download and set up initially
- Worked effectively for classifying documents
- Was replaced with the Google API solution for efficiency and ease of setup

### Limitations and Future Improvements

- Authentication and rate limiting are not implemented
- For production use, the CORS policy should be restricted to specific origins
- Adding caching for frequent document types could improve performance


## Testing

To run the basic tests:

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## License

This project is intended as a coding challenge for TAHO AI and is not licensed for public use.

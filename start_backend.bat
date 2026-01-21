@echo off
echo Starting NoteTracker Backend (FastAPI)...
cd api
python -m uvicorn main:app --reload --port 8000

from fastapi import Request
from backend.core.detector import MicroplasticDetector
from backend.db.database import SessionLocal

def get_detector(request: Request) -> MicroplasticDetector:
    """
    FastAPI dependency to retrieve the globally loaded 
    MicroplasticDetector instance from the application state.
    """
    return request.app.state.detector

def get_db():
    """
    FastAPI dependency to provide a database session per request.
    Closes the session automatically when the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

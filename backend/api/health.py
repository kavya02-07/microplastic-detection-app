from fastapi import APIRouter, Depends
from backend.core.detector import MicroplasticDetector
from backend.dependencies import get_detector

router = APIRouter()

@router.get("/health")
def check_health(detector: MicroplasticDetector = Depends(get_detector)):
    """
    Check if the API and the AI Model are running properly.
    """
    return {
        "status": "ok",
        "model_loaded": detector is not None,
        "model_name": detector.model_name if detector else None,
        "message": "Microplastic Detection API is ready."
    }

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Schema for an individual detection (response)
class DetectionResponse(BaseModel):
    id: int
    class_id: int
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    width: float
    height: float
    area: float
    aspect_ratio: float

    class Config:
        from_attributes = True

# Schema for an analysis summary (response)
class AnalysisBase(BaseModel):
    id: int
    user_id: Optional[int] = None
    original_filename: str
    confidence_threshold: float
    total_detections: int
    average_confidence: float
    inference_time_ms: float
    created_at: datetime

    class Config:
        from_attributes = True

# Schema for an analysis that includes its child detections
class AnalysisWithDetections(AnalysisBase):
    detections: List[DetectionResponse] = []

import io
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from backend.core.detector import MicroplasticDetector
from backend.db import models
from backend.db.models import User
from backend.dependencies import get_detector, get_db
from backend.auth.dependencies import get_current_user

router = APIRouter()

@router.post("/detect")
async def detect_microplastics(
    file: UploadFile = File(...),
    confidence: float = Form(0.40),
    detector: MicroplasticDetector = Depends(get_detector),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accepts an uploaded image and an optional confidence threshold,
    runs the microplastic YOLO detection, saves results to the database
    under the authenticated user, and returns structured JSON results.
    """
    # 1. Validate inputs
    if confidence < 0.0 or confidence > 1.0:
        raise HTTPException(status_code=400, detail="Confidence must be between 0.0 and 1.0.")

    # 2. Validate and load the image
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Ensure image is in RGB format for YOLO
        if image.mode != "RGB":
            image = image.convert("RGB")
            
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading image: {str(e)}")

    # 3. Perform AI Inference (reusing Phase 1 MicroplasticDetector)
    try:
        result = detector.detect(image, confidence=confidence)
        
        # 4. Save to Database (tied to the authenticated user)
        db_analysis = models.Analysis(
            user_id=current_user.id,
            original_filename=file.filename,
            confidence_threshold=confidence,
            total_detections=result.summary.total_detections,
            average_confidence=result.summary.average_confidence,
            inference_time_ms=result.summary.inference_time_ms
        )
        db.add(db_analysis)
        db.flush() # Flush to get the ID without fully committing yet
        
        # Save individual detections
        for obj in result.objects:
            db_det = models.Detection(
                analysis_id=db_analysis.id,
                class_id=obj.class_id,
                class_name=obj.class_name,
                confidence=obj.confidence,
                x1=obj.bbox.x1,
                y1=obj.bbox.y1,
                x2=obj.bbox.x2,
                y2=obj.bbox.y2,
                width=obj.width,
                height=obj.height,
                area=obj.area,
                aspect_ratio=obj.aspect_ratio
            )
            db.add(db_det)
            
        db.commit()
        db.refresh(db_analysis)
        
        # 5. Return structured JSON exactly matching Phase 1 schemas
        # We also inject the database record ID as requested.
        out = result.to_dict()
        out["id"] = db_analysis.id
        return out
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Detection inference failed: {str(e)}")

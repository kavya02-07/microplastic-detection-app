from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.db import models, schemas
from backend.db.models import User
from backend.dependencies import get_db
from backend.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/analyses", response_model=List[schemas.AnalysisBase])
def list_analyses(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve previously saved analyses for the authenticated user, ordered newest first.
    """
    analyses = db.query(models.Analysis)\
                 .filter(models.Analysis.user_id == current_user.id)\
                 .order_by(models.Analysis.id.desc())\
                 .offset(skip).limit(limit).all()
    return analyses


@router.get("/analyses/{analysis_id}", response_model=schemas.AnalysisWithDetections)
def get_analysis(
    analysis_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve one specific analysis together with its individual detections,
    ensuring it belongs to the authenticated user.
    """
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    if analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this analysis")
        
    return analysis

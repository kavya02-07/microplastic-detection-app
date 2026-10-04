"""
Model Evaluation endpoint.

Exposes the research/evaluation metrics that were extracted from the deployed
checkpoint (weights/t29.pt) into backend/core/model_metrics.json. Read-only,
served from an in-memory cache — the 52 MB checkpoint is never reloaded here.
"""

from fastapi import APIRouter, Depends, HTTPException

from backend.db.models import User
from backend.auth.dependencies import get_current_user
from backend.core import model_evaluation

router = APIRouter()


@router.get("/model/evaluation")
def get_model_evaluation_metrics(current_user: User = Depends(get_current_user)):
    """
    Return the deployed model's embedded training-run validation metrics,
    training configuration, and full per-epoch history.

    Evidence type is 'training_run_validation': these are validation-split
    figures recorded during the original training run, not independent
    test-set results.
    """
    try:
        return model_evaluation.get_model_evaluation()
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Model evaluation metrics are not available. "
                "The extraction step (scripts/extract_model_metrics.py) has not been run."
            ),
        )

"""
CarePath AI — Prediction API Routes
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.prediction import WaitTimePredictionRequest, WaitTimePredictionResponse
from app.services.wait_prediction_service import WaitPredictionService

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.post("/wait-time", response_model=WaitTimePredictionResponse, summary="Predict wait time")
async def predict_wait_time(
    request: WaitTimePredictionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a wait-time prediction using the trained LightGBM model.
    Input features must match the model's training schema (20 queue-theory-augmented features).
    """
    svc = WaitPredictionService(db)
    return await svc.predict(request)

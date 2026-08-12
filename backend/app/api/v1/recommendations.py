"""
CarePath AI — Recommendation & Optimization API Routes
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    OptimizationRequest,
    OptimizationResponse,
    ExplanationResponse,
)
from app.services.recommendation_service import RecommendationService

router = APIRouter(tags=["Recommendations"])


@router.post("/recommendations", response_model=RecommendationResponse, summary="Generate recommendations")
async def generate_recommendations(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Orchestrates the complete pipeline: referral → analysis → candidates →
    wait prediction → optimization → ranked recommendations.
    """
    svc = RecommendationService(db)
    result = await svc.generate(
        referral_id=request.referral_id,
        top_k=request.top_k,
        max_distance_km=request.max_distance_km,
        weight_wait_time=request.weight_wait_time,
        weight_distance=request.weight_distance,
        weight_capacity=request.weight_capacity,
        weight_fairness=request.weight_fairness,
    )
    return RecommendationResponse(**result)


@router.get(
    "/recommendations/{recommendation_id}/explanation",
    response_model=ExplanationResponse,
    summary="Get recommendation explanation",
)
async def get_explanation(recommendation_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get the evidence-grounded explanation for a recommendation.
    Based on actual prediction outputs, optimization scores, and constraints.
    """
    svc = RecommendationService(db)
    result = await svc.get_explanation(recommendation_id)
    return ExplanationResponse(**result)

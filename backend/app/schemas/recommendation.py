"""
CarePath AI — Pydantic Schemas for Recommendations & Optimization
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class OptimizationRequest(BaseModel):
    referral_id: UUID
    candidate_provider_ids: Optional[list[UUID]] = None
    # Objective weights (configurable, not hard-coded)
    weight_wait_time: float = Field(default=0.4, ge=0, le=1)
    weight_distance: float = Field(default=0.3, ge=0, le=1)
    weight_capacity: float = Field(default=0.2, ge=0, le=1)
    weight_fairness: float = Field(default=0.1, ge=0, le=1)
    top_k: int = Field(default=3, ge=1, le=20)
    max_distance_km: Optional[float] = None
    enforce_specialty_match: bool = True
    enforce_active_only: bool = True


class OptimizationCandidateResponse(BaseModel):
    rank: int
    provider_id: UUID
    provider_name: Optional[str] = None
    provider_npi: Optional[str] = None
    specialty: Optional[str] = None
    predicted_wait_days: Optional[float] = None
    distance_km: Optional[float] = None
    capacity_score: Optional[float] = None
    objective_score: float
    constraints_satisfied: list[str] = []
    reasons: list[str] = []


class OptimizationResponse(BaseModel):
    optimization_id: UUID
    referral_id: UUID
    recommendations: list[OptimizationCandidateResponse]
    optimization_method: str = "OR-Tools CP-SAT"
    optimization_time_ms: float
    config_used: dict
    timestamp: datetime


class RecommendationRequest(BaseModel):
    referral_id: UUID
    top_k: int = Field(default=3, ge=1, le=10)
    max_distance_km: float = Field(default=50.0, ge=1, le=500)
    weight_wait_time: float = Field(default=0.4, ge=0, le=1)
    weight_distance: float = Field(default=0.3, ge=0, le=1)
    weight_capacity: float = Field(default=0.2, ge=0, le=1)
    weight_fairness: float = Field(default=0.1, ge=0, le=1)


class RecommendationResponse(BaseModel):
    recommendation_id: UUID
    referral_id: UUID
    recommendations: list[OptimizationCandidateResponse]
    optimization_method: str
    explanation: Optional[str] = None
    optimization_time_ms: float
    timestamp: datetime


class ExplanationResponse(BaseModel):
    recommendation_id: UUID
    explanation: str
    evidence: dict = {}
    generated_at: datetime

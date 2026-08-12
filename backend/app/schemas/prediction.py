"""
CarePath AI — Pydantic Schemas for Predictions
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class WaitTimePredictionRequest(BaseModel):
    """Input for wait-time prediction — mirrors the actual trained model features."""
    provider_id: Optional[UUID] = None
    specialty: str
    arrival_rate_lambda: float = Field(ge=0)
    queue_length_Lq: float = Field(ge=0)
    utilization_rho: float = Field(ge=0, le=1)
    active_backlog: int = Field(ge=0)
    server_count: int = Field(default=15, ge=1)
    service_rate_mu: float = Field(default=3.5, gt=0)
    day_of_week: int = Field(default=1, ge=0, le=6)
    month: int = Field(default=6, ge=1, le=12)
    hour_of_day: int = Field(default=10, ge=0, le=23)
    org_size: int = Field(default=200, ge=1)
    offers_telehealth: int = Field(default=0, ge=0, le=1)


class WaitTimePredictionResponse(BaseModel):
    prediction_id: UUID
    predicted_wait_days: float
    model_name: str = "carepath_wait_time"
    model_version: str
    features_used: dict
    shap_values: Optional[dict] = None
    inference_time_ms: float
    timestamp: datetime
    # No fabricated confidence — the model does not produce calibrated intervals
    data_source_note: str = "Prediction based on queue-theory-augmented LightGBM model trained on synthetic data calibrated from real distributions."


class BatchPredictionRequest(BaseModel):
    predictions: list[WaitTimePredictionRequest]


class BatchPredictionResponse(BaseModel):
    predictions: list[WaitTimePredictionResponse]
    total: int
    batch_inference_time_ms: float

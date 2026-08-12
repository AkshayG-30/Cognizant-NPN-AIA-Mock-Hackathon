"""
CarePath AI — Pydantic Schemas for Referrals
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ReferralCreateRequest(BaseModel):
    patient_id: Optional[UUID] = None
    clinical_text: Optional[str] = None
    symptoms: Optional[list[str]] = None
    conditions: Optional[list[str]] = None
    target_specialty: Optional[str] = None
    urgency: str = Field(default="routine", pattern="^(routine|urgent|emergent|stat)$")
    referring_provider_npi: Optional[str] = None
    preferred_location_lat: Optional[float] = None
    preferred_location_lng: Optional[float] = None
    max_distance_km: float = Field(default=50.0, ge=1, le=500)
    insurance_network: Optional[str] = None
    patient_preferences: Optional[dict] = None


class ReferralUpdateRequest(BaseModel):
    clinical_text: Optional[str] = None
    symptoms: Optional[list[str]] = None
    conditions: Optional[list[str]] = None
    target_specialty: Optional[str] = None
    urgency: Optional[str] = None
    status: Optional[str] = None
    max_distance_km: Optional[float] = None
    insurance_network: Optional[str] = None


class ReferralResponse(BaseModel):
    id: UUID
    patient_id: Optional[UUID] = None
    referring_provider_npi: Optional[str] = None
    clinical_text: Optional[str] = None
    symptoms: Optional[list[str]] = None
    conditions: Optional[list[str]] = None
    target_specialty: Optional[str] = None
    target_subspecialty: Optional[str] = None
    urgency: str
    status: str
    inferred_specialty: Optional[str] = None
    inferred_urgency: Optional[str] = None
    missing_information: Optional[list[str]] = None
    max_distance_km: Optional[float] = None
    insurance_network: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReferralListResponse(BaseModel):
    referrals: list[ReferralResponse]
    total: int
    page: int = 1
    page_size: int = 50


class ReferralAnalysisResponse(BaseModel):
    referral_id: UUID
    specialty: Optional[str] = None
    subspecialty: Optional[str] = None
    urgency: Optional[str] = None
    entities: list[dict] = []
    missing_information: list[str] = []
    extraction_confidence: Optional[str] = None  # "EXTRACTED" | "INFERRED" | "MISSING"
    model: Optional[str] = None
    model_version: Optional[str] = None
    status: str = "analyzed"

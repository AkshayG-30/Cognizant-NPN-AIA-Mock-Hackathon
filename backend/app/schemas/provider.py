"""
CarePath AI — Pydantic Schemas for Providers
Request/response models for provider APIs.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProviderBase(BaseModel):
    npi: str
    first_name: str
    last_name: str
    specialty: str
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None


class ProviderResponse(ProviderBase):
    id: UUID
    gender: Optional[str] = None
    credential: Optional[str] = None
    original_specialty: Optional[str] = None
    secondary_specialties: Optional[str] = None
    offers_telehealth: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accepts_medicare_individual: Optional[str] = None
    accepts_medicare_group: Optional[str] = None
    is_active: bool = True
    data_source: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProviderListResponse(BaseModel):
    providers: list[ProviderResponse]
    total: int
    page: int = 1
    page_size: int = 50


class ProviderCapacityResponse(BaseModel):
    provider_id: UUID
    current_queue_length: int = 0
    active_backlog: int = 0
    appointment_capacity: Optional[int] = None
    server_count: Optional[int] = None
    service_rate_mu: Optional[float] = None
    utilization_rho: Optional[float] = None
    arrival_rate_lambda: Optional[float] = None
    is_synthetic: bool = True
    snapshot_at: datetime

    model_config = {"from_attributes": True}


class ProviderWaitHistoryResponse(BaseModel):
    provider_id: UUID
    avg_wait_days: Optional[float] = None
    median_wait_days: Optional[float] = None
    p90_wait_days: Optional[float] = None
    sample_count: Optional[int] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    is_synthetic: bool = True

    model_config = {"from_attributes": True}


class ProviderSearchRequest(BaseModel):
    specialty: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    max_distance_km: float = Field(default=50.0, ge=1, le=500)
    offers_telehealth: Optional[bool] = None
    accepts_medicare: Optional[bool] = None
    is_active: bool = True
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)

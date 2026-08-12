"""
CarePath AI — Pydantic Schemas for Appointments, FHIR, Monitoring, and System
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Appointment Schemas ──────────────────────────────────────

class AppointmentCreateRequest(BaseModel):
    referral_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None
    provider_id: UUID
    recommendation_id: Optional[UUID] = None
    slot_id: Optional[UUID] = None
    scheduled_date: datetime
    scheduled_time: Optional[str] = None
    notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: UUID
    referral_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None
    provider_id: UUID
    slot_id: Optional[UUID] = None
    recommendation_id: Optional[UUID] = None
    status: str
    scheduled_date: datetime
    scheduled_time: Optional[str] = None
    notes: Optional[str] = None
    is_synthetic: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AppointmentUpdateRequest(BaseModel):
    status: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    scheduled_time: Optional[str] = None
    notes: Optional[str] = None


class SlotResponse(BaseModel):
    id: UUID
    provider_id: UUID
    slot_date: datetime
    slot_time: Optional[str] = None
    duration_mins: int = 30
    is_available: bool = True
    is_synthetic: bool = True

    model_config = {"from_attributes": True}


# ── Patient Schemas ──────────────────────────────────────────

class PatientCreateRequest(BaseModel):
    external_id: Optional[str] = None
    first_name: str
    last_name: str
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    insurance: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PatientResponse(BaseModel):
    id: UUID
    external_id: Optional[str] = None
    first_name: str
    last_name: str
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    insurance: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── FHIR Schemas ─────────────────────────────────────────────

class FHIRServiceRequestResponse(BaseModel):
    """FHIR R4-compatible prototype representation."""
    resourceType: str = "ServiceRequest"
    id: str
    status: str
    intent: str = "order"
    category: Optional[list[dict]] = None
    priority: Optional[str] = None
    code: Optional[dict] = None
    subject: Optional[dict] = None
    requester: Optional[dict] = None
    performer: Optional[list[dict]] = None
    reasonCode: Optional[list[dict]] = None
    note: Optional[list[dict]] = None
    meta: Optional[dict] = None
    _carepath_disclaimer: str = "FHIR R4-compatible prototype representation. Not certified for clinical use."


# ── Monitoring Schemas ───────────────────────────────────────

class ReferralMonitoringResponse(BaseModel):
    referral_id: UUID
    status: str
    elapsed_days: Optional[float] = None
    expected_wait_days: Optional[float] = None
    appointment_status: Optional[str] = None
    delay_risk: str = "unknown"  # low, medium, high, unknown
    capacity_change: Optional[str] = None
    rerouting_recommended: bool = False
    last_evaluated_at: Optional[datetime] = None


class RerouteEvaluationResponse(BaseModel):
    referral_id: UUID
    current_pathway: Optional[dict] = None
    alternative_pathways: list[dict] = []
    rerouting_recommended: bool = False
    reason: str = ""
    evaluated_at: datetime


# ── Model/System Schemas ─────────────────────────────────────

class ModelInfoResponse(BaseModel):
    model_name: str
    version: str
    is_production: bool = False
    metrics: Optional[dict] = None
    feature_schema: Optional[list[str]] = None
    training_data_source: Optional[str] = None
    n_train: Optional[int] = None
    n_test: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ModelEvaluationRequest(BaseModel):
    dataset_reference: str = Field(description="Path or identifier for the evaluation dataset")
    sample_size: Optional[int] = None


class ModelEvaluationResponse(BaseModel):
    model_name: str
    model_version: str
    dataset_reference: str
    sample_count: int
    mae: float
    rmse: float
    r2: float
    mape: Optional[float] = None
    breakdown_by_specialty: Optional[dict] = None
    evaluation_timestamp: datetime


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
    environment: str
    database: str = "unknown"
    model_available: bool = False
    model_version: Optional[str] = None
    timestamp: datetime


class SystemInfoResponse(BaseModel):
    app_name: str
    version: str
    environment: str
    api_prefix: str
    database_connected: bool
    model_loaded: bool
    model_version: Optional[str] = None
    model_metrics: Optional[dict] = None
    specialties_count: Optional[int] = None
    storage_provider: str
    timestamp: datetime


# ── Data Import Schemas ──────────────────────────────────────

class DataImportRequest(BaseModel):
    source: str = Field(default="master", description="Dataset source: 'master' or path")
    table: str = Field(description="Target table: 'providers', 'appointments', etc.")
    limit: Optional[int] = Field(default=None, description="Max records to import")
    validate_only: bool = Field(default=False, description="Only validate, don't import")


class DataImportResponse(BaseModel):
    table: str
    records_processed: int
    records_imported: int
    records_rejected: int
    rejected_reasons: list[dict] = []
    validation_only: bool = False
    duration_seconds: float
    timestamp: datetime

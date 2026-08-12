"""
CarePath AI — Database Models
Normalized PostgreSQL schema for the CarePath AI platform.

Design principles:
  - UUIDs for all primary keys
  - NPI preserved as external healthcare identifier
  - created_at/updated_at timestamps on all tables
  - Proper foreign keys, indexes, and constraints
  - Internal domain models separate from FHIR representation
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.types import Uuid as UUID
JSONB = JSON
from sqlalchemy.orm import relationship

from app.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return uuid.uuid4()


# ── Enums ────────────────────────────────────────────────────

class ReferralStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REROUTING = "rerouting"


class UrgencyLevel(str, enum.Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENT = "emergent"
    STAT = "stat"


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class EventType(str, enum.Enum):
    REFERRAL_CREATED = "referral_created"
    REFERRAL_ANALYZED = "referral_analyzed"
    PREDICTION_GENERATED = "prediction_generated"
    RECOMMENDATION_GENERATED = "recommendation_generated"
    RECOMMENDATION_VIEWED = "recommendation_viewed"
    APPOINTMENT_CREATED = "appointment_created"
    APPOINTMENT_CHANGED = "appointment_changed"
    REROUTING_EVALUATED = "rerouting_evaluated"
    MODEL_LOADED = "model_loaded"
    OPTIMIZATION_EXECUTED = "optimization_executed"
    DATA_IMPORTED = "data_imported"


# ── User Account ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), default="patient", nullable=False)  # patient, doctor, admin, care_coordinator
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ── Specialty Reference ──────────────────────────────────────

class Specialty(Base):
    __tablename__ = "specialties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name = Column(String(200), nullable=False, unique=True, index=True)
    category = Column(String(100))  # surgical, primary_care, mental_health, etc.
    base_wait_days = Column(Float)
    service_rate_mu = Column(Float)
    capacity = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=utcnow)


# ── Organization ─────────────────────────────────────────────

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    pac_id = Column(String(50), unique=True, index=True)
    name = Column(String(500))
    member_count = Column(Integer)
    city = Column(String(200))
    state = Column(String(10))
    zip_code = Column(String(10))
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    providers = relationship("Provider", back_populates="organization")


# ── Provider ─────────────────────────────────────────────────

class Provider(Base):
    __tablename__ = "providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    npi = Column(String(20), nullable=False, index=True)  # NOT unique — same NPI at multiple locations
    pac_id = Column(String(50))
    enrl_id = Column(String(50))
    last_name = Column(String(200), nullable=False)
    first_name = Column(String(200), nullable=False)
    gender = Column(String(20))
    credential = Column(String(50))
    specialty = Column(String(200), nullable=False, index=True)
    original_specialty = Column(String(200))
    secondary_specialties = Column(Text)
    offers_telehealth = Column(Boolean, default=False)
    city = Column(String(200))
    state = Column(String(10), index=True)
    zip_code = Column(String(10), index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    accepts_medicare_individual = Column(String(10))
    accepts_medicare_group = Column(String(10))
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    data_source = Column(String(50), default="CMS_DAC_REAL")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    organization = relationship("Organization", back_populates="providers")
    capacity_records = relationship("ProviderCapacity", back_populates="provider")
    wait_history = relationship("ProviderWaitHistory", back_populates="provider")

    __table_args__ = (
        Index("ix_providers_specialty_state", "specialty", "state"),
        Index("ix_providers_npi_specialty", "npi", "specialty"),
        Index("ix_providers_geo", "latitude", "longitude"),
    )


# ── Provider Capacity ────────────────────────────────────────

class ProviderCapacity(Base):
    __tablename__ = "provider_capacity"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False, index=True)
    current_queue_length = Column(Integer, default=0)
    active_backlog = Column(Integer, default=0)
    appointment_capacity = Column(Integer)
    server_count = Column(Integer)
    service_rate_mu = Column(Float)
    utilization_rho = Column(Float)
    arrival_rate_lambda = Column(Float)
    is_synthetic = Column(Boolean, default=True)
    snapshot_at = Column(DateTime(timezone=True), default=utcnow)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    provider = relationship("Provider", back_populates="capacity_records")


# ── Provider Wait History ────────────────────────────────────

class ProviderWaitHistory(Base):
    __tablename__ = "provider_wait_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False, index=True)
    avg_wait_days = Column(Float)
    median_wait_days = Column(Float)
    p90_wait_days = Column(Float)
    sample_count = Column(Integer)
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))
    is_synthetic = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    provider = relationship("Provider", back_populates="wait_history")


# ── Patient ──────────────────────────────────────────────────

class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    external_id = Column(String(50), unique=True, index=True)  # ABHA-compatible
    first_name = Column(String(200))
    last_name = Column(String(200))
    date_of_birth = Column(DateTime)
    gender = Column(String(20))
    insurance = Column(String(200))
    city = Column(String(200))
    state = Column(String(10))
    zip_code = Column(String(10))
    latitude = Column(Float)
    longitude = Column(Float)
    data_source = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    referrals = relationship("Referral", back_populates="patient")


# ── Referral ─────────────────────────────────────────────────

class Referral(Base):
    __tablename__ = "referrals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True)
    referring_provider_npi = Column(String(20))
    clinical_text = Column(Text)
    symptoms = Column(JSONB)  # list of symptom strings
    conditions = Column(JSONB)  # list of condition strings
    target_specialty = Column(String(200))
    target_subspecialty = Column(String(200))
    urgency = Column(Enum(UrgencyLevel), default=UrgencyLevel.ROUTINE)
    status = Column(Enum(ReferralStatus), default=ReferralStatus.DRAFT, index=True)
    # Analysis results (populated after clinical NLP)
    extracted_entities = Column(JSONB)
    inferred_specialty = Column(String(200))
    inferred_urgency = Column(Enum(UrgencyLevel))
    missing_information = Column(JSONB)
    analysis_model = Column(String(100))
    analysis_model_version = Column(String(50))
    # Constraints
    preferred_location_lat = Column(Float)
    preferred_location_lng = Column(Float)
    max_distance_km = Column(Float, default=50.0)
    insurance_network = Column(String(200))
    patient_preferences = Column(JSONB)
    # Document
    document_path = Column(String(500))
    document_type = Column(String(20))  # pdf, txt, docx, image
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    patient = relationship("Patient", back_populates="referrals")
    events = relationship("ReferralEvent", back_populates="referral")
    recommendations = relationship("Recommendation", back_populates="referral")

    __table_args__ = (
        Index("ix_referrals_status_created", "status", "created_at"),
    )


# ── Referral Events (Event Sourcing) ────────────────────────

class ReferralEvent(Base):
    __tablename__ = "referral_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    referral_id = Column(UUID(as_uuid=True), ForeignKey("referrals.id"), nullable=False, index=True)
    event_type = Column(Enum(EventType), nullable=False)
    event_data = Column(JSONB)
    actor_id = Column(String(100))
    actor_role = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=utcnow)

    referral = relationship("Referral", back_populates="events")


# ── Predictions ──────────────────────────────────────────────

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=True)
    referral_id = Column(UUID(as_uuid=True), ForeignKey("referrals.id"), nullable=True)
    model_name = Column(String(100), default="carepath_wait_time")
    model_version = Column(String(50))
    predicted_wait_days = Column(Float, nullable=False)
    features_used = Column(JSONB)
    shap_values = Column(JSONB)
    inference_time_ms = Column(Float)
    created_at = Column(DateTime(timezone=True), default=utcnow)


# ── Recommendations ──────────────────────────────────────────

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    referral_id = Column(UUID(as_uuid=True), ForeignKey("referrals.id"), nullable=False, index=True)
    optimization_method = Column(String(50), default="OR-Tools")
    optimization_config = Column(JSONB)
    optimization_time_ms = Column(Float)
    top_k = Column(Integer, default=3)
    explanation_text = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    referral = relationship("Referral", back_populates="recommendations")
    candidates = relationship("RecommendationCandidate", back_populates="recommendation")


class RecommendationCandidate(Base):
    __tablename__ = "recommendation_candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("recommendations.id"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False)
    rank = Column(Integer, nullable=False)
    predicted_wait_days = Column(Float)
    distance_km = Column(Float)
    capacity_score = Column(Float)
    objective_score = Column(Float)
    constraints_satisfied = Column(JSONB)
    reasons = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    recommendation = relationship("Recommendation", back_populates="candidates")


# ── Appointments ─────────────────────────────────────────────

class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False, index=True)
    slot_date = Column(DateTime(timezone=True), nullable=False)
    slot_time = Column(String(20))
    duration_mins = Column(Integer, default=30)
    is_available = Column(Boolean, default=True, index=True)
    is_synthetic = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("ix_slots_provider_date", "provider_id", "slot_date"),
    )


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    referral_id = Column(UUID(as_uuid=True), ForeignKey("referrals.id"), nullable=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False)
    slot_id = Column(UUID(as_uuid=True), ForeignKey("appointment_slots.id"), nullable=True)
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("recommendations.id"), nullable=True)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED, index=True)
    scheduled_date = Column(DateTime(timezone=True))
    scheduled_time = Column(String(20))
    notes = Column(Text)
    is_synthetic = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_appointments_provider_status", "provider_id", "status"),
    )


# ── Model Versions ───────────────────────────────────────────

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    model_name = Column(String(100), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    file_path = Column(String(500))
    metrics = Column(JSONB)
    feature_schema = Column(JSONB)
    is_production = Column(Boolean, default=False)
    training_data_source = Column(String(200))
    n_train = Column(Integer)
    n_test = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        UniqueConstraint("model_name", "version", name="uq_model_version"),
    )


# ── Audit Logs ───────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    event_type = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100))
    resource_id = Column(String(100))
    actor_id = Column(String(100))
    actor_role = Column(String(50))
    action = Column(String(200))
    details = Column(JSONB)
    request_id = Column(String(50))
    ip_address = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)

    __table_args__ = (
        Index("ix_audit_resource", "resource_type", "resource_id"),
    )

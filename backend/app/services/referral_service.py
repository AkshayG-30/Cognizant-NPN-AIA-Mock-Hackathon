"""
CarePath AI — Referral Service
Referral lifecycle management and clinical analysis orchestration.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.db.models import Referral, ReferralEvent, ReferralStatus, UrgencyLevel, EventType
from app.schemas.referral import (
    ReferralCreateRequest,
    ReferralUpdateRequest,
    ReferralResponse,
    ReferralAnalysisResponse,
)

logger = get_logger("services.referral")


class ReferralService:
    """Manages referral lifecycle — create, update, analyze."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, request: ReferralCreateRequest, actor_id: str = "system") -> Referral:
        """Create a new referral."""
        referral = Referral(
            id=uuid.uuid4(),
            patient_id=request.patient_id,
            clinical_text=request.clinical_text,
            symptoms=request.symptoms,
            conditions=request.conditions,
            target_specialty=request.target_specialty,
            urgency=UrgencyLevel(request.urgency),
            status=ReferralStatus.SUBMITTED,
            referring_provider_npi=request.referring_provider_npi,
            preferred_location_lat=request.preferred_location_lat,
            preferred_location_lng=request.preferred_location_lng,
            max_distance_km=request.max_distance_km,
            insurance_network=request.insurance_network,
            patient_preferences=request.patient_preferences,
        )
        self.db.add(referral)

        # Audit event
        event = ReferralEvent(
            referral_id=referral.id,
            event_type=EventType.REFERRAL_CREATED,
            event_data={"urgency": request.urgency, "specialty": request.target_specialty},
            actor_id=actor_id,
        )
        self.db.add(event)

        logger.info("referral_created", referral_id=str(referral.id), specialty=request.target_specialty)
        await self.db.flush()
        return referral

    async def get_by_id(self, referral_id: uuid.UUID) -> Referral:
        result = await self.db.execute(
            select(Referral).where(Referral.id == referral_id)
        )
        referral = result.scalar_one_or_none()
        if not referral:
            raise NotFoundError("Referral", str(referral_id))
        return referral

    async def list_referrals(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Referral], int]:
        query = select(Referral)
        if status:
            query = query.where(Referral.status == ReferralStatus(status))
        query = query.order_by(Referral.created_at.desc())

        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        offset = (page - 1) * page_size
        result = await self.db.execute(query.offset(offset).limit(page_size))
        return list(result.scalars().all()), total

    async def update(self, referral_id: uuid.UUID, request: ReferralUpdateRequest) -> Referral:
        referral = await self.get_by_id(referral_id)

        if request.clinical_text is not None:
            referral.clinical_text = request.clinical_text
        if request.symptoms is not None:
            referral.symptoms = request.symptoms
        if request.conditions is not None:
            referral.conditions = request.conditions
        if request.target_specialty is not None:
            referral.target_specialty = request.target_specialty
        if request.urgency is not None:
            referral.urgency = UrgencyLevel(request.urgency)
        if request.status is not None:
            referral.status = ReferralStatus(request.status)
        if request.max_distance_km is not None:
            referral.max_distance_km = request.max_distance_km
        if request.insurance_network is not None:
            referral.insurance_network = request.insurance_network

        referral.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return referral

    async def analyze(self, referral_id: uuid.UUID) -> ReferralAnalysisResponse:
        """
        Run the clinical analysis pipeline on a referral.
        Currently uses rule-based extraction.
        LLM-based extraction can be plugged in when llm_provider != 'none'.
        """
        referral = await self.get_by_id(referral_id)
        referral.status = ReferralStatus.ANALYZING

        # ── Rule-based clinical extraction ────────────────────
        extracted_specialty = referral.target_specialty
        extracted_urgency = referral.urgency
        entities = []
        missing = []
        extraction_confidence = "EXTRACTED"

        # If clinical text is present, do basic extraction
        if referral.clinical_text:
            text_upper = referral.clinical_text.upper()

            # Urgency inference from keywords
            if any(kw in text_upper for kw in ["EMERGENT", "EMERGENCY", "STAT", "IMMEDIATE"]):
                extracted_urgency = UrgencyLevel.EMERGENT
                extraction_confidence = "INFERRED"
            elif any(kw in text_upper for kw in ["URGENT", "ASAP", "SOON"]):
                extracted_urgency = UrgencyLevel.URGENT
                extraction_confidence = "INFERRED"

            # Extract conditions from symptoms
            if referral.symptoms:
                for symptom in referral.symptoms:
                    entities.append({"type": "symptom", "value": symptom, "source": "EXTRACTED"})

            if referral.conditions:
                for condition in referral.conditions:
                    entities.append({"type": "condition", "value": condition, "source": "EXTRACTED"})
        else:
            missing.append("clinical_text")

        if not extracted_specialty:
            missing.append("target_specialty")
            extraction_confidence = "MISSING"

        if not referral.symptoms and not referral.conditions:
            missing.append("symptoms_or_conditions")

        # Update referral
        referral.inferred_specialty = extracted_specialty
        referral.inferred_urgency = extracted_urgency
        referral.extracted_entities = entities
        referral.missing_information = missing
        referral.analysis_model = "rule_based_v1"
        referral.analysis_model_version = "1.0.0"
        referral.status = ReferralStatus.ANALYZED
        referral.updated_at = datetime.now(timezone.utc)

        # Audit event
        event = ReferralEvent(
            referral_id=referral.id,
            event_type=EventType.REFERRAL_ANALYZED,
            event_data={
                "inferred_specialty": extracted_specialty,
                "inferred_urgency": extracted_urgency.value if extracted_urgency else None,
                "entity_count": len(entities),
                "missing_count": len(missing),
            },
        )
        self.db.add(event)
        await self.db.flush()

        logger.info(
            "referral_analyzed",
            referral_id=str(referral_id),
            specialty=extracted_specialty,
            urgency=extracted_urgency.value if extracted_urgency else None,
            entities=len(entities),
        )

        return ReferralAnalysisResponse(
            referral_id=referral_id,
            specialty=extracted_specialty,
            urgency=extracted_urgency.value if extracted_urgency else None,
            entities=entities,
            missing_information=missing,
            extraction_confidence=extraction_confidence,
            model="rule_based_v1",
            model_version="1.0.0",
        )

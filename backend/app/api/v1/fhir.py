"""
CarePath AI — FHIR API Routes
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.fhir.mapper import FHIRMapper
from app.services.referral_service import ReferralService

router = APIRouter(prefix="/fhir", tags=["FHIR"])


@router.post(
    "/referrals/{referral_id}/service-request",
    summary="Generate FHIR ServiceRequest from referral",
)
async def create_service_request(referral_id: UUID, db: AsyncSession = Depends(get_db)):
    """Convert internal referral to FHIR R4-compatible ServiceRequest."""
    svc = ReferralService(db)
    referral = await svc.get_by_id(referral_id)
    return FHIRMapper.referral_to_service_request(referral)


@router.get(
    "/referrals/{referral_id}/service-request",
    summary="Get FHIR ServiceRequest for referral",
)
async def get_service_request(referral_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get the FHIR R4-compatible ServiceRequest for a referral."""
    svc = ReferralService(db)
    referral = await svc.get_by_id(referral_id)
    resource = FHIRMapper.referral_to_service_request(referral)

    # Validate
    errors = FHIRMapper.validate_service_request(resource)
    if errors:
        resource["_validation_errors"] = errors

    return resource

"""
CarePath AI — Monitoring API Routes
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.database import get_db
from app.db.models import Referral, Appointment, ReferralStatus, AppointmentStatus
from app.schemas.common import ReferralMonitoringResponse, RerouteEvaluationResponse

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/referrals/{referral_id}", summary="Monitor referral status")
async def monitor_referral(referral_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Referral).where(Referral.id == referral_id))
    referral = result.scalar_one_or_none()
    if not referral:
        raise NotFoundError("Referral", str(referral_id))

    now = datetime.now(timezone.utc)
    elapsed = None
    if referral.created_at:
        elapsed = (now - referral.created_at).total_seconds() / 86400  # days

    # Check appointment
    appt_result = await db.execute(
        select(Appointment).where(Appointment.referral_id == referral_id).limit(1)
    )
    appt = appt_result.scalar_one_or_none()

    delay_risk = "unknown"
    if elapsed and elapsed > 14:
        delay_risk = "high"
    elif elapsed and elapsed > 7:
        delay_risk = "medium"
    elif elapsed is not None:
        delay_risk = "low"

    return ReferralMonitoringResponse(
        referral_id=referral_id,
        status=referral.status.value if hasattr(referral.status, 'value') else str(referral.status),
        elapsed_days=round(elapsed, 1) if elapsed else None,
        appointment_status=appt.status.value if appt and hasattr(appt.status, 'value') else None,
        delay_risk=delay_risk,
        rerouting_recommended=delay_risk == "high",
        last_evaluated_at=now,
    )


@router.post("/referrals/{referral_id}/evaluate", summary="Evaluate referral for rerouting")
async def evaluate_rerouting(referral_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Evaluate whether a referral should be rerouted.
    Does NOT automatically change appointments.
    """
    result = await db.execute(select(Referral).where(Referral.id == referral_id))
    referral = result.scalar_one_or_none()
    if not referral:
        raise NotFoundError("Referral", str(referral_id))

    now = datetime.now(timezone.utc)
    elapsed = (now - referral.created_at).total_seconds() / 86400 if referral.created_at else 0

    rerouting_recommended = elapsed > 14

    return RerouteEvaluationResponse(
        referral_id=referral_id,
        current_pathway={"status": referral.status.value if hasattr(referral.status, 'value') else str(referral.status), "elapsed_days": round(elapsed, 1)},
        rerouting_recommended=rerouting_recommended,
        reason="Referral has exceeded 14-day threshold" if rerouting_recommended else "Within acceptable timeframe",
        evaluated_at=now,
    )

"""
CarePath AI — Notifications API
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter(prefix="/notifications", tags=["Notifications"])

NOTIFICATIONS_DB: list[dict] = [
    {
        "id": "notif_01",
        "title": "Clinical Recommendation Ready",
        "body": "CarePath AI has analyzed your medical referral and matched you with top-ranked specialist Dr. Sarah Williams, MD.",
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "notif_02",
        "title": "Welcome to CarePath AI",
        "body": "Your patient account is active. Upload your clinical notes and test reports to optimize your specialty care journey.",
        "read": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
]


@router.get("")
async def get_notifications():
    return NOTIFICATIONS_DB


@router.post("/{notif_id}/read")
async def mark_read(notif_id: str):
    for n in NOTIFICATIONS_DB:
        if n["id"] == notif_id:
            n["read"] = True
            break
    return {"success": True}

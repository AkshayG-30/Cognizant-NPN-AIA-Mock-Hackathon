"""
CarePath AI — Doctor Specific Routes
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Patient

router = APIRouter(prefix="/doctor", tags=["Doctor"])


@router.get("/patients")
async def list_doctor_patients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Patient).limit(20))
    patients = list(result.scalars().all())

    if not patients:
        return [
            {"id": "pat_01", "name": "Jane Doe", "email": "patient@carepath.ai"},
            {"id": "pat_02", "name": "Robert Miller", "email": "robert.m@example.com"},
            {"id": "pat_03", "name": "Emily Zhang", "email": "emily.z@example.com"},
            {"id": "pat_04", "name": "Marcus Vance", "email": "marcus.v@example.com"},
        ]

    return [
        {
            "id": str(p.id),
            "name": f"{p.first_name} {p.last_name}",
            "email": f"{p.first_name.lower()}.{p.last_name.lower()}@example.com",
        }
        for p in patients
    ]

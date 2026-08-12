"""
CarePath AI — Specialties API Routes
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.specialties import CANONICAL_SPECIALTIES
from app.db.database import get_db
from app.db.models import Provider

router = APIRouter(prefix="/specialties", tags=["Specialties"])


@router.get("")
async def list_specialties(db: AsyncSession = Depends(get_db)):
    # Return canonical specialties
    return sorted(list(CANONICAL_SPECIALTIES))

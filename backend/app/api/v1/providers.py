"""
CarePath AI — Provider API Routes
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.database import get_db
from app.schemas.provider import (
    ProviderCapacityResponse,
    ProviderListResponse,
    ProviderResponse,
    ProviderSearchRequest,
    ProviderWaitHistoryResponse,
)
from app.services.provider_service import ProviderService

router = APIRouter(prefix="/providers", tags=["Providers"])


@router.get("", response_model=ProviderListResponse, summary="List providers")
async def list_providers(
    specialty: str | None = None,
    state: str | None = None,
    city: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    svc = ProviderService(db)
    providers, total = await svc.search(
        specialty=specialty, state=state, city=city,
        page=page, page_size=page_size,
    )
    return ProviderListResponse(
        providers=[ProviderResponse.model_validate(p) for p in providers],
        total=total, page=page, page_size=page_size,
    )


@router.get("/{provider_id}", response_model=ProviderResponse, summary="Get provider by ID")
async def get_provider(provider_id: UUID, db: AsyncSession = Depends(get_db)):
    svc = ProviderService(db)
    provider = await svc.get_by_id(provider_id)
    if not provider:
        raise NotFoundError("Provider", str(provider_id))
    return ProviderResponse.model_validate(provider)


@router.get("/{provider_id}/capacity", response_model=ProviderCapacityResponse, summary="Get provider capacity")
async def get_capacity(provider_id: UUID, db: AsyncSession = Depends(get_db)):
    svc = ProviderService(db)
    cap = await svc.get_capacity(provider_id)
    if not cap:
        raise NotFoundError("ProviderCapacity", str(provider_id))
    return ProviderCapacityResponse.model_validate(cap)


@router.get("/{provider_id}/wait-history", summary="Get provider wait history")
async def get_wait_history(provider_id: UUID, db: AsyncSession = Depends(get_db)):
    svc = ProviderService(db)
    history = await svc.get_wait_history(provider_id)
    return [ProviderWaitHistoryResponse.model_validate(h) for h in history]


@router.post("/search", response_model=ProviderListResponse, summary="Search providers with filters")
async def search_providers(
    request: ProviderSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = ProviderService(db)
    providers, total = await svc.search(
        specialty=request.specialty,
        state=request.state,
        city=request.city,
        zip_code=request.zip_code,
        offers_telehealth=request.offers_telehealth,
        accepts_medicare=request.accepts_medicare,
        latitude=request.latitude,
        longitude=request.longitude,
        max_distance_km=request.max_distance_km,
        page=request.page,
        page_size=request.page_size,
    )
    return ProviderListResponse(
        providers=[ProviderResponse.model_validate(p) for p in providers],
        total=total, page=request.page, page_size=request.page_size,
    )

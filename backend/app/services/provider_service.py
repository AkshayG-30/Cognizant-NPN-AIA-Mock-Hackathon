"""
CarePath AI — Provider Service
Business logic for provider search, filtering, and capacity management.
"""
from __future__ import annotations

import math
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.specialties import normalize_specialty
from app.db.models import Provider, ProviderCapacity, ProviderWaitHistory

logger = get_logger("services.provider")


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in km."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class ProviderService:
    """Provider search, filtering, and capacity operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, provider_id: UUID) -> Optional[Provider]:
        result = await self.db.execute(
            select(Provider).where(Provider.id == provider_id)
        )
        return result.scalar_one_or_none()

    async def get_by_npi(self, npi: str) -> list[Provider]:
        result = await self.db.execute(
            select(Provider).where(Provider.npi == npi)
        )
        return list(result.scalars().all())

    async def search(
        self,
        specialty: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        zip_code: Optional[str] = None,
        offers_telehealth: Optional[bool] = None,
        accepts_medicare: Optional[bool] = None,
        is_active: bool = True,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        max_distance_km: float = 50.0,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Provider], int]:
        """Search providers with filtering. Returns (providers, total_count)."""
        conditions = []

        if is_active:
            conditions.append(Provider.is_active == True)  # noqa: E712

        if specialty:
            norm_spec = normalize_specialty(specialty)
            conditions.append(
                func.upper(Provider.specialty) == norm_spec
            )

        if state:
            conditions.append(
                func.upper(Provider.state) == state.strip().upper()
            )

        if city:
            conditions.append(
                func.upper(Provider.city).contains(city.strip().upper())
            )

        if zip_code:
            conditions.append(Provider.zip_code == zip_code.strip())

        if offers_telehealth is not None:
            conditions.append(Provider.offers_telehealth == offers_telehealth)

        if accepts_medicare:
            conditions.append(Provider.accepts_medicare_individual == "Y")

        # Spatial bounding box pre-filter if coordinates are provided
        if latitude is not None and longitude is not None and max_distance_km:
            lat_delta = (max_distance_km * 1.2) / 111.0
            lng_delta = (max_distance_km * 1.2) / max(1.0, 111.0 * math.cos(math.radians(latitude)))
            conditions.append(Provider.latitude.is_not(None))
            conditions.append(Provider.longitude.is_not(None))
            conditions.append(Provider.latitude.between(latitude - lat_delta, latitude + lat_delta))
            conditions.append(Provider.longitude.between(longitude - lng_delta, longitude + lng_delta))

        # Build query
        query = select(Provider).where(and_(*conditions)) if conditions else select(Provider)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        providers = list(result.scalars().all())

        # Post-filter and sort by exact distance if coordinates provided
        if latitude is not None and longitude is not None:
            filtered = []
            for p in providers:
                if p.latitude is not None and p.longitude is not None:
                    d = haversine_distance(latitude, longitude, p.latitude, p.longitude)
                    if d <= max_distance_km:
                        filtered.append(p)
            providers = filtered

        logger.info(
            "provider_search",
            specialty=specialty,
            state=state,
            results=len(providers),
            total=total,
        )

        return providers, total

    async def get_candidates_for_optimization(
        self,
        specialty: str,
        state: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        max_distance_km: float = 100.0,
        limit: int = 50,
    ) -> list[dict]:
        """
        Get provider candidates with capacity data for the optimizer.
        Uses spatial bounding box and single-query capacity joining.
        Falls back to regional/nationwide search if radius is too restrictive.
        """
        norm_spec = normalize_specialty(specialty)
        
        # Build base query joining Provider and latest ProviderCapacity
        conditions = [
            Provider.is_active == True,  # noqa: E712
            func.upper(Provider.specialty) == norm_spec,
        ]

        if state:
            conditions.append(func.upper(Provider.state) == state.strip().upper())

        spatial_conditions = list(conditions)
        has_spatial = latitude is not None and longitude is not None

        if has_spatial:
            lat_delta = (max_distance_km * 1.5) / 111.0
            lng_delta = (max_distance_km * 1.5) / max(1.0, 111.0 * math.cos(math.radians(latitude)))
            spatial_conditions.extend([
                Provider.latitude.is_not(None),
                Provider.longitude.is_not(None),
                Provider.latitude.between(latitude - lat_delta, latitude + lat_delta),
                Provider.longitude.between(longitude - lng_delta, longitude + lng_delta),
            ])

        # Query 1: Try spatial search with bounding box
        query = (
            select(Provider, ProviderCapacity)
            .outerjoin(ProviderCapacity, Provider.id == ProviderCapacity.provider_id)
            .where(and_(*spatial_conditions))
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        # If spatial search yielded < 3 candidates, fallback to broader search
        if has_spatial and len(rows) < 3:
            logger.info("expanding_candidate_search", specialty=norm_spec, prev_count=len(rows))
            broader_query = (
                select(Provider, ProviderCapacity)
                .outerjoin(ProviderCapacity, Provider.id == ProviderCapacity.provider_id)
                .where(and_(*conditions))
                .limit(limit)
            )
            result = await self.db.execute(broader_query)
            rows = result.all()

        candidates = []
        for p, capacity in rows:
            distance = None
            if latitude and longitude and p.latitude and p.longitude:
                distance = round(haversine_distance(latitude, longitude, p.latitude, p.longitude), 2)

            candidates.append({
                "provider_id": p.id,
                "npi": p.npi,
                "name": f"{p.first_name or ''} {p.last_name or ''}".strip() or "Specialist Provider",
                "specialty": p.specialty,
                "city": p.city,
                "state": p.state,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "offers_telehealth": bool(p.offers_telehealth),
                "distance_km": distance if distance is not None else 15.0,
                "org_size": 200,
                # Capacity data (from table or calibrated defaults)
                "current_queue_length": capacity.current_queue_length if capacity else 2,
                "active_backlog": capacity.active_backlog if capacity else 2,
                "server_count": capacity.server_count if capacity else 15,
                "service_rate_mu": capacity.service_rate_mu if capacity else 3.5,
                "utilization_rho": capacity.utilization_rho if capacity else 0.65,
                "arrival_rate_lambda": capacity.arrival_rate_lambda if capacity else 22.0,
                "is_synthetic_capacity": capacity.is_synthetic if capacity else True,
            })

        logger.info(
            "candidates_generated",
            specialty=norm_spec,
            eligible=len(candidates),
        )

        return candidates

    async def get_capacity(self, provider_id: UUID) -> Optional[ProviderCapacity]:
        result = await self.db.execute(
            select(ProviderCapacity)
            .where(ProviderCapacity.provider_id == provider_id)
            .order_by(ProviderCapacity.snapshot_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_wait_history(self, provider_id: UUID) -> list[ProviderWaitHistory]:
        result = await self.db.execute(
            select(ProviderWaitHistory)
            .where(ProviderWaitHistory.provider_id == provider_id)
            .order_by(ProviderWaitHistory.period_end.desc())
            .limit(12)
        )
        return list(result.scalars().all())

    async def count_by_specialty(self) -> dict[str, int]:
        result = await self.db.execute(
            select(Provider.specialty, func.count())
            .where(Provider.is_active == True)  # noqa: E712
            .group_by(Provider.specialty)
            .order_by(func.count().desc())
        )
        return {row[0]: row[1] for row in result.all()}

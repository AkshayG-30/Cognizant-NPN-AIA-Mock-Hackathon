"""
CarePath AI — Health & System API Routes
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.database import get_db
from app.ml.model_registry import get_model_registry
from app.schemas.common import HealthResponse, SystemInfoResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Health check", tags=["System"])
async def health_check(db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    registry = get_model_registry()

    db_status = "unknown"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version=settings.app_version,
        environment=settings.app_env,
        database=db_status,
        model_available=registry.is_loaded,
        model_version=registry.get_version() if registry.is_loaded else None,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/system/info", response_model=SystemInfoResponse, summary="System information", tags=["System"])
async def system_info(db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    registry = get_model_registry()

    db_connected = False
    try:
        await db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        pass

    return SystemInfoResponse(
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        api_prefix=settings.api_prefix,
        database_connected=db_connected,
        model_loaded=registry.is_loaded,
        model_version=registry.get_version() if registry.is_loaded else None,
        model_metrics=registry.get_metadata() if registry.is_loaded else None,
        storage_provider=settings.storage_provider,
        timestamp=datetime.now(timezone.utc),
    )

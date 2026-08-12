"""
CarePath AI — Data Import & Model Management API Routes
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import UserRole, require_role
from app.db.database import get_db
from app.ml.model_registry import get_model_registry
from app.schemas.common import DataImportRequest, DataImportResponse, ModelInfoResponse
from app.services.data_ingestion_service import DataIngestionService

router = APIRouter(tags=["Data & Models"])


@router.post(
    "/data/import/master",
    response_model=DataImportResponse,
    summary="Import master dataset",
    description="Administrative endpoint to import the master provider dataset into PostgreSQL.",
)
async def import_master_dataset(
    request: DataImportRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = DataIngestionService(db)

    if request.table == "providers":
        result = await svc.import_providers(
            limit=request.limit,
            validate_only=request.validate_only,
        )
        return DataImportResponse(**result)

    return DataImportResponse(
        table=request.table,
        records_processed=0,
        records_imported=0,
        records_rejected=0,
        rejected_reasons=[{"reason": f"Table '{request.table}' import not yet implemented"}],
        duration_seconds=0,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/models", summary="List available models")
async def list_models():
    registry = get_model_registry()
    models = []

    if registry.is_loaded:
        metadata = registry.get_metadata("wait_time")
        models.append(ModelInfoResponse(
            model_name="carepath_wait_time",
            version=registry.get_version("wait_time"),
            is_production=True,
            metrics=metadata,
            feature_schema=registry.get_feature_columns("wait_time"),
            training_data_source=metadata.get("data_source"),
            n_train=metadata.get("n_train"),
            n_test=metadata.get("n_test"),
            created_at=datetime.fromisoformat(metadata["timestamp"]) if "timestamp" in metadata else None,
        ))

    return models


@router.get("/models/{model_name}", response_model=ModelInfoResponse, summary="Get model info")
async def get_model_info(model_name: str):
    registry = get_model_registry()

    if model_name in ("carepath_wait_time", "wait_time") and registry.is_loaded:
        metadata = registry.get_metadata("wait_time")
        return ModelInfoResponse(
            model_name="carepath_wait_time",
            version=registry.get_version("wait_time"),
            is_production=True,
            metrics=metadata,
            feature_schema=registry.get_feature_columns("wait_time"),
            training_data_source=metadata.get("data_source"),
            n_train=metadata.get("n_train"),
            n_test=metadata.get("n_test"),
            created_at=datetime.fromisoformat(metadata["timestamp"]) if "timestamp" in metadata else None,
        )

    from app.core.exceptions import NotFoundError
    raise NotFoundError("Model", model_name)

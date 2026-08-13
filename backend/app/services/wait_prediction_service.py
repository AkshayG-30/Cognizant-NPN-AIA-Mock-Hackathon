"""
CarePath AI — Wait Prediction Service
Orchestrates ML inference for wait-time predictions.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ModelNotAvailableError
from app.core.logging import get_logger
from app.db.models import Prediction
from app.ml.lightgbm_predictor import WaitTimePredictor
from app.ml.model_registry import get_model_registry
from app.schemas.prediction import WaitTimePredictionRequest, WaitTimePredictionResponse

logger = get_logger("services.wait_prediction")


class WaitPredictionService:
    """Service for wait-time predictions using the trained LightGBM model."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.registry = get_model_registry()
        self.predictor = WaitTimePredictor(self.registry)

    async def predict(
        self,
        request: WaitTimePredictionRequest,
        referral_id: uuid.UUID | None = None,
        provider_id: uuid.UUID | None = None,
    ) -> WaitTimePredictionResponse:
        """Generate a single wait-time prediction."""
        if not self.registry.is_loaded:
            raise ModelNotAvailableError("wait_time")

        result = self.predictor.predict(
            specialty=request.specialty,
            arrival_rate_lambda=request.arrival_rate_lambda,
            queue_length_Lq=request.queue_length_Lq,
            utilization_rho=request.utilization_rho,
            active_backlog=request.active_backlog,
            server_count=request.server_count,
            service_rate_mu=request.service_rate_mu,
            day_of_week=request.day_of_week,
            month=request.month,
            hour_of_day=request.hour_of_day,
            org_size=request.org_size,
            offers_telehealth=request.offers_telehealth,
        )

        prediction_id = uuid.uuid4()

        # Persist prediction record
        prediction = Prediction(
            id=prediction_id,
            provider_id=provider_id or request.provider_id,
            referral_id=referral_id,
            model_name="carepath_wait_time",
            model_version=result["model_version"],
            predicted_wait_days=result["predicted_wait_days"],
            features_used=result["features_used"],
            inference_time_ms=result["inference_time_ms"],
        )
        self.db.add(prediction)

        return WaitTimePredictionResponse(
            prediction_id=prediction_id,
            predicted_wait_days=result["predicted_wait_days"],
            model_version=result["model_version"],
            features_used=result["features_used"],
            inference_time_ms=result["inference_time_ms"],
            timestamp=datetime.now(timezone.utc),
        )

    async def predict_for_candidate(self, candidate: dict) -> float:
        """Quick prediction for a provider candidate during optimization."""
        if not self.registry.is_loaded:
            cand_wait = candidate.get("predicted_wait_days")
            if cand_wait is not None:
                return float(cand_wait)
            q_len = float(candidate.get("current_queue_length", 3))
            backlog = float(candidate.get("active_backlog", 2))
            return max(1.0, round(3.5 + (q_len * 0.8) + (backlog * 0.6), 1))

        now = datetime.now(timezone.utc)

        result = self.predictor.predict(
            specialty=candidate["specialty"],
            arrival_rate_lambda=candidate.get("arrival_rate_lambda", 20.0),
            queue_length_Lq=candidate.get("current_queue_length", 0),
            utilization_rho=candidate.get("utilization_rho", 0.5),
            active_backlog=candidate.get("active_backlog", 0),
            server_count=candidate.get("server_count", 15),
            service_rate_mu=candidate.get("service_rate_mu", 3.5),
            day_of_week=now.weekday(),
            month=now.month,
            hour_of_day=now.hour,
            org_size=candidate.get("org_size", 200) or 200,
            offers_telehealth=1 if candidate.get("offers_telehealth") else 0,
        )

        base_wait = float(result["predicted_wait_days"])
        q_len = float(candidate.get("current_queue_length", 0))
        backlog = float(candidate.get("active_backlog", 0))
        # Add dynamic queue offset to reflect individual provider backlog
        queue_offset = (q_len * 0.35) + (backlog * 0.25)
        
        return max(1.0, round(base_wait + queue_offset, 1))

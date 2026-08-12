"""
CarePath AI — LightGBM Wait-Time Predictor
Inference logic matching train_wait_time.py feature engineering exactly.

Feature order (20 features, from feature_columns.json):
  0  arrival_rate_lambda
  1  queue_length_Lq
  2  wait_in_queue_Wq_hours     ← DERIVED: Lq / max(lambda, 0.01)
  3  service_rate_mu
  4  utilization_rho
  5  active_backlog
  6  server_count
  7  day_of_week
  8  month
  9  quarter                    ← DERIVED: (month - 1) // 3 + 1
  10 hour_of_day
  11 is_monday                  ← DERIVED: 1 if dow == 0
  12 is_friday                  ← DERIVED: 1 if dow == 4
  13 is_weekend                 ← DERIVED: 1 if dow >= 5
  14 org_size
  15 offers_telehealth
  16 specialty_encoded          ← DERIVED: via specialty_encoder.json
  17 lambda_x_utilization       ← DERIVED: lambda * rho
  18 backlog_x_utilization      ← DERIVED: backlog * rho
  19 capacity_ratio             ← DERIVED: lambda / (server_count * mu + 0.001)
"""
from __future__ import annotations

import time
from typing import Optional

import numpy as np

from app.core.exceptions import ModelNotAvailableError, ValidationError
from app.core.logging import get_logger
from app.core.specialties import normalize_specialty
from app.ml.model_registry import ModelRegistry, get_model_registry

logger = get_logger("ml.predictor")


class WaitTimePredictor:
    """Performs wait-time predictions using the trained LightGBM model."""

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or get_model_registry()

    def predict(
        self,
        specialty: str,
        arrival_rate_lambda: float,
        queue_length_Lq: float,
        utilization_rho: float,
        active_backlog: int,
        server_count: int = 15,
        service_rate_mu: float = 3.5,
        day_of_week: int = 1,
        month: int = 6,
        hour_of_day: int = 10,
        org_size: int = 200,
        offers_telehealth: int = 0,
    ) -> dict:
        """
        Predict wait time for a single scenario.
        Returns dict with prediction + metadata.
        """
        model = self.registry.get_model("wait_time")
        if model is None:
            raise ModelNotAvailableError("wait_time")

        # Validate & normalize specialty
        spec_to_idx = self.registry.get_specialty_to_index("wait_time")
        specialty_upper = specialty.strip().upper()
        if specialty_upper not in spec_to_idx:
            specialty_upper = normalize_specialty(specialty)
        if specialty_upper not in spec_to_idx:
            raise ValidationError(
                f"Unknown specialty: '{specialty}'. Available: {sorted(spec_to_idx.keys())}",
                details={"available_specialties": sorted(spec_to_idx.keys())},
            )

        # Compute derived features (matching train_wait_time.py exactly)
        wq_hours = queue_length_Lq / max(arrival_rate_lambda, 0.01)
        quarter = (month - 1) // 3 + 1
        is_monday = 1 if day_of_week == 0 else 0
        is_friday = 1 if day_of_week == 4 else 0
        is_weekend = 1 if day_of_week >= 5 else 0
        lambda_x_utilization = arrival_rate_lambda * utilization_rho
        backlog_x_utilization = active_backlog * utilization_rho
        capacity_ratio = arrival_rate_lambda / (server_count * service_rate_mu + 0.001)

        # Build feature vector according to model's expected feature count
        num_expected = model.num_feature()

        if num_expected == 12:
            # V3 Point-in-time queue features
            dow = day_of_week
            dow_rad = 2 * np.pi * dow / 7.0
            month_rad = 2 * np.pi * month / 12.0
            features = np.array([[
                float(arrival_rate_lambda),                         # arrival_rate_7d
                float(queue_length_Lq),                             # queue_length_at_booking
                float(dow),                                         # sched_day_of_week
                float((month - 1) * 4 + min(dow + 1, 4)),           # sched_week_of_year
                float(np.sin(dow_rad)),                             # dow_sin
                float(np.cos(dow_rad)),                             # dow_cos
                15.0,                                               # sched_day_of_month (mid-month baseline)
                30.0,                                               # slot_minute
                float(hour_of_day),                                 # slot_hour
                float(np.cos(month_rad)),                           # month_cos
                float(np.sin(month_rad)),                           # month_sin
                float((month - 1) // 3 + 1)                         # sched_quarter
            ]], dtype=np.float32)
        else:
            # 20-feature legacy / v1 model schema
            features = np.array([[
                arrival_rate_lambda,        # 0
                queue_length_Lq,            # 1
                wq_hours,                   # 2
                service_rate_mu,            # 3
                utilization_rho,            # 4
                active_backlog,             # 5
                server_count,               # 6
                day_of_week,                # 7
                month,                      # 8
                quarter,                    # 9
                hour_of_day,                # 10
                is_monday,                  # 11
                is_friday,                  # 12
                is_weekend,                 # 13
                org_size,                   # 14
                offers_telehealth,          # 15
                spec_to_idx.get(specialty_upper, 0),  # 16
                lambda_x_utilization,       # 17
                backlog_x_utilization,      # 18
                capacity_ratio,             # 19
            ]], dtype=np.float32)

        # Inference with timing
        t_start = time.time()
        raw_pred = float(model.predict(features)[0])
        inference_ms = (time.time() - t_start) * 1000

        # Clamp prediction (matching test_wait_time.py: max(0.5, ...))
        predicted_wait_days = max(0.5, round(float(raw_pred), 1))

        feature_cols = self.registry.get_feature_columns("wait_time")
        features_used = dict(zip(feature_cols, features[0].tolist()))

        logger.info(
            "prediction_complete",
            specialty=specialty_upper,
            predicted_wait_days=predicted_wait_days,
            inference_ms=round(inference_ms, 2),
        )

        return {
            "predicted_wait_days": predicted_wait_days,
            "model_version": self.registry.get_version("wait_time"),
            "features_used": features_used,
            "inference_time_ms": round(inference_ms, 2),
            "raw_prediction": round(float(raw_pred), 4),
        }

    def predict_batch(self, scenarios: list[dict]) -> list[dict]:
        """Predict wait times for multiple scenarios."""
        results = []
        for scenario in scenarios:
            result = self.predict(**scenario)
            results.append(result)
        return results

    def get_shap_values(
        self,
        features: np.ndarray,
    ) -> Optional[dict]:
        """Compute SHAP values for a prediction (if shap is available)."""
        try:
            import shap

            model = self.registry.get_model("wait_time")
            if model is None:
                return None

            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(features)
            feature_cols = self.registry.get_feature_columns("wait_time")

            return dict(zip(feature_cols, [round(float(v), 4) for v in shap_values[0]]))
        except ImportError:
            logger.warning("shap_not_available")
            return None
        except Exception as e:
            logger.warning("shap_computation_failed", error=str(e))
            return None

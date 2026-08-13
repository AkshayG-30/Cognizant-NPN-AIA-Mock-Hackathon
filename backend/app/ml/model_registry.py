"""
CarePath AI — LightGBM Model Registry & Loader
Loads the trained wait-time model ONCE at startup.
Model format: LightGBM Booster saved as .txt via model.save_model()
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

import lightgbm as lgb
import numpy as np

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("ml.model_registry")


class ModelRegistry:
    """Singleton registry that holds loaded ML models."""

    _instance: Optional[ModelRegistry] = None

    def __init__(self):
        self._models: dict[str, lgb.Booster] = {}
        self._metadata: dict[str, dict] = {}
        self._feature_columns: dict[str, list[str]] = {}
        self._specialty_encoder: dict[str, dict] = {}
        self._specialty_params: dict[str, dict] = {}
        self._loaded = False

    @classmethod
    def get_instance(cls) -> ModelRegistry:
        if cls._instance is None:
            cls._instance = ModelRegistry()
        return cls._instance

    @property
    def is_loaded(self) -> bool:
        return self._loaded and "wait_time" in self._models

    def load_wait_time_model(self) -> bool:
        """
        Load the LightGBM wait-time model and its artifacts.
        Returns True on success, False on failure.
        """
        settings = get_settings()

        model_path = settings.resolve_path(settings.wait_model_path)
        feature_path = settings.resolve_path(settings.feature_columns_path)
        encoder_path = settings.resolve_path(settings.specialty_encoder_path)
        params_path = settings.resolve_path(settings.specialty_params_path)

        # Candidate model paths to check
        candidate_model_paths = [
            settings.resolve_path(settings.wait_model_path),
            settings.resolve_path("../models/artifacts/v4/wait_time_lgbm_v4.txt"),
            settings.resolve_path("../models/artifacts/v4/wait_time_lgbm_v4.lgb"),
            settings.resolve_path("../models/artifacts/v3/wait_time_lgbm_v3.txt"),
            settings.resolve_path("../models/artifacts/v3/wait_time_lgbm_v3.lgb"),
            settings.resolve_path("../models/artifacts/v1/wait_time_lgbm.txt"),
        ]
        model_path = next((p for p in candidate_model_paths if p.exists()), None)

        if not model_path:
            logger.error("model_file_not_found", paths=[str(p) for p in candidate_model_paths])
            return False

        try:
            t_start = time.time()
            booster = lgb.Booster(model_file=str(model_path))
            load_time = (time.time() - t_start) * 1000

            self._models["wait_time"] = booster
            logger.info(
                "model_loaded",
                model="wait_time",
                version=settings.wait_model_version,
                path=str(model_path),
                load_time_ms=round(load_time, 1),
                num_trees=booster.num_trees(),
            )
        except Exception as e:
            logger.error("model_load_failed", model="wait_time", error=str(e))
            return False

        # Candidate artifact search directories
        artifact_dirs = [
            model_path.parent,
            settings.resolve_path("../models/artifacts/v4"),
            settings.resolve_path("../models/artifacts/v3"),
            settings.resolve_path("../models/artifacts/v1"),
            settings.resolve_path("../models/artifacts"),
        ]

        # Load feature columns
        for ad in artifact_dirs:
            fp = ad / "feature_columns.json"
            if fp.exists():
                with open(fp) as f:
                    self._feature_columns["wait_time"] = json.load(f)
                logger.info("feature_schema_loaded", path=str(fp), count=len(self._feature_columns["wait_time"]))
                break
        else:
            # Fallback default feature column schema
            self._feature_columns["wait_time"] = [
                "arrival_rate_lambda", "service_rate_mu", "server_count", "current_queue_length",
                "active_backlog", "utilization_rho", "traffic_intensity", "distance_km", "quality_score"
            ]

        # Load specialty encoder
        for ad in artifact_dirs:
            ep = ad / "specialty_encoder.json"
            if ep.exists():
                with open(ep) as f:
                    self._specialty_encoder["wait_time"] = json.load(f)
                logger.info("specialty_encoder_loaded", path=str(ep), count=len(self._specialty_encoder["wait_time"]))
                break

        # Load specialty params
        for ad in artifact_dirs:
            pp = ad / "specialty_params.json"
            if pp.exists():
                with open(pp) as f:
                    self._specialty_params["wait_time"] = json.load(f)
                logger.info("specialty_params_loaded", path=str(pp), count=len(self._specialty_params["wait_time"]))
                break

        # Load metrics
        for ad in artifact_dirs:
            mp = ad / "metrics.json"
            if mp.exists():
                with open(mp) as f:
                    self._metadata["wait_time"] = json.load(f)
                logger.info("model_metrics_loaded", path=str(mp))
                break

        self._loaded = True
        return True

    def get_model(self, name: str = "wait_time") -> Optional[lgb.Booster]:
        return self._models.get(name)

    def get_feature_columns(self, name: str = "wait_time") -> list[str]:
        return self._feature_columns.get(name, [])

    def get_specialty_encoder(self, name: str = "wait_time") -> dict:
        return self._specialty_encoder.get(name, {})

    def get_specialty_to_index(self, name: str = "wait_time") -> dict[str, int]:
        encoder = self.get_specialty_encoder(name)
        return {v: int(k) for k, v in encoder.items()}

    def get_specialty_params(self, name: str = "wait_time") -> dict:
        return self._specialty_params.get(name, {})

    def get_metadata(self, name: str = "wait_time") -> dict:
        return self._metadata.get(name, {})

    def get_version(self, name: str = "wait_time") -> str:
        settings = get_settings()
        return settings.wait_model_version


def get_model_registry() -> ModelRegistry:
    """FastAPI dependency — provides the model registry."""
    return ModelRegistry.get_instance()

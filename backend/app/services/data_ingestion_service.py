"""
CarePath AI — Data Ingestion Service
Imports the master provider dataset into PostgreSQL with validation.
"""
from __future__ import annotations

import hashlib
import math
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import (
    Provider,
    ProviderCapacity,
    Specialty,
    Organization,
    AuditLog,
    EventType,
)

logger = get_logger("services.data_ingestion")


# ZIP to approximate lat/lng (US state centroids as fallback)
STATE_CENTROIDS = {
    "AL": (32.8, -86.8), "AK": (64.2, -152.5), "AZ": (34.0, -111.1),
    "AR": (35.2, -91.8), "CA": (36.8, -119.4), "CO": (39.1, -105.4),
    "CT": (41.6, -72.7), "DE": (39.0, -75.5), "FL": (27.8, -81.7),
    "GA": (33.0, -83.5), "HI": (19.9, -155.6), "ID": (44.2, -114.4),
    "IL": (40.3, -89.0), "IN": (40.3, -86.1), "IA": (42.0, -93.2),
    "KS": (38.5, -98.8), "KY": (37.7, -84.3), "LA": (31.2, -92.1),
    "ME": (45.4, -69.4), "MD": (39.0, -76.8), "MA": (42.4, -71.4),
    "MI": (44.3, -85.6), "MN": (46.7, -94.7), "MS": (32.7, -89.7),
    "MO": (37.9, -91.8), "MT": (47.0, -110.4), "NE": (41.1, -98.3),
    "NV": (38.8, -116.4), "NH": (43.5, -71.6), "NJ": (40.1, -74.5),
    "NM": (34.2, -105.6), "NY": (43.0, -75.5), "NC": (35.6, -79.8),
    "ND": (47.5, -100.5), "OH": (40.4, -82.9), "OK": (35.6, -96.9),
    "OR": (43.8, -120.6), "PA": (41.2, -77.2), "RI": (41.6, -71.5),
    "SC": (33.8, -81.2), "SD": (43.9, -99.9), "TN": (35.5, -86.6),
    "TX": (31.1, -97.6), "UT": (39.3, -111.1), "VT": (44.0, -72.7),
    "VA": (37.8, -78.2), "WA": (47.4, -121.5), "WV": (38.6, -80.6),
    "WI": (43.8, -88.8), "WY": (43.1, -107.6), "DC": (38.9, -77.0),
}


class DataIngestionService:
    """Imports master datasets into PostgreSQL."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def import_providers(
        self,
        limit: Optional[int] = None,
        validate_only: bool = False,
    ) -> dict:
        """Import providers from master provider.csv into PostgreSQL."""
        settings = get_settings()
        t_start = time.time()

        master_dir = settings.resolve_path(settings.master_dataset_dir)
        candidates = [
            master_dir / "provider.csv",
            master_dir / "v2_enriched" / "provider.csv",
            master_dir / "provider.parquet",
            master_dir / "v2_enriched" / "provider.parquet",
        ]
        provider_path = None
        for candidate in candidates:
            if candidate.exists():
                provider_path = candidate
                break

        if not provider_path:
            return {
                "table": "providers",
                "records_processed": 0,
                "records_imported": 0,
                "records_rejected": 0,
                "rejected_reasons": [{"reason": f"Provider file not found at {master_dir}"}],
                "validation_only": validate_only,
                "duration_seconds": 0,
                "timestamp": datetime.now(timezone.utc),
            }

        logger.info("provider_import_started", path=str(provider_path), limit=limit)

        # Load data
        if str(provider_path).endswith(".parquet"):
            df = pd.read_parquet(provider_path)
            if limit:
                df = df.head(limit)
        else:
            if limit:
                df = pd.read_csv(provider_path, nrows=limit, low_memory=False)
            else:
                df = pd.read_csv(provider_path, low_memory=False)

        total = len(df)
        imported = 0
        rejected = 0
        reject_reasons = []

        # Import specialties first
        unique_specs = df["specialty"].dropna().unique()
        for spec_name in unique_specs:
            existing = await self.db.execute(
                select(Specialty).where(Specialty.name == spec_name)
            )
            if not existing.scalar_one_or_none():
                self.db.add(Specialty(name=spec_name))

        if validate_only:
            # Validation pass only
            for idx, row in df.iterrows():
                npi = str(row.get("provider_npi", ""))
                if not npi or len(npi) < 10:
                    rejected += 1
                    reject_reasons.append({"row": idx, "reason": f"Invalid NPI: {npi}"})
                else:
                    imported += 1

            duration = time.time() - t_start
            return {
                "table": "providers",
                "records_processed": total,
                "records_imported": imported,
                "records_rejected": rejected,
                "rejected_reasons": reject_reasons[:100],
                "validation_only": True,
                "duration_seconds": round(duration, 2),
                "timestamp": datetime.now(timezone.utc),
            }

        # Batch import
        batch_size = 500
        for start in range(0, total, batch_size):
            batch = df.iloc[start:start + batch_size]

            for _, row in batch.iterrows():
                try:
                    npi = str(int(row["provider_npi"])) if pd.notna(row.get("provider_npi")) else None
                    if not npi or len(npi) < 10:
                        rejected += 1
                        if len(reject_reasons) < 100:
                            reject_reasons.append({"npi": npi, "reason": "Invalid NPI"})
                        continue

                    # Generate synthetic geo coordinates from state
                    lat, lng = None, None
                    state = str(row.get("state", "")).strip().upper() if pd.notna(row.get("state")) else None
                    if state and state in STATE_CENTROIDS:
                        base_lat, base_lng = STATE_CENTROIDS[state]
                        # Add jitter for spatial distribution
                        np.random.seed(hash(npi) % (2**32))
                        lat = base_lat + np.random.uniform(-1.5, 1.5)
                        lng = base_lng + np.random.uniform(-1.5, 1.5)

                    telehealth = str(row.get("offers_telehealth", "N"))
                    provider_id = uuid.uuid4()
                    provider = Provider(
                        id=provider_id,
                        npi=npi,
                        pac_id=str(row.get("provider_pac_id", "")) if pd.notna(row.get("provider_pac_id")) else None,
                        enrl_id=str(row.get("provider_enrl_id", "")) if pd.notna(row.get("provider_enrl_id")) else None,
                        last_name=str(row.get("provider_last_name", "UNKNOWN")),
                        first_name=str(row.get("provider_first_name", "UNKNOWN")),
                        gender=str(row.get("provider_gender", "Unknown")) if pd.notna(row.get("provider_gender")) else "Unknown",
                        credential=str(row.get("provider_credential", "UNKNOWN")) if pd.notna(row.get("provider_credential")) else "UNKNOWN",
                        specialty=str(row.get("specialty", "UNKNOWN")) if pd.notna(row.get("specialty")) else "UNKNOWN",
                        original_specialty=str(row.get("original_specialty", "")) if pd.notna(row.get("original_specialty")) else None,
                        secondary_specialties=str(row.get("secondary_specialties", "")) if pd.notna(row.get("secondary_specialties")) else None,
                        offers_telehealth=telehealth.upper() in ("Y", "YES", "TRUE", "1"),
                        city=str(row.get("city", "")) if pd.notna(row.get("city")) else None,
                        state=state,
                        zip_code=str(int(row.get("zip_code", 0))).zfill(5) if pd.notna(row.get("zip_code")) else None,
                        latitude=lat,
                        longitude=lng,
                        accepts_medicare_individual=str(row.get("accepts_medicare_individual", "")) if pd.notna(row.get("accepts_medicare_individual")) else None,
                        accepts_medicare_group=str(row.get("accepts_medicare_group", "")) if pd.notna(row.get("accepts_medicare_group")) else None,
                        data_source=str(row.get("data_source", "CMS_DAC_REAL")),
                    )
                    self.db.add(provider)

                    # Generate synthetic capacity snapshot
                    specialty_upper = provider.specialty.upper()
                    np.random.seed(hash(f"{npi}_{specialty_upper}") % (2**32))

                    cap = ProviderCapacity(
                        provider_id=provider_id,
                        current_queue_length=int(np.random.poisson(3)),
                        active_backlog=int(np.random.poisson(2)),
                        appointment_capacity=int(np.random.randint(8, 30)),
                        server_count=int(np.random.randint(5, 25)),
                        service_rate_mu=round(float(np.random.uniform(2.5, 5.0)), 2),
                        utilization_rho=round(float(np.random.uniform(0.3, 0.95)), 3),
                        arrival_rate_lambda=round(float(np.random.uniform(10, 50)), 2),
                        is_synthetic=True,
                    )
                    self.db.add(cap)

                    imported += 1

                except Exception as e:
                    rejected += 1
                    if len(reject_reasons) < 100:
                        reject_reasons.append({"error": str(e)})

            await self.db.flush()
            logger.info("import_batch", imported=imported, rejected=rejected, batch_end=start + batch_size)

        # Audit log
        self.db.add(AuditLog(
            event_type="data_imported",
            resource_type="providers",
            action=f"Imported {imported} providers from master dataset",
            details={"total": total, "imported": imported, "rejected": rejected},
        ))

        duration = time.time() - t_start
        logger.info(
            "provider_import_complete",
            total=total,
            imported=imported,
            rejected=rejected,
            duration_s=round(duration, 2),
        )

        return {
            "table": "providers",
            "records_processed": total,
            "records_imported": imported,
            "records_rejected": rejected,
            "rejected_reasons": reject_reasons[:100],
            "validation_only": False,
            "duration_seconds": round(duration, 2),
            "timestamp": datetime.now(timezone.utc),
        }

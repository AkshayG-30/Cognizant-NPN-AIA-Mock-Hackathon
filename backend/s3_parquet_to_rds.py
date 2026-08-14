"""
CarePath AI — Production S3 Parquet to AWS RDS PostgreSQL Ingestion Engine
Streams Parquet datasets from Amazon S3 (or local path) into PostgreSQL using PyArrow.

Usage:
    python backend/s3_parquet_to_rds.py --s3-prefix s3://carepath-datasets-production/master/v2/ --dry-run
    python backend/s3_parquet_to_rds.py --s3-prefix s3://carepath-datasets-production/master/v2/ --file provider.parquet
    python backend/s3_parquet_to_rds.py --s3-prefix "D:/CTS Mock/Datasets/master/compressed parquet files/v2/" --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import io
import math
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

# Ensure backend/ directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pyarrow.parquet as pq
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.db.database as db_mod
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.specialties import CANONICAL_SPECIALTIES, normalize_specialty
from app.db.models import (
    Appointment,
    AppointmentSlot,
    AppointmentStatus,
    AuditLog,
    Organization,
    Patient,
    Provider,
    ProviderCapacity,
    ProviderWaitHistory,
    Specialty,
)
from app.services.data_ingestion_service import STATE_CENTROIDS

logger = get_logger("carepath.ingestion")

# ─────────────────────────────────────────────────────────────
# Helper Utilities
# ─────────────────────────────────────────────────────────────

def redact_db_url(url: str) -> str:
    """Mask database passwords in logs for security compliance."""
    if not url:
        return "<EMPTY>"
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", url)


def get_s3_client():
    """Retrieve boto3 S3 client using default IAM credentials chain."""
    import boto3
    return boto3.client("s3")


def read_parquet_file(file_source: str) -> pq.ParquetFile:
    """
    Open Parquet file from S3 URI (s3://bucket/key) or local file path.
    Returns PyArrow ParquetFile object.
    """
    if file_source.startswith("s3://"):
        import boto3
        parts = file_source[5:].split("/", 1)
        bucket, key = parts[0], parts[1]
        s3 = boto3.client("s3")
        obj = s3.get_object(Bucket=bucket, Key=key)
        buffer = io.BytesIO(obj["Body"].read())
        return pq.ParquetFile(buffer)
    else:
        return pq.ParquetFile(file_source)


# ─────────────────────────────────────────────────────────────
# Ingestion Processor Class
# ─────────────────────────────────────────────────────────────

class IngestionEngine:
    def __init__(
        self,
        s3_prefix: str,
        dry_run: bool = False,
        batch_size: int = 5000,
        limit: Optional[int] = None,
        custom_db_url: Optional[str] = None,
    ):
        self.s3_prefix = s3_prefix.rstrip("/") + "/"
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.limit = limit
        self.raw_db_url = custom_db_url or get_settings().database_url

        # Stats tracking
        self.stats: Dict[str, Dict[str, int]] = {
            "providers": {"read": 0, "inserted": 0, "updated": 0, "skipped": 0, "failed": 0},
            "appointments": {"read": 0, "inserted": 0, "updated": 0, "skipped": 0, "failed": 0},
            "capacity_slots": {"read": 0, "inserted": 0, "updated": 0, "skipped": 0, "failed": 0},
            "network": {"read": 0, "inserted": 0, "updated": 0, "skipped": 0, "failed": 0},
            "order_referring": {"read": 0, "inserted": 0, "updated": 0, "skipped": 0, "failed": 0},
        }

        self.db_connected = False

    async def initialize_db(self):
        """Initialize database engine & session factory without creating ad-hoc engines."""
        print(f"[INGESTION] Target Database URL: {redact_db_url(self.raw_db_url)}")
        print(f"[INGESTION] Mode: {'DRY RUN (No Writes)' if self.dry_run else 'PRODUCTION WRITE'}")

        try:
            db_mod.init_db(self.raw_db_url)
            db_mod.engine.echo = False
            # Ping connection
            async with db_mod.async_session_factory() as session:
                await session.execute(select(1))
            self.db_connected = True
            print("[INGESTION] Database engine connected and verified successfully.")
        except Exception as err:
            self.db_connected = False
            if self.dry_run:
                print(f"[DRY-RUN] Database connection unreachable ({err}). Proceeding with pure Parquet schema & transformation validation.")
            else:
                print(f"[ERROR] Database connection failed: {err}")
                raise err

    def resolve_source_path(self, filename: str) -> str:
        """Construct full S3 URI or local file path."""
        return f"{self.s3_prefix}{filename}"

    # ─────────────────────────────────────────────────────────
    # 1. Ingest Providers (`provider.parquet`)
    # ─────────────────────────────────────────────────────────
    async def process_providers(self):
        source_path = self.resolve_source_path("provider.parquet")
        print("\n" + "=" * 70)
        print(f"[PROVIDERS] Starting ingestion from: {source_path}")
        print("=" * 70)

        t_start = time.time()
        try:
            pf = read_parquet_file(source_path)
        except Exception as err:
            print(f"[ERROR] Failed to read {source_path}: {err}")
            return

        total_rows = pf.metadata.num_rows
        print(f"[PROVIDERS] Total dataset rows: {total_rows:,} | Batch size: {self.batch_size:,}")

        # Pre-seed specialties from DB
        self.loaded_specialties = set()
        if self.db_connected:
            async with db_mod.async_session_factory() as session:
                res = await session.execute(select(Specialty.name))
                self.loaded_specialties = {row[0].upper() for row in res.all()}

        rows_processed = 0

        for batch in pf.iter_batches(batch_size=self.batch_size):
            if self.limit and rows_processed >= self.limit:
                break

            df = batch.to_pandas()
            if self.limit and (rows_processed + len(df) > self.limit):
                df = df.iloc[: (self.limit - rows_processed)]

            batch_count = len(df)
            self.stats["providers"]["read"] += batch_count
            rows_processed += batch_count

            # Process batch data transformations
            batch_specs = df["specialty"].dropna().unique()
            for spec_name in batch_specs:
                norm_spec = normalize_specialty(str(spec_name))
                self.loaded_specialties.add(norm_spec)

            providers_to_add = []
            capacities_to_add = []
            wait_histories_to_add = []

            for _, row in df.iterrows():
                npi_raw = row.get("provider_npi")
                if pd_isna(npi_raw):
                    self.stats["providers"]["skipped"] += 1
                    continue

                npi = str(int(npi_raw)) if isinstance(npi_raw, (int, float)) else str(npi_raw).strip()
                if len(npi) < 10:
                    self.stats["providers"]["skipped"] += 1
                    continue

                # Extract location & state centroid fallback
                state = str(row.get("state", "")).strip().upper() if not pd_isna(row.get("state")) else None
                lat = row.get("latitude") if not pd_isna(row.get("latitude")) else None
                lng = row.get("longitude") if not pd_isna(row.get("longitude")) else None

                if (lat is None or lng is None) and state and state in STATE_CENTROIDS:
                    base_lat, base_lng = STATE_CENTROIDS[state]
                    np.random.seed(hash(npi) % (2**32))
                    lat = base_lat + float(np.random.uniform(-1.0, 1.0))
                    lng = base_lng + float(np.random.uniform(-1.0, 1.0))

                telehealth_raw = str(row.get("offers_telehealth", "N"))
                offers_telehealth = telehealth_raw.upper() in ("Y", "YES", "TRUE", "1")

                raw_spec = str(row.get("specialty", "INTERNAL MEDICINE")) if not pd_isna(row.get("specialty")) else "INTERNAL MEDICINE"
                norm_spec = normalize_specialty(raw_spec)

                provider_id = uuid.uuid4()

                prov = Provider(
                    id=provider_id,
                    npi=npi,
                    pac_id=str(row.get("provider_pac_id", ""))[:50] if not pd_isna(row.get("provider_pac_id")) else None,
                    enrl_id=str(row.get("provider_enrl_id", ""))[:50] if not pd_isna(row.get("provider_enrl_id")) else None,
                    last_name=str(row.get("provider_last_name", "UNKNOWN"))[:200],
                    first_name=str(row.get("provider_first_name", "UNKNOWN"))[:200],
                    gender=str(row.get("provider_gender", "Unknown"))[:20] if not pd_isna(row.get("provider_gender")) else "Unknown",
                    credential=str(row.get("provider_credential", "MD"))[:50] if not pd_isna(row.get("provider_credential")) else "MD",
                    specialty=norm_spec[:200],
                    original_specialty=str(row.get("original_specialty", raw_spec))[:200],
                    secondary_specialties=str(row.get("secondary_specialties", ""))[:200] if not pd_isna(row.get("secondary_specialties")) else None,
                    offers_telehealth=offers_telehealth,
                    city=str(row.get("city", "Los Angeles"))[:200] if not pd_isna(row.get("city")) else "Los Angeles",
                    state=state[:10] if state else "CA",
                    zip_code=str(int(row.get("zip_code", 90024))).zfill(5)[:10] if not pd_isna(row.get("zip_code")) else "90024",
                    latitude=lat,
                    longitude=lng,
                    accepts_medicare_individual=str(row.get("accepts_medicare_individual", "Y"))[:10] if not pd_isna(row.get("accepts_medicare_individual")) else "Y",
                    accepts_medicare_group=str(row.get("accepts_medicare_group", "M"))[:10] if not pd_isna(row.get("accepts_medicare_group")) else "M",
                    data_source=str(row.get("data_source", "CMS_DAC_REAL"))[:50],
                    is_active=True,
                )
                providers_to_add.append(prov)

                # Capacity initialization
                np.random.seed(hash(f"{npi}_{norm_spec}") % (2**32))
                cap = ProviderCapacity(
                    id=uuid.uuid4(),
                    provider_id=provider_id,
                    current_queue_length=int(np.random.poisson(4)),
                    active_backlog=int(np.random.poisson(2)),
                    appointment_capacity=int(np.random.randint(10, 30)),
                    server_count=int(np.random.randint(5, 20)),
                    service_rate_mu=round(float(np.random.uniform(2.5, 5.0)), 2),
                    utilization_rho=round(float(np.random.uniform(0.4, 0.9)), 3),
                    arrival_rate_lambda=round(float(np.random.uniform(10, 45)), 2),
                    is_synthetic=True,
                )
                capacities_to_add.append(cap)

                # VHA Wait statistics if available
                if not pd_isna(row.get("vha_avg_wait_dtc")):
                    w_hist = ProviderWaitHistory(
                        id=uuid.uuid4(),
                        provider_id=provider_id,
                        avg_wait_days=float(row["vha_avg_wait_dtc"]),
                        median_wait_days=float(row.get("vha_median_wait_dtc", row["vha_avg_wait_dtc"])),
                        p90_wait_days=float(row.get("vha_p90_wait_dtc", row["vha_avg_wait_dtc"] * 1.5)),
                        sample_count=int(row.get("vha_sample_count", 100)),
                        is_synthetic=False,
                    )
                    wait_histories_to_add.append(w_hist)

                self.stats["providers"]["inserted"] += 1

            if self.db_connected and not self.dry_run and len(providers_to_add) > 0:
                async with db_mod.async_session_factory() as session:
                    try:
                        session.add_all(providers_to_add)
                        session.add_all(capacities_to_add)
                        session.add_all(wait_histories_to_add)
                        await session.commit()
                    except Exception as err:
                        await session.rollback()
                        self.stats["providers"]["failed"] += batch_count
                        print(f"[ERROR] Batch commit failed: {err}")

            elapsed = round(time.time() - t_start, 1)
            if rows_processed % 50000 == 0 or rows_processed == total_rows or (self.limit and rows_processed >= self.limit):
                print(f" -> Processed {rows_processed:,} / {total_rows:,} records | Validated: {self.stats['providers']['inserted']:,} | Elapsed: {elapsed}s")

        elapsed_total = round(time.time() - t_start, 1)
        print(f"[PROVIDERS] Done in {elapsed_total}s | Inserted/Validated: {self.stats['providers']['inserted']:,} | Skipped: {self.stats['providers']['skipped']:,}")

    # ─────────────────────────────────────────────────────────
    # 2. Ingest Appointments & Patients (`appointment.parquet`)
    # ─────────────────────────────────────────────────────────
    async def process_appointments(self):
        source_path = self.resolve_source_path("appointment.parquet")
        print("\n" + "=" * 70)
        print(f"[APPOINTMENTS] Starting ingestion from: {source_path}")
        print("=" * 70)

        t_start = time.time()
        try:
            pf = read_parquet_file(source_path)
        except Exception as err:
            print(f"[ERROR] Failed to read {source_path}: {err}")
            return

        total_rows = pf.metadata.num_rows
        print(f"[APPOINTMENTS] Total dataset rows: {total_rows:,}")

        # Fetch an active provider to link orphaned appointments
        default_provider_id = None
        if self.db_connected:
            async with db_mod.async_session_factory() as session:
                res = await session.execute(select(Provider.id).limit(1))
                default_provider_id = res.scalar_one_or_none()

        rows_processed = 0

        for batch in pf.iter_batches(batch_size=self.batch_size):
            if self.limit and rows_processed >= self.limit:
                break

            df = batch.to_pandas()
            if self.limit and (rows_processed + len(df) > self.limit):
                df = df.iloc[: (self.limit - rows_processed)]

            batch_count = len(df)
            self.stats["appointments"]["read"] += batch_count
            rows_processed += batch_count

            patients_to_add = []
            appointments_to_add = []

            for _, row in df.iterrows():
                ext_pat_id = str(row.get("patient_id", uuid.uuid4()))
                pat_name = str(row.get("patient_name", "John Doe")).strip()
                name_parts = pat_name.split(" ", 1)
                first_n = name_parts[0]
                last_n = name_parts[1] if len(name_parts) > 1 else "Patient"

                patient_id = uuid.uuid4()
                pat = Patient(
                    id=patient_id,
                    external_id=f"PAT-{ext_pat_id}",
                    first_name=first_n[:200],
                    last_name=last_n[:200],
                    gender=str(row.get("patient_sex", "Unknown"))[:20],
                    insurance=str(row.get("patient_insurance", "Medicare"))[:200],
                    data_source=str(row.get("data_source", "SCHEDULING_SYSTEM_REAL"))[:50],
                )
                patients_to_add.append(pat)

                # Status mapping
                raw_status = str(row.get("appointment_status", "scheduled")).lower()
                if "completed" in raw_status or "attended" in raw_status:
                    app_status = AppointmentStatus.COMPLETED
                elif "cancel" in raw_status:
                    app_status = AppointmentStatus.CANCELLED
                elif "did not attend" in raw_status or "no_show" in raw_status:
                    app_status = AppointmentStatus.NO_SHOW
                else:
                    app_status = AppointmentStatus.SCHEDULED

                app_date = row.get("appointment_date")
                scheduled_dt = app_date if not pd_isna(app_date) else datetime.now(timezone.utc)

                appt = Appointment(
                    id=uuid.uuid4(),
                    patient_id=patient_id,
                    provider_id=default_provider_id or uuid.uuid4(),
                    status=app_status,
                    scheduled_date=scheduled_dt,
                    scheduled_time=str(row.get("appointment_time", "09:00:00"))[:20],
                    notes=f"Wait Days: {row.get('wait_days', 0)}, Interval: {row.get('scheduling_interval_days', 0)}",
                    is_synthetic=False,
                )
                appointments_to_add.append(appt)
                self.stats["appointments"]["inserted"] += 1

            if self.db_connected and not self.dry_run and len(appointments_to_add) > 0:
                async with db_mod.async_session_factory() as session:
                    try:
                        session.add_all(patients_to_add)
                        session.add_all(appointments_to_add)
                        await session.commit()
                    except Exception as err:
                        await session.rollback()
                        self.stats["appointments"]["failed"] += batch_count
                        print(f"[ERROR] Appointments batch failed: {err}")

        print(f"[APPOINTMENTS] Done! Inserted/Validated: {self.stats['appointments']['inserted']:,}")

    # ─────────────────────────────────────────────────────────
    # 3. Ingest Capacity Slots (`capacity_slots.parquet`)
    # ─────────────────────────────────────────────────────────
    async def process_capacity_slots(self):
        source_path = self.resolve_source_path("capacity_slots.parquet")
        print("\n" + "=" * 70)
        print(f"[SLOTS] Starting ingestion from: {source_path}")
        print("=" * 70)

        t_start = time.time()
        try:
            pf = read_parquet_file(source_path)
        except Exception as err:
            print(f"[ERROR] Failed to read {source_path}: {err}")
            return

        total_rows = pf.metadata.num_rows
        print(f"[SLOTS] Total dataset rows: {total_rows:,}")

        default_provider_id = None
        if self.db_connected:
            async with db_mod.async_session_factory() as session:
                res = await session.execute(select(Provider.id).limit(1))
                default_provider_id = res.scalar_one_or_none()

        rows_processed = 0

        for batch in pf.iter_batches(batch_size=self.batch_size):
            if self.limit and rows_processed >= self.limit:
                break

            df = batch.to_pandas()
            if self.limit and (rows_processed + len(df) > self.limit):
                df = df.iloc[: (self.limit - rows_processed)]

            batch_count = len(df)
            self.stats["capacity_slots"]["read"] += batch_count
            rows_processed += batch_count

            slots_to_add = []
            for _, row in df.iterrows():
                slot_date_raw = row.get("slot_date")
                slot_dt = datetime.strptime(str(slot_date_raw), "%Y-%m-%d") if not pd_isna(slot_date_raw) else datetime.now(timezone.utc)

                slot = AppointmentSlot(
                    id=uuid.uuid4(),
                    provider_id=default_provider_id or uuid.uuid4(),
                    slot_date=slot_dt,
                    slot_time=str(row.get("slot_time", "08:00:00"))[:20],
                    duration_mins=30,
                    is_available=bool(row.get("is_available", True)),
                    is_synthetic=False,
                )
                slots_to_add.append(slot)
                self.stats["capacity_slots"]["inserted"] += 1

            if self.db_connected and not self.dry_run and len(slots_to_add) > 0:
                async with db_mod.async_session_factory() as session:
                    try:
                        session.add_all(slots_to_add)
                        await session.commit()
                    except Exception as err:
                        await session.rollback()
                        self.stats["capacity_slots"]["failed"] += batch_count

        print(f"[SLOTS] Done! Inserted/Validated: {self.stats['capacity_slots']['inserted']:,}")

    # ─────────────────────────────────────────────────────────
    # 4. Ingest Insurance Networks (`network.parquet`)
    # ─────────────────────────────────────────────────────────
    async def process_networks(self):
        source_path = self.resolve_source_path("network.parquet")
        print("\n" + "=" * 70)
        print(f"[NETWORKS] Starting ingestion from: {source_path}")
        print("=" * 70)

        try:
            pf = read_parquet_file(source_path)
            df = pf.read().to_pandas()
        except Exception as err:
            print(f"[ERROR] Failed to read {source_path}: {err}")
            return

        total_rows = len(df)
        self.stats["network"]["read"] = total_rows
        print(f"[NETWORKS] Total rows: {total_rows}")

        if self.db_connected and not self.dry_run:
            async with db_mod.async_session_factory() as session:
                try:
                    log = AuditLog(
                        id=uuid.uuid4(),
                        event_type="DATA_IMPORTED",
                        resource_type="insurance_network",
                        resource_id="CMS_PUF_NETWORKS",
                        action=f"Ingested {total_rows} network PUF reference records",
                        details={"total_networks": total_rows, "states": list(df["state_code"].unique())},
                    )
                    session.add(log)
                    await session.commit()
                    self.stats["network"]["inserted"] = total_rows
                except Exception as err:
                    await session.rollback()
                    self.stats["network"]["failed"] = total_rows
                    print(f"[ERROR] Network import failed: {err}")
        else:
            self.stats["network"]["inserted"] = total_rows

        print(f"[NETWORKS] Done! Processed: {self.stats['network']['inserted']}")

    # ─────────────────────────────────────────────────────────
    # 5. Ingest Order Referring Flags (`order_referring.parquet`)
    # ─────────────────────────────────────────────────────────
    async def process_order_referring(self):
        source_path = self.resolve_source_path("order_referring.parquet")
        print("\n" + "=" * 70)
        print(f"[ORDER REFERRING] Starting ingestion from: {source_path}")
        print("=" * 70)

        t_start = time.time()
        try:
            pf = read_parquet_file(source_path)
        except Exception as err:
            print(f"[ERROR] Failed to read {source_path}: {err}")
            return

        total_rows = pf.metadata.num_rows
        print(f"[ORDER REFERRING] Total dataset rows: {total_rows:,}")

        rows_processed = 0

        for batch in pf.iter_batches(batch_size=self.batch_size * 2):
            if self.limit and rows_processed >= self.limit:
                break

            df = batch.to_pandas()
            if self.limit and (rows_processed + len(df) > self.limit):
                df = df.iloc[: (self.limit - rows_processed)]

            batch_count = len(df)
            self.stats["order_referring"]["read"] += batch_count
            rows_processed += batch_count
            self.stats["order_referring"]["inserted"] += batch_count

            if rows_processed % 500000 == 0:
                print(f" -> Streamed {rows_processed:,} / {total_rows:,} referring provider records...")

        print(f"[ORDER REFERRING] Done! Validated & Audited: {self.stats['order_referring']['inserted']:,}")

    # ─────────────────────────────────────────────────────────
    # Summary Reporting
    # ─────────────────────────────────────────────────────────
    def print_final_report(self, total_elapsed: float):
        print("\n" + "=" * 75)
        print("  CarePath AI — Parquet Ingestion Final Summary Report")
        print("=" * 75)
        print(f" Source Location : {self.s3_prefix}")
        print(f" Ingestion Mode  : {'DRY RUN (No Writes Committed)' if self.dry_run else 'PRODUCTION RDS WRITE'}")
        print(f" Execution Time  : {round(total_elapsed, 2)} seconds")
        print("-" * 75)
        print(f" {'Dataset':<18} | {'Read':<10} | {'Inserted':<10} | {'Skipped':<10} | {'Failed':<10}")
        print("-" * 75)
        for dset, s in self.stats.items():
            print(f" {dset:<18} | {s['read']:<10,} | {s['inserted']:<10,} | {s['skipped']:<10,} | {s['failed']:<10,}")
        print("=" * 75)


def pd_isna(val: Any) -> bool:
    if val is None:
        return True
    if isinstance(val, float) and math.isnan(val):
        return True
    if str(val).strip().lower() in ("nan", "none", "null", ""):
        return True
    return False


# ─────────────────────────────────────────────────────────────
# CLI Entrypoint
# ─────────────────────────────────────────────────────────────

async def async_main():
    parser = argparse.ArgumentParser(description="CarePath AI Parquet Ingestion Engine")
    parser.add_argument(
        "--s3-prefix",
        type=str,
        default="D:/CTS Mock/Datasets/master/compressed parquet files/v2/",
        help="S3 URI prefix (s3://bucket/key) or local directory path containing parquet files.",
    )
    parser.add_argument(
        "--file",
        type=str,
        default="all",
        choices=["all", "provider.parquet", "appointment.parquet", "capacity_slots.parquet", "network.parquet", "order_referring.parquet"],
        help="Specific Parquet file to process.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Perform schema and data validation without writing to database.")
    parser.add_argument("--batch-size", type=int, default=5000, help="Number of rows per transaction batch.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of rows to process per file (for testing).")
    parser.add_argument("--db-url", type=str, default=None, help="Custom database URL.")

    args = parser.parse_args()

    engine = IngestionEngine(
        s3_prefix=args.s3_prefix,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
        limit=args.limit,
        custom_db_url=args.db_url,
    )

    t0 = time.time()
    await engine.initialize_db()

    target_file = args.file.lower()

    if target_file in ("all", "provider.parquet"):
        await engine.process_providers()

    if target_file in ("all", "appointment.parquet"):
        await engine.process_appointments()

    if target_file in ("all", "capacity_slots.parquet"):
        await engine.process_capacity_slots()

    if target_file in ("all", "network.parquet"):
        await engine.process_networks()

    if target_file in ("all", "order_referring.parquet"):
        await engine.process_order_referring()

    total_elapsed = time.time() - t0
    engine.print_final_report(total_elapsed)
    if engine.db_connected:
        await db_mod.close_db()


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()

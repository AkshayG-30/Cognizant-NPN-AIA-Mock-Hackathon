"""
CarePath AI — High-Performance Bulk Provider Ingestion Script
Streams and ingests provider records into PostgreSQL database in batches.
"""
import asyncio
import time
import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

import app.db.database as db_mod
from app.db.models import Provider, ProviderCapacity, Specialty
from app.services.data_ingestion_service import STATE_CENTROIDS

BATCH_SIZE = 5000  # 5,000 records per SQL transaction commit

async def main(limit: int | None = None):
    print("=" * 60)
    print("  CarePath AI — Bulk Provider Data Ingestion Engine")
    print("=" * 60)
    
    db_mod.init_db()
    db_mod.engine.echo = False
    
    # Locate dataset
    base = Path("d:/CTS Mock/Datasets/master")
    provider_path = None
    for cand in [base / "v2_enriched" / "provider.csv", base / "provider.csv"]:
        if cand.exists():
            provider_path = cand
            break
            
    if not provider_path:
        print(f"Error: provider.csv not found in {base}")
        return

    print(f"Reading dataset: {provider_path}")
    t_start = time.time()
    
    # Check current DB count
    async with db_mod.async_session_factory() as session:
        cur_count = (await session.execute(text("SELECT COUNT(*) FROM providers"))).scalar_one()
        print(f"Current DB Provider Count: {cur_count}")

    # Read CSV stream in chunks
    chunksize = 10000
    total_processed = 0
    total_imported = 0
    total_skipped = 0
    loaded_specialties = set()

    print("Beginning batch ingestion stream...")

    for chunk in pd.read_csv(provider_path, chunksize=chunksize, low_memory=False):
        if limit and total_processed >= limit:
            break
            
        if limit and (total_processed + len(chunk) > limit):
            chunk = chunk.iloc[:(limit - total_processed)]

        async with db_mod.async_session_factory() as session:
            # 1. Collect unique specialties (cached in memory)
            unique_specs = chunk["specialty"].dropna().unique()
            for spec_name in unique_specs:
                spec_str = str(spec_name).strip().upper()
                if not spec_str or spec_str in loaded_specialties:
                    continue
                res = await session.execute(select(Specialty).where(Specialty.name == spec_str))
                if not res.scalar_one_or_none():
                    session.add(Specialty(name=spec_str))
                loaded_specialties.add(spec_str)
            await session.flush()

            # 2. Extract valid rows
            providers_to_add = []
            capacity_to_add = []

            for _, row in chunk.iterrows():
                total_processed += 1
                try:
                    npi_raw = row.get("provider_npi")
                    if pd.isna(npi_raw):
                        total_skipped += 1
                        continue
                    npi = str(int(npi_raw)) if isinstance(npi_raw, (int, float)) else str(npi_raw).strip()
                    if len(npi) < 10:
                        total_skipped += 1
                        continue

                    # Spatial coordinates
                    lat, lng = None, None
                    state = str(row.get("state", "")).strip().upper() if pd.notna(row.get("state")) else None
                    if state and state in STATE_CENTROIDS:
                        base_lat, base_lng = STATE_CENTROIDS[state]
                        np.random.seed(hash(npi) % (2**32))
                        lat = base_lat + np.random.uniform(-1.5, 1.5)
                        lng = base_lng + np.random.uniform(-1.5, 1.5)

                    telehealth = str(row.get("offers_telehealth", "N"))
                    provider_id = uuid.uuid4()
                    
                    prov = Provider(
                        id=provider_id,
                        npi=npi,
                        pac_id=str(row.get("provider_pac_id", ""))[:50] if pd.notna(row.get("provider_pac_id")) else None,
                        enrl_id=str(row.get("provider_enrl_id", ""))[:50] if pd.notna(row.get("provider_enrl_id")) else None,
                        last_name=str(row.get("provider_last_name", "UNKNOWN"))[:100],
                        first_name=str(row.get("provider_first_name", "UNKNOWN"))[:100],
                        gender=str(row.get("provider_gender", "Unknown"))[:20] if pd.notna(row.get("provider_gender")) else "Unknown",
                        credential=str(row.get("provider_credential", "UNKNOWN"))[:50] if pd.notna(row.get("provider_credential")) else "UNKNOWN",
                        specialty=str(row.get("specialty", "UNKNOWN")).strip().upper()[:100] if pd.notna(row.get("specialty")) else "UNKNOWN",
                        original_specialty=str(row.get("original_specialty", ""))[:100] if pd.notna(row.get("original_specialty")) else None,
                        secondary_specialties=str(row.get("secondary_specialties", ""))[:200] if pd.notna(row.get("secondary_specialties")) else None,
                        offers_telehealth=telehealth.upper() in ("Y", "YES", "TRUE", "1"),
                        city=str(row.get("city", ""))[:100] if pd.notna(row.get("city")) else None,
                        state=state[:10] if state else None,
                        zip_code=str(int(row.get("zip_code", 0))).zfill(5)[:10] if pd.notna(row.get("zip_code")) else None,
                        latitude=lat,
                        longitude=lng,
                        accepts_medicare_individual=str(row.get("accepts_medicare_individual", ""))[:10] if pd.notna(row.get("accepts_medicare_individual")) else None,
                        accepts_medicare_group=str(row.get("accepts_medicare_group", ""))[:10] if pd.notna(row.get("accepts_medicare_group")) else None,
                        data_source=str(row.get("data_source", "CMS_DAC_REAL"))[:50],
                    )
                    providers_to_add.append(prov)

                    specialty_upper = prov.specialty.upper()
                    np.random.seed(hash(f"{npi}_{specialty_upper}") % (2**32))

                    cap = ProviderCapacity(
                        id=uuid.uuid4(),
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
                    capacity_to_add.append(cap)

                    total_imported += 1
                except Exception as e:
                    total_skipped += 1

            # Save batch to DB
            session.add_all(providers_to_add)
            session.add_all(capacity_to_add)
            await session.commit()
            
            elapsed = round(time.time() - t_start, 1)
            print(f" -> Processed {total_processed:,} records | Imported {total_imported:,} | Elapsed: {elapsed}s")

    elapsed_total = round(time.time() - t_start, 1)
    
    async with db_mod.async_session_factory() as session:
        final_count = (await session.execute(text("SELECT COUNT(*) FROM providers"))).scalar_one()

    print("=" * 60)
    print(f"  INGESTION COMPLETE")
    print(f"  Total Processed : {total_processed:,}")
    print(f"  Total Imported  : {total_imported:,}")
    print(f"  Total Skipped   : {total_skipped:,}")
    print(f"  Total DB Providers: {final_count:,}")
    print(f"  Time Taken      : {elapsed_total} seconds")
    print("=" * 60)

if __name__ == "__main__":
    import sys
    limit_val = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    asyncio.run(main(limit=limit_val))

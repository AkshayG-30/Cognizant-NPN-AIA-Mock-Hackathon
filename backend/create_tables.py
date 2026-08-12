"""
CarePath AI — Database Table Creation Script
Creates all tables defined in app.db.models using synchronous SQLAlchemy.
"""
import sys
sys.path.insert(0, ".")

from sqlalchemy import create_engine, text
from app.core.config import get_settings
from app.db.database import Base
# Import all models to register them with Base.metadata
from app.db.models import (
    Specialty, Organization, Provider, ProviderCapacity, ProviderWaitHistory,
    Patient, Referral, ReferralEvent, Prediction, Recommendation,
    RecommendationCandidate, AppointmentSlot, Appointment, ModelVersion, AuditLog,
)

settings = get_settings()

# Build sync URL from async URL
sync_url = str(settings.database_url).replace("+asyncpg", "").replace("postgresql://", "postgresql+psycopg2://")
if "+psycopg2" not in sync_url and "psycopg2" not in sync_url:
    sync_url = sync_url.replace("postgresql://", "postgresql+psycopg2://")

# Try the sync URL from settings first, fall back to derived
try:
    engine = create_engine(settings.database_sync_url)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print(f"Using DATABASE_SYNC_URL: {settings.database_sync_url}")
except Exception:
    engine = create_engine(sync_url)
    print(f"Using derived sync URL: {sync_url}")

print(f"\nRegistered tables: {list(Base.metadata.tables.keys())}")
print(f"Total: {len(Base.metadata.tables)} tables\n")

Base.metadata.create_all(bind=engine)

print("All tables created successfully!")

# Verify
with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
    ))
    tables = [row[0] for row in result]
    print(f"\nTables in database ({len(tables)}):")
    for t in tables:
        print(f"  - {t}")

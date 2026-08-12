"""
CarePath AI — Database Connection
Async SQLAlchemy 2.x engine and session management.
"""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass


def get_engine(custom_url: str | None = None):
    """Create async engine (cached via module-level)."""
    settings = get_settings()
    url = custom_url or settings.database_url
    
    if "sqlite" in url:
        return create_async_engine(
            url,
            echo=settings.debug and not settings.is_production,
            connect_args={"check_same_thread": False},
        )
    
    return create_async_engine(
        url,
        echo=settings.debug and not settings.is_production,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )


engine = None
async_session_factory = None


def init_db(custom_url: str | None = None):
    """Initialize the database engine and session factory."""
    global engine, async_session_factory
    engine = get_engine(custom_url)
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def seed_default_providers():
    """Seed default active providers if database is empty."""
    from app.db.models import Provider
    from sqlalchemy import select
    import uuid

    if async_session_factory is None:
        return

    async with async_session_factory() as session:
        try:
            res = await session.execute(select(Provider).limit(1))
            if res.scalar_one_or_none() is not None:
                return

            default_providers = [
                Provider(
                    id=uuid.uuid4(),
                    npi="1982749102",
                    first_name="Sarah",
                    last_name="Williams",
                    credential="MD, FACC",
                    specialty="CARDIOVASCULAR DISEASE",
                    subspecialty="Interventional Cardiology",
                    city="Los Angeles",
                    state="CA",
                    zip_code="90024",
                    latitude=34.0736,
                    longitude=-118.3775,
                    is_active=True,
                    offers_telehealth=True,
                ),
                Provider(
                    id=uuid.uuid4(),
                    npi="1827491029",
                    first_name="Michael",
                    last_name="Chang",
                    credential="MD, PhD",
                    specialty="CARDIOVASCULAR DISEASE",
                    subspecialty="Electrophysiology",
                    city="Beverly Hills",
                    state="CA",
                    zip_code="90210",
                    latitude=34.0664,
                    longitude=-118.4452,
                    is_active=True,
                    offers_telehealth=True,
                ),
                Provider(
                    id=uuid.uuid4(),
                    npi="1736291048",
                    first_name="Emily",
                    last_name="Vance",
                    credential="MD",
                    specialty="CARDIOVASCULAR DISEASE",
                    subspecialty="Preventive Cardiology",
                    city="Pasadena",
                    state="CA",
                    zip_code="91101",
                    latitude=34.1478,
                    longitude=-118.1445,
                    is_active=True,
                    offers_telehealth=False,
                ),
                Provider(
                    id=uuid.uuid4(),
                    npi="1648291037",
                    first_name="David",
                    last_name="Miller",
                    credential="MD, FAAD",
                    specialty="DERMATOLOGY",
                    subspecialty="Dermatopathologist",
                    city="Los Angeles",
                    state="CA",
                    zip_code="90095",
                    latitude=34.0689,
                    longitude=-118.4451,
                    is_active=True,
                    offers_telehealth=True,
                ),
                Provider(
                    id=uuid.uuid4(),
                    npi="1527491083",
                    first_name="Robert",
                    last_name="Chen",
                    credential="MD, FAAOS",
                    specialty="ORTHOPEDIC SURGERY",
                    subspecialty="Sports Medicine",
                    city="Santa Monica",
                    state="CA",
                    zip_code="90404",
                    latitude=34.0259,
                    longitude=-118.4861,
                    is_active=True,
                    offers_telehealth=False,
                ),
            ]

            for p in default_providers:
                session.add(p)
            await session.commit()
        except Exception:
            await session.rollback()


async def create_tables():
    """Create all schema tables if they do not exist with automatic SQLite fallback."""
    global engine, async_session_factory
    if engine is None:
        init_db()
    from app.db.models import Base
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await seed_default_providers()
    except Exception as exc:
        # Fallback to local SQLite database when PostgreSQL is unreachable
        fallback_url = "sqlite+aiosqlite:///./carepath_dev.db"
        if engine:
            await engine.dispose()
        init_db(fallback_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await seed_default_providers()



async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — provides an async database session."""
    if async_session_factory is None:
        init_db()
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_db():
    """Close the database engine."""
    global engine
    if engine:
        await engine.dispose()

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


def get_engine():
    """Create async engine (cached via module-level)."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.debug and not settings.is_production,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )


engine = None
async_session_factory = None


def init_db():
    """Initialize the database engine and session factory."""
    global engine, async_session_factory
    engine = get_engine()
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def create_tables():
    """Create all schema tables if they do not exist."""
    global engine
    if engine is None:
        init_db()
    from app.db.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)



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

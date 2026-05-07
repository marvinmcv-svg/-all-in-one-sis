from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import Column, DateTime
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import get_settings


def _get_settings():
    """Lazy-load settings to avoid module-load-time calls."""
    return get_settings()


# Create async engine (lazy URL resolution via function)
def _get_engine():
    settings = _get_settings()
    return create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


# Module-level engine instance (created lazily on first use)
_engine = None


def _get_engine_instance():
    """Get or create the engine singleton."""
    global _engine
    if _engine is None:
        _engine = _get_engine()
    return _engine

# Create async session maker (lazy - engine created on first use)
_session_maker = None


def _get_session_maker():
    """Get or create the session maker singleton."""
    global _session_maker
    if _session_maker is None:
        _session_maker = async_sessionmaker(
            _get_engine_instance(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _session_maker


def async_session_maker():
    """Alias for backward compatibility with dependency injection."""
    return _get_session_maker()()


class Base(DeclarativeBase):
    """Base class for all database models with common fields."""

    __abstract__ = True

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.

    Yields:
        AsyncSession: Database session that auto-closes after use.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database - creates all tables."""
    async with _get_engine_instance().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await _get_engine_instance().dispose()

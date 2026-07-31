"""SQLAlchemy engine/session wiring and the declarative base every domain model inherits.

Tenant-scoped tables get their `org_id` column and Postgres Row-Level Security
policy from `TenantScopedMixin` / the migration that creates them (see
backend/migrations) — this module only provides the mechanism, per
CLAUDE.md INV-18.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for every domain model in every Bounded Context."""


class TenantScopedMixin:
    """Marker mixin for every tenant-scoped entity (Phase 0 §6).

    Does not itself declare the `org_id` column: each concrete model
    declares its own `org_id` with a `ForeignKey("organizations.id")`,
    since a mixin-level column would be silently overridden by every
    subclass's own declaration anyway (Python attribute resolution finds
    the subclass's own class-body attribute before any mixin's). This
    class exists purely so `BaseRepository.list_for_organization`
    (shared_kernel/repository.py) and future authorization code have a
    single type to check against ("is this model tenant-scoped?").

    `org_id` denormalization itself is Phase 0 §6 / DR-003's concrete
    field-level mechanism; the RLS policy enforcing it at the database
    layer is created in the Alembic migration, not here.
    """


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(settings.database_url, echo=settings.sql_echo, pool_pre_ping=True)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a request-scoped session. This is the
    project's dependency-injection foundation (Technology Stack §3/§4 —
    FastAPI's own `Depends` mechanism, not a separate DI framework)."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session

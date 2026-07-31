from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.models_registry import Base


@pytest_asyncio.fixture
async def async_client() -> AsyncIterator[AsyncClient]:
    """FastAPI app under test, ASGI in-process — no network, no live DB."""
    from src.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def sqlite_session() -> AsyncIterator[AsyncSession]:
    """In-memory SQLite session for schema-level model smoke tests only.

    NOT a substitute for Postgres-specific behavior (RLS, JSONB) — those
    are covered by tests/tenant_isolation against a real Postgres instance
    (docker-compose), per CLAUDE.md §7.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    from src.config import get_settings

    get_settings.cache_clear()

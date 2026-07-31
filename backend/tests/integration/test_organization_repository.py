"""Exercises the base repository pattern end-to-end against an in-memory
SQLite schema (portable subset only — no RLS/JSONB semantics)."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.identity_access.domain.models import Organization, OrganizationStatus
from src.identity_access.repository import OrganizationRepository


@pytest.mark.asyncio
async def test_add_and_get_round_trip(sqlite_session: AsyncSession) -> None:
    repo = OrganizationRepository(sqlite_session)
    org = Organization(name="Acme Co", status=OrganizationStatus.ACTIVE)

    await repo.add(org)
    fetched = await repo.get_by_id(org.id)

    assert fetched is not None
    assert fetched.name == "Acme Co"
    assert fetched.status == OrganizationStatus.ACTIVE

"""Generic repository base (CLAUDE.md §3.1/§3.3-I).

Each Bounded Context defines its own narrow repository interfaces per
aggregate (e.g. `OrganizationRepository`, `BrandGenomeRepository`) rather
than sharing one `DataAccess` interface — this base class only factors out
the mechanical CRUD plumbing every one of those repositories needs, never
business rules. Business rules (e.g. Genome's three-step atomic activation,
Phase 0 §3.6) belong in a context's service layer, not here.
"""
from __future__ import annotations

import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: ModelT) -> ModelT:
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def add_all(self, entities: list[ModelT]) -> list[ModelT]:
        self._session.add_all(entities)
        await self._session.flush()
        return entities

    async def get_by_id(self, entity_id: uuid.UUID) -> ModelT | None:
        return await self._session.get(self.model, entity_id)

    async def list_for_organization(self, org_id: str) -> list[ModelT]:
        """Only valid for models using `TenantScopedMixin` (Phase 0 §6)."""
        stmt = select(self.model).where(self.model.org_id == org_id)  # type: ignore[attr-defined]
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

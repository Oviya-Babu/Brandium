"""Repository interfaces for Bounded Context 2 (CLAUDE.md §3.1/§3.3-I) —
one narrow interface per aggregate, following `identity_access/repository.py`'s
worked example."""
from __future__ import annotations

import uuid

from sqlalchemy import select

from src.brand_governance.domain.models import (
    Assertion,
    Brand,
    BrandGenome,
    BrandHistory,
    GenomeCategory,
    GenomeComponent,
    Policy,
)
from src.shared_kernel.repository import BaseRepository


class BrandRepository(BaseRepository[Brand]):
    model = Brand


class BrandHistoryRepository(BaseRepository[BrandHistory]):
    model = BrandHistory

    async def list_for_brand(self, brand_id: uuid.UUID) -> list[BrandHistory]:
        stmt = select(BrandHistory).where(BrandHistory.brand_id == brand_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class BrandGenomeRepository(BaseRepository[BrandGenome]):
    model = BrandGenome

    async def list_for_brand(self, brand_id: uuid.UUID) -> list[BrandGenome]:
        stmt = select(BrandGenome).where(BrandGenome.brand_id == brand_id).order_by(BrandGenome.version_number)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def next_version_number(self, brand_id: uuid.UUID) -> int:
        existing = await self.list_for_brand(brand_id)
        return (max((g.version_number for g in existing), default=0)) + 1

    async def get_categories(self, genome_id: uuid.UUID) -> list[GenomeCategory]:
        stmt = select(GenomeCategory).where(GenomeCategory.genome_id == genome_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_components(self, category_id: uuid.UUID) -> list[GenomeComponent]:
        stmt = select(GenomeComponent).where(GenomeComponent.category_id == category_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_assertions(self, component_id: uuid.UUID) -> list[Assertion]:
        stmt = select(Assertion).where(Assertion.component_id == component_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_assertions_by_ids(self, assertion_ids: list[uuid.UUID]) -> list[Assertion]:
        """Used by the execution runtime (`workers/tasks.py`) to
        reconstruct one Work Unit's assigned Assertions inside its own
        task/session, without recomputing the full Applicability Set."""
        if not assertion_ids:
            return []
        stmt = select(Assertion).where(Assertion.id.in_(assertion_ids))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class PolicyRepository(BaseRepository[Policy]):
    model = Policy

    async def list_for_brand(self, brand_id: uuid.UUID) -> list[Policy]:
        stmt = select(Policy).where(Policy.brand_id == brand_id).order_by(Policy.version_number)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def next_version_number(self, brand_id: uuid.UUID) -> int:
        existing = await self.list_for_brand(brand_id)
        return (max((p.version_number for p in existing), default=0)) + 1

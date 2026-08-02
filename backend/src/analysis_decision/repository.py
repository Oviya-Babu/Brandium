from __future__ import annotations

import uuid

from sqlalchemy import select

from src.analysis_decision.domain.models import (
    AnalysisRun,
    AssertionOutcome,
    Decision,
    Evidence,
    Observation,
    Recommendation,
)
from src.shared_kernel.repository import BaseRepository


class AnalysisRunRepository(BaseRepository[AnalysisRun]):
    model = AnalysisRun


class ObservationRepository(BaseRepository[Observation]):
    model = Observation

    async def list_for_run(self, analysis_run_id: uuid.UUID) -> list[Observation]:
        stmt = select(Observation).where(Observation.analysis_run_id == analysis_run_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class EvidenceRepository(BaseRepository[Evidence]):
    model = Evidence

    async def list_for_run(self, analysis_run_id: uuid.UUID) -> list[Evidence]:
        stmt = select(Evidence).where(Evidence.analysis_run_id == analysis_run_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class AssertionOutcomeRepository(BaseRepository[AssertionOutcome]):
    model = AssertionOutcome


class DecisionRepository(BaseRepository[Decision]):
    model = Decision

    async def get_for_run(self, analysis_run_id: uuid.UUID) -> Decision | None:
        stmt = select(Decision).where(Decision.analysis_run_id == analysis_run_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class RecommendationRepository(BaseRepository[Recommendation]):
    model = Recommendation

    async def list_for_run(self, analysis_run_id: uuid.UUID) -> list[Recommendation]:
        stmt = select(Recommendation).where(Recommendation.analysis_run_id == analysis_run_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

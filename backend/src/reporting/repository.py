from __future__ import annotations

import uuid

from sqlalchemy import select

from src.reporting.domain.models import Report
from src.shared_kernel.repository import BaseRepository


class ReportRepository(BaseRepository[Report]):
    model = Report

    async def get_for_run(self, analysis_run_id: uuid.UUID) -> Report | None:
        stmt = select(Report).where(Report.analysis_run_id == analysis_run_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

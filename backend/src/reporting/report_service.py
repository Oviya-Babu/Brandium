"""Report Service (Phase 0 §3.16) — materializes a persisted read model
from exactly one Decision, its Evidence, and its Recommendations,
reachable via `analysis_run_id`, plus the mutable review/flag overlay
(the one deliberate exception to immutability elsewhere in this model)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.reporting.domain.models import Report, ReportReviewStatus
from src.reporting.repository import ReportRepository


class ReportFlagError(Exception):
    pass


class ReportService:
    def __init__(self, repo: ReportRepository) -> None:
        self._repo = repo

    async def generate(self, *, org_id: uuid.UUID, analysis_run_id: uuid.UUID, decision_id: uuid.UUID) -> Report:
        report = Report(
            org_id=org_id,
            analysis_run_id=analysis_run_id,
            decision_id=decision_id,
            generated_at=datetime.now(timezone.utc),
            review_status=ReportReviewStatus.UNREVIEWED,
        )
        return await self._repo.add(report)

    async def approve(self, *, report: Report, reviewer_id: uuid.UUID) -> Report:
        """PRD §11.4: Marketing Manager approves for publication."""
        report.review_status = ReportReviewStatus.APPROVED
        report.reviewed_by = reviewer_id
        report.reviewed_at = datetime.now(timezone.utc)
        return report

    async def flag(self, *, report: Report, reviewer_id: uuid.UUID, reason: str) -> Report:
        """Phase 2 §9: feeds the Mediated Path — never an automatic
        Genome/Policy/decision_function_version change."""
        if not reason.strip():
            raise ReportFlagError("flag_reason is required when flagging a Report.")
        report.review_status = ReportReviewStatus.FLAGGED
        report.reviewed_by = reviewer_id
        report.reviewed_at = datetime.now(timezone.utc)
        report.flag_reason = reason
        return report

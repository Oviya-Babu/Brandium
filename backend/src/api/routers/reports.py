"""Report endpoints (Phase 0 §3.16, PRD §11.4)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.dependencies import CurrentActor, get_current_actor
from src.identity_access.authorization import has_role
from src.identity_access.domain.enums import Role, ScopeTier
from src.reporting.domain.models import ReportReviewStatus
from src.reporting.report_service import ReportFlagError, ReportService
from src.reporting.repository import ReportRepository
from src.shared_kernel.db import get_session

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportOut(BaseModel):
    id: uuid.UUID
    analysis_run_id: uuid.UUID
    decision_id: uuid.UUID
    review_status: ReportReviewStatus
    flag_reason: str | None

    class Config:
        from_attributes = True


class FlagRequest(BaseModel):
    reason: str


@router.get("/by-run/{run_id}", response_model=ReportOut)
async def get_report_for_run(
    run_id: uuid.UUID, actor: CurrentActor = Depends(get_current_actor), session=Depends(get_session)
):
    report = await ReportRepository(session).get_for_run(run_id)
    if report is None or report.org_id != actor.org_id:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


@router.post("/{report_id}/approve", response_model=ReportOut)
async def approve_report(
    report_id: uuid.UUID, actor: CurrentActor = Depends(get_current_actor), session=Depends(get_session)
):
    """PRD §11.4: Marketing Manager approves for publication — a
    distinct authority from Brand Administrator's Genome/Policy approval
    (Phase 5 §3, never substitutable)."""
    repo = ReportRepository(session)
    report = await repo.get_by_id(report_id)
    if report is None or report.org_id != actor.org_id:
        raise HTTPException(status_code=404, detail="Report not found.")
    if not has_role(actor.authorization, actor.org_id, ScopeTier.ORGANIZATION, actor.org_id, Role.MARKETING_MANAGER):
        raise HTTPException(status_code=403, detail="Requires MarketingManager.")
    service = ReportService(repo)
    await service.approve(report=report, reviewer_id=actor.user_id)
    await session.commit()
    return report


@router.post("/{report_id}/flag", response_model=ReportOut)
async def flag_report(
    report_id: uuid.UUID,
    body: FlagRequest,
    actor: CurrentActor = Depends(get_current_actor),
    session=Depends(get_session),
):
    repo = ReportRepository(session)
    report = await repo.get_by_id(report_id)
    if report is None or report.org_id != actor.org_id:
        raise HTTPException(status_code=404, detail="Report not found.")
    service = ReportService(repo)
    try:
        await service.flag(report=report, reviewer_id=actor.user_id, reason=body.reason)
    except ReportFlagError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await session.commit()
    return report

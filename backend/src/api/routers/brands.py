"""Brand endpoints (Phase 0 §3.5)."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analysis_decision.domain.models import AnalysisRun, AnalysisRunStatus, Decision
from src.api.dependencies import CurrentActor, get_current_actor
from src.brand_governance.domain.models import Brand, BrandStatus
from src.campaign_asset.domain.models import Asset, AssetModality, AssetVersion, Campaign
from src.shared_kernel.db import get_session

router = APIRouter(prefix="/brands", tags=["brands"])


class BrandCreate(BaseModel):
    workspace_id: uuid.UUID
    name: str


class BrandOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    status: BrandStatus
    active_genome_version_id: uuid.UUID | None
    active_policy_version_id: uuid.UUID | None

    class Config:
        from_attributes = True


@router.post("", response_model=BrandOut, status_code=201)
async def create_brand(
    body: BrandCreate,
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> Brand:
    brand = Brand(org_id=actor.org_id, workspace_id=body.workspace_id, name=body.name, status=BrandStatus.ACTIVE)
    session.add(brand)
    await session.flush()
    await session.commit()
    return brand


@router.get("/{brand_id}", response_model=BrandOut)
async def get_brand(
    brand_id: uuid.UUID,
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> Brand:
    brand = await session.get(Brand, brand_id)
    if brand is None or brand.org_id != actor.org_id:
        raise HTTPException(status_code=404, detail="Brand not found.")
    return brand


class AnalysisRunSummaryOut(BaseModel):
    id: uuid.UUID
    status: AnalysisRunStatus
    failure_reason: str | None
    started_at: datetime | None
    completed_at: datetime | None
    asset_name: str
    asset_modality: AssetModality
    score: float | None
    verdict: str | None


@router.get("/{brand_id}/analysis-runs", response_model=list[AnalysisRunSummaryOut])
async def list_analysis_runs(
    brand_id: uuid.UUID,
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
):
    """Asset Analysis history (redesigned Brand Workspace/Dashboard) —
    `AnalysisRun` has no `brand_id` of its own (Phase 0 §3.11 pins only
    `asset_version_id`/genome/policy version), so this joins back through
    AssetVersion -> Asset -> Campaign to reach it, the same path the
    Decision Engine itself follows to resolve a run's Brand."""
    stmt = (
        select(AnalysisRun, Asset.name, Asset.modality, Decision.score, Decision.verdict)
        .join(AssetVersion, AssetVersion.id == AnalysisRun.asset_version_id)
        .join(Asset, Asset.id == AssetVersion.asset_id)
        .join(Campaign, Campaign.id == Asset.campaign_id)
        .outerjoin(Decision, Decision.analysis_run_id == AnalysisRun.id)
        .where(Campaign.brand_id == brand_id, AnalysisRun.org_id == actor.org_id)
        .order_by(AnalysisRun.completed_at.desc().nullsfirst(), AnalysisRun.started_at.desc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        AnalysisRunSummaryOut(
            id=run.id,
            status=run.status,
            failure_reason=run.failure_reason,
            started_at=run.started_at,
            completed_at=run.completed_at,
            asset_name=asset_name,
            asset_modality=asset_modality,
            score=score,
            verdict=verdict,
        )
        for run, asset_name, asset_modality, score, verdict in rows
    ]

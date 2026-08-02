"""Analysis endpoints (Phase 0 §3.11, Phase 3, Phase 4, PRD §11.2)."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.analysis_decision import execution_progress
from src.analysis_decision.domain.models import AnalysisRun, AnalysisRunStatus
from src.analysis_decision.repository import (
    AnalysisRunRepository,
    EvidenceRepository,
    RecommendationRepository,
)
from src.api.dependencies import CurrentActor, get_current_actor
from src.brand_governance.domain.models import Brand
from src.brand_governance.repository import BrandRepository
from src.campaign_asset.domain.models import AssetModality, Campaign
from src.campaign_asset.repository import AssetRepository, AssetVersionRepository
from src.shared_kernel.db import get_session

router = APIRouter(prefix="/analysis-runs", tags=["analysis"])


class AnalysisRunCreate(BaseModel):
    asset_version_id: uuid.UUID


class AnalysisRunOut(BaseModel):
    id: uuid.UUID
    asset_version_id: uuid.UUID
    genome_version_id: uuid.UUID
    policy_version_id: uuid.UUID
    status: AnalysisRunStatus
    failure_reason: str | None
    started_at: datetime | None
    completed_at: datetime | None
    brand_id: uuid.UUID
    asset_name: str
    asset_modality: AssetModality

    class Config:
        from_attributes = True


async def _to_run_out(session, run: AnalysisRun, asset=None, brand_id: uuid.UUID | None = None) -> AnalysisRunOut:
    """`AnalysisRun` itself has no `brand_id`/asset display fields (Phase
    0 §3.11 pins only version ids) — every read path needs the same join
    back through AssetVersion -> Asset -> Campaign, so it lives here once."""
    if asset is None:
        asset_version = await AssetVersionRepository(session).get_by_id(run.asset_version_id)
        asset = await AssetRepository(session).get_by_id(asset_version.asset_id)
    if brand_id is None:
        campaign = await session.get(Campaign, asset.campaign_id)
        brand_id = campaign.brand_id
    return AnalysisRunOut(
        id=run.id,
        asset_version_id=run.asset_version_id,
        genome_version_id=run.genome_version_id,
        policy_version_id=run.policy_version_id,
        status=run.status,
        failure_reason=run.failure_reason,
        started_at=run.started_at,
        completed_at=run.completed_at,
        brand_id=brand_id,
        asset_name=asset.name,
        asset_modality=asset.modality,
    )


@router.post("", response_model=AnalysisRunOut, status_code=201)
async def trigger_analysis(
    body: AnalysisRunCreate,
    actor: CurrentActor = Depends(get_current_actor),
    session=Depends(get_session),
):
    """PRD §11.2, Phase 4 §1. Creates the AnalysisRun in `queued` and
    dispatches it to the Celery-backed execution runtime
    (`workers/tasks.py`) — the request never itself waits for
    Applicability/Planning/Worker Execution/Decision to run; the caller
    polls `GET /{run_id}` (coarse status) or `GET /{run_id}/progress`
    (Phase 4 §11's real-time Work Unit visibility) instead."""
    asset_version_repo = AssetVersionRepository(session)
    asset_repo = AssetRepository(session)
    asset_version = await asset_version_repo.get_by_id(body.asset_version_id)
    if asset_version is None or asset_version.org_id != actor.org_id:
        raise HTTPException(status_code=404, detail="AssetVersion not found.")
    asset = await asset_repo.get_by_id(asset_version.asset_id)

    brand_repo = BrandRepository(session)
    campaign = await session.get(Campaign, asset.campaign_id)
    brand: Brand | None = await brand_repo.get_by_id(campaign.brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found.")

    if brand.active_genome_version_id is None or brand.active_policy_version_id is None:
        # Pre-Phase-7 correction 4: content evaluation is unavailable
        # until both a Genome and a Policy are active for this Brand.
        raise HTTPException(
            status_code=422,
            detail="This Brand has no active Genome and/or Policy — activate both before submitting content for analysis.",
        )

    run = AnalysisRun(
        org_id=actor.org_id,
        asset_version_id=asset_version.id,
        genome_version_id=brand.active_genome_version_id,
        policy_version_id=brand.active_policy_version_id,
        status=AnalysisRunStatus.QUEUED,
    )
    run_repo = AnalysisRunRepository(session)
    await run_repo.add(run)
    await session.commit()

    from workers.tasks import dispatch_analysis_run

    dispatch_analysis_run.delay(str(run.id), str(actor.org_id))

    return await _to_run_out(session, run, asset=asset, brand_id=brand.id)


@router.get("/{run_id}/progress")
async def get_analysis_progress(
    run_id: uuid.UUID, actor: CurrentActor = Depends(get_current_actor), session=Depends(get_session)
):
    """Phase 4 §11: real-time Work Unit state + coarse AnalysisRun-level
    progress, for the frontend's Live Analysis Progress view."""
    run = await AnalysisRunRepository(session).get_by_id(run_id)
    if run is None or run.org_id != actor.org_id:
        raise HTTPException(status_code=404, detail="AnalysisRun not found.")
    progress = execution_progress.get_progress(run_id)
    return {"run_status": run.status.value, **progress}


@router.get("/{run_id}", response_model=AnalysisRunOut)
async def get_analysis_run(
    run_id: uuid.UUID, actor: CurrentActor = Depends(get_current_actor), session=Depends(get_session)
):
    run = await AnalysisRunRepository(session).get_by_id(run_id)
    if run is None or run.org_id != actor.org_id:
        raise HTTPException(status_code=404, detail="AnalysisRun not found.")
    return await _to_run_out(session, run)


@router.get("/{run_id}/evidence")
async def list_evidence(run_id: uuid.UUID, actor: CurrentActor = Depends(get_current_actor), session=Depends(get_session)):
    """Evidence Explorer's data source (deliverable §18 of the frontend request)."""
    evidence = await EvidenceRepository(session).list_for_run(run_id)
    return [
        {
            "id": str(e.id),
            "assertion_id": str(e.assertion_id),
            "alignment_indicator": e.alignment_indicator.value,
            "confidence": e.confidence,
            "observed_characteristic": e.observed_characteristic,
            "source_observation_ids": e.source_observation_ids,
        }
        for e in evidence
    ]


@router.get("/{run_id}/recommendations")
async def list_recommendations(
    run_id: uuid.UUID, actor: CurrentActor = Depends(get_current_actor), session=Depends(get_session)
):
    recs = await RecommendationRepository(session).list_for_run(run_id)
    return [
        {
            "id": str(r.id),
            "component_id": str(r.component_id),
            "text": r.text,
            "priority": r.priority,
            "related_evidence_ids": r.related_evidence_ids,
        }
        for r in recs
    ]

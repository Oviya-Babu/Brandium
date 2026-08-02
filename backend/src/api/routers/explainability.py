"""Explainability endpoint (Phase 2 §7, CLAUDE.md §1.7 — "never more than
one click away from the evidence")."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from src.analysis_decision.domain.models import AnalysisRunStatus
from src.analysis_decision.explainability_service import ExplainabilityService
from src.analysis_decision.repository import AnalysisRunRepository, EvidenceRepository
from src.api.dependencies import CurrentActor, get_current_actor
from src.brand_governance.repository import BrandGenomeRepository, PolicyRepository
from src.campaign_asset.repository import AssetRepository, AssetVersionRepository, CampaignRepository
from src.shared_kernel.db import get_session

router = APIRouter(prefix="/analysis-runs/{run_id}/explainability", tags=["explainability"])


@router.get("")
async def get_explainability(
    run_id: uuid.UUID, actor: CurrentActor = Depends(get_current_actor), session=Depends(get_session)
):
    """`ExplainabilityService.reconstruct` independently re-derives a
    full score/verdict from whatever Evidence exists — it has no notion
    of Completeness Verification and doesn't consult the persisted
    Decision row, so calling it for a run that never reached `complete`
    silently fabricates a plausible-looking chain from partial coverage
    exactly the coverage Completeness Verification rejected as
    insufficient (confirmed live: a `failed` run with only 4 of 7
    required assertions judged still produced a "Compliant, 75.0"
    chain). Guarding here, at the request boundary, is cheaper and
    safer than changing `reconstruct`'s own recomputation semantics."""
    run = await AnalysisRunRepository(session).get_by_id(run_id)
    if run is None or run.org_id != actor.org_id:
        raise HTTPException(status_code=404, detail="AnalysisRun not found.")
    if run.status != AnalysisRunStatus.COMPLETE:
        raise HTTPException(
            status_code=422,
            detail=f"AnalysisRun {run_id} is '{run.status.value}', not 'complete' — no explainability chain to reconstruct.",
        )
    service = ExplainabilityService(
        AnalysisRunRepository(session),
        EvidenceRepository(session),
        BrandGenomeRepository(session),
        PolicyRepository(session),
        AssetRepository(session),
        AssetVersionRepository(session),
        CampaignRepository(session),
    )
    return await service.reconstruct(run_id)

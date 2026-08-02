"""Brand Genome endpoints (Phase 0 §3.6, Phase 1 §5/§10, DR-006/INV-15)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.dependencies import CurrentActor, get_current_actor, get_llm_client
from src.brand_governance import genome_compilation_progress
from src.brand_governance.domain.models import GenomeStatus
from src.brand_governance.genome_service import GenomeActivationError, GenomeService, GenomeValidationError
from src.brand_governance.repository import BrandGenomeRepository, BrandHistoryRepository, BrandRepository
from src.identity_access.authorization import has_role
from src.identity_access.domain.enums import Role, ScopeTier
from src.platform_governance.audit_service import AuditService
from src.platform_governance.repository import AuditLogRepository
from src.shared_kernel.db import get_session
from src.shared_kernel.llm.client import LLMClient

router = APIRouter(prefix="/brands/{brand_id}/genomes", tags=["genomes"])


class GenomeOut(BaseModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    version_number: int
    status: GenomeStatus
    activated_by: uuid.UUID | None

    class Config:
        from_attributes = True


def _service(session, llm: LLMClient) -> GenomeService:
    return GenomeService(
        BrandGenomeRepository(session),
        BrandRepository(session),
        BrandHistoryRepository(session),
        AuditService(AuditLogRepository(session)),
        llm,
        session,
    )


async def _require_brand_administrator(actor: CurrentActor, brand_id: uuid.UUID) -> None:
    if not has_role(actor.authorization, actor.org_id, ScopeTier.BRAND, brand_id, Role.BRAND_ADMINISTRATOR):
        raise HTTPException(status_code=403, detail="Requires BrandAdministrator at this Brand's scope.")


class GenomeCompileStatusOut(BaseModel):
    stage: str
    error: str | None = None
    genome: GenomeOut | None = None


@router.post("", status_code=202)
async def compile_genome_draft(
    brand_id: uuid.UUID,
    actor: CurrentActor = Depends(get_current_actor),
):
    """Phase 1 §5 steps 1-4 — compiles every BrandHistory item ingested
    so far for this Brand into a new draft Genome version.

    Dispatched to the Celery-backed execution runtime
    (`workers/tasks.py::compile_genome_draft_task`), mirroring
    `POST /analysis-runs`'s async pattern, rather than blocking the
    request on however many sequential LLM calls compilation needs —
    that used to run inline here and is exactly what "Compiling Genome
    Draft" hanging was (one blocking Ollama call per ingested
    BrandHistory item, no client-side timeout). The caller polls
    `GET /brands/{brand_id}/genomes/compile-status/{job_id}` instead."""
    await _require_brand_administrator(actor, brand_id)

    job_id = uuid.uuid4()
    from workers.tasks import compile_genome_draft_task

    compile_genome_draft_task.delay(str(job_id), str(brand_id), str(actor.org_id), str(actor.user_id))
    return {"job_id": str(job_id)}


@router.get("/compile-status/{job_id}", response_model=GenomeCompileStatusOut)
async def get_genome_compile_status(
    brand_id: uuid.UUID,
    job_id: uuid.UUID,
    actor: CurrentActor = Depends(get_current_actor),
    session=Depends(get_session),
    llm: LLMClient = Depends(get_llm_client),
):
    progress = genome_compilation_progress.get_progress(job_id)
    genome = None
    if progress["stage"] == "complete" and progress.get("genome_id"):
        service = _service(session, llm)
        found = await service.get_genome(uuid.UUID(progress["genome_id"]))
        if found is not None and found.brand_id == brand_id:
            genome = found
    return GenomeCompileStatusOut(stage=progress["stage"], error=progress.get("error"), genome=genome)


@router.post("/{genome_id}/submit-for-review", response_model=GenomeOut)
async def submit_genome_for_review(
    brand_id: uuid.UUID,
    genome_id: uuid.UUID,
    actor: CurrentActor = Depends(get_current_actor),
    session=Depends(get_session),
    llm: LLMClient = Depends(get_llm_client),
):
    await _require_brand_administrator(actor, brand_id)
    service = _service(session, llm)
    genome = await service.get_genome(genome_id)
    if genome is None or genome.brand_id != brand_id:
        raise HTTPException(status_code=404, detail="Genome not found.")
    categories, components, assertions = await service.load_full_tree(genome_id)
    try:
        await service.submit_for_review(
            genome=genome, categories=categories, components=components, assertions=assertions, actor_id=actor.user_id
        )
    except GenomeValidationError as exc:
        raise HTTPException(status_code=422, detail={"errors": exc.errors}) from exc
    await session.commit()
    return genome


@router.post("/{genome_id}/activate", response_model=GenomeOut)
async def activate_genome(
    brand_id: uuid.UUID,
    genome_id: uuid.UUID,
    actor: CurrentActor = Depends(get_current_actor),
    session=Depends(get_session),
    llm: LLMClient = Depends(get_llm_client),
):
    """DR-006/INV-15: `activated_by` becomes non-null exactly here, via
    an authenticated User (never InternalOperator, never automatic)."""
    await _require_brand_administrator(actor, brand_id)
    service = _service(session, llm)
    genome = await service.get_genome(genome_id)
    if genome is None or genome.brand_id != brand_id:
        raise HTTPException(status_code=404, detail="Genome not found.")
    try:
        await service.activate(genome=genome, actor_id=actor.user_id)
    except GenomeActivationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await session.commit()
    return genome


@router.get("/{genome_id}/tree")
async def get_genome_tree(
    brand_id: uuid.UUID,
    genome_id: uuid.UUID,
    actor: CurrentActor = Depends(get_current_actor),
    session=Depends(get_session),
    llm: LLMClient = Depends(get_llm_client),
):
    service = _service(session, llm)
    return await service.get_tree(genome_id)


@router.get("/compare")
async def compare_genomes(
    brand_id: uuid.UUID,
    from_genome_id: uuid.UUID,
    to_genome_id: uuid.UUID,
    actor: CurrentActor = Depends(get_current_actor),
    session=Depends(get_session),
    llm: LLMClient = Depends(get_llm_client),
):
    """Phase 1 §9: derived diff, never stored."""
    service = _service(session, llm)
    return await service.compare(from_genome_id, to_genome_id)

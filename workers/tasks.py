"""Celery task implementations — the Phase 4 execution runtime that
actually carries an AnalysisRun through `running` (§1/§3).

Replaces the previous pass's synchronous in-request execution
(`AnalysisOrchestrator.execute`, called directly from the API): the API
now only creates the `queued` AnalysisRun row and calls
`dispatch_analysis_run.delay(...)` — every remaining stage runs inside a
Celery worker process. Business logic itself still lives in
`src.analysis_decision.analysis_orchestrator` (`plan_run` /
`execute_work_unit` / `finalize_run`); this module is only the
session/retry/progress plumbing Phase 4 calls the Orchestrator's
"platform orchestration responsibilities" (§3) — deliberately thin, so
Celery is never something `src.*` needs to import.

Each task opens its own database session and sets the per-transaction
tenant context (`shared_kernel/tenant_context.py`) exactly like the
FastAPI request path does — Postgres RLS (Phase 0 §6) is enforced
identically whether a query originates from the API process or a worker
process. `org_id` is passed into every task explicitly by the caller
(the API, which already has it from the authenticated actor) rather than
looked up from the AnalysisRun row first — an AnalysisRun is itself a
tenant-scoped, RLS-protected row, so it cannot be the thing that tells a
worker which tenant context to set before querying it.
"""
from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from celery.exceptions import SoftTimeLimitExceeded
from celery import chord
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Import-for-registration-side-effect, not for any name used directly:
# every tenant-scoped table has a `ForeignKey("organizations.id")` (via
# TenantScopedMixin's convention), and SQLAlchemy can't resolve that
# cross-bounded-context FK during flush unless `identity_access.domain.models`
# (where `organizations` is mapped) has actually been imported somewhere
# in this process — the API process gets this for free because
# `uvicorn src.main:app` transitively imports every router, and every
# router imports its bounded context's domain models. A Celery worker
# process has no such entrypoint of its own, so without this import the
# first flush touching any tenant-scoped table raises
# `NoReferencedTableError` for `organizations` (observed: `analysis_runs`).
# `src.main` is the one module already guaranteed to import all of them.
import src.main  # noqa: F401,E402

from src.analysis_decision import execution_progress
from src.analysis_decision.analysis_orchestrator import (
    RunPlan,
    WorkUnitOutcome,
    execute_work_unit,
    finalize_run,
    plan_run,
)
from src.analysis_decision.domain.models import AnalysisRunStatus
from src.analysis_decision.planning import WorkerType, WorkUnit
from src.analysis_decision.repository import (
    AnalysisRunRepository,
    AssertionOutcomeRepository,
    DecisionRepository,
    EvidenceRepository,
    ObservationRepository,
    RecommendationRepository,
)
from src.brand_governance import genome_compilation_progress
from src.brand_governance.genome_service import GenomeService
from src.brand_governance.repository import (
    BrandGenomeRepository,
    BrandHistoryRepository,
    BrandRepository,
    PolicyRepository,
)
from src.campaign_asset.repository import AssetRepository, AssetVersionRepository
from src.logging import configure_logging, get_logger
from src.platform_governance.audit_service import AuditService
from src.platform_governance.repository import AuditLogRepository
from src.reporting.report_service import ReportService
from src.reporting.repository import ReportRepository
from src.config import get_settings
from src.shared_kernel.llm.client import LLMClient
from src.shared_kernel.object_storage import ObjectStorageClient
from src.shared_kernel.tenant_context import set_tenant_context

from workers.celery_app import app

configure_logging()
logger = get_logger(__name__)

_MAX_RETRIES = 2
# CPU-only qwen3:4b decodes at ~7 tok/s (measured live). A Work Unit
# batches every applicable Assertion for one worker type into a single
# LLM call (`planning.py`'s `build_execution_plan` — one ImageWorker
# call covers all in-scope Visual Identity assertions at once), so this
# budget has to cover the largest real batch, not a typical one. 120s
# was tuned against a single-assertion call and cut off a 7-assertion
# batch mid-generation; 300s was then tuned against that 7-assertion
# batch but still cut off a real 30-assertion Visual Identity batch
# (Red Bull's compiled Genome) mid-generation, confirmed live: it hit
# the soft limit at exactly 300.0s. Sized here for that batch size with
# headroom, not just the smallest brand tested so far.
_SOFT_TIME_LIMIT = 900
_TIME_LIMIT = 930


@asynccontextmanager
async def _tenant_session(org_id: uuid.UUID):
    # Deliberately not `shared_kernel.db.get_session_factory()` — that
    # engine is a process-lifetime singleton, correct for the FastAPI
    # app's one long-lived event loop, but wrong here: every Celery task
    # body runs inside its own `asyncio.run()` call, which tears down
    # its event loop when the task returns. A cached engine's pooled
    # asyncpg connections stay bound to whichever loop first created
    # them, so a second task in the same forked worker process reusing
    # that engine fails with "attached to a different loop" / "Event
    # loop is closed" (confirmed live: this is exactly the error a
    # `finalize_analysis_run` task hit after `execute_work_unit_task`
    # had already used the shared engine in the same worker process).
    # A fresh engine per task, disposed on exit, keeps it scoped to the
    # event loop that's actually running.
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    try:
        session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with session_factory() as session:
            await set_tenant_context(session, org_id)
            yield session
    finally:
        await engine.dispose()


async def _load_run_context(session, run_id: uuid.UUID):
    run = await AnalysisRunRepository(session).get_by_id(run_id)
    asset_version = await AssetVersionRepository(session).get_by_id(run.asset_version_id)
    asset = await AssetRepository(session).get_by_id(asset_version.asset_id)
    return run, asset, asset_version


# ---------------------------------------------------------------------
# Stage 1+2: dispatch — Applicability Determination + Planning, then
# release every Work Unit for execution (Phase 4 §3 steps 1-3).
# ---------------------------------------------------------------------


@app.task(name="workers.tasks.dispatch_analysis_run")
def dispatch_analysis_run(run_id: str, org_id: str) -> None:
    asyncio.run(_dispatch_analysis_run_async(run_id, org_id))


async def _dispatch_analysis_run_async(run_id: str, org_id: str) -> None:
    run_uuid = uuid.UUID(run_id)
    org_uuid = uuid.UUID(org_id)

    async with _tenant_session(org_uuid) as session:
        run, asset, asset_version = await _load_run_context(session, run_uuid)

        run.status = AnalysisRunStatus.RUNNING
        run.started_at = datetime.now(timezone.utc)
        await session.commit()

        execution_progress.set_stage(run_uuid, "applicability")
        genome_repo = BrandGenomeRepository(session)
        plan: RunPlan = await plan_run(genome_repo, run, asset, asset_version)
        execution_progress.set_stage(run_uuid, "planning")

    work_unit_payloads = [
        {
            "work_unit_id": str(index),
            "worker_type": wu.worker_type.value,
            "assertion_ids": [str(a) for a in wu.assertion_ids],
        }
        for index, wu in enumerate(plan.work_units)
    ]
    execution_progress.init_work_units(run_uuid, work_unit_payloads)

    if not work_unit_payloads:
        # Nothing in-scope needed a worker at all for this modality — the
        # run still must reach a terminal state via Completeness
        # Verification rather than staying `running` forever.
        finalize_analysis_run.delay([], run_id, org_id)
        return

    execution_progress.set_stage(run_uuid, "worker_execution")
    header = [execute_work_unit_task.s(run_id, org_id, payload) for payload in work_unit_payloads]
    chord(header)(finalize_analysis_run.s(run_id, org_id))


# ---------------------------------------------------------------------
# Stage 3: Worker Execution — one Work Unit's full Invocation ->
# Attempt -> Resolution -> Handoff lifecycle (Phase 4 §4).
# ---------------------------------------------------------------------


@app.task(
    bind=True,
    name="workers.tasks.execute_work_unit_task",
    max_retries=_MAX_RETRIES,
    soft_time_limit=_SOFT_TIME_LIMIT,
    time_limit=_TIME_LIMIT,
)
def execute_work_unit_task(self, run_id: str, org_id: str, work_unit_payload: dict) -> dict:
    """Phase 4 §6: bounded retry on transient failures. `failed` /
    `timed_out` are legitimate terminal Work Unit states (Phase 4 §2),
    recorded here and returned normally rather than raised through the
    chord — Completeness Verification (Phase 3 §6), not Celery's own
    failure handling, is what's entitled to decide whether a Work Unit
    failure fails the whole AnalysisRun."""
    run_uuid = uuid.UUID(run_id)
    work_unit_id = work_unit_payload["work_unit_id"]
    execution_progress.set_work_unit_state(run_uuid, work_unit_id, "executing")

    try:
        return asyncio.run(_execute_work_unit_async(run_id, org_id, work_unit_payload))
    except SoftTimeLimitExceeded:
        logger.warning("work_unit.timed_out", run_id=run_id, work_unit_id=work_unit_id)
        execution_progress.set_work_unit_state(run_uuid, work_unit_id, "timed_out")
        return {**work_unit_payload, "outcome": "timed_out", "no_signal_assertion_ids": []}
    except Exception as exc:  # noqa: BLE001 — deliberately broad: any worker-side failure is a Work Unit failure, not a task crash to surface elsewhere
        if self.request.retries < self.max_retries:
            execution_progress.set_work_unit_state(run_uuid, work_unit_id, "assigned")
            raise self.retry(exc=exc, countdown=2**self.request.retries) from exc
        logger.error("work_unit.failed", run_id=run_id, work_unit_id=work_unit_id, error=str(exc))
        execution_progress.set_work_unit_state(run_uuid, work_unit_id, "failed")
        return {**work_unit_payload, "outcome": "failed", "no_signal_assertion_ids": []}


async def _execute_work_unit_async(run_id: str, org_id: str, work_unit_payload: dict) -> dict:
    run_uuid = uuid.UUID(run_id)
    org_uuid = uuid.UUID(org_id)
    work_unit = WorkUnit(
        worker_type=WorkerType(work_unit_payload["worker_type"]),
        assertion_ids=[uuid.UUID(a) for a in work_unit_payload["assertion_ids"]],
    )

    async with _tenant_session(org_uuid) as session:
        run, asset, asset_version = await _load_run_context(session, run_uuid)

        genome_repo = BrandGenomeRepository(session)
        assertions = await genome_repo.get_assertions_by_ids(work_unit.assertion_ids)
        assertion_by_id = {a.id: a for a in assertions}

        storage = ObjectStorageClient()
        content = storage.get_object(asset_version.storage_ref)
        llm = LLMClient()

        outcome: WorkUnitOutcome = await execute_work_unit(
            ObservationRepository(session),
            run,
            work_unit_payload["work_unit_id"],
            work_unit,
            assertion_by_id,
            content,
            llm,
        )
        await session.commit()

    execution_progress.set_work_unit_state(
        run_uuid, outcome.work_unit_id, "succeeded" if outcome.outcome == "succeeded" else "failed"
    )
    return {
        "work_unit_id": outcome.work_unit_id,
        "worker_type": outcome.worker_type,
        "assertion_ids": outcome.assertion_ids,
        "outcome": outcome.outcome,
        "no_signal_assertion_ids": outcome.no_signal_assertion_ids,
    }


# ---------------------------------------------------------------------
# Stage 4+5 + Decision Engine handoff — the Celery chord callback,
# guaranteed to run only once every dispatched Work Unit has reached a
# terminal state (Phase 4 §3 step 6).
# ---------------------------------------------------------------------


@app.task(name="workers.tasks.finalize_analysis_run")
def finalize_analysis_run(work_unit_outcomes: list[dict], run_id: str, org_id: str) -> None:
    try:
        asyncio.run(_finalize_analysis_run_async(work_unit_outcomes, run_id, org_id))
    except Exception as exc:  # noqa: BLE001 - deliberately broad: this is the terminal
        # step of the pipeline (Phase 4 §3 step 6) — an unhandled exception here
        # previously left the AnalysisRun stuck in `running` forever (confirmed
        # live: a Decision Engine handoff bug left a run spinning with no
        # failure_reason and no way for the frontend to ever stop polling it).
        # Same fail-safe shape as `compile_genome_draft_task`'s broad catch.
        logger.error("analysis.finalize.failed", run_id=run_id, error=str(exc))
        asyncio.run(_mark_run_failed(run_id, org_id, str(exc)))


async def _mark_run_failed(run_id: str, org_id: str, error: str) -> None:
    run_uuid = uuid.UUID(run_id)
    async with _tenant_session(uuid.UUID(org_id)) as session:
        run = await AnalysisRunRepository(session).get_by_id(run_uuid)
        if run is not None and run.status != AnalysisRunStatus.COMPLETE:
            run.status = AnalysisRunStatus.FAILED
            run.failure_reason = f"Internal error during finalization: {error}"[:500]
            run.completed_at = datetime.now(timezone.utc)
            await session.commit()
    execution_progress.set_stage(run_uuid, "failed")


async def _finalize_analysis_run_async(work_unit_outcomes: list[dict], run_id: str, org_id: str) -> None:
    run_uuid = uuid.UUID(run_id)
    org_uuid = uuid.UUID(org_id)

    outcomes = [
        WorkUnitOutcome(
            work_unit_id=o["work_unit_id"],
            worker_type=o["worker_type"],
            assertion_ids=o["assertion_ids"],
            outcome=o["outcome"],
            no_signal_assertion_ids=o.get("no_signal_assertion_ids", []),
        )
        for o in work_unit_outcomes
    ]

    async with _tenant_session(org_uuid) as session:
        run, asset, asset_version = await _load_run_context(session, run_uuid)

        genome_repo = BrandGenomeRepository(session)
        # Phase 4 §9: the Applicability Set/Execution Plan are derived and
        # reproducible — re-deriving them here rather than serializing
        # ORM objects across the Celery boundary is the architecture-
        # sanctioned choice, not a workaround.
        plan: RunPlan = await plan_run(genome_repo, run, asset, asset_version)

        run = await finalize_run(
            AnalysisRunRepository(session),
            ObservationRepository(session),
            EvidenceRepository(session),
            AssertionOutcomeRepository(session),
            DecisionRepository(session),
            RecommendationRepository(session),
            PolicyRepository(session),
            run,
            plan.applicable_set,
            outcomes,
            LLMClient(),
            on_stage=lambda stage: execution_progress.set_stage(run_uuid, stage),
        )

        if run.status == AnalysisRunStatus.COMPLETE:
            decision = await DecisionRepository(session).get_for_run(run.id)
            if decision is not None:
                await ReportService(ReportRepository(session)).generate(
                    org_id=org_uuid, analysis_run_id=run.id, decision_id=decision.id
                )
            execution_progress.set_stage(run_uuid, "report_ready")
            execution_progress.set_stage(run_uuid, "complete")
        else:
            execution_progress.set_stage(run_uuid, "failed")

        await session.commit()


# ---------------------------------------------------------------------
# Genome compilation — same async-dispatch-and-poll shape as AnalysisRun
# above, sized for a much simpler workflow (one job, no Work Units, no
# chord). Replaces `POST /brands/{brand_id}/genomes` running
# `GenomeService.create_draft()` synchronously in the HTTP request, which
# is what "Compiling Genome Draft" hanging actually was: one blocking
# Ollama call per ingested BrandHistory item, in one HTTP request, with
# no client-side timeout at all.
# ---------------------------------------------------------------------


@app.task(name="workers.tasks.compile_genome_draft_task")
def compile_genome_draft_task(job_id: str, brand_id: str, org_id: str, actor_id: str) -> None:
    asyncio.run(_compile_genome_draft_async(job_id, brand_id, org_id, actor_id))


async def _compile_genome_draft_async(job_id: str, brand_id: str, org_id: str, actor_id: str) -> None:
    job_uuid = uuid.UUID(job_id)
    org_uuid = uuid.UUID(org_id)

    try:
        async with _tenant_session(org_uuid) as session:
            genome_service = GenomeService(
                BrandGenomeRepository(session),
                BrandRepository(session),
                BrandHistoryRepository(session),
                AuditService(AuditLogRepository(session)),
                LLMClient(),
                session,
            )
            genome, *_ = await genome_service.create_draft(
                org_id=org_uuid,
                brand_id=uuid.UUID(brand_id),
                actor_id=uuid.UUID(actor_id),
                on_stage=lambda stage: genome_compilation_progress.set_stage(job_uuid, stage),
            )
            await session.commit()
        genome_compilation_progress.set_stage(job_uuid, "complete", genome_id=genome.id)
    except Exception as exc:  # noqa: BLE001 - deliberately broad: any compilation failure must
        # resolve the polled job to `failed` with a message, never leave
        # it stuck at its last stage forever — same rationale as
        # `execute_work_unit_task`'s broad catch above.
        logger.error("genome.compile.failed", job_id=job_id, brand_id=brand_id, error=str(exc))
        genome_compilation_progress.set_stage(job_uuid, "failed", error=str(exc))

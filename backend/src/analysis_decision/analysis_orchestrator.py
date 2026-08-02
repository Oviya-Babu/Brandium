"""AnalysisRun orchestration (Phase 4 §1/§3).

Split into three stage functions — `plan_run`, `execute_work_unit`,
`finalize_run` — so the Celery-backed execution runtime
(`analysis_decision/tasks.py`, Phase 4) can invoke each across separate
task boundaries instead of one long synchronous call. This module still
owns *what* each stage does; `tasks.py` owns only session/retry/progress
plumbing around them (thin task, business logic here — the same split
already used for the API routers).

None of these functions decide business outcomes themselves — they
apply rules Phase 2/3 already define (Phase 4 §3: "The Orchestrator does
not itself decide business outcomes"). The Decision Engine, Completeness
Verification, and Evidence Fusion this module calls into remain exactly
the already-frozen, already-verified modules from the previous pass.
"""
from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.analysis_decision.applicability import EvaluationContext, resolve_applicability
from src.analysis_decision.applicability import ApplicableSet
from src.analysis_decision.completeness_verification import OutcomeType, verify_completeness
from src.analysis_decision.decision_engine.engine import compute_decision
from src.analysis_decision.decision_engine.policy_schema import policy_rules_from_json
from src.analysis_decision.decision_engine.schemas import AlignmentIndicator as EngineAlignment
from src.analysis_decision.decision_engine.schemas import EvidenceItem
from src.analysis_decision.domain.models import (
    AnalysisRun,
    AnalysisRunStatus,
    AssertionOutcome,
    AssertionOutcomeType,
    Decision,
    Evidence,
    Observation,
    Recommendation,
)
from src.analysis_decision.evidence_fusion import RawObservation, fuse
from src.analysis_decision.genome_tree_builder import build_genome_tree
from src.analysis_decision.planning import WorkerType, WorkUnit, build_execution_plan
from src.analysis_decision.recommendation_narration import narrate_recommendation
from src.analysis_decision.repository import (
    AnalysisRunRepository,
    AssertionOutcomeRepository,
    DecisionRepository,
    EvidenceRepository,
    ObservationRepository,
    RecommendationRepository,
)
from src.analysis_decision.workers.base import WorkerResult
from src.analysis_decision.workers.image_worker import run_image_worker
from src.analysis_decision.workers.text_worker import run_text_worker
from src.brand_governance.domain.models import Assertion
from src.brand_governance.repository import BrandGenomeRepository, PolicyRepository
from src.campaign_asset.domain.models import Asset, AssetVersion
from src.logging import get_logger
from src.shared_kernel.llm.client import LLMClient
from src.shared_kernel.object_storage import ObjectStorageClient

logger = get_logger(__name__)

_OUTCOME_TYPE_MAP = {
    OutcomeType.EVIDENCE: AssertionOutcomeType.EVIDENCE,
    OutcomeType.ATTEMPTED_NO_SIGNAL: AssertionOutcomeType.ATTEMPTED_NO_SIGNAL,
    OutcomeType.WORKER_FAILURE: AssertionOutcomeType.WORKER_FAILURE,
    OutcomeType.NOT_APPLICABLE: AssertionOutcomeType.NOT_APPLICABLE,
}


@dataclass(frozen=True)
class RunPlan:
    """Stage 1+2 output — the derived, reproducible (Phase 4 §9)
    Applicability Set and Execution Plan for one AnalysisRun."""

    applicable_set: ApplicableSet
    work_units: list[WorkUnit]
    assertion_by_id: dict[uuid.UUID, Assertion]


async def plan_run(genome_repo: BrandGenomeRepository, run: AnalysisRun, asset: Asset, asset_version: AssetVersion) -> RunPlan:
    """Stage 1: Applicability Determination (Phase 3 §2) + Stage 2:
    Planning (Phase 3 §3). Pure with respect to the database beyond
    reading the pinned Genome version — never mutates anything."""
    categories = await genome_repo.get_categories(run.genome_version_id)
    components_by_category: dict = {}
    assertions_by_component: dict = {}
    assertion_by_id: dict[uuid.UUID, Assertion] = {}
    for category in categories:
        components = await genome_repo.get_components(category.id)
        components_by_category[category.id] = components
        for component in components:
            assertions = await genome_repo.get_assertions(component.id)
            assertions_by_component[component.id] = assertions
            for a in assertions:
                assertion_by_id[a.id] = a

    context = EvaluationContext(modality=asset.modality.value, context_tags=asset_version.context_tags or [])
    applicable_set = resolve_applicability(categories, components_by_category, assertions_by_component, context)
    plan = build_execution_plan(applicable_set, asset.modality)

    return RunPlan(applicable_set=applicable_set, work_units=plan, assertion_by_id=assertion_by_id)


@dataclass(frozen=True)
class WorkUnitOutcome:
    """Phase 4 §2's Work Unit terminal outcome, in a form serializable
    across a Celery chord boundary (`tasks.py`) — everything downstream
    (`finalize_run`) needs to reconstruct Completeness Verification's
    inputs without re-touching a worker or the database it wrote to."""

    work_unit_id: str
    worker_type: str
    assertion_ids: list[str]
    outcome: str  # "succeeded" | "failed" | "timed_out"
    no_signal_assertion_ids: list[str] = field(default_factory=list)


async def execute_work_unit(
    observation_repo: ObservationRepository,
    run: AnalysisRun,
    work_unit_id: str,
    work_unit: WorkUnit,
    assertion_by_id: dict[uuid.UUID, Assertion],
    content: bytes,
    llm: LLMClient,
) -> WorkUnitOutcome:
    """Stage 3: Worker Execution (Phase 3 §3/§4, Phase 4 §4) for exactly
    one Work Unit. Persists its Observations (Phase 0 §3.12) as it goes —
    the durable record survives even if a later Work Unit or the
    finalize stage fails."""
    assertions = [assertion_by_id[aid] for aid in work_unit.assertion_ids]
    assertion_id_strs = [str(aid) for aid in work_unit.assertion_ids]

    if work_unit.worker_type == WorkerType.TEXT_WORKER:
        result: WorkerResult = await run_text_worker(
            asset_text=content.decode("utf-8", errors="replace"), assertions=assertions, llm=llm
        )
    else:
        result = await run_image_worker(image_bytes=content, assertions=assertions, llm=llm)

    if not result.succeeded:
        return WorkUnitOutcome(
            work_unit_id=work_unit_id,
            worker_type=work_unit.worker_type.value,
            assertion_ids=assertion_id_strs,
            outcome="failed",
        )

    for judgment in result.judgments:
        obs = Observation(
            org_id=run.org_id,
            analysis_run_id=run.id,
            assertion_id=uuid.UUID(judgment.assertion_id),
            worker_type=work_unit.worker_type.value,
            raw_output=judgment.model_dump(),
            confidence=judgment.confidence,
        )
        await observation_repo.add(obs)

    return WorkUnitOutcome(
        work_unit_id=work_unit_id,
        worker_type=work_unit.worker_type.value,
        assertion_ids=assertion_id_strs,
        outcome="succeeded",
        no_signal_assertion_ids=[str(aid) for aid in result.no_signal_assertion_ids],
    )


async def finalize_run(
    run_repo: AnalysisRunRepository,
    observation_repo: ObservationRepository,
    evidence_repo: EvidenceRepository,
    outcome_repo: AssertionOutcomeRepository,
    decision_repo: DecisionRepository,
    recommendation_repo: RecommendationRepository,
    policy_repo: PolicyRepository,
    run: AnalysisRun,
    applicable_set: ApplicableSet,
    work_unit_outcomes: list[WorkUnitOutcome],
    llm: LLMClient,
    on_stage: Callable[[str], None] | None = None,
) -> AnalysisRun:
    """Stage 4: Evidence Normalization & Fusion (Phase 3 §5) through
    Stage 5: Completeness Verification (Phase 3 §6), then handoff to the
    (already frozen, already verified) Decision Engine and Recommendation
    generation. Runs once, after every dispatched Work Unit has reached a
    terminal state (Phase 4 §3 step 6) — the Celery chord callback in
    `tasks.py` is what guarantees that ordering.

    `on_stage`, if given, is called with a `execution_progress.PipelineStage`
    name at each sub-stage boundary — kept as a plain callback rather than
    importing `execution_progress` directly here so this module (and the
    Decision Engine handoff it performs) stays free of any infra-layer
    dependency; `tasks.py` is the only caller that knows Celery/Redis exist.
    """

    def _stage(name: str) -> None:
        if on_stage is not None:
            on_stage(name)

    no_signal_ids: set[uuid.UUID] = set()
    failed_ids: set[uuid.UUID] = set()
    for wu_outcome in work_unit_outcomes:
        if wu_outcome.outcome == "succeeded":
            no_signal_ids.update(uuid.UUID(i) for i in wu_outcome.no_signal_assertion_ids)
        else:
            failed_ids.update(uuid.UUID(i) for i in wu_outcome.assertion_ids)

    # --- Stage 4: Evidence Normalization & Fusion (Phase 3 §5) ---
    observations = await observation_repo.list_for_run(run.id)
    raw_observations = [
        RawObservation(
            id=obs.id,
            assertion_id=obs.assertion_id,
            alignment_indicator=obs.raw_output["alignment_indicator"],
            confidence=obs.confidence,
            observed_characteristic=obs.raw_output.get("observed_characteristic", ""),
        )
        for obs in observations
    ]
    fused_evidence = fuse(raw_observations)
    evidence_rows: list[Evidence] = []
    for item in fused_evidence:
        ev = Evidence(
            org_id=run.org_id,
            analysis_run_id=run.id,
            assertion_id=item.assertion_id,
            observed_characteristic={"description": item.observed_characteristic},
            alignment_indicator=item.alignment_indicator,
            confidence=item.confidence,
            source_observation_ids=[str(i) for i in item.source_observation_ids],
        )
        await evidence_repo.add(ev)
        evidence_rows.append(ev)

    # --- Stage 5: Completeness Verification (Phase 3 §6) ---
    _stage("completeness_verification")
    evidence_assertion_ids = {e.assertion_id for e in evidence_rows}
    completeness = verify_completeness(applicable_set, evidence_assertion_ids, no_signal_ids, failed_ids)

    all_applicable_assertion_ids = {
        a.id for assertions in applicable_set.assertions_by_component.values() for a in assertions
    }
    for assertion_id in all_applicable_assertion_ids:
        outcome_type = completeness.outcomes.get(assertion_id, OutcomeType.NOT_APPLICABLE)
        await outcome_repo.add(
            AssertionOutcome(
                org_id=run.org_id,
                analysis_run_id=run.id,
                assertion_id=assertion_id,
                outcome_type=_OUTCOME_TYPE_MAP[outcome_type],
                recorded_at=datetime.now(timezone.utc),
            )
        )

    if not completeness.can_complete:
        run.status = AnalysisRunStatus.FAILED
        run.failure_reason = completeness.failure_reason
        run.completed_at = datetime.now(timezone.utc)
        return run

    # --- Handoff to Decision Engine (Phase 2) ---
    _stage("decision_engine")
    policy = await policy_repo.get_by_id(run.policy_version_id)
    policy_rules = policy_rules_from_json(policy.rules or {})
    genome_tree = build_genome_tree(applicable_set)
    evidence_by_assertion: dict[uuid.UUID, list[EvidenceItem]] = {}
    for ev in evidence_rows:
        evidence_by_assertion.setdefault(ev.assertion_id, []).append(
            EvidenceItem(id=ev.id, alignment_indicator=EngineAlignment(ev.alignment_indicator.value), confidence=ev.confidence)
        )

    decision_result = compute_decision(genome_tree, evidence_by_assertion, policy_rules)

    decision = Decision(
        org_id=run.org_id,
        analysis_run_id=run.id,
        score=decision_result.score,
        verdict=decision_result.verdict.verdict,
        verdict_source=decision_result.verdict.source,
        decision_function_version=decision_result.decision_function_version,
        computed_at=datetime.now(timezone.utc),
    )
    await decision_repo.add(decision)

    # --- Recommendation Generation (Phase 2 §6) ---
    _stage("recommendation_generation")
    component_name_by_id = {
        c.id: c.name for components in applicable_set.components_by_category.values() for c in components
    }
    for triggered in decision_result.recommendations:
        evidence_descriptions = [
            ev.observed_characteristic.get("description", "")
            for ev in evidence_rows
            if ev.id in triggered.related_evidence_ids
        ]
        text = await narrate_recommendation(
            component_name=component_name_by_id.get(triggered.component_id, "this component"),
            evidence_descriptions=evidence_descriptions,
            llm=llm,
        )
        await recommendation_repo.add(
            Recommendation(
                org_id=run.org_id,
                analysis_run_id=run.id,
                component_id=triggered.component_id,
                related_evidence_ids=[str(i) for i in triggered.related_evidence_ids],
                text=text,
                priority=triggered.priority,
                generated_at=datetime.now(timezone.utc),
            )
        )

    run.status = AnalysisRunStatus.COMPLETE
    run.completed_at = datetime.now(timezone.utc)
    return run

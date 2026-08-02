"""Execution-runtime progress tracking (Phase 4 §11).

Work Units are explicitly **not** a persisted domain entity (Phase 4 §2:
"exist only for the duration of one AnalysisRun's execution... not a
stored, versioned entity in its own right" — Phase 4 §5 says the same of
the Execution Plan). Phase 4 §12 leaves the tracking *mechanism* entirely
to this layer, only requiring that Work Unit state and AnalysisRun-level
progress be inspectable in real time (§11) and that transitions be
auditable.

This module stores that transient state in Redis (Technology Stack
§8/§9 — already the Celery broker/result backend, so no new
infrastructure dependency), keyed by AnalysisRun id, with a bounded TTL.
Redis is the right store *because* it is not meant to be durable: the
authoritative, permanent record of what happened during a run is the
Observation/Evidence/AssertionOutcome rows Postgres holds afterward
(Phase 0 §3.12-3.14) — this module only answers "what is happening
right now," which is exactly what Phase 4 §2/§5 says a Work Unit and an
Execution Plan are (derived, transient, reproducible), never a second
source of truth for anything Postgres also records.

Every state write here is also logged via the platform's structured
logger so operators still get an append-only trail of transitions
(Phase 4 §11's "auditability of transitions") — the durable audit
record for the *business* event (an AnalysisRun completing or failing)
is still the AuditLogEntry the orchestration layer writes on top of
this, unaffected by this module.
"""
from __future__ import annotations

import json
import uuid
from typing import Literal

from src.config import get_settings
from src.logging import get_logger

logger = get_logger(__name__)

# Phase 4 §1's pipeline stages, expressed for real-time reporting only —
# no new AnalysisRun state is introduced (Phase 4 §1 explicitly keeps
# `queued -> running -> {complete, failed}` as the only persisted states).
PipelineStage = Literal[
    "queued",
    "applicability",
    "planning",
    "worker_execution",
    "evidence_fusion",
    "completeness_verification",
    "decision_engine",
    "recommendation_generation",
    "report_ready",
    "complete",
    "failed",
]

# Phase 4 §2's Work Unit state machine, verbatim.
WorkUnitState = Literal["assigned", "executing", "succeeded", "failed", "timed_out"]

_KEY_PREFIX = "analysis:progress:"
# Long enough to review a just-finished run's timeline in the UI; not a
# durable store (see module docstring) so an aggressive TTL is correct,
# not a shortcut.
_TTL_SECONDS = 60 * 60 * 6


def _client():
    import redis

    return redis.Redis.from_url(get_settings().redis_url, decode_responses=True)


def _key(run_id: uuid.UUID) -> str:
    return f"{_KEY_PREFIX}{run_id}"


def set_stage(run_id: uuid.UUID, stage: PipelineStage) -> None:
    """Records which of Phase 4 §1's conceptual execution steps an
    AnalysisRun is currently in. Never used as a substitute for the real
    AnalysisRun.status column — that remains queued/running/complete/failed
    (Phase 0 §3.11); this is strictly the finer-grained view §11 asks for."""
    client = _client()
    key = _key(run_id)
    client.hset(key, "stage", stage)
    client.expire(key, _TTL_SECONDS)
    logger.info("analysis.progress.stage", run_id=str(run_id), stage=stage)


def init_work_units(run_id: uuid.UUID, work_units: list[dict]) -> None:
    """Called once, immediately after Planning (Phase 3 §3) produces the
    Execution Plan, before any Work Unit is released for execution —
    records every Work Unit as `assigned` (Phase 4 §2)."""
    client = _client()
    key = _key(run_id)
    pipe = client.pipeline()
    for wu in work_units:
        record = {**wu, "state": "assigned"}
        pipe.hset(key, f"wu:{wu['work_unit_id']}", json.dumps(record))
    pipe.expire(key, _TTL_SECONDS)
    pipe.execute()
    logger.info("analysis.progress.plan", run_id=str(run_id), work_unit_count=len(work_units))


def set_work_unit_state(run_id: uuid.UUID, work_unit_id: str, state: WorkUnitState) -> None:
    """Phase 4 §2's monotonic state transition — callers only ever move a
    Work Unit forward through assigned -> executing -> a terminal state;
    this module does not itself enforce monotonicity (that discipline
    lives in the Celery task calling it, `analysis_decision/tasks.py`),
    it only records whatever transition it is told about."""
    client = _client()
    key = _key(run_id)
    field = f"wu:{work_unit_id}"
    raw = client.hget(key, field)
    record = json.loads(raw) if raw else {"work_unit_id": work_unit_id}
    record["state"] = state
    client.hset(key, field, json.dumps(record))
    logger.info("analysis.progress.work_unit", run_id=str(run_id), work_unit_id=work_unit_id, state=state)


def get_progress(run_id: uuid.UUID) -> dict:
    """AnalysisRun-level progress (Phase 4 §11 item 2): the current
    pipeline stage plus a coarse per-state count of Work Units, alongside
    the full per-Work-Unit detail (item 1) for drill-down."""
    client = _client()
    key = _key(run_id)
    raw = client.hgetall(key)
    stage = raw.pop("stage", "queued")
    work_units = [json.loads(v) for k, v in raw.items() if k.startswith("wu:")]
    counts: dict[str, int] = {}
    for wu in work_units:
        counts[wu["state"]] = counts.get(wu["state"], 0) + 1
    return {"stage": stage, "work_units": work_units, "counts": counts}

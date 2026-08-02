"""Genome compilation progress tracking — the same rationale and
mechanism as `analysis_decision/execution_progress.py`, sized for a much
simpler workflow: one job, no Work Units, no chord.

`POST /brands/{brand_id}/genomes` used to run `GenomeService.create_draft()`
synchronously in the HTTP request — one blocking LLM call per ingested
BrandHistory item, with no visibility and no timeout on the frontend
(observed live: this is what "Compiling Genome Draft" hanging actually
was). It now dispatches a Celery task and returns a `job_id` immediately;
this module is what the polled status endpoint reads.

Like `execution_progress.py`, this is transient Redis state, not a
second source of truth — the durable record of a compiled Genome is the
`BrandGenome`/`GenomeCategory`/`GenomeComponent`/`Assertion` rows
Postgres holds once the job reaches `complete`.
"""
from __future__ import annotations

import uuid
from typing import Literal

from src.config import get_settings
from src.logging import get_logger

logger = get_logger(__name__)

CompilationStage = Literal[
    "queued",
    "extracting_candidates",
    "consolidating",
    "assembling_draft",
    "complete",
    "failed",
]

_KEY_PREFIX = "genome:compile:progress:"
# Long enough to review a just-finished compile in the UI; not a durable
# store (see module docstring) so an aggressive TTL is correct.
_TTL_SECONDS = 60 * 60 * 6


def _client():
    import redis

    return redis.Redis.from_url(get_settings().redis_url, decode_responses=True)


def _key(job_id: uuid.UUID) -> str:
    return f"{_KEY_PREFIX}{job_id}"


def set_stage(
    job_id: uuid.UUID,
    stage: CompilationStage,
    *,
    error: str | None = None,
    genome_id: uuid.UUID | None = None,
) -> None:
    client = _client()
    key = _key(job_id)
    mapping: dict[str, str] = {"stage": stage}
    if error is not None:
        mapping["error"] = error
    if genome_id is not None:
        mapping["genome_id"] = str(genome_id)
    client.hset(key, mapping=mapping)
    client.expire(key, _TTL_SECONDS)
    logger.info("genome.compile.progress", job_id=str(job_id), stage=stage)


def get_progress(job_id: uuid.UUID) -> dict:
    client = _client()
    raw = client.hgetall(_key(job_id))
    if not raw:
        # Not yet observed (task hasn't run its first stage update) or
        # expired — `queued` is the correct default either way, never an
        # error: the caller can't distinguish "not started yet" from
        # "started a moment ago" without this being the safe default.
        return {"stage": "queued", "error": None, "genome_id": None}
    return {
        "stage": raw.get("stage", "queued"),
        "error": raw.get("error"),
        "genome_id": raw.get("genome_id"),
    }

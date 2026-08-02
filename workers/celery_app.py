"""Celery application (Technology Stack §9/§10) — the execution substrate
Phase 4 describes: Redis-backed task queue, per-worker-type routing, and
(via task decorators in `tasks.py`) bounded retry.

`tasks.py` holds the actual task implementations, importing business
logic from `src.analysis_decision.*` — this module only wires the app
and its routing, so `src.*` never has to import Celery at all.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Resolve the `backend/` package root under both layouts this app runs
# in: (a) locally from the repo root, where `workers/` and `backend/`
# are siblings, so `<repo_root>/backend` holds `src/`; and (b) inside
# the `worker`/`backend` Docker services, where the backend image's
# WORKDIR *is* `/app` (backend's own content copied straight in) and
# `workers/` is volume-mounted alongside it at `/app/workers` — there is
# no `/app/backend`, `src/` lives directly under the same root as this
# file's parent. Trying the first candidate and falling back to the
# second covers both without branching on an environment flag.
_repo_root = Path(__file__).resolve().parent.parent
for _candidate in (_repo_root / "backend", _repo_root):
    if (_candidate / "src").is_dir() and str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))
        break

from celery import Celery  # noqa: E402

from src.config import get_settings  # noqa: E402

settings = get_settings()

app = Celery("brandium", broker=settings.redis_url, backend=settings.redis_url, include=["workers.tasks"])

# Text/Image workers this pass actually implements route through two
# consolidated queues (see `analysis_decision/planning.py`'s docstring
# for the flagged five-role-to-two-module simplification this build
# makes). The finer five-queue split Phase 3 §4 names conceptually is
# left as documented reserved routing for when those roles split back
# into distinct code modules — not implemented against here, so not
# declared as live routes.
app.conf.task_routes = {
    "workers.tasks.dispatch_analysis_run": {"queue": "orchestration"},
    "workers.tasks.execute_work_unit_task": {"queue": "worker.text_image"},
    "workers.tasks.finalize_analysis_run": {"queue": "orchestration"},
    # Genome compilation's one blocking-LLM-calls job is orchestration-tier
    # work, not a content Worker — same queue as dispatch/finalize above.
    "workers.tasks.compile_genome_draft_task": {"queue": "orchestration"},
}
app.conf.task_serializer = "json"
app.conf.result_serializer = "json"
app.conf.accept_content = ["json"]
# Phase 4 §6: retries are bounded, never open-ended.
app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 1

"""Celery application skeleton (Technology Stack §9/§10).

Defines the app instance and the per-worker-type queue names only — no
task implementations. Per-modality workers (Visual, Verbal, Compliance &
Accessibility, Distinctiveness, Values & Mission) are Phase 3 (CLAUDE.md
§14 Milestones 3/6/7), explicitly out of scope for this milestone.

Each worker type gets its own dedicated queue so a load spike in one
never starves another (Technology Stack §10) — this is a routing/config
concern, enforced here by queue naming, not by application code.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from celery import Celery  # noqa: E402

from src.config import get_settings  # noqa: E402

settings = get_settings()

app = Celery("brandium", broker=settings.redis_url, backend=settings.redis_url)

app.conf.task_routes = {
    "workers.visual.*": {"queue": "worker.visual"},
    "workers.verbal.*": {"queue": "worker.verbal"},
    "workers.compliance_accessibility.*": {"queue": "worker.compliance_accessibility"},
    "workers.distinctiveness.*": {"queue": "worker.distinctiveness"},
    "workers.values_mission.*": {"queue": "worker.values_mission"},
}

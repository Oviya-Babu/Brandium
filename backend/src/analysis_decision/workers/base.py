"""Common Worker result shape (Phase 3 §4/§5, Phase 4 §2/§4).

**Hard boundary (CLAUDE.md §5.1):** a worker never returns a score,
verdict, or recommendation priority — this dataclass structurally has no
field for any of those; only Observation/Evidence-shaped data and the
Phase 3 §5 outcome taxonomy.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from src.analysis_decision.workers.judgment_schemas import AssertionJudgment


@dataclass(frozen=True)
class WorkerResult:
    succeeded: bool
    """Phase 4 §2 Work Unit outcome — False means every assigned Assertion
    gets a worker-failure outcome; True means judgments/no_signal below
    are authoritative per-Assertion."""

    judgments: list[AssertionJudgment] = field(default_factory=list)
    no_signal_assertion_ids: list[uuid.UUID] = field(default_factory=list)

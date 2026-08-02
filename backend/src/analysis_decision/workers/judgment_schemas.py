"""Shared Pydantic output schema for evidence-extraction worker LLM
calls (CLAUDE.md §5.1: a worker's output type is Observation -> Evidence
only — `alignment_indicator`/`confidence`, never a score, verdict, or
priority)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AssertionJudgment(BaseModel):
    assertion_id: str
    alignment_indicator: Literal["aligned", "partially_aligned", "misaligned"]
    confidence: float = Field(ge=0.0, le=1.0)
    observed_characteristic: str = Field(description="What specifically in the content supports this judgment.")


class WorkerJudgmentResult(BaseModel):
    judgments: list[AssertionJudgment] = Field(default_factory=list)
    no_signal_assertion_ids: list[str] = Field(
        default_factory=list,
        description="Assertion ids the content simply doesn't contain enough material to judge "
        "(Phase 3 §5 outcome 2 — attempted-no-signal, not a failure).",
    )

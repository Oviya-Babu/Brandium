"""Pydantic schemas constraining the Candidate Assertion Formation LLM
call (Phase 1 §5 step 2). Schema-first per CLAUDE.md §5.4 — the prompt is
built to satisfy this shape, not the other way around."""
from __future__ import annotations

from pydantic import BaseModel, Field


class CandidateAssertionLLM(BaseModel):
    category: str = Field(description="Must be one of the six fixed Genome Category names.")
    component: str = Field(description="Must be one of the platform-defined Component names for that Category.")
    assertion: str = Field(description="A single, atomic, evaluable claim about the brand's identity.")
    confidence: float = Field(ge=0.0, le=1.0)


class CandidateExtractionResult(BaseModel):
    candidates: list[CandidateAssertionLLM] = Field(default_factory=list)
